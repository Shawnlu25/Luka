import pkgutil

from typing import Tuple, List, Dict
from selenium import webdriver

js_retrieve_elements = pkgutil.get_data(__name__, "javascript/retrieve_elements.js").decode("utf-8")

def retrieve_elements_from_viewport(driver: webdriver.Chrome):
    driver.execute_script(js_retrieve_elements)
    elements = driver.execute_script(js_retrieve_elements)

    idx = 0
    idx_map = {}
    def assign_idx(elements) -> Tuple[List[Dict], Dict[int, Dict]]:
        nonlocal idx
        for e in elements:
            e["id"] = idx
            idx += 1
            if e["children"] != None:
                assign_idx(e["children"])
            if e["tag"] != "text":
                idx_map[e["id"]] = e

    assign_idx(elements)
    return elements, idx_map


def get_text_representation(elements: List[Dict]) -> str:
    text_repr = ""
    for e in elements:
        if e["tag"] in ["textinput", "select", "datepicker"]:
            text_attrs = ["text", "placeholder"]
            meta_attrs = ["type", "alt", "title", "aria_label", "value", "required", "checked", "min", "max"]
        elif e["tag"] == "text":
            text_attrs = ["text"]
            meta_attrs = []
        else:
            text_attrs = ["text", "aria_label", "alt"]
            meta_attrs = ["type", "value"]

        text = [x for x in filter(lambda x: x is not None and len(x) > 0, [e[attr] for attr in text_attrs])]
        text = text[0] if len(text) > 0 else None
        if text != None and text != e["text"]:
            text = "(" + text + ")"
        
        if e["children"] != None:
            text = "" if text == None else text
            text = get_text_representation(e["children"]) + text
        
        if text == None:
            text = ""
        
        meta_str = " ".join([attr + "=\"" + e[attr] + "\"" for attr in meta_attrs if e[attr] is not None])
        if len(meta_str) > 0:
            meta_str = " " + meta_str

        if e["tag"] == "text":
            text_repr += text
            continue
        if e["tag"] in ["img", "map", "area", "canvas", "figcaption", "figure", "picture", "svg"]:
            text_repr += f"![{e['tag']}]({text})"
            continue
        
        if text is None: 
            text_repr += f"<{e["tag"]} id=\"{e["id"]}\"{meta_str}/>\n"
        elif len(text.split("\n")) > 1:
            text = text.strip()
            text_repr += f"<{e["tag"]} id=\"{e["id"]}\"{meta_str}>\n{text}\n</{e["tag"]}>\n"
        else:
            text_repr += f"<{e["tag"]} id=\"{e["id"]}\"{meta_str}>{text}</{e["tag"]}>\n"
    
    return text_repr

def get_scroll_status(driver: webdriver.Chrome) -> Dict:
    
    scroll_y = driver.execute_script("return window.scrollY;")
    scroll_height = driver.execute_script("return document.body.scrollHeight - window.innerHeight;")
    if scroll_height <= 0:
        scroll_height = 0
        percentage_y = 1.0
    else:
        percentage_y = scroll_y / scroll_height

    scroll_x = driver.execute_script("return window.scrollX;")
    scroll_width = driver.execute_script("return document.body.scrollWidth - window.innerWidth;")
    if scroll_width <= 0:
        scroll_width = 0
        percentage_x = 1.0
    else:
        percentage_x = scroll_x / scroll_width
        
    return {
        "percentage_y": percentage_y,
        "scroll_y": scroll_y,
        "scroll_height": scroll_height,
        "percentage_x": percentage_x,
        "scroll_x": scroll_x,
        "scroll_width": scroll_width
    }