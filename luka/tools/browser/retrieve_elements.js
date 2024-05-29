// HTML tag categories from https://www.w3schools.com/tags/ref_byfunc.asp
const TAGS_BASIC = "html, head, title, body" 
const TAGS_CONTENT = "h1, h2, h3, h4, h5, h6, p, br, hr"
const TAGS_FORMAT_INLINE = "abbr, b, bdi, bdo, cite, del, dfn, em, i, ins, kbd, mark, meter, progress, q, rp, rt, ruby, s, small, strong, sub, sup, time, u, var, wbr"
const TAGS_FORMAT_BLOCK = "address, blockquote, code, pre, samp, template"
const TAGS_FORM = "form, input, textarea, button, select, optgroup, option, label, fieldset, legend, datalist, output"
const TAGS_FRAMES = "iframe"
const TAGS_IMAGES = "img, map, area, canvas, figcaption, figure, picture, svg"
const TAGS_AV = "audio, video, source, track"
const TAGS_LINKS = "a, link, nav"
const TAGS_LISTS = "menu, ol, ul, li, dir, dl, dt, dd"
const TAGS_TABLE = "table, caption, th, tr, td, thead, tbody, tfoot, col, colgroup"
const TAGS_SEMANTICS = "style, div, span, header, hgroup, footer, main, section, search, article, aside, details, dialog, summary, data"
const TAGS_META = "head, meta, base, basefont"
const TAGS_PROGRAMMING = "script, noscript, applet, embed, object, param";

const tagPureTextElements = (element) => {
    if (element.hasAttribute("llm-dom-skip")) {
        return true;
    }
    if (element.hasAttribute("llm-dom-pure-text")) {
        return element.getAttribute("llm-dom-pure-text") === "true";
    }

    // Ignore invisible elements
    if (!element.checkVisibility({contentVisibilityAuto: true, opacityProperty: true, visibilityProperty:true})) {
        element.setAttribute("llm-dom-skip", "true");
        return true;
    }

    // Ignore tags
    if (element.matches([TAGS_META, TAGS_PROGRAMMING, TAGS_FRAMES, "style"].join(","))) {
        element.setAttribute("llm-dom-skip", "true");
        return true;
    }

    if (element.matches([TAGS_FORM, TAGS_IMAGES, TAGS_AV, TAGS_LINKS, "style"].join(","))) {
        element.setAttribute("llm-dom-pure-text", "false");
        return false;
    }

    var result = true;
    var childElements = element.childElements;
    if (childElements) {
        for (var i = 0; i < childElements.length; i++) {
            result = result && tagPureTextElements(childElements[i]);
        }
    }
    
    if (!result) {
        element.setAttribute("llm-dom-pure-text", "false");
        return false;
    }
    element.setAttribute("llm-dom-pure-text", "true");
    return true;
}

const getPureText = (element) => {
    // Ignore meta, programming, and frames tags
    if (element.matches([TAGS_META, TAGS_PROGRAMMING, TAGS_FRAMES, "style"].join(", "))) {
        return "";
    }

    // Ignore invisible elements
    if (!element.checkVisibility({contentVisibilityAuto: true, opacityProperty: true, visibilityProperty:true})) {
        return "";
    }

    var result_text = "";

    var childNodes = element.childNodes;
    for (var i = 0; i < childNodes.length; i++) {
        var child = childNodes[i]; 
        if (child.nodeType === Node.TEXT_NODE) {
            result_text += child.nodeValue.trim() + " ";
        } else if (child.nodeType === Node.ELEMENT_NODE) {
            result_text += getPureText(child);
        }
    }

    // Trim for each line, filter out empty lines
    //result_text = result_text.split("\n").map(line => line.trim()).filter(line => line.length > 0).join("\n");
    result_text = result_text.trim();

    // Content Tags
    if (element.matches("hr")) {
        return "\n" + "------" + result_text + "\n";
    } else if (element.matches("br")) {
        if (result_text.length > 0) {
            return "\n" + result_text + "\n";
        }
        return "\n";
    } else if (element.matches("p")) {
        return "\n" + result_text + "\n";
    } else if (element.matches("h1, h2, h3, h4, h5, h6")) {
        return "\n" + "#".repeat(parseInt(element.nodeName.toLowerCase().replace("h", ""))) + " " + result_text + "\n";
    }

    // Format Tags
    if (element.matches(TAGS_FORMAT_INLINE)) {
        if (element.matches("b, strong, em, ins, mark")) {
            result_text =  "**" + result_text + "**";
        } else if (element.matches("i, sub, dfn, var")) {
            result_text = "_" + result_text + "_";
        } else if (element.matches("u, ins")) {
            result_text = "<u>" + result_text + "</u>";
        } else if (element.matches("s, del")) {
            result_text = "~~" + result_text + "~~";
        }
        return " " + result_text + " ";
    } else if (element.matches(TAGS_FORMAT_BLOCK)) {
        if (element.matches("code, samp, pre")) {
            result_text = "```\n" + result_text + "\n```";
        } else if (element.matches("blockquote")) {
            result_text = result_text.split("\n").map(line => "> " + line).join("\n");
        }
        return "\n" + result_text + "\n";
    }

    // Semantics Tags
    if (element.matches(TAGS_SEMANTICS)) {
        if (element.matches("span")) {
            return result_text;
        }
        if (result_text.length > 0) {
            return "\n"+ result_text + "\n";
        }
        return result_text;
    }

    if (result_text.length == 0) {
        return "";
    }
    return result_text + "\n";
}


const selectedElements = [];

const selectElement = (element) => {
    if (element.parentElement && element.parentElement.hasAttribute("llm-dom-visited")) {
        element.setAttribute("llm-dom-visited", "true");
    }
    if (!element.checkVisibility({contentVisibilityAuto: true, opacityProperty: true, visibilityProperty:true})) {
        return;
    }
    const rect = element.getBoundingClientRect();
    var tag = null;
    var text = null;

    if (element.matches("a, link, nav, button, input[type=button], input[type=submit], input[type=reset], [role=\"button\"]")) {
        tag = "link",
        text = getPureText(element).trim();
        if (text && text.length >= 0) {
            element.setAttribute("llm-dom-visited", "true");
        }

    } else if (element.matches("p, h1, h2, h3, h4, h5, h6, span, div, label, option, ul, li")) {
        if (!Array.from(element.childNodes).some(node => node.nodeType === Node.TEXT_NODE && node.textContent.trim() !== '')) {
            return;
        }
        if (element.parentElement && element.parentElement.hasAttribute("llm-dom-visited")) {
            return;
        }
        tag = "text";
        text = getPureText(element);

    } else if (element.matches('textarea, input[type=text], input[type=password], input[type=email], input[type=search], input[type=number], input[type=tel], input[type=url], input[type=search]')) {
        tag = "textinput";
        text = getPureText(element).trim();
        element.setAttribute("llm-dom-visited", "true");

    } else if (element.matches('input[type=checkbox], input[type=radio]')) {
        tag = element.getAttribute('type').toLowerCase();
        text = getPureText(element).trim();
        element.setAttribute("llm-dom-visited", "true");

    } else if (element.matches('input[type=date], input[type=datetime-local], input[type=month], input[type=week], input[type=time]')) {
        // set tag based on type
        tag = "datepicker";
        text = getPureText(element).trim();
        element.setAttribute("llm-dom-visited", "true");

    } else if (element.matches('input[type=range]')) {
        tag = "slider";
        text = getPureText(element).trim();
        element.setAttribute("llm-dom-visited", "true");

    } else if (element.matches('select')) {
        tag = "select";
        text = getPureText(element).trim();
        element.setAttribute("llm-dom-visited", "true");
    }

    if (!tag) {
        return;
    }

    selectedElements.push({
        element: element,
        x: rect.x,
        y: rect.y,
        width: rect.width,
        height: rect.height,
        tag: tag,
        text: text,
        name: element.getAttribute('name'),
        type: element.getAttribute('type'),
        placeholder: element.getAttribute('placeholder'),
        aria_label: element.getAttribute('aria-label'),
        title: element.getAttribute('title'),
        alt: element.getAttribute('alt'),
        checked: element.getAttribute('checked'),
        value: element.getAttribute('value'),
        required: element.getAttribute('required'),
        min: element.getAttribute('min'),
        max: element.getAttribute('max'),
    });
}

Array.from(document.querySelectorAll('*')).filter(el => {
    const rect = el.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    return centerX >= 0 && centerX <= window.innerWidth && centerY >= 0 && centerY <= window.innerHeight && rect.width > 0 && rect.height > 0;
}).forEach(tagPureTextElements);

// Select llm-pure-text elements, no matter true or false
Array.from(document.querySelectorAll('*')).filter(el => {
    return el.hasAttribute("llm-dom-pure-text");
}).forEach(selectElement);

// clear all llm-dom-visited, llm-dom-skip, llm-dom-pure-text attributes
Array.from(document.querySelectorAll('*')).forEach(el => {
    el.removeAttribute("llm-dom-visited");
    el.removeAttribute("llm-dom-skip");
    el.removeAttribute("llm-dom-pure-text");
});

return selectedElements;