from luka.tools.browser import TextualBrowserEnv
from luka.memory import FIFOConversationMemory
from luka.utils import Message

import os
import instructor
from instructor.exceptions import InstructorRetryException
from litellm import completion, encode
from termcolor import colored
from datetime import datetime

from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Union, Literal

SYSTEM_PROMPT = """
You are an agent controlling a browser. You are given:

	(1) an objective that you are trying to achieve
	(2) a simplified DOM of what's visible in the browser window (more on that below)
    (3) a history of previous interactions that lead you to the current state

The format of the browser content is highly simplified; it is a mix of pure text and html tags where all formatting elements are stripped.
Interactive elements such as links, inputs are represented like this:

    <link id="1">Some link</link>
    <textinput id="2" title="search">Placeholder</textinput>

The list of previous interactions is an interleave of your explanations, your commands, and the browser's responses, messages from the user, etc.
The browser's responses give you a high-level description or any errors occurred. e.g.:

    [2024-05-01 15:30:00] user:   Buy me a box of paperclips on Amazon
    [2024-05-01 15:35:00] agent:  First, I need to get to the Amazon website.
    [2024-05-01 15:35:30] agent:  VISIT www.amazon.com
    [2024-05-01 15:35:30] chrome: Success. 
                                  Current page: www.amazon.com
                                  Current scroll position: 0% (scroll-y=0, scroll-height=2094)

You can issue these commands to the browser (namespace="browser"):

$browser_actions

You can also issue the following commands control interaction with user (namespace="ui"):

$ui_actions


IMPORTANT: Based on your given objective, you must first provide a rationale in text for the next action, then issue any command that you beleive will get you closer to achieving the goal.
The rationale and command will be added to the history of interactions for your reference at future steps. 
The rationale should be kept concise, less than 30 words, and must be a natural continuation of previous interactions.


NOTE:
* You start on google.com, but you can visit any website directly. 
* Don't try to interact with elements that you cannot see.
* Avoid entering made-up information, especially when personal information is involved.
* If you encounter an exception, an error, an effectless command, or find yourself in a loop or dead-end, avoid repeating the same commands. Try something different to achieve the goal.


The current browser content, history of interactions, and objective follow. 
Reply with your rationale and issue the next command to the browser.
"""

USER_PROMPT = """
------------------
CURRENT BROWSER CONTENT:
$page_text
------------------
HISTORY:
$history
------------------
OBJECTIVE:
$objective
------------------
YOUR COMMAND:
"""


# TODO: functions for ui actions
UI_ACTIONS = {
    "complete": {
        "function": None,
        "description": "Indicate that the user's objective has been achieved and the agent's work is completed.",
        "params": [
            {
                "name": "message",
                "type": str,
                "required": True,
                "description": "Message to the user for any final comments."
            }
        ]
    },
    "yield": {
        "function": None,
        "description": "Indicate that the agent is yielding control to the user. E.g., when encountering a CAPTCHA, sign-in with username/email/password, entering payment information, etc. The goal is not breach user privacy and security.",
        "params": [
            {
                "name": "message",
                "type": str,
                "required": True,
                "description": "Message to the user to instruct user what to do."
            }
        ]
    }
}

def generate_help_text(actions):
    help_texts = []
    for k, v in sorted(actions.items(), key=lambda x: x[0]):
        help_text = f"{k.upper()}\n{v["description"]}\n"
        for param in v["params"]:
            help_text += f"    {param["name"]} ({param["type"].__name__}): [{str(param["required"])}] {param["description"]}\n"
        help_texts.append(help_text)
    
    return "\n".join(help_texts)

class _AgentReply(BaseModel):
    rationale: str = Field(..., description="The rationale behind the command")
    namespace: Literal["browser", "ui"] = Field(..., description="The namespace of the command must be one of 'browser' and 'ui', etc.")
    command: str = Field(..., description="The command to execute, e.g., click, visit, etc.")
    parameters: Dict[str, Union[str, int, float, bool]] = Field(...,description="Parameters for the command in key-value format. Pay attention to the type of value for each key. Supports str, int, float, and bool types.")

class BrowserAgent:
    def __init__(self, model="gpt-4o"):
        self._env = TextualBrowserEnv(timeout_s=15)
        self._model = model
        self._openai_key = os.getenv("OPENAI_API_KEY")
        self._client = instructor.from_litellm(completion)

        def litellm_tokenize(x):
            return encode(model=self._model, text=x)
        
        def litellm_summarize(msg_list):
            prompt = """
            You are given a history of previous interactions among an agent, a user, and a browser. The 
            agent is controlling a browser to achieve a given objective specified by the user. The agent
            can issue commands to the browser, and the browser can respond with high-level descriptions,
            errors, or other messages. The user specifies the objective at first and can provide additional
            information to help the agent along the way. 
            You goal is to summarize the given messages in three sentences. The reader of the message should
            be able to understand the objective, the actions the agent has attempted so far, and the current
            progress towards completing the objective. 
            Now, summarize the given messages in three sentences.
            """
            msg_str = "\n".join([str(msg) for msg in msg_list])
            response = completion(
                model = self._model,
                messages = [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": msg_str}
                ]
            )
            summary = response["choices"][0]["message"]["content"]
            return summary

        self._fifo_mem = FIFOConversationMemory(
            tokenize=litellm_tokenize, 
            summarize=litellm_summarize, 
            max_size=1024, 
            trigger_threshold=0.8, 
            target_threshold=0.5
        )

        self._obs = None
        self._info = None
        self.reset()

    def reset(self):
        self._obs, self._info = self._env.reset(options={"url": "https://www.google.com"})
        self._fifo_mem.reset()

    def run(self, objective):
        self._fifo_mem.insert(Message(role="user", content=objective, timestamp=datetime.now()))
        
        completed = False
        while not completed:
            print(self._obs["page_text"])
            print(self._obs["scroll_status"])
            print(self._obs["action_result"])

            # Construct system prompt
            system_prompt = SYSTEM_PROMPT.replace("$browser_actions", generate_help_text(self._info["actions"])).replace("$ui_actions", generate_help_text(UI_ACTIONS))
            
            # Construct user prompt
            user_prompt = USER_PROMPT.replace("$page_text", self._obs["page_text"]).replace("$history", str(self._fifo_mem)).replace("$objective", objective)
            
            reply = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
                response_model=_AgentReply,
            )

            msg = Message(role="agent", content=reply.rationale, timestamp=datetime.now())
            self._fifo_mem.insert(msg)
            print(msg)

            command_content = f"{reply.namespace}.{reply.command} {' '.join([f"{k}='{v}'" for k, v in reply.parameters.items()])}"
            msg = Message(role="agent", content=command_content, timestamp=datetime.now())
            self._fifo_mem.insert(msg)
            print(msg)

            if reply["namespace"] == "browser":
                self._obs, self._info = self._env.step({"command": reply.command.lower(), "args": reply.parameters})
                
            elif reply["namespace"] == "ui":
                pass
                


            



if __name__ == "__main__":
    agent = BrowserAgent(model="gpt-4o")
    while True:
        agent.reset()
        print("Please enter your objective (type `exit` to exit): ")
        objective = input("> ")
        if objective == "exit":
            break
        agent.run(objective)
        input("Press Enter to continue...")