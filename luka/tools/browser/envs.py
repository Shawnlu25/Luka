import gymnasium as gym
import numpy as np

from typing import Tuple, List, Dict

from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common import exceptions as E
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .spaces import Unicode, AnyDict
from .observations import *

import validators
import atexit
import os

TEXT_MAX_LENGTH = 2**32-1

class TextualBrowserEnv(gym.Env):
    metadata = {"render_modes": None}

    def __init__(
            self, 
            viewport: Tuple[int, int] = (1366, 1024), 
            headless: bool = False,
            timeout_s: int = 20,
        ):
        super().__init__()

        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
        options.add_argument(f"--window-size={viewport[0]},{viewport[1]}")
        self._driver = webdriver.Chrome(options=options)
        self._driver.set_page_load_timeout(timeout_s)

        # All printable elements on the page with their useful attributes
        self._elements: List[Dict] = []

        # Interactable elements on the page, indexed by id
        self._element_index: Dict[int, WebElement] = {}

        self.observation_space = gym.spaces.Dict({
            "url": Unicode(min_length=0, max_length=TEXT_MAX_LENGTH),
            "scroll_status": AnyDict(),
            "screenshot_base64": Unicode(min_length=0, max_length=TEXT_MAX_LENGTH),
            "page_text": Unicode(min_length=0,max_length=TEXT_MAX_LENGTH),
        })

        self.action_space = gym.spaces.Dict({
            "command": Unicode(min_length=0, max_length=TEXT_MAX_LENGTH),
            "args": gym.spaces.Sequence(Unicode(min_length=1, max_length=TEXT_MAX_LENGTH)),
        })

    def _get_obs(self):
        self._elements, self._element_index = retrieve_elements_from_viewport(self._driver)

        return {
            "url": self._driver.current_url,
            "scroll_status": get_scroll_status(self._driver),
            "screenshot_base64": self._driver.get_screenshot_as_base64(),
            "page_text": get_text_representation(self._elements),
        }

    def _get_info(self):
        return {}

    def step(self, action):
        
        return self._get_obs(), self._get_info()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        for handle in self._driver.window_handles[1:]:
            self._driver.switch_to.window(handle)
            self._driver.close()
        self._driver.switch_to.window(self._driver.window_handles[0])

        url = options.get("url", "about:blank")
        url = url if url.startswith("http") else "http://" + url
        if not validators.url(url):
            url = "about:blank"

        self._driver.get(url)

        return self._get_obs(), self._get_info()

    def render(self):
        pass

    def close(self):
        self._driver.quit()