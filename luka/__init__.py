from .basic_browser_agent import BasicBrowserAgent
from .tty_agent import TTYAgent

AGENT_REGISTRY = {
    "browser": {
        "cls": BasicBrowserAgent,
        "description": "Have access to a web browser to gather information or complete jobs online.",
    },
    "tty": {
        "cls": TTYAgent,
        "description": "Have access to a TTY bash terminal to run commands, modifiy files, and interact with the system.",
    }
}

