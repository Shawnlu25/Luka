from pydantic import BaseModel, Field

from litellm import completion, encode, decode
import instructor
import os

from luka.sandbox import SeleniumSandbox
from luka.memory import FIFOConversationMemory

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
    COMPLETE - indicate that you have completed the objective

Based on your given objective, issue whatever command you believe will get you closest to 
achieving your goal. Your format consists of one rationale in text, followed by a command. The 
details of the format will be provided later. The rationale and command will be added to the 
history of interactions for your reference at future steps.
    
You start on about:blank, but you can visit any site directly. Usually you should start on 
google.com and search from there. Don't try to interact with elements that you can't see. If you 
encounter an error or an effectless command, avoid repeating the same command, try something else 
to achieve the goal. 

Here are some examples:

EXAMPLE 1:
==================================================
CURRENT BROWSER CONTENT:
<link id=1>About</link>
<link id=2>Store</link>
<link id=3>Gmail</link>
<link id=4>Images</link>
<link id=5>(Google apps)</link>
<link id=6>Sign in</link>
<img id=7 alt="(Google)"/>
<input id=8 alt="Search"></input>
<link id=9>(Search by voice)</button>
<link id=10>(Google Search)</button>
<link id=11>(I'm Feeling Lucky)</button>
<link id=12>Advertising</link>
<link id=13>Business</link>
<link id=14>How Search works</link>
<link id=15>Carbon neutral since 2007</link>
<link id=16>Privacy</link>
<link id=17>Terms</link>
<text id=18>Settings</text>
------------------
HISTORY: 
[2024-05-01 15:30:00] user:   Find a 2 bedroom house for sale in Anchorage AK for under $750k
[2024-05-01 15:30:00] agent:  First, I need to get to the Google website.
[2024-05-01 15:30:30] agent:  VISIT www.google.com
[2024-05-01 15:30:30] chrome: Success. 
                              Current page: www.google.com
                              Current scroll position: 0% (scroll-y=0, scroll-height=2094)
------------------
OBJECTIVE:
Find a 2 bedroom house for sale in Anchorage AK for under $750k
------------------
YOUR COMMAND: 
TYPESUBMIT 8 anchorage redfin
==================================================

The current browser content, history of interactions, and objective follow. 
Reply with your next command to the browser.
"""

class ReActBrowserAgent:

    class _AgentReply(BaseModel):
        rationale: str = Field(..., description="The rationale behind the command")
        command: str = Field(..., description="The command to execute")

    def __init__(self):
        self._sandbox = SeleniumSandbox()

        self._model = "gpt-4-turbo"
        self._openai_key = os.getenv("OPENAI_API_KEY")
        
        def litellm_tokenize(x):
            return encode(model=self._model, text=x)
        
        def litellm_summarize(msg_list):
            #TODO: Implement a summarization function
            return ""
        
        self._fifo_mem = FIFOConversationMemory(
            tokenize=litellm_tokenize, 
            summarize=litellm_summarize, 
            max_size=512, 
            trigger_threshold=0.8, 
            target_threshold=0.5
        )
        
    
    def reset(self):
        self._sandbox.reset()

    def simplify_web_elements(self, elements):
        simplified_dom = ""
        for e in elements:
            if e["tag"] == "input":
                text_attrs = ["text", "placeholder"]
                meta_attrs = ["type", "alt", "title", "aria_label"]
            elif e["tag"] == "link":
                text_attrs = ["text", "aria_label", "title"]
                meta_attrs = ["type", "alt"]
            else:
                text_attrs = ["text"]
                meta_attrs = []

            text = [x for x in filter(lambda x: x is not None and len(x) > 0, [e[attr] for attr in text_attrs])]
            text = text[0] if len(text) > 0 else None
            if text != None and text != e["text"]:
                text = "(" + text + ")"

            meta_str = " ".join([attr + "=\"" + e[attr] + "\"" for attr in meta_attrs if e[attr] is not None])
            if len(meta_str) > 0:
                meta_str = " " + meta_str

            if text is None: 
                simplified_dom += f"<{e["tag"]} id=\"{e["id"]}\"{meta_str}/>\n"
            else:
                simplified_dom += f"<{e["tag"]} id=\"{e["id"]}\"{meta_str}>{text}</{e["tag"]}>\n"
            return simplified_dom



    def _act(self):
        raise NotImplementedError
    
    def run(self, objective, bg_info=None):

        pass


if __name__ == "__main__":
    agent = ReActBrowserAgent()
    while True:
        agent.reset()
        print("Please enter your objective (type `exit` to exit): ")
        objective = input("> ")
        if objective == "exit":
            break
        agent.run(objective)
        input("Press enter to continue...")
    