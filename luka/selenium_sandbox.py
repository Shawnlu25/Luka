from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import validators
from time import sleep

class SeleniumSandbox(object):
    def __init__(self, window_size=(1024, 768)):
        self.driver = webdriver.Chrome()

        self.window_size = window_size
        self.driver.set_window_size(window_size[0], window_size[1])

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
        
if __name__ == "__main__":
    sandbox = SeleniumSandbox()
    

