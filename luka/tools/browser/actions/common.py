from dataclasses import dataclass

@dataclass
class ActionResult:
    success: bool
    message: str = ""

TAGS_CLICKABLE = ["link", "button", "checkbox", "radio"]