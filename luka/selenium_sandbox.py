from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import validators

class SeleniumSandbox(object):
    def __init__(self, window_size=(1024, 768)):
        self.driver = webdriver.Chrome()

        self.window_size = window_size
        self.driver.set_window_size(window_size[0], window_size[1])
        self.elements_clickable = {}

    def get_clickable_items_in_viewport(self):
        find_items_script = """
        return Array.from(document.querySelectorAll('a, button, input[type=button], input[type=submit], [role="button"]'))
            .filter(el => {
                const rect = el.getBoundingClientRect();
                const isVisible = rect.top >= 0 && rect.bottom <= window.innerHeight && rect.left >= 0 && rect.right <= window.innerWidth && rect.height > 0 && rect.width > 0;
                const isNotOccluded = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2) === el;
                return isVisible && isNotOccluded;
                }
            ); 
        """
        return self.driver.execute_script(find_items_script)

    @staticmethod
    def retrieve_clickable_elements(func):
        def wrapper(*args, **kwargs):
            find_items_script = """
                return Array.from(document.querySelectorAll('a, button, input[type=button], input[type=submit], [role="button"]'))
                    .filter(el => {
                        const rect = el.getBoundingClientRect();
                        const isVisible = (rect.top >= 0 || rect.bottom <= window.innerHeight) && (rect.left >= 0 || rect.right <= window.innerWidth) && rect.height > 0 && rect.width > 0;
                        const isNotOccluded = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2) === el;
                        return isVisible && isNotOccluded;
                        }
                    ); 
                """
            args[0].elements_clickable = args[0].driver.execute_script(find_items_script)
            return func(*args, **kwargs)
        return wrapper

    @retrieve_clickable_elements
    def click(self, index):
        if index >= len(self.elements_clickable):
            raise ValueError("error: index out of range")
        self.elements_clickable[index].click()

    def visit(self, url):
        url = url if url.startswith("http") else "http://" + url
        if not validators.url(url):
            raise ValueError("error: visiting invalid URL")

        self.driver.get(url)

    def scroll(self, scroll_down=True, duration = 1000):
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

        self.driver.execute_script(ease_out_scroll_script)
        WebDriverWait(self.driver, duration / 1000 + 2).until(
            check_scroll_complete
        )

    def reset_overlay(self):
        self.driver.execute_script("""
            if (window.clickableOverlays && window.clickableOverlays.length > 0) {
                window.clickableOverlays.forEach(function(overlay) {
                    overlay.style.display = 'none';
                });
            }
            window.clickableOverlays = [];
        """)

    @retrieve_clickable_elements
    def apply_clickable_overlays(self):
        overlay_script = """
        var els = arguments[0];
        window.clickableOverlays = [];
        els.forEach(function(el, index) {
            var overlay = document.createElement('div');
            overlay.style.position = 'absolute';
            overlay.style.left = (el.getBoundingClientRect().left + window.scrollX) + 'px';
            overlay.style.top = (el.getBoundingClientRect().top + window.scrollY) + 'px';
            overlay.style.width = el.getBoundingClientRect().width + 'px';
            overlay.style.height = el.getBoundingClientRect().height + 'px';
            overlay.style.backgroundColor = 'rgba(255, 255, 0, 0.5)'; // Semi-transparent yellow
            overlay.style.color = 'black';
            overlay.style.zIndex = '10000';
            overlay.style.pointerEvents = 'none'; // Allows clicks to pass through
            overlay.textContent = index; // Sequence number
            overlay.style.textAlign = 'center';
            overlay.style.lineHeight = el.getBoundingClientRect().height + 'px';
            document.body.appendChild(overlay);
            window.clickableOverlays.push(overlay);
        });
        """
        self.driver.execute_script(overlay_script, self.elements_clickable)

if __name__ == "__main__":
    sandbox = SeleniumSandbox()
    sandbox.visit("https://google.com")
    sandbox.apply_clickable_overlays()
    while True:
        command = input("> ")
        sandbox.reset_overlay()
        
        if command.startswith("c"):
            try:
                index = int(command.split(" ")[1])
                sandbox.click(index)
            except ValueError:
                print("error: invalid index")
        elif command == "u":
            sandbox.scroll(scroll_down=False)
        else:
            sandbox.scroll()

        sandbox.apply_clickable_overlays()

            
        
    

