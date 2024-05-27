const selectedElements = [];

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
    } else if (
        element.matches("a, button, input[type=button], input[type=submit], input[type=reset], [role=\"button\"]") || 
        (element.tagName.toLowerCase() === 'div' && element.onclick)
    ) {
        tag = "link",
        text = element.innerText.trim();
        if (text && text.length >= 0) {
            element.setAttribute("luka-skip-element", "true");
        }

    } else if (element.matches("p, h1, h2, h3, h4, h5, h6, span, div, label, option")) {
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