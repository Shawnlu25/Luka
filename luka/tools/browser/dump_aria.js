function isVisible(node) {
    const style = getComputedStyle(node);
    const rect = node.getBoundingClientRect();
    return style && style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0' && node.getAttribute('aria-hidden') !== 'true' && rect.width > 0 && rect.height > 0 && node.getAttribute('aria-expanded') !== 'false';
}

function dumpARIA(node, indent = '') {
    if (node.nodeType === Node.ELEMENT_NODE && isVisible(node)) {
        const attrs = Array.from(node.attributes)
        .filter(attr => attr.name.startsWith('aria-') || attr.name === 'placeholder')
        .map(attr => `${attr.name}: ${attr.value}`)
        .join(', ');
        if (attrs) {
        console.log(`${indent}${node.nodeName} {${attrs}}`);
        }
        if (node.childNodes) {
        node.childNodes.forEach(child => {
            if (child.nodeType === Node.TEXT_NODE && child.textContent.trim() !== '') {
            console.log(`${indent}  ${child.textContent.trim()}`);
            }
        });
        }
        for (let i = 0; i < node.children.length; i++) {
        if (isVisible(node.children[i])) {
            dumpARIA(node.children[i], indent + '  ');
        }
        }
    }
}

dumpARIA(document.body);