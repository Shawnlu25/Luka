from pydantic import BaseModel, Field
from typing import Tuple, Optional

from litellm import completion, encode
import instructor
import os
from datetime import datetime

from luka.envs import SeleniumSandbox
from luka.memory import FIFOConversationMemory
from luka.utils import Message


SYSTEM_PROMPT = """
You are an agent controlling a browser. You are given:

	(1) an objective that you are trying to achieve
	(2) a simplified DOM of what's visible in the browser window (more on that below)
    (3) a history of previous interactions that lead you to the current state

The format of the browser content is highly simplified; all formatting elements are stripped.
Interactive elements such as links, inputs are represented like this:

    <link id=1>text</link>
    <input id=2>text</input>

The list of previous interactions is an interleave of your explanations, your commands, and 
the browser's responses. It might also contain sporadic messages from the user. The browser's 
responses never contain the actual DOM, but only give you a high-level description or any 
errors occurred. e.g.:

    [2024-05-01 15:30:00] user:   Buy me a box of clips on Amazon
    [2024-05-01 15:35:00] agent:  First, I need to get to the Amazon website.
    [2024-05-01 15:35:30] agent:  VISIT www.amazon.com
    [2024-05-01 15:35:30] chrome: Success. 
                                  Current page: www.amazon.com
                                  Current scroll position: 0% (scroll-y=0, scroll-height=2094)

You can issue these commands:

    VISIT <URL> - visit a new URL
	SUP - scroll up one page
	SDOWN - scroll down one page
	CLICK <ID> - click on a given element. You can only click on links!
	TYPE <ID> <TEXT> - type the specified text into the input with id
	TYPESUBMIT <ID> <TEXT> - same as TYPE above, except then it presses ENTER to submit the form
    BACK - go back to the previous page
    FORWARD - go forward to the next page
    COMPLETE <TEXT> - indicate that you have completed the objective and provide any comments in <TEXT>

IMPORTANT: Based on your given objective, you must first provide a rationale in text for the next
action, then issue any command that you beleive will get you closer to achieving the goal. The rationale 
and command will be added to the history of interactions for your reference at future steps. The 
rationale should be kept concise, less than 30 words, and must be a natural continuation of previous 
interactions.

Note: 
* You start on about:blank, but you can visit any site directly. Usually you should start on 
  google.com and search from there. Don't try to interact with elements that you can't see. 
* You must make appropriate adjustment if the user provides additional information, changes the objective,
or specifies a concrete way of achieving the goal.
* If you believe you have reached the objective, issue a `COMPLETE` command with any additional comments.
* If you encounter an exception, an effectless command, or find yourself in a loop, avoid repeating the 
same command and try something else to achieve the goal.

The current browser content, history of interactions, and objective follow. 
Reply with your rationale and issue the next command to the browser.
"""

USER_PROMPT = """
------------------
CURRENT BROWSER CONTENT:
$dom
------------------
HISTORY:
$history
------------------
OBJECTIVE:
$objective
------------------
YOUR COMMAND:
"""

class _AgentReply(BaseModel):
    rationale: str = Field(..., description="The rationale behind the command")
    command: str = Field(..., description="The command to execute")


class ReActBrowserAgent:

    def __init__(self):
        self._sandbox = SeleniumSandbox()

        self._model = "gpt-4-turbo"
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
    
    def reset(self):
        self._sandbox.reset()
        self._fifo_mem.reset()

    def _act(self, command:str) -> Tuple[bool, Optional[str]]:
        """
        Execute a command on the browser sandbox
        Returns a tuple of (completed, msg)
        """
        command = command.split(" ")
        exception_msg = None

        if command[0] == "COMPLETE":
            return True, " ".join(command[1:])
        elif command[0] == "VISIT":
            try:
                url = command[1]
                self._sandbox.visit(url)
            except Exception as e:
                exception_msg = str(e)
        elif command[0] == "SUP":
            self._sandbox.scroll(scroll_down=False)
        elif command[0] == "SDOWN":
            self._sandbox.scroll()
        elif command[0] == "CLICK":
            try:
                index = int(command[1])
                self._sandbox.click(index)
            except Exception as e:
                exception_msg = str(e)
        elif command[0] == "TYPE":
            try:
                index = int(command[1])
                text = " ".join(command[2:])
                self._sandbox.type(index, text)
            except Exception as e:
                exception_msg = str(e)
        elif command[0] == "TYPESUBMIT":
            try:
                index = int(command[1])
                text = " ".join(command[2:])
                self._sandbox.type(index, text, enter=True)
            except Exception as e:
                exception_msg = str(e)
        elif command[0] == "BACK":
            self._sandbox.go_back()
        elif command == "FORWARD":
            self._sandbox.go_forward()
        else:
            exception_msg = "Invalid command."
        
        current_url = self._sandbox.current_url
        scroll_percentage, scroll_y, scroll_height = self._sandbox.scroll_progress
        scroll_percentage = "{:3.2f}".format(scroll_percentage * 100)
        info_str = f"Current url: {current_url}\nCurrent scroll position: {scroll_percentage}% (scroll-y={scroll_y}, scroll-height={scroll_height})"

        if exception_msg is not None:
            return False, f"Action unsuccessful, an exception occured: {exception_msg}\n" + info_str
        return False, "Action successful!\n" + info_str
    
    def run(self, objective, bg_info=None):
        self._fifo_mem.insert(Message(role="user", content=objective, timestamp=datetime.now()))
        completed = False

        while not completed:
            dom = self._sandbox.simplify_web_elements()
            if dom is None:
                dom = "[empty page]"
            history = str(self._fifo_mem)
            user_prompt = USER_PROMPT.replace("$dom", dom).replace("$history", history).replace("$objective", objective)

            reply = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
                response_model=_AgentReply,
            )
            # TODO: replace print statements with logging
            msg = Message(role="agent", content=reply.rationale, timestamp=datetime.now())
            self._fifo_mem.insert(msg)
            print(msg)

            msg = Message(role="agent", content=reply.command, timestamp=datetime.now())
            self._fifo_mem.insert(msg)
            print(msg)

            completed, browser_msg = self._act(reply.command)
            if not completed:
                msg = Message(role="chrome", content=browser_msg, timestamp=datetime.now())
                self._fifo_mem.insert(msg)
                print(msg)
            else:
                msg = Message(role="agent", content=browser_msg, timestamp=datetime.now())
                self._fifo_mem.insert(msg)
                print(msg)

    