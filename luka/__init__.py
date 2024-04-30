from .browser_agent import BrowserAgent
from .tty_agent import TTYAgent

AGENT_REGISTRY = {
    "browser": {
        "cls": BrowserAgent,
        "description": "Have access to a web browser to gather information or complete jobs online.",
    },
    "tty": {
        "cls": TTYAgent,
        "description": "Have access to a TTY bash terminal to run commands, modifiy files, and interact with the system.",
    }
}

