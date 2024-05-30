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


// Useful functions for processing text elements at both end of an element list
// The point is to merge text elements rather than having multiple text elements in a row
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
    } else {
        el_list.push(el);
    }
}

const prependElement = (el_list, el) => {
    if (el_list.length != 0  && el_list[0].tag == el.tag && el.tag == "text") {
        console.log("prepend text with text")
        el_list[0].text = el.text + el_list[0].text;
        el_list[0].element = el.element;
    } else {
        el_list.unshift(el);
    }
}

const getRepresentationOfElement = (element, tag, content) => {
    var obj = {
        element: element,
        tag: tag,
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
    if (typeof content === "string") {
        obj.text = content;
        obj.children = null;
    } else if (Array.isArray(content)) {
        obj.text = null;
        obj.children = content;
    } 
    return obj;
}

const retrieveElements = (element) => {
    // content: TAGS_CONTENT
    // structure: TAGS_FORMAT, TAGS_BASIC

    if (element.hasAttribute("textual-browser-env-skip")) {
        return [];
    }
    element.setAttribute("textual-browser-env-skip", "true");

    // Skip meta, programming, and frames tags
    if (element.matches([TAGS_META, TAGS_PROGRAMMING, TAGS_FRAMES, "style"].join(", "))) {
        Array.from(element.querySelectorAll("*")).forEach(el => {
            el.setAttribute("textual-browser-env-skip", "true");
        });
        return [];
    }

    // Skip invisible elements
    if (!element.checkVisibility({contentVisibilityAuto: true, opacityProperty: true, visibilityProperty:true}) && !element.matches("option"))  {

        Array.from(element.querySelectorAll("*")).forEach(el => {
            el.setAttribute("textual-browser-env-skip", "true");
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
            appendElement(el_list, getRepresentationOfElement(element, "text", child.nodeValue.trim() + postfix));
        } else if (child.nodeType === Node.ELEMENT_NODE) {
            retrieveElements(child).forEach(el => {
                appendElement(el_list, el);
            });
        }
    }

    // ========================
    // Forms
    if (element.matches("textarea, input[type=text], input[type=password], input[type=email], input[type=search], input[type=number], input[type=tel], input[type=url], input[type=search]")) {
        el_list = [getRepresentationOfElement(element, "textinput", el_list)];   
        return el_list;
    }

    if (element.matches("input[type=date], input[type=datetime-local], input[type=month], input[type=week], input[type=time]")) {
        el_list = [getRepresentationOfElement(element, "datepicker", el_list)];   
        return el_list;
    }

    if (element.matches("input[type=button], input[type=submit], div[role=button], span[role=button], input[type=reset]")) {
        el_list = [getRepresentationOfElement(element, "button", el_list)];
        return el_list;
    }

    if (element.matches("select, div[role=combobox]")) {
        el_list = [getRepresentationOfElement(element, "select", el_list)];
        return el_list;
    }

    if (element.matches("optgroup")) {
        el_list = [getRepresentationOfElement(element, "select", el_list)];
        return el_list;
    }

    if (element.matches("option, div[role=option], span[role=option]")) {
        prependElement(el_list, getRepresentationOfElement(element, "text", "\n* "));
        return el_list;
    }

    if (element.matches("input[type=checkbox], div[role=checkbox], span[role=checkbox]")) {
        el_list = [getRepresentationOfElement(element, "checkbox", el_list)];
        return el_list;
    }

    if (element.matches("input[type=radio], div[role=checkbox], span[role=checkbox]")) {
        el_list = [getRepresentationOfElement(element, "radio", el_list)];
        return el_list;
    }

    // range, color, file

    // ========================
    // Links
    if (element.matches(TAGS_LINKS)) {
        if (element.matches("a, link")) {
            el_list = [getRepresentationOfElement(element, "link", el_list)];
        }
        return el_list;
    }

    // ========================
    // Images and AV
    if (element.matches(TAGS_IMAGES) || element.matches(TAGS_AV)) {
        el_list = [getRepresentationOfElement(element, element.tagName.toLowerCase(), el_list)];
        return el_list
    }

     // ========================
    // Lists
    if (element.matches(TAGS_LISTS)) {
        if (element.matches("li")) {
            prependElement(el_list, getRepresentationOfElement(element, "text", "\n* "));
        }
        if (element.matches("menu, ol, ul, dl")) {
            prependElement(el_list, getRepresentationOfElement(element, "text", "\n"));
            appendElement(el_list, getRepresentationOfElement(element, "text", "\n"));
        }
        if (element.matches("dt")) {
            appendElement(el_list, getRepresentationOfElement(element, "text", "\n"));
        }
        if (element.matches("dd")) {
            prependElement(el_list, getRepresentationOfElement(element, "text", "\n\t"));
        }

        return el_list;
    }

    // ========================
    // Content Tags
    trimList(el_list);
    
    if (element.matches("hr")) {
        prependElement(el_list, getRepresentationOfElement(element, "text", "\n------"));
        appendElement(el_list, getRepresentationOfElement(element, "text", "\n"));
        return el_list;
    }

    if (element.matches("br")) {
        if (el_list.length > 0) {
            prependElement(el_list, getRepresentationOfElement(element, "text", "\n"));
            return el_list;
        }
        appendElement(el_list, getRepresentationOfElement(element, "text", "\n"));
        return el_list;
    }
    if (element.matches("p")) {
        prependElement(el_list, getRepresentationOfElement(element, "text", "\n"));
        appendElement(el_list, getRepresentationOfElement(element, "text", "\n"));
        return el_list;
    } 
    
    if (element.matches("h1, h2, h3, h4, h5, h6")) {
        prependElement(el_list, getRepresentationOfElement(element, "text", "\n" + "#".repeat(parseInt(element.nodeName.toLowerCase().replace("h", ""))) + " "));
        appendElement(el_list, getRepresentationOfElement(element, "text", "\n"));
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
        prependElement(el_list, getRepresentationOfElement(element, "text", " " + l));
        appendElement(el_list, getRepresentationOfElement(element, "text", r + " "));
        return el_list;
    } 
    
    if (element.matches(TAGS_FORMAT_BLOCK)) {
        prependElement(el_list, getRepresentationOfElement(element, "text", "\n```\n"));
        appendElement(el_list, getRepresentationOfElement(element, "text", "\n```\n"));
        return el_list;
    }

    // ========================
    // Semantics Tags
    if (element.matches(TAGS_SEMANTICS)) {
        if (element.matches("span")) {
            return el_list;
        }
        if (el_list.length > 0) {
            prependElement(el_list, getRepresentationOfElement(element, "text", "\n"));
            appendElement(el_list, getRepresentationOfElement(element, "text", "\n"));
        }
        return el_list;
    }

    // ========================
    // Tables
    // TODO: Implement table representation

    // ========================
    // Default
    if (el_list.length == 0) {
        return el_list;
    }
    appendElement(el_list, getRepresentationOfElement(element, "text", "\n"));
    return el_list;
}

var result_list = [];
Array.from(document.querySelectorAll('*')).filter(el => {
    const rect = el.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    return centerX >= 0 && centerX <= window.innerWidth && centerY >= 0 && centerY <= window.innerHeight && rect.width > 0 && rect.height > 0 && rect.width < window.innerWidth && rect.height < window.innerHeight;
}).forEach(el => {
    retrieveElements(el).forEach(e => {
        appendElement(result_list, e);
    });
});

// clear all llm-dom-visited attributes
Array.from(document.querySelectorAll("*")).forEach(el => {
    el.removeAttribute("textual-browser-env-skip");
});

return result_list;
