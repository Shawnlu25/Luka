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
from typing import Dict, Union, Literal, Tuple, List

SYSTEM_PROMPT = """
You are an agent controlling a browser. You are given:

	(1) an objective that you are trying to achieve
	(2) a simplified DOM of what's visible in the browser window (more on that below)
    (3) a history of previous interactions that lead you to the current state

The format of the browser content is highly simplified; it is a mix of pure text and html tags where all formatting elements are stripped.
Scroll status is represented as a percentage of the maximum scroll position in both x and y directions at the end of the current viewport.
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
* Compare current status with the objective criteria. If you think you have achieved the goal, issue the "complete" command with a message to the user.


The current browser content, history of interactions, and objective follow. 
Reply with your rationale and issue the next command to the browser.
"""

USER_PROMPT = """
------------------
CURRENT BROWSER CONTENT:
$page_text

$url
Y-Scroll $percentage_y % ($scroll_y / $scroll_height)
X-Scroll $percentage_x % ($scroll_x / $scroll_width)
------------------
HISTORY:
$history
------------------
OBJECTIVE:
$objective
------------------
YOUR COMMAND:
You must provide your command through json with following format:
{
    "rationale": "",
    "namespace": "",
    "command": "",
    "parameters": {
        "param1": "",
    }
}
"""

def complete_task(message: str = "") -> Tuple[bool, List[Message]]:
    return True, [Message(role="agent", content=message, timestamp=datetime.now())]

def yield_control(message: str = "") -> Tuple[bool, List[Message]]:
    agent_msg = Message(role="agent", content=message, timestamp=datetime.now())
    print(colored("agent: ", "light_green", attrs=["bold"]), colored(message, "light_green"))
    feedback = input(colored("> ", "light_blue", attrs=["bold"]))
    return False, [agent_msg, Message(role="user", content=feedback, timestamp=datetime.now())]

def handle_ui_actions(self, action):
    command = action["command"].lower()
    parameters = action["parameters"]

    if command not in UI_ACTIONS:
        return False, [Message(role="agent", content=f"Error: Command `{command}` not supported.", timestamp=datetime.now())]
    
    parameters = {k:v for k,v in parameters.items() if k in [param["name"] for param in UI_ACTIONS[command]["params"]]}

    for param in UI_ACTIONS[command]["params"]:
        if param["required"] and param["name"] not in parameters:
            return False, [Message(role="agent", content=f"Error: Missing required argument `{param['name']}`.", timestamp=datetime.now())]
        if type(parameters[param["name"]]) != param["type"]:
            return False, [Message(role="agent", content=f"Error: Argument `{param['name']}` must be of type `{param['type']}`, but a `{type(parameters[param["name"]])}` is provided instead.", timestamp=datetime.now())]
        if param["name"] not in parameters:
            parameters[param["name"]] = None
    
    return UI_ACTIONS[command]["function"](**parameters)

# TODO: functions for ui actions
UI_ACTIONS = {
    "complete": {
        "function": complete_task,
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
        "function": yield_control,
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

    def _enrich_objective(self, objective):
        sys_prompt = """
        The user will give you an objective to achieve something with a browser. Your goal is to expand the objective to include the following information:
        * Completion criteria: What is the last webpage or the final state of the browser, which is what the user want to see.
        * Constraints: Are there any constraints or limitations that must be considered while achieving the objective?
        * Additional information: Any other information that might be useful for the agent to achieve the objective.
        Now, expand the given objective from the user to include the completion criteria, constraints, and additional information. The total length of the objective should be less than 300 characters.
        """
        class Objective(BaseModel):
            objective: str = Field(..., description="The objective given by the user.")
            criteria: str = Field(..., description="The completion criteria for the objective.")
            constraints: str = Field(..., description="The constraints or limitations that must be considered.")
            additional: str = Field(..., description="Any additional information that might be useful for the agent.")

        reply = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": sys_prompt,
                },
                {
                    "role": "user",
                    "content": objective,
                }
            ],
            response_model=Objective,
        )
        result = f"{reply.objective}\n\nCompletion Criteria: {reply.criteria}\nConstraints: {reply.constraints}\nAdditional Information: {reply.additional}"
        return result

    def run(self, objective):

        objective = self._enrich_objective(objective)
        print(objective)
        self._fifo_mem.insert(Message(role="user", content=objective, timestamp=datetime.now()))
        
        completed = False
        while not completed:
            # Construct system prompt
            system_prompt = SYSTEM_PROMPT.replace("$browser_actions", generate_help_text(self._info["actions"])).replace("$ui_actions", generate_help_text(UI_ACTIONS))
            
            # Construct user prompt
            user_prompt = USER_PROMPT.replace("$page_text", self._obs["page_text"]).replace("$history", str(self._fifo_mem)).replace("$objective", objective)
            
            user_prompt = user_prompt.replace("$percentage_y", str(self._obs["scroll_status"]["percentage_y"]*100.0)).replace("$scroll_y", str(self._obs["scroll_status"]["scroll_y"])).replace("$scroll_height", str(self._obs["scroll_status"]["scroll_height"]))

            user_prompt = user_prompt.replace("$percentage_x", str(self._obs["scroll_status"]["percentage_x"]*100.0)).replace("$scroll_x", str(self._obs["scroll_status"]["scroll_x"])).replace("$scroll_width", str(self._obs["scroll_status"]["scroll_width"]))

            user_prompt = user_prompt.replace("$url", self._obs["url"])

            try:
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
            except ValidationError as e:
                print(e.errors())
                exit(0)
            except InstructorRetryException as e:
                print(e)
                exit(0)

            msg = Message(role="agent", content=reply.rationale, timestamp=datetime.now())
            self._fifo_mem.insert(msg)
            print(msg)

            command_content = f"{reply.namespace}.{reply.command} {' '.join([f"{k}='{v}'" for k, v in reply.parameters.items()])}"
            msg = Message(role="agent", content=command_content, timestamp=datetime.now())
            self._fifo_mem.insert(msg)
            print(msg)

            if reply.namespace == "browser":
                self._obs, self._info = self._env.step({"command": reply.command.lower(), "parameters": reply.parameters})
                
                success, message = self._obs["action_result"]
                message = f"Action successful!" if success else message
                message = f"{message}\n current url: {self._obs['url']}\n"
                msg = Message(role="browser", content=message, timestamp=datetime.now())
                self._fifo_mem.insert(msg)
                print(msg)

            elif reply.namespace == "ui":
                completed, messages = handle_ui_actions(self, {"command": reply.command.lower(), "parameters": reply.parameters})
                self._obs, self._info = self._env.step({"command": "pass", "parameters": {}})
                for msg in messages:
                    self._fifo_mem.insert(msg)
                    print(msg)
            else:
                self._fifo_mem.insert(Message(role="agent", content=f"Error: Invalid namespace {reply["namespace"]}", timestamp=datetime.now()))


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