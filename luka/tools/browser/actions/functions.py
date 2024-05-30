import validators

from typing import Tuple, List, Dict
from selenium import webdriver
from selenium.common import exceptions as E
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from .common import ActionResult, TAGS_CLICKABLE


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
    ):
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
    ):
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
    
    return ActionResult(True)
