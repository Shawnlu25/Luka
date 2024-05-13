from selenium import webdriver
from selenium.common import exceptions as E
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import atexit
import validators

class SeleniumSandbox(object):
    def __init__(self, window_size=(1024, 768)):
        self._driver = webdriver.Chrome()

        self._window_size = window_size
        self._driver.set_window_size(window_size[0], window_size[1])

        self._elements = []
        atexit.register(self.cleanup)

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

    def click(self, index: int):
        if index >= len(self._elements):
            raise ValueError("error: index out of range")
        if self._elements[index]["tag"] != "link":
            raise ValueError("error: element is not clickable")
        
        remove_target_attr_script = """
            var element = arguments[0];
            element.removeAttribute('target');
        """
        self._driver.execute_script(remove_target_attr_script, self._elements[index]["element"])

        try:
            self._elements[index]["element"].click()
        except Exception as e:
            raise e

    def type(self, index: int, text: str, enter: bool=False, clear: bool=True):
        if index >= len(self._elements):
            raise ValueError("error: index out of range")
        if self._elements[index]["tag"] != "input":
            raise ValueError("error: element is not textable")
        if clear:
            self._elements[index]["element"].clear()
        
        self._elements[index]["element"].send_keys(text)
        
        if enter:
            self._elements[index]["element"].send_keys(Keys.RETURN)

    def visit(self, url: str):
        url = url if url.startswith("http") else "http://" + url
        if not validators.url(url):
            raise ValueError("error: visiting invalid URL")

        self._driver.get(url)
    
    def go_back(self):
        self._driver.execute_script("window.history.go(-1)")
    
    def go_forward(self):
        self._driver.execute_script("window.history.go(1)")

    def scroll(self, scroll_down: bool=True, duration: int=1000):
        if scroll_down:
            scroll_direction = "+"
        else:
            scroll_direction = "-"

        completion_signal = "scroll_complete"
        
        ease_out_scroll_script = f"""
        function smoothScroll(duration) {{
            var startY = window.pageYOffset;
            var endY = startY {scroll_direction} window.innerHeight;
            var maxY = document.body.scrollHeight;

            if (endY > maxY) {{
                endY = maxY;
            }} else if (endY < 0) {{
                endY = 0;
            }}

            var diff = endY - startY;
            var startTime = null;

            function step(time) {{
                if (startTime === null) startTime = time;
                var t = time - startTime;
                var percent = Math.min(1, t / duration);
                var easing = 1 - Math.pow(1 - percent, 3);  
                window.scrollTo(0, startY + diff * easing);
                if (t < duration) {{
                    window.requestAnimationFrame(step);
                }} else {{
                    document.body.setAttribute('data-{completion_signal}', 'true');
                }}
            }}
            window.requestAnimationFrame(step);
        }}
        document.body.setAttribute('data-{completion_signal}', 'false');
        smoothScroll({duration});
        """
        def check_scroll_complete(driver):
            element = driver.find_element(By.TAG_NAME, "body")
            return element.get_attribute(f"data-{completion_signal}") == "true"

        self._driver.execute_script(ease_out_scroll_script)
        WebDriverWait(self._driver, duration / 1000 + 2).until(
            check_scroll_complete
        )

    def _apply_overlays_by_elements(self, elements, ids, rgba_color=(255, 255, 0, 0.5)):
        rgba_color_str = f"rgba({int(rgba_color[0])}, {int(rgba_color[1])}, {int(rgba_color[2])}, {float(rgba_color[3])})"
        overlay_script = f"""
        var els = arguments[0];
        var ids = arguments[1];
        if (!window.clickableOverlays) {{
            window.clickableOverlays = [];
        }}
        els.forEach(function(el, index) {{
            var overlay = document.createElement('div');
            overlay.style.position = 'absolute';
            overlay.style.left = (el.getBoundingClientRect().left + window.scrollX) + 'px';
            overlay.style.top = (el.getBoundingClientRect().top + window.scrollY) + 'px';
            overlay.style.width = el.getBoundingClientRect().width + 'px';
            overlay.style.height = el.getBoundingClientRect().height + 'px';
            overlay.style.backgroundColor = '{rgba_color_str}'; 
            overlay.style.color = 'black';
            overlay.style.zIndex = '10000';
            overlay.style.pointerEvents = 'none'; // Allows clicks to pass through
            overlay.textContent = ids[index]; // Sequence number
            overlay.style.textAlign = 'center';
            overlay.style.lineHeight = el.getBoundingClientRect().height + 'px';
            document.body.appendChild(overlay);
            window.clickableOverlays.push(overlay);
        }});
        """
        self._driver.execute_script(overlay_script, elements, ids)

    def reset_overlays(self):
        self._driver.execute_script("""
            if (window.clickableOverlays && window.clickableOverlays.length > 0) {
                window.clickableOverlays.forEach(function(overlay) {
                    overlay.style.display = 'none';
                });
            }
            window.clickableOverlays = [];
        """)

    def apply_overlays(self):
        self._apply_overlays_by_elements([e["element"] for e in self._elements if e["tag"] == "link"], [e["id"] for e in self._elements if e["tag"] == "link"], rgba_color=(255, 255, 0, 0.5))
        self._apply_overlays_by_elements([e["element"] for e in self._elements if e["tag"] == "input"], [e["id"] for e in self._elements if e["tag"] == "input"], rgba_color=(255, 0, 255, 0.5))
        self._apply_overlays_by_elements([e["element"] for e in self._elements if e["tag"] == "text"], [e["id"] for e in self._elements if e["tag"] == "text"], rgba_color=(0, 255, 255, 0.5))
    
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
    sandbox.visit("https://google.com")
    
    sandbox.reset_overlays()
    sandbox.retrieve_elements()
    sandbox.apply_overlays()
    print(sandbox.current_url)
    print(sandbox.scroll_progress)

    while True:
        command = input("> ")
        
        if command.startswith("v"):
            try:
                url = command.split(" ")[1]
                sandbox.visit(url)
            except Exception as e:
                print(e)

        elif command == "b":
            sandbox.go_back()

        elif command == "f":
            sandbox.go_forward()

        elif command.startswith("c"):
            try:
                index = int(command.split(" ")[1])
                sandbox.click(index)
            except Exception as e:
                print(e)

        elif command.startswith("t"):
            try:
                cmd = command.split(" ")[0]
                index = int(command.split(" ")[1])
                text = " ".join(command.split(" ")[2:])
                if cmd == "t":
                    sandbox.type(index, text)
                elif cmd == "te":
                    sandbox.type(index, text, enter=True)
            except Exception as e:
                print(e)
        elif command.startswith("j"):
            sandbox.reset_overlays()
            print(sandbox.get_text_content())

        elif command == "u":
            sandbox.scroll(scroll_down=False)

        else:
            sandbox.scroll()

        sandbox.reset_overlays()
        sandbox.retrieve_elements()
        sandbox.apply_overlays()
        print(sandbox.current_url)
        print(sandbox.scroll_progress)