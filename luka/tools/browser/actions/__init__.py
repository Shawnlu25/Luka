from .functions import ActionResult, TAGS_CLICKABLE, TAGS_FILLABLE
from .functions import visit, click, back, forward, scroll, fill, fill_submit

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
                "description": "ID of the element to click."
            }
        ]
    },
    "back": {
        "function": back,
        "description": "Go back one page in the current window's history.",
        "params": []
    },
    "forward": {
        "function": forward,
        "description": "Go forward one page in the current window's history.",
        "params": []
    },
    "scroll": {
        "function": scroll,
        "description": "Scroll the page in y-direction by inner window height. Set `scroll_down` parameter to control direction of scrolling.",
        "params": [
            {
                "name": "scroll_down",
                "type": bool,
                "required": False,
                "description": "Default to be `True`."
            }
        ]
    },
    "fill": {
        "function": fill,
        "description": f"Fill in a form element with id=`id` with the provided `value`. Only {", ".join(["<" + t + ">" for t in TAGS_FILLABLE])} elements are fillable.",
        "params": [
            {
                "name": "id",
                "type": int,
                "required": True,
                "description": "ID of the element to fill."
            },
            {
                "name": "value",
                "type": str,
                "required": True,
                "description": "The text to fill in."
            },
            {
                "name": "clear",
                "type": bool,
                "required": False,
                "description": "Clear the element value before filling in. Default to be `True`."
            }
        ]
    },
    "fill_submit": {
        "function": fill_submit,
        "description": f"Fill in a form element with id=`id` with the provided `value` and submit the form (i.e., pressing `[Enter]` at the end). Only {", ".join(["<" + t + ">" for t in TAGS_FILLABLE])} elements are supported. Prefer using this action over `fill` when you want to submit a form after filling in the value.",
        "params": [
            {
                "name": "id",
                "type": int,
                "required": True,
                "description": "ID of the element to fill."
            },
            {
                "name": "value",
                "type": str,
                "required": True,
                "description": "The text to fill in."
            },
            {
                "name": "clear",
                "type": bool,
                "required": False,
                "description": "Clear the element value before filling in. Default to be `True`."
            }
        ]
    }
}