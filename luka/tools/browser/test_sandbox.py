from selenium import webdriver
from selenium.common import exceptions as E
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import html2text
import atexit
import validators
import os
import re

class SeleniumSandbox(object):
    def __init__(self, window_size=(1024, 768)):
        self._driver = webdriver.Chrome()

        self._window_size = window_size
        self._driver.set_window_size(window_size[0], window_size[1])

        self._elements = []
        atexit.register(self.cleanup)

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'retrieve_elements.js'), "r") as f:
            self._js_script = f.read()
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dump_aria.js'), "r") as f:
            self._aria_script = f.read()
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

    def simplify_web_elements(self):
        # TODO: turn retrieve_elements into a decorator
        self.retrieve_elements_3()
        
        elements = self.page_elements
        simplified_dom = ""
        for e in elements:
            if e["tag"] == "input":
                text_attrs = ["text", "placeholder"]
                meta_attrs = ["type", "alt", "title", "aria_label", "value"]
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
            if text == None:
                text = " "
            
            meta_str = " ".join([attr + "=\"" + e[attr] + "\"" for attr in meta_attrs if e[attr] is not None])
            if len(meta_str) > 0:
                meta_str = " " + meta_str

            if e["tag"] == "text":
                simplified_dom += text
                continue

            #if e["tag"] == "link":
            #    # if text has [] or () we need to escape them
            #    if "[" in text or "]" in text or "(" in text or ")" in text:
            #        text = re.escape(text)
            #    simplified_dom += f"[{text}](id=\"{e["id"]}\"{meta_str})"
            #    continue
            
            if text is None: 
                simplified_dom += f"<{e["tag"]} id=\"{e["id"]}\"{meta_str}/>\n"
            elif len(text.split("\n")) > 1:
                text = text.strip()
                simplified_dom += f"<{e["tag"]} id=\"{e["id"]}\"{meta_str}>\n{text}\n</{e["tag"]}>\n"
            else:
                simplified_dom += f"<{e["tag"]} id=\"{e["id"]}\"{meta_str}>{text}</{e["tag"]}>\n"
        return simplified_dom

    
    
    def get_text_content(self):
        script = """
            return Array.from(document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, div, label'))
                .filter(el => 
                    Array.from(el.childNodes).some(node => node.nodeType === Node.TEXT_NODE && node.textContent.trim() !== '')
                ).map(
                    el => {
                        const textContent = Array.from(el.childNodes).filter(node => node.nodeType === Node.TEXT_NODE).map(node => node.nodeValue.trim()).join(' ');
                        return {
                            element: el,
                            tag: "text",
                            text: textContent
                        }
                    }
                );
        """
        elements = self._driver.execute_script(script)
        texts = [e["text"] for e in elements]
        return texts

    def retrieve_elements_2(self):
        elements = self._driver.execute_script(self._js_script)
        for idx, e in enumerate(elements):
            e["id"] = idx
        self._elements = elements

    def retrieve_elements_3(self):
        elements = self._driver.execute_script(self._repr_script)
        for idx, e in enumerate(elements):
            if e["tag"] != "text":
                e["id"] = idx
            print(e["tag"], repr(e["text"]))
        self._elements = elements
            

if __name__ == "__main__":
    sandbox = SeleniumSandbox()
    html_text_converter = html2text.HTML2Text()
    html_text_converter.ignore_links = False
    html_text_converter.ignore_images = True
    html_text_converter.images_to_alt = True
    html_text_converter.body_width = 0

    while True:
        print(sandbox.simplify_web_elements())
        print(sandbox.current_url)
        print(sandbox.scroll_progress)
        command = input("> ")