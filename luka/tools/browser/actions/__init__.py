from .functions import ActionResult, TAGS_CLICKABLE
from .functions import click

ACTION_GROUP = {
    "click": {
        "function": click,
        "params": [
            {
                "name": "id",
                "type": int,
                "required": True,
                "description": f"ID of the element to click. Only {", ".join(["<" + t + ">" for t in TAGS_CLICKABLE])} elements are clickable."
            }
        ]
    }
}