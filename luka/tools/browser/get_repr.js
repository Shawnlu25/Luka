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

const trimList = (el_list) => {
    if (el_list.length > 0 && el_list[0].tag == "text") {
        el_list[0].text = el_list[0].text.trimStart();
    }
    if (el_list.length > 0 && el_list[el_list.length-1].tag == "text") {
        el_list[el_list.length-1].text = el_list[el_list.length-1].text.trimEnd();
    }
}

const appendElement = (el_list, el) => {
    if (el_list.length != 0 && el_list[el_list.length - 1].tag == el.tag && el.tag == "text") {
        console.log("append text with text")
        el_list[el_list.length - 1].text += el.text;
        el_list[el_list.length - 1].element = el.element;
        /^\s/.test(el_list[el_list.length - 1].text) ? prefix = " " : prefix = "";
        /^\n/.test(el_list[el_list.length - 1].text) ? prefix = "\n" : prefix = "";
        /\s$/.test(el_list[el_list.length - 1].text) ? postfix = " " : postfix = "";
        /\n$/.test(el_list[el_list.length - 1].text) ? postfix = "\n" : postfix = "";
        el_list[el_list.length - 1].text = prefix + el_list[el_list.length - 1].text.trim() + postfix;
    } else {
        el_list.push(el);
    }
}

const prependElement = (el_list, el) => {
    if (el_list.length != 0  && el_list[0].tag == el.tag && el.tag == "text") {
        console.log("prepend text with text")
        el_list[0].text = el.text + el_list[0].text;
        el_list[0].element = el.element;
        /^\s/.test(el_list[0].text) ? prefix = " " : prefix = "";
        /^\n/.test(el_list[0].text) ? prefix = "\n" : prefix = "";
        /\s$/.test(el_list[0].text) ? postfix = " " : postfix = "";
        /\n$/.test(el_list[0].text) ? postfix = "\n" : postfix = "";
        el_list[0].text = prefix + el_list[0].text.trim() + postfix;
    } else {
        el_list.unshift(el);
    }
}

const getTextFromList = (el_list) => {
    // filter out text == null
    return el_list.filter(el => el.text != null).map(el => el.text).join("");
}

const transformElement = (element, tag, text) => {
    return {
        element: element,
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
    }
}

const getDOMRepresentation = (element) => {
    // content: TAGS_CONTENT
    // structure: TAGS_FORMAT, TAGS_BASIC
    // interactive: TAGS_LINKS, TAGS_FORM, TAGS_IMAGES, TAGS_AV

    if (element.hasAttribute("llm-dom-skip")) {
        return [];
    }
    element.setAttribute("llm-dom-skip", "true");

    // Skip meta, programming, and frames tags
    if (element.matches([TAGS_META, TAGS_PROGRAMMING, TAGS_FRAMES, "style"].join(", "))) {
        Array.from(element.querySelectorAll("*")).forEach(el => {
            el.setAttribute("llm-dom-skip", "true");
        });
        return [];
    }

    // Skip invisible elements
    if (!element.checkVisibility({contentVisibilityAuto: true, opacityProperty: true, visibilityProperty:true})) {
        Array.from(element.querySelectorAll("*")).forEach(el => {
            el.setAttribute("llm-dom-skip", "true");
        });
        return [];
    }

    // Get representations of children, including text and element nodes.
    var el_list = [];
    var childNodes = element.childNodes;
    for (var i = 0; i < childNodes.length; i++) {
        var child = childNodes[i]; 
        if (child.nodeType === Node.TEXT_NODE) {
            postfix = "";
            /\s$/.test(child.nodeValue) ? postfix = " " : postfix = "";
            /\n$/.test(child.nodeValue) ? postfix = "\n" : postfix = "";
            appendElement(el_list, transformElement(element, "text", child.nodeValue.trim() + postfix));
        } else if (child.nodeType === Node.ELEMENT_NODE) {
            getDOMRepresentation(child).forEach(el => {
                appendElement(el_list, el);
            });
        }
    }

    // ========================
    // Content Tags
    trimList(el_list);
    
    if (element.matches("hr")) {
        prependElement(el_list, transformElement(element, "text", "\n------"));
        appendElement(el_list, transformElement(element, "text", "\n"));
        return el_list;
    }

    if (element.matches("br")) {
        if (el_list.length > 0) {
            prependElement(el_list, transformElement(element, "text", "\n"));
            return el_list;
        }
        appendElement(el_list, transformElement(element, "text", "\n"));
        return el_list;
    }
    if (element.matches("p")) {
        prependElement(el_list, transformElement(element, "text", "\n"));
        appendElement(el_list, transformElement(element, "text", "\n"));
        return el_list;
    } 
    
    if (element.matches("h1, h2, h3, h4, h5, h6")) {
        prependElement(el_list, transformElement(element, "text", "\n" + "#".repeat(parseInt(element.nodeName.toLowerCase().replace("h", ""))) + " "));
        appendElement(el_list, transformElement(element, "text", "\n"));
        return el_list;
    }

    // ========================
    // Format Tags

    if (element.matches(TAGS_FORMAT_INLINE)) {
        var l = "", r = "";

        if (element.matches("b, strong, em, ins, mark")) {
            l = r = "**";
        } else if (element.matches("i, sub, dfn, var")) {
            l = r = "_";
        } else if (element.matches("u, ins")) {
            l = "<u>";
            r = "</u>";
        } else if (element.matches("s, del")) {
            l = r = "~~";
        }
        prependElement(el_list, transformElement(element, "text", " " + l));
        appendElement(el_list, transformElement(element, "text", r + " "));
        return el_list;
    } 
    
    if (element.matches(TAGS_FORMAT_BLOCK)) {
        prependElement(el_list, transformElement(element, "text", "\n```\n"));
        appendElement(el_list, transformElement(element, "text", "\n```\n"));
        return el_list;
    }

    // ========================
    // Semantics Tags
    if (element.matches(TAGS_SEMANTICS)) {
        if (element.matches("span")) {
            return el_list;
        }
        if (el_list.length > 0) {
            prependElement(el_list, transformElement(element, "text", "\n"));
            appendElement(el_list, transformElement(element, "text", "\n"));
        }
        return el_list;
    }

    // ========================
    // Links
    if (element.matches(TAGS_LINKS)) {
        if (element.matches("a, link")) {
            el_list = [transformElement(element, "link", getTextFromList(el_list))];
        }
        return el_list;
    }

    // ========================
    // Default
    if (el_list.length == 0) {
        return el_list;
    }
    appendElement(el_list, transformElement(element, "text", "\n"));
    return el_list;
}

var result_list = [];
Array.from(document.querySelectorAll('*')).filter(el => {
    const rect = el.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    return centerX >= 0 && centerX <= window.innerWidth && centerY >= 0 && centerY <= window.innerHeight && rect.width > 0 && rect.height > 0 && rect.width < window.innerWidth && rect.height < window.innerHeight;
}).forEach(el => {
    getDOMRepresentation(el).forEach(e => {
        appendElement(result_list, e);
    });
});

// clear all llm-dom-visited attributes
Array.from(document.querySelectorAll("*")).forEach(el => {
    el.removeAttribute("llm-dom-skip");
});

return result_list;
