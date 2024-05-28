const selectedElements = [];

// HTML tag categories from https://www.w3schools.com/tags/ref_byfunc.asp
const TAGS_PROGRAMMING = "script, noscript, applet, embed, object, param";
const TAGS_META = "head, meta, base, basefont"
const TAGS_SEMANTICS = "style, div, span, header, hgroup, footer, main, section, search, article, aside, details, dialog, summary, data"
const TAGS_TABLE = "table, caption, th, tr, td, thead, tbody, tfoot, col, colgroup"
const TAGS_LISTS = "menu, ol, ul, li, dir, dl, dt, dd"
const TAGS_LINKS = "a, link, nav"
const TAGS_AV = "audio, video, source, track"
const TAGS_IMAGES = "img, map, area, canvas, figcaption, figure, picture, svg"
const TAGS_FRAMES = "iframe"
const TAGS_INPUT = "form, input, textarea, button, select, optgroup, option, label, fieldset, legend, datalist, output"
const TAGS_FORMAT = "abbr, address, b, bdi, bdo, blockquote, cite, code, del, dfn, em, i, ins, kbd, mark, meter, pre, progress, q, rp, rt, ruby, s, samp, small, strong, strong, sub, sup, template, time, u, var, wbr"
const TAGS_BASIC = "html, head, title, body" 
const TAGS_CONTENT = "h1, h2, h3, h4, h5, h6, p, br, hr"

const isPureText = (element) => {
    if (element.matches("a, link, nav, button, input, textarea, select")) {
        return false;
    }

}

const selectElement = (element) => {
    if (element.parentElement && element.parentElement.hasAttribute("luka-skip-element")) {
        element.setAttribute("luka-skip-element", "true");
        //return;
    }
    if (!element.checkVisibility({contentVisibilityAuto: true, opacityProperty: true, visibilityProperty:true})) {
        return;
    }
    const rect = element.getBoundingClientRect();
    var tag = null;
    var text = null;

    if (element.matches("iframe")) {
        //if (element.contentWindow && element.contentWindow.origin === window.origin) {
        //    element.contentWindow.document.querySelectorAll('*').forEach(selectElement);
        //}
    } else if (element.matches("a, link, nav, button, input[type=button], input[type=submit], input[type=reset], [role=\"button\"]")) {
        tag = "link",
        text = element.innerText.trim();
        if (text && text.length >= 0) {
            element.setAttribute("luka-skip-element", "true");
        }

    } else if (element.matches("p, h1, h2, h3, h4, h5, h6, span, div, label, option, ul, li")) {
        if (!Array.from(element.childNodes).some(node => node.nodeType === Node.TEXT_NODE && node.textContent.trim() !== '')) {
            return;
        }
        if (element.parentElement && element.parentElement.hasAttribute("luka-skip-element")) {
            return;
        }
        tag = "text";
        text = Array.from(element.childNodes).filter(node => node.nodeType === Node.TEXT_NODE).map(node => node.nodeValue.trim()).join(' ')

    } else if (element.matches('textarea, input[type=text], input[type=password], input[type=email], input[type=search], input[type=number], input[type=tel], input[type=url], input[type=search]')) {
        tag = "textinput";
        text = element.innerText.trim();
        element.setAttribute("luka-skip-element", "true");

    } else if (element.matches('input[type=checkbox], input[type=radio]')) {
        tag = element.getAttribute('type').toLowerCase();
        text = element.innerText.trim();
        element.setAttribute("luka-skip-element", "true");

    } else if (element.matches('input[type=date], input[type=datetime-local], input[type=month], input[type=week], input[type=time]')) {
        // set tag based on type
        tag = "datepicker";
        text = element.innerText.trim();
        element.setAttribute("luka-skip-element", "true");

    } else if (element.matches('input[type=range]')) {
        tag = "slider";
        text = element.innerText.trim();
        element.setAttribute("luka-skip-element", "true");

    } else if (element.matches('select')) {
        tag = "select";
        text = element.innerText.trim();
        element.setAttribute("luka-skip-element", "true");

        // TODO: ???
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

document.querySelectorAll('*').forEach(selectElement);
return selectedElements;