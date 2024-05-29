from selenium import webdriver
from selenium.common import exceptions as E
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import html2text
import atexit
import os

class SeleniumSandbox(object):
    def __init__(self, window_size=(1024, 768)):
        self._driver = webdriver.Chrome()

        self._window_size = window_size
        self._driver.set_window_size(window_size[0], window_size[1])

        self._elements = []
        atexit.register(self.cleanup)

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'get_repr.js'), "r") as f:
            self._repr_script = f.read()

    @property
    def current_url(self):
        return self._driver.current_url

    @property
    def scroll_progress(self):
        scroll_y = self._driver.execute_script("return window.scrollY;")
        scroll_height = self._driver.execute_script("return document.body.scrollHeight- window.innerHeight;")
        if scroll_height == 0:
            return 1.0, scroll_y, scroll_height
        percentage = scroll_y / scroll_height
        return percentage, scroll_y, scroll_height
    
    @property
    def page_elements(self):
        return [{k: e[k] for k in e if k != "element"} for e in self._elements]

    def reset(self):
        self._driver.quit()
        self._driver = webdriver.Chrome()
    
    def cleanup(self):
        self._driver.quit()

    def simplifed_dom(self):
        self.retrieve_elements()
        return self._simplify_web_elements(self.page_elements)

    def _simplify_web_elements(self, elements):
        simplified_dom = ""
        for e in elements:
            if e["tag"] in ["textinput", "select", "datepicker"]:
                text_attrs = ["text", "placeholder"]
                meta_attrs = ["type", "alt", "title", "aria_label", "value", "required", "checked", "min", "max"]
            elif e["tag"] == "text":
                text_attrs = ["text"]
                meta_attrs = []
            else:
                text_attrs = ["text", "aria_label", "alt"]
                meta_attrs = ["type", "value"]

            text = [x for x in filter(lambda x: x is not None and len(x) > 0, [e[attr] for attr in text_attrs])]
            text = text[0] if len(text) > 0 else None
            if text != None and text != e["text"]:
                text = "(" + text + ")"
            
            if e["children"] != None:
                text = "" if text == None else text
                text = self._simplify_web_elements(e["children"]) + text
            
            if text == None:
                text = ""
            
            meta_str = " ".join([attr + "=\"" + e[attr] + "\"" for attr in meta_attrs if e[attr] is not None])
            if len(meta_str) > 0:
                meta_str = " " + meta_str

            if e["tag"] == "text":
                simplified_dom += text
                continue
            if e["tag"] in ["img", "map", "area", "canvas", "figcaption", "figure", "picture", "svg"]:
                simplified_dom += f"![{e['tag']}]({text})"
                continue
            
            if text is None: 
                simplified_dom += f"<{e["tag"]} id=\"{e["id"]}\"{meta_str}/>\n"
            elif len(text.split("\n")) > 1:
                text = text.strip()
                simplified_dom += f"<{e["tag"]} id=\"{e["id"]}\"{meta_str}>\n{text}\n</{e["tag"]}>\n"
            else:
                simplified_dom += f"<{e["tag"]} id=\"{e["id"]}\"{meta_str}>{text}</{e["tag"]}>\n"
        
        return simplified_dom

    def retrieve_elements(self):
        elements = self._driver.execute_script(self._repr_script)

        idx = 0
        def assign_idx(elements):
            nonlocal idx
            for e in elements:
                e["id"] = idx
                idx += 1
                if e["children"] != None:
                    assign_idx(e["children"])

        assign_idx(elements)
        self._elements = elements
            

if __name__ == "__main__":
    sandbox = SeleniumSandbox()
    html_text_converter = html2text.HTML2Text()
    html_text_converter.ignore_links = False
    html_text_converter.ignore_images = True
    html_text_converter.images_to_alt = True
    html_text_converter.body_width = 0

    while True:
        print(sandbox.simplifed_dom())
        print(sandbox.current_url)
        print(sandbox.scroll_progress)
        command = input("> ")