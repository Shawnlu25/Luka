import gymnasium as gym
import validators

from typing import Tuple, List, Dict
from selenium import webdriver

from .spaces import Unicode, AnyDict
from .observations import *
from .actions import ActionResult, ACTION_GROUP


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
        self._element_index: Dict[int, Dict] = {}

        # Previous action result
        self._action_result: ActionResult = ActionResult(True)

        self.observation_space = gym.spaces.Dict({
            "url": Unicode(min_length=0, max_length=TEXT_MAX_LENGTH),
            "scroll_status": AnyDict(),
            "screenshot_base64": Unicode(min_length=0, max_length=TEXT_MAX_LENGTH),
            "page_text": Unicode(min_length=0,max_length=TEXT_MAX_LENGTH),
            "action_result": AnyDict(),
        })

        self.action_space = gym.spaces.Dict({
            "command": Unicode(min_length=0, max_length=TEXT_MAX_LENGTH),
            "args": AnyDict(),
        })

    def _get_obs(self):
        self._elements, self._element_index = retrieve_elements_from_viewport(self._driver)

        return {
            "url": self._driver.current_url,
            "scroll_status": get_scroll_status(self._driver),
            "screenshot_base64": self._driver.get_screenshot_as_base64(),
            "page_text": get_text_representation(self._elements),
            "action_result": {
                "success": self._action_result.success,
                "message": self._action_result.message,
            },
        }

    def _get_info(self):
        return {}

    def step(self, action):
        command = action["command"]
        args = action["args"]

        if command not in ACTION_GROUP:
            self._action_result = ActionResult(False, f"Command `{command}` not supported.")
            return self._get_obs(), self._get_info()
        
        # Filter out unsupported arguments
        args = {k:v for k,v in args.items() if k in [param["name"] for param in ACTION_GROUP[command]["params"]]}

        # Check if all required arguments are present and if all type constraints are satisfied
        for param in ACTION_GROUP[command]["params"]:
            if param["required"] and param["name"] not in args:
                self._action_result = ActionResult(False, f"Missing required argument `{param['name']}`.")
                return self._get_obs(), self._get_info()
            if type(args[param["name"]]) != param["type"]:
                self._action_result = ActionResult(False, f"Argument `{param['name']}` must be of type `{param['type']}`, but a `{type(args[param["name"]])}` is provided instead.")
                return self._get_obs(), self._get_info()
            if param["name"] not in args:
                args[param["name"]] = None

        # Execute the action
        self._action_result = ACTION_GROUP[command]["function"](self._driver, self._element_index, **args)
        
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