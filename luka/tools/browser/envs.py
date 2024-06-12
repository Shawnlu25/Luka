import gymnasium as gym
import validators

from typing import Tuple, List, Dict
from selenium import webdriver

from .spaces import Unicode, AnyDict
from .observations import *
from .actions import ActionResult, DEFAULT_ACTIONS


TEXT_MAX_LENGTH = 2**32-1

class TextualBrowserEnv(gym.Env):
    metadata = {"render_modes": None}

    def __init__(
            self, 
            viewport: Tuple[int, int] = (1024, 768), 
            headless: bool = False,
            timeout_s: int = 20,
            actions: Dict = DEFAULT_ACTIONS
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

        # Supported actions
        self._actions = actions

        # Result of the last action
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
        help_texts = []
        for k, v in sorted(self._actions.items(), key=lambda x: x[0]):
            help_text = f"{k.upper()}\n{v["description"]}\n"
            for param in v["params"]:
                help_text += f"    {param["name"]} ({param["type"].__name__}): {param["description"]}\n"
            help_texts.append(help_text)
        
        return {
            "actions": "\n".join(help_texts)
        }

    def step(self, action):
        command = action["command"].lower()
        args = action["args"]

        if command not in self._actions:
            self._action_result = ActionResult(False, f"Command `{command}` not supported.")
            return self._get_obs(), self._get_info()
        
        # Filter out unsupported arguments
        args = {k:v for k,v in args.items() if k in [param["name"] for param in self._actions[command]["params"]]}

        # Check if all required arguments are present and if all type constraints are satisfied
        for param in self._actions[command]["params"]:
            if param["required"] and param["name"] not in args:
                self._action_result = ActionResult(False, f"Missing required argument `{param['name']}`.")
                return self._get_obs(), self._get_info()
            if type(args[param["name"]]) != param["type"]:
                self._action_result = ActionResult(False, f"Argument `{param['name']}` must be of type `{param['type']}`, but a `{type(args[param["name"]])}` is provided instead.")
                return self._get_obs(), self._get_info()
            if param["name"] not in args:
                args[param["name"]] = None

        # Execute the action
        self._action_result = self._actions[command]["function"](self._driver, self._element_index, **args)
        
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

        return self.step({"command": "visit", "args": {"url": url}})

    def render(self):
        pass

    def close(self):
        self._driver.quit()