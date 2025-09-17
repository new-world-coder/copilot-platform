// DOM capture content script for Copilot Platform Extension
class DOMCapture {
    constructor() {
        this.isCapturing = false;
        this.init();
    }

    init() {
        this.setupTextSelectionListener();
        this.setupMessageListener();
    }

    setupTextSelectionListener() {
        // Listen for text selection events
        document.addEventListener('mouseup', (e) => {
            this.handleTextSelection();
        });

        // Also listen for keyboard selection
        document.addEventListener('keyup', (e) => {
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight' || 
                e.key === 'ArrowUp' || e.key === 'ArrowDown' ||
                e.key === 'Home' || e.key === 'End') {
                this.handleTextSelection();
            }
        });
    }

    setupMessageListener() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            switch (request.type) {
                case 'GET_PAGE_CONTENT':
                    sendResponse(this.getPageContent());
                    break;
                case 'CAPTURE_SELECTION':
                    this.captureCurrentSelection();
                    sendResponse({ success: true });
                    break;
                default:
                    sendResponse({ error: 'Unknown message type' });
            }
        });
    }

    handleTextSelection() {
        const selection = window.getSelection();
        const selectedText = selection.toString().trim();
        
        if (selectedText.length > 0) {
            this.sendSelectedText(selectedText);
        }
    }

    captureCurrentSelection() {
        const selection = window.getSelection();
        const selectedText = selection.toString().trim();
        
        if (selectedText.length > 0) {
            this.sendSelectedText(selectedText);
        } else {
            console.log('No text selected');
        }
    }

    sendSelectedText(text) {
        // Send selected text to background script
        chrome.runtime.sendMessage({
            type: 'SELECTED_TEXT',
            text: text,
            url: window.location.href,
            timestamp: new Date().toISOString()
        });
    }

    getPageContent() {
        return {
            url: window.location.href,
            title: document.title,
            text: document.body.innerText,
            html: document.body.innerHTML,
            meta: this.extractMetaData(),
            links: this.extractLinks(),
            images: this.extractImages()
        };
    }

    extractMetaData() {
        const meta = {};
        const metaTags = document.querySelectorAll('meta');
        metaTags.forEach(tag => {
            const name = tag.getAttribute('name') || tag.getAttribute('property');
            const content = tag.getAttribute('content');
            if (name && content) {
                meta[name] = content;
            }
        });
        return meta;
    }

    extractLinks() {
        const links = [];
        document.querySelectorAll('a[href]').forEach(link => {
            links.push({
                text: link.textContent.trim(),
                href: link.href,
                title: link.title
            });
        });
        return links;
    }

    extractImages() {
        const images = [];
        document.querySelectorAll('img[src]').forEach(img => {
            images.push({
                src: img.src,
                alt: img.alt,
                title: img.title
            });
        });
        return images;
    }
}

// Initialize DOM capture
new DOMCapture();
