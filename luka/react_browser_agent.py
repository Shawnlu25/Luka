from luka.sandbox import SeleniumSandbox
from litellm import completion
import os

def simplify_web_elements(elements):
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

class ReActBrowserAgent:
    def __init__(self):
        self._sandbox = SeleniumSandbox()

        self._model = "gpt-4-turbo"
        self._openai_key = os.getenv("OPENAI_API_KEY")
    
    def reset(self):
        self._sandbox.reset()

    def _act_step(self):
        raise NotImplementedError
    
    def _reflect_step(self):
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