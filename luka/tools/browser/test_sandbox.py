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
        self.retrieve_elements_2()
        elements = self.page_elements
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

    def dump_aria(self):
        result = self._driver.execute_script(self._aria_script)
        return result

    def retrieve_elements(self):
        script = """
            // Get clickable elements
            var clickableElements = Array.from(document.querySelectorAll('a, button, input[type=button], input[type=submit], [role="button"]'))
                .filter(el => {
                    const rect = el.getBoundingClientRect();
                    const centerX = rect.left + rect.width / 2;
                    const centerY = rect.top + rect.height / 2;
                    return centerX >= 0 && centerX <= window.innerWidth && centerY >= 0 && centerY <= window.innerHeight && rect.width > 0 && rect.height > 0;
                    }
                ).map(
                    el => ({
                        element: el,
                        tag: "link",
                        text: el.innerText.trim()
                    })
                );
            
            // Get text input elements
            const textareas = Array.from(document.querySelectorAll('textarea'));
            const textInputs = Array.from(document.querySelectorAll(
                'input[type="text"], input[type="password"], input[type="email"], input[type="search"], input[type="number"], input[type="tel"], input[type="url"]'
            ));
            var textInputElements = textareas.concat(textInputs)
                .filter(el => {
                    const rect = el.getBoundingClientRect();
                    const centerX = rect.left + rect.width / 2;
                    const centerY = rect.top + rect.height / 2;
                    return centerX >= 0 && centerX <= window.innerWidth && centerY >= 0 && centerY <= window.innerHeight && rect.width > 0 && rect.height > 0;
                    }
                ).map(
                    el => ({
                        element: el,
                        tag: "input",
                        text: el.innerText.trim()
                    })
                );
            
            // Get readable elements
            var readableElements = Array.from(document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, div, label'))
                .filter(el => {
                    const rect = el.getBoundingClientRect();
                    const centerX = rect.left + rect.width / 2;
                    const centerY = rect.top + rect.height / 2;
                    return centerX >= 0 && centerX <= window.innerWidth && centerY >= 0 && centerY <= window.innerHeight && rect.width > 0 && rect.height > 0 && el.textContent.trim().length > 0;
                })
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
            
            return clickableElements.concat(textInputElements).concat(readableElements)
                .map(el => ({
                    element: el.element,
                    tag: el.tag,
                    text: el.text,
                    x: el.element.getBoundingClientRect().x,
                    y: el.element.getBoundingClientRect().y,
                    type: el.element.getAttribute('type'),
                    placeholder: el.element.getAttribute('placeholder'),
                    aria_label: el.element.getAttribute('aria-label'),
                    title: el.element.getAttribute('title'),
                    alt: el.element.getAttribute('alt')
                }));
        """
        elements = self._driver.execute_script(script)
        
        # sort according to y then x element position
        elements = sorted(elements, key=lambda e: (e["y"], e["x"]))
        for idx, e in enumerate(elements):
            e["id"] = idx
        self._elements = elements
            

if __name__ == "__main__":
    sandbox = SeleniumSandbox()
    html_text_converter = html2text.HTML2Text()
    html_text_converter.ignore_links = False
    html_text_converter.ignore_images = True
    html_text_converter.images_to_alt = True
    html_text_converter.body_width = 0

    while True:
        sandbox.retrieve_elements()
        print(sandbox.simplify_web_elements())
        print(sandbox.dump_aria())
        #print(html_text_converter.handle(sandbox._driver.page_source))
        #for x in sandbox.page_elements:
        #    print(x)
        print(sandbox.current_url)
        print(sandbox.scroll_progress)
        command = input("> ")