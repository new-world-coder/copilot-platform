// Content script for Copilot Platform Extension
class CopilotContentScript {
    constructor() {
        this.isActive = false;
        this.observer = null;
        this.init();
    }

    init() {
        this.setupMessageListener();
        this.setupContextMenu();
        this.observePageChanges();
    }

    setupMessageListener() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            switch (request.type) {
                case 'GET_PAGE_CONTENT':
                    sendResponse(this.getPageContent());
                    break;
                case 'HIGHLIGHT_ELEMENT':
                    this.highlightElement(request.selector);
                    sendResponse({ success: true });
                    break;
                case 'EXTRACT_DATA':
                    sendResponse(this.extractData(request.selectors));
                    break;
                case 'INJECT_OVERLAY':
                    this.injectOverlay(request.content);
                    sendResponse({ success: true });
                    break;
                default:
                    sendResponse({ error: 'Unknown message type' });
            }
        });
    }

    setupContextMenu() {
        // Add context menu for text selection
        document.addEventListener('mouseup', (e) => {
            const selection = window.getSelection();
            if (selection.toString().trim().length > 0) {
                this.showContextMenu(e, selection.toString());
            }
        });
    }

    showContextMenu(event, selectedText) {
        // Remove existing context menu
        const existingMenu = document.getElementById('copilot-context-menu');
        if (existingMenu) {
            existingMenu.remove();
        }

        // Create context menu
        const menu = document.createElement('div');
        menu.id = 'copilot-context-menu';
        menu.style.cssText = `
            position: fixed;
            top: ${event.pageY + 10}px;
            left: ${event.pageX}px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            padding: 8px 0;
            min-width: 200px;
        `;

        const actions = [
            { text: 'Ask about this text', action: 'ask' },
            { text: 'Summarize', action: 'summarize' },
            { text: 'Translate', action: 'translate' },
            { text: 'Extract key points', action: 'extract' }
        ];

        actions.forEach(action => {
            const item = document.createElement('div');
            item.textContent = action.text;
            item.style.cssText = `
                padding: 8px 16px;
                cursor: pointer;
                font-size: 14px;
                color: #333;
            `;
            item.addEventListener('mouseenter', () => {
                item.style.backgroundColor = '#f0f0f0';
            });
            item.addEventListener('mouseleave', () => {
                item.style.backgroundColor = 'transparent';
            });
            item.addEventListener('click', () => {
                this.handleContextAction(action.action, selectedText);
                menu.remove();
            });
            menu.appendChild(item);
        });

        document.body.appendChild(menu);

        // Remove menu when clicking elsewhere
        setTimeout(() => {
            document.addEventListener('click', () => menu.remove(), { once: true });
        }, 100);
    }

    handleContextAction(action, text) {
        chrome.runtime.sendMessage({
            type: 'CONTEXT_ACTION',
            action: action,
            text: text,
            url: window.location.href
        });
    }

    observePageChanges() {
        // Observe DOM changes for dynamic content
        this.observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    this.handlePageChange();
                }
            });
        });

        this.observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    handlePageChange() {
        // Notify background script of page changes
        chrome.runtime.sendMessage({
            type: 'PAGE_CHANGED',
            url: window.location.href,
            title: document.title
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

    highlightElement(selector) {
        const element = document.querySelector(selector);
        if (element) {
            element.style.outline = '2px solid #007bff';
            element.style.outlineOffset = '2px';
            
            setTimeout(() => {
                element.style.outline = '';
                element.style.outlineOffset = '';
            }, 3000);
        }
    }

    extractData(selectors) {
        const data = {};
        selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            data[selector] = Array.from(elements).map(el => el.textContent.trim());
        });
        return data;
    }

    injectOverlay(content) {
        // Remove existing overlay
        const existingOverlay = document.getElementById('copilot-overlay');
        if (existingOverlay) {
            existingOverlay.remove();
        }

        // Create overlay
        const overlay = document.createElement('div');
        overlay.id = 'copilot-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 300px;
            max-height: 400px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            padding: 16px;
            overflow-y: auto;
        `;

        overlay.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h3 style="margin: 0; font-size: 16px;">Copilot Assistant</h3>
                <button id="close-overlay" style="background: none; border: none; font-size: 18px; cursor: pointer;">×</button>
            </div>
            <div style="font-size: 14px; line-height: 1.4;">${content}</div>
        `;

        document.body.appendChild(overlay);

        // Close button functionality
        overlay.querySelector('#close-overlay').addEventListener('click', () => {
            overlay.remove();
        });

        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.remove();
            }
        }, 10000);
    }
}

// Initialize content script
new CopilotContentScript();
