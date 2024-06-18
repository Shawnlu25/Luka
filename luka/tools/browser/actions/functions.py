import validators

from typing import Tuple, List, Dict
from selenium import webdriver
from selenium.common import exceptions as E
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from .common import ActionResult, TAGS_CLICKABLE, TAGS_FILLABLE


def handle_timeout(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except E.TimeoutException:
            driver = args[0]
            driver.execute_script("window.stop();")
            return ActionResult(True, f"Action timed out. Stopped loading page.")
    return wrapper

def _scroll_into_view_if_needed(driver: webdriver.Chrome, element: WebElement):
    # NOTE: This method is not supported in all browsers, e.g., Firefox
    #       Check https://developer.mozilla.org/en-US/docs/Web/API/Element/scrollIntoViewIfNeeded
    driver.execute_script(
        "arguments[0].scrollIntoViewIfNeeded(true);", 
        element)


@handle_timeout
def visit(
        driver: webdriver.Chrome, 
        element_idx: Dict, 
        url: str
    ) -> ActionResult:
    if url == "about:blank":
        driver.get("about:blank")
        return ActionResult(True)
    
    url = url if url.startswith("http") else "http://" + url
    if not validators.url(url):
        return ActionResult(False, f"Invalid URL: {url}")

    driver.get(url)

    return ActionResult(True)


@handle_timeout
def click(
        driver: webdriver.Chrome, 
        element_idx: Dict, 
        id: int
    ) -> ActionResult:
    if id not in element_idx:
        return ActionResult(False, f"Cannot find element with id={id}.")
    
    element = element_idx[id]
    if element["tag"] not in TAGS_CLICKABLE:
        return ActionResult(False, f"Element with id={id} is not clickable.")
    
    # Override target attribute in order to open in the same tab
    remove_target_attr_script = """
        var element = arguments[0];
        element.removeAttribute('target');
    """
    driver.execute_script(remove_target_attr_script, element["element"])
    
    _scroll_into_view_if_needed(driver, element["element"])

    try:
        element["element"].click()
    except E.ElementClickInterceptedException:
        return ActionResult(False, f"Element with id={id} is obscured by another element.")
    except E.ElementNotInteractableException:
        return ActionResult(False, f"Element with id={id} is not interactable.")
    except E.ElementNotVisibleException:
        return ActionResult(False, f"Element with id={id} is not visible.")
    except E.StaleElementReferenceException:
        return ActionResult(False, f"Element with id={id} is no longer attached to the DOM.")
    
    return ActionResult(True)


@handle_timeout
def back(
        driver: webdriver.Chrome, 
        element_idx: Dict
    ) -> ActionResult:
    driver.execute_script("window.history.go(-1)")
    return ActionResult(True)

@handle_timeout
def forward(
        driver: webdriver.Chrome, 
        element_idx: Dict
    ) -> ActionResult:
    driver.execute_script("window.history.go(1)")
    return ActionResult(True)

@handle_timeout
def scroll(
        driver: webdriver.Chrome, 
        element_idx: Dict,
        scroll_down: bool=True, 
        duration_ms: int=1000
    ) -> ActionResult:
        scroll_direction = "+" if scroll_down else "-"

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
            smoothScroll({duration_ms});
        """
        def check_scroll_complete(driver):
            element = driver.find_element(By.TAG_NAME, "body")
            return element.get_attribute(f"data-{completion_signal}") == "true"

        driver.execute_script(ease_out_scroll_script)
        WebDriverWait(driver, duration_ms / 1000 + 2).until(
            check_scroll_complete
        )
        return ActionResult(True)

@handle_timeout
def fill(
        driver: webdriver.Chrome, 
        element_idx: Dict, 
        id: int, 
        value: str,
        clear: bool=True,
        submit: bool=False
    ) -> ActionResult:
    if id not in element_idx:
        return ActionResult(False, f"Cannot find element with id={id}.")

    element = element_idx[id]
    if element["tag"] not in TAGS_FILLABLE:
        return ActionResult(False, f"Element with id={id} is not fillable.")
    
    _scroll_into_view_if_needed(driver, element["element"])
    
    try:
        if clear:
            element["element"].clear()
        element["element"].send_keys(value)
        if submit:
            element["element"].send_keys(Keys.RETURN)
    except E.ElementNotInteractableException:
        return ActionResult(False, f"Element with id={id} is not interactable.")
    except E.ElementNotVisibleException:
        return ActionResult(False, f"Element with id={id} is not visible.")
    except E.StaleElementReferenceException:
        return ActionResult(False, f"Element with id={id} is no longer attached to the DOM.")

    return ActionResult(True)

def fill_submit(
        driver: webdriver.Chrome, 
        element_idx: Dict, 
        id: int, 
        value: str,
        clear: bool=True,
    ) -> ActionResult:
    return fill(driver, element_idx, id, value, clear, submit=True)
