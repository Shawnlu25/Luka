from luka.sandbox import SeleniumSandbox
from litellm import completion
import os

SYSTEM_PROMPT = """
You are an agent controlling a browser. You are given:

	(1) an objective that you are trying to achieve
	(2) the URL of your current web page
    (3) the scroll position of current web page in percentage 
	(4) a simplified text description of what's visible in the browser window (more on that below)
    (5) a history of previous commands that lead you to the current state of the browser

You can issue these commands:
    VISIT <URL> - visit a new URL
	SCROLL UP - scroll up one page
	SCROLL DOWN - scroll down one page
	CLICK <ID> - click on a given element. You can only click on links!
	TYPE <ID> <TEXT> - type the specified text into the input with id
	TYPESUBMIT <ID> <TEXT> - same as TYPE above, except then it presses ENTER to submit the form
    BACK - go back to the previous page
    FORWARD - go forward to the next page
    COMPLETE <TEXT> - indicate that you have completed the objective, and provide any comments you have in <TEXT>

The format of the browser content is highly simplified; all formatting elements are stripped.
Interactive elements such as links, inputs are represented like this:

		<link id=1>text</link>
		<input id=3>text</input>

Based on your given objective, issue whatever command you believe will get you closest to achieving your goal.
You always start on Google; you should submit a search query to Google that will take you to the best page for
achieving your objective. And then interact with that page to achieve your objective.

Don't try to interact with elements that you can't see.

Here are some examples:

EXAMPLE 1:
==================================================
CURRENT BROWSER CONTENT:
------------------
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
OBJECTIVE: Find a 2 bedroom house for sale in Anchorage AK for under $750k
CURRENT URL: https://www.google.com/
YOUR COMMAND: 
TYPESUBMIT 8 anchorage redfin
==================================================

The current browser content, objective, and current URL follow. Reply with your next command to the browser.
"""

USER_PROMPT = """
HISTORY: 
------------------
$history
------------------

CURRENT BROWSER CONTENT:
------------------
$browser_content
------------------

OBJECTIVE: $objective
CURRENT URL: $url
CURRENT SCROLL POSITION: $scroll_position
YOUR COMMAND:
"""



class BrowserAgent:
    def __init__(self):
        self._sandbox = SeleniumSandbox()
        self._history = []

        self._model = "gpt-4-turbo"
        self._openai_key = os.getenv("OPENAI_API_KEY")
    
    def reset(self):
        self._history = []
        self._sandbox.visit("https://www.google.com/")

    def _get_history(self):
        history = ""
        for idx, item in enumerate(self._history):
            history += f"{idx + 1}. \n"
            history += f"URL: {item['url']}\n"
            history += f"COMMAND: {item['command']}\n"
            if item["error"]:
                history += f"ERROR: {item['error']}\n"
        return history

    def _get_sandbox_state(self):
        elements = self._sandbox.page_elements
        browser_content = ""
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
                browser_content += f"<{e["tag"]} id=\"{e["id"]}\"{meta_str}/>\n"
            else:
                browser_content += f"<{e["tag"]} id=\"{e["id"]}\"{meta_str}>{text}</{e["tag"]}>\n"
            
        return {
            "browser_content": browser_content,
            "url": self._sandbox.current_url,
            "scroll_position": "{:3.2f}".format(self._sandbox.scroll_progress * 100),
        }

    def _act(self, command):
        prev_url = self._sandbox.current_url
        exception = None
        completed = None

        command = command.split(" ")
        if command[0] == "COMPLETE":
            if len(command) == 1:
                completed = ""
            else:
                completed = " ".join(command[1:])
        elif command[0] == "VISIT":
            try:
                url = command[1]
                self._sandbox.visit(url)
            except Exception as e:
                exception = e
        elif command[0] == "SCROLL":
            if len(command) == 1:
                exception = "Please specify a direction"
            elif command[1] == "UP":
                self._sandbox.scroll(scroll_down=False)
            else:
                self._sandbox.scroll()
        elif command[0] == "CLICK":
            try:
                index = int(command[1])
                self._sandbox.click(index)
            except Exception as e:
                exception = e
        elif command[0] == "TYPE":
            try:
                index = int(command[1])
                text = " ".join(command[2:])
                self._sandbox.type(index, text)
            except Exception as e:
                exception = e
        elif command[0] == "TYPESUBMIT":
            try:
                index = int(command[1])
                text = " ".join(command[2:])
                self._sandbox.type(index, text, enter=True)
            except Exception as e:
                exception = e
        
        elif command[0] == "BACK":
            self._sandbox.go_back()
        elif command == "f":
            self._sandbox.go_forward()
        else:
            exception = "Invalid command"

        self._history.append({
            "command": command,
            "url": prev_url,
            "error": exception,
            "completed": completed,
        })
        

    def run(self, objective):
        completed = False
        while not completed:
            self._sandbox.retrieve_elements()
            state = self._get_sandbox_state()

            # Construct user prompt
            user_prompt = USER_PROMPT
            user_prompt = user_prompt.replace("$browser_content", state["browser_content"])
            user_prompt = user_prompt.replace("$objective", objective)
            user_prompt = user_prompt.replace("$url", state["url"])
            user_prompt = user_prompt.replace("$scroll_position", state["scroll_position"])
            user_prompt = user_prompt.replace("$history", self._get_history())

            # Get command from llm
            response = completion(
                model=self._model,
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ]
            )
            command = response["choices"][0]["message"]["content"]
            # Act on command
            self._act(command)

            if self._history[-1]["completed"]:
                print("Objective completed!")
                print(self._history[-1]["completed"])
                completed = True

    
if __name__ == "__main__":
    agent = BrowserAgent()
    while True:
        agent.reset()
        print("Please enter your objective (type `exit` to exit): ")
        objective = input("> ")
        if objective == "exit":
            break
        agent.run(objective)
        input("Press enter to continue...")