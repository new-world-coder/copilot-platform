/**
 * DOM Observer - MutationObserver stub to capture DOM changes
 * Browser-compatible JavaScript for content scripts
 */

class DOMObserver {
    constructor(options = {}) {
        this.observers = new Map();
        this.changeCallbacks = [];
        this.isObserving = false;
        this.options = {
            childList: true,
            subtree: true,
            attributes: true,
            attributeOldValue: true,
            characterData: true,
            characterDataOldValue: true,
            ...options
        };
        
        this.init();
    }

    init() {
        this.setupMessageListener();
        this.setupStyles();
    }

    setupMessageListener() {
        // Listen for messages from background script
        if (typeof chrome !== 'undefined' && chrome.runtime) {
            chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
                this.handleMessage(request, sender, sendResponse);
            });
        }
    }

    setupStyles() {
        // Inject CSS for highlighting changes
        if (!document.getElementById('dom-observer-styles')) {
            const style = document.createElement('style');
            style.id = 'dom-observer-styles';
            style.textContent = `
                .dom-observer-change {
                    outline: 2px solid #007bff !important;
                    outline-offset: 2px !important;
                    transition: outline 0.3s ease !important;
                }
                
                .dom-observer-added {
                    background-color: rgba(40, 167, 69, 0.2) !important;
                    border: 1px solid #28a745 !important;
                }
                
                .dom-observer-removed {
                    background-color: rgba(220, 53, 69, 0.2) !important;
                    border: 1px solid #dc3545 !important;
                }
                
                .dom-observer-modified {
                    background-color: rgba(255, 193, 7, 0.2) !important;
                    border: 1px solid #ffc107 !important;
                }
            `;
            document.head.appendChild(style);
        }
    }

    handleMessage(request, sender, sendResponse) {
        switch (request.type) {
            case 'START_OBSERVING':
                this.startObserving(request.target);
                sendResponse({ success: true });
                break;
            case 'STOP_OBSERVING':
                this.stopObserving();
                sendResponse({ success: true });
                break;
            case 'GET_CHANGES':
                sendResponse({ changes: this.getRecentChanges() });
                break;
            case 'HIGHLIGHT_CHANGES':
                this.highlightChanges(request.duration || 3000);
                sendResponse({ success: true });
                break;
            default:
                sendResponse({ error: 'Unknown message type' });
        }
    }

    startObserving(target = null) {
        if (this.isObserving) {
            console.log('DOM Observer already running');
            return;
        }

        try {
            const observer = new MutationObserver((mutations) => {
                this.handleMutations(mutations);
            });

            const targetElement = target ? document.querySelector(target) : document.body;
            if (!targetElement) {
                console.error('Target element not found:', target);
                return;
            }

            observer.observe(targetElement, this.options);
            this.observers.set('main', observer);
            this.isObserving = true;

            console.log('DOM Observer started');
        } catch (error) {
            console.error('Error starting DOM Observer:', error);
        }
    }

    stopObserving() {
        this.observers.forEach((observer, key) => {
            observer.disconnect();
        });
        this.observers.clear();
        this.isObserving = false;
        console.log('DOM Observer stopped');
    }

    handleMutations(mutations) {
        const changes = [];
        
        mutations.forEach((mutation) => {
            const change = this.processMutation(mutation);
            if (change) {
                changes.push(change);
            }
        });

        if (changes.length > 0) {
            this.notifyCallbacks(changes);
            this.storeChanges(changes);
        }
    }

    processMutation(mutation) {
        const change = {
            type: mutation.type,
            target: this.getElementInfo(mutation.target),
            timestamp: new Date().toISOString(),
            addedNodes: [],
            removedNodes: [],
            attributeChanges: []
        };

        // Process added nodes
        mutation.addedNodes.forEach((node) => {
            if (node.nodeType === Node.ELEMENT_NODE) {
                change.addedNodes.push(this.getElementInfo(node));
            }
        });

        // Process removed nodes
        mutation.removedNodes.forEach((node) => {
            if (node.nodeType === Node.ELEMENT_NODE) {
                change.removedNodes.push(this.getElementInfo(node));
            }
        });

        // Process attribute changes
        if (mutation.type === 'attributes') {
            change.attributeChanges.push({
                attribute: mutation.attributeName,
                oldValue: mutation.oldValue,
                newValue: mutation.target.getAttribute(mutation.attributeName)
            });
        }

        return change;
    }

    getElementInfo(element) {
        return {
            tagName: element.tagName,
            id: element.id,
            className: element.className,
            textContent: element.textContent ? element.textContent.substring(0, 100) : '',
            attributes: this.getElementAttributes(element),
            selector: this.generateSelector(element)
        };
    }

    getElementAttributes(element) {
        const attributes = {};
        for (let attr of element.attributes) {
            attributes[attr.name] = attr.value;
        }
        return attributes;
    }

    generateSelector(element) {
        if (element.id) {
            return `#${element.id}`;
        }
        
        if (element.className) {
            const classes = element.className.split(' ').filter(c => c);
            if (classes.length > 0) {
                return `.${classes.join('.')}`;
            }
        }
        
        let selector = element.tagName.toLowerCase();
        let parent = element.parentElement;
        let index = 0;
        
        if (parent) {
            const siblings = Array.from(parent.children);
            index = siblings.indexOf(element);
            if (index > 0) {
                selector += `:nth-child(${index + 1})`;
            }
        }
        
        return selector;
    }

    notifyCallbacks(changes) {
        this.changeCallbacks.forEach((callback) => {
            try {
                callback(changes);
            } catch (error) {
                console.error('Error in change callback:', error);
            }
        });
    }

    storeChanges(changes) {
        // Store recent changes for retrieval
        if (!this.recentChanges) {
            this.recentChanges = [];
        }
        
        this.recentChanges.push(...changes);
        
        // Keep only last 100 changes
        if (this.recentChanges.length > 100) {
            this.recentChanges = this.recentChanges.slice(-100);
        }
    }

    getRecentChanges() {
        return this.recentChanges || [];
    }

    addChangeCallback(callback) {
        this.changeCallbacks.push(callback);
    }

    removeChangeCallback(callback) {
        const index = this.changeCallbacks.indexOf(callback);
        if (index > -1) {
            this.changeCallbacks.splice(index, 1);
        }
    }

    highlightChanges(duration = 3000) {
        if (!this.recentChanges) return;

        this.recentChanges.forEach((change) => {
            if (change.target && change.target.selector) {
                const element = document.querySelector(change.target.selector);
                if (element) {
                    element.classList.add('dom-observer-change');
                    
                    setTimeout(() => {
                        element.classList.remove('dom-observer-change');
                    }, duration);
                }
            }
        });
    }

    // Utility methods for specific change types
    observeFormChanges(formSelector = 'form') {
        const forms = document.querySelectorAll(formSelector);
        forms.forEach((form) => {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'attributes' && 
                        mutation.attributeName === 'value') {
                        this.handleFormChange(mutation.target);
                    }
                });
            });
            
            observer.observe(form, {
                subtree: true,
                attributes: true,
                attributeFilter: ['value']
            });
            
            this.observers.set(`form-${form.id || 'default'}`, observer);
        });
    }

    handleFormChange(input) {
        const change = {
            type: 'form_change',
            target: this.getElementInfo(input),
            timestamp: new Date().toISOString(),
            value: input.value,
            name: input.name
        };
        
        this.notifyCallbacks([change]);
        this.storeChanges([change]);
    }

    observeTextChanges(textSelector = null) {
        const target = textSelector ? document.querySelector(textSelector) : document.body;
        if (!target) return;

        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'characterData') {
                    this.handleTextChange(mutation.target);
                }
            });
        });

        observer.observe(target, {
            subtree: true,
            characterData: true,
            characterDataOldValue: true
        });

        this.observers.set('text-observer', observer);
    }

    handleTextChange(textNode) {
        const change = {
            type: 'text_change',
            target: this.getElementInfo(textNode.parentElement),
            timestamp: new Date().toISOString(),
            oldText: textNode.data,
            newText: textNode.data
        };
        
        this.notifyCallbacks([change]);
        this.storeChanges([change]);
    }

    // Method to detect specific patterns
    detectPattern(pattern, callback) {
        const patternCallback = (changes) => {
            changes.forEach((change) => {
                if (this.matchesPattern(change, pattern)) {
                    callback(change);
                }
            });
        };
        
        this.addChangeCallback(patternCallback);
        return patternCallback;
    }

    matchesPattern(change, pattern) {
        // Simple pattern matching - can be extended
        if (pattern.type && change.type !== pattern.type) {
            return false;
        }
        
        if (pattern.tagName && change.target.tagName !== pattern.tagName) {
            return false;
        }
        
        if (pattern.className && !change.target.className.includes(pattern.className)) {
            return false;
        }
        
        return true;
    }

    // Cleanup method
    destroy() {
        this.stopObserving();
        this.changeCallbacks = [];
        this.recentChanges = [];
    }
}

// Global instance for easy access
window.domObserver = new DOMObserver();

// Auto-start if in content script context
if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.id) {
    // This is a content script, auto-start observing
    window.domObserver.startObserving();
    
    // Add default callback to log changes
    window.domObserver.addChangeCallback((changes) => {
        console.log('DOM Changes detected:', changes);
    });
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DOMObserver;
}
