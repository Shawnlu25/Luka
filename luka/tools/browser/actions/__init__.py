from .functions import ActionResult, TAGS_CLICKABLE
from .functions import click, visit

DEFAULT_ACTIONS = {
    "visit": {
        "function": visit,
        "description": "Visit a URL in the current tab. Only URLs starting with 'http' or 'https' or `about:blank` are supported.",
        "params": [
            {
                "name": "url",
                "type": str,
                "required": True,
                "description": "URL to visit."
            }
        ]
    },
    "click": {
        "function": click,
        "description": f"Click on an element with id=`id`. Only {", ".join(["<" + t + ">" for t in TAGS_CLICKABLE])} elements are clickable.",
        "params": [
            {
                "name": "id",
                "type": int,
                "required": True,
                "description": "id of the element to click."
            }
        ]
    },
}