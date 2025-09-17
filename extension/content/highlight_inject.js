// Highlight injection content script for Copilot Platform Extension
class HighlightInject {
    constructor() {
        this.highlightedSpans = new Set();
        this.highlightId = 'copilot-highlight';
        this.init();
    }

    init() {
        this.setupMessageListener();
        this.setupStyles();
    }

    setupMessageListener() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            switch (request.type) {
                case 'HIGHLIGHT_SPANS':
                    this.highlightSpans(request.spans);
                    sendResponse({ success: true });
                    break;
                case 'CLEAR_HIGHLIGHTS':
                    this.clearHighlights();
                    sendResponse({ success: true });
                    break;
                case 'HIGHLIGHT_TEXT':
                    this.highlightText(request.text, request.color);
                    sendResponse({ success: true });
                    break;
                default:
                    sendResponse({ error: 'Unknown message type' });
            }
        });
    }

    setupStyles() {
        // Inject CSS styles for highlighting
        if (!document.getElementById('copilot-highlight-styles')) {
            const style = document.createElement('style');
            style.id = 'copilot-highlight-styles';
            style.textContent = `
                .copilot-highlight {
                    background-color: rgba(255, 235, 59, 0.3) !important;
                    border: 1px solid #ffc107 !important;
                    border-radius: 2px !important;
                    padding: 1px 2px !important;
                    transition: all 0.3s ease !important;
                }
                
                .copilot-highlight:hover {
                    background-color: rgba(255, 235, 59, 0.5) !important;
                    border-color: #ff9800 !important;
                }
                
                .copilot-highlight-temporary {
                    background-color: rgba(76, 175, 80, 0.3) !important;
                    border: 1px solid #4caf50 !important;
                    border-radius: 2px !important;
                    padding: 1px 2px !important;
                    animation: copilot-pulse 2s ease-in-out;
                }
                
                @keyframes copilot-pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.7; }
                }
            `;
            document.head.appendChild(style);
        }
    }

    highlightSpans(spans) {
        try {
            // Clear existing highlights first
            this.clearHighlights();

            spans.forEach((span, index) => {
                this.highlightSpan(span, index);
            });

            console.log(`Highlighted ${spans.length} spans`);
        } catch (error) {
            console.error('Error highlighting spans:', error);
        }
    }

    highlightSpan(span, index = 0) {
        try {
            const { text, startOffset, endOffset, elementSelector } = span;

            if (elementSelector) {
                // Highlight specific element
                const element = document.querySelector(elementSelector);
                if (element) {
                    this.highlightElement(element, index);
                    return;
                }
            }

            // Find and highlight text in the document
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );

            let node;
            let currentOffset = 0;
            let found = false;

            while (node = walker.nextNode()) {
                const nodeText = node.textContent;
                const nodeLength = nodeText.length;

                if (currentOffset + nodeLength >= startOffset && currentOffset <= endOffset) {
                    const startInNode = Math.max(0, startOffset - currentOffset);
                    const endInNode = Math.min(nodeLength, endOffset - currentOffset);

                    if (startInNode < endInNode) {
                        this.highlightTextInNode(node, startInNode, endInNode, index);
                        found = true;
                    }
                }

                currentOffset += nodeLength;
            }

            if (!found) {
                console.warn('Could not find text to highlight:', text);
            }
        } catch (error) {
            console.error('Error highlighting span:', error);
        }
    }

    highlightTextInNode(textNode, startOffset, endOffset, index) {
        try {
            const parent = textNode.parentNode;
            const text = textNode.textContent;
            
            const beforeText = text.substring(0, startOffset);
            const highlightText = text.substring(startOffset, endOffset);
            const afterText = text.substring(endOffset);

            // Create highlight span
            const highlightSpan = document.createElement('span');
            highlightSpan.className = 'copilot-highlight';
            highlightSpan.setAttribute('data-copilot-highlight-id', index);
            highlightSpan.textContent = highlightText;

            // Replace text node with highlighted version
            const fragment = document.createDocumentFragment();
            
            if (beforeText) {
                fragment.appendChild(document.createTextNode(beforeText));
            }
            
            fragment.appendChild(highlightSpan);
            
            if (afterText) {
                fragment.appendChild(document.createTextNode(afterText));
            }

            parent.replaceChild(fragment, textNode);
            
            // Store reference for cleanup
            this.highlightedSpans.add(highlightSpan);
        } catch (error) {
            console.error('Error highlighting text in node:', error);
        }
    }

    highlightElement(element, index = 0) {
        try {
            element.classList.add('copilot-highlight');
            element.setAttribute('data-copilot-highlight-id', index);
            this.highlightedSpans.add(element);
        } catch (error) {
            console.error('Error highlighting element:', error);
        }
    }

    highlightText(text, color = 'yellow') {
        try {
            // Find all instances of the text and highlight them
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );

            let node;
            const nodesToProcess = [];

            while (node = walker.nextNode()) {
                if (node.textContent.includes(text)) {
                    nodesToProcess.push(node);
                }
            }

            nodesToProcess.forEach((textNode, index) => {
                this.highlightTextInNode(textNode, 0, textNode.textContent.length, index);
            });

            console.log(`Highlighted text "${text}" in ${nodesToProcess.length} locations`);
        } catch (error) {
            console.error('Error highlighting text:', error);
        }
    }

    clearHighlights() {
        try {
            // Remove all highlighted spans
            this.highlightedSpans.forEach(span => {
                if (span.parentNode) {
                    // Replace highlighted span with its text content
                    const textNode = document.createTextNode(span.textContent);
                    span.parentNode.replaceChild(textNode, span);
                }
            });

            // Remove highlight classes from elements
            const highlightedElements = document.querySelectorAll('.copilot-highlight');
            highlightedElements.forEach(element => {
                element.classList.remove('copilot-highlight');
                element.removeAttribute('data-copilot-highlight-id');
            });

            this.highlightedSpans.clear();
            console.log('Cleared all highlights');
        } catch (error) {
            console.error('Error clearing highlights:', error);
        }
    }

    // Utility method to get highlighted text
    getHighlightedText() {
        const highlightedTexts = [];
        
        this.highlightedSpans.forEach(span => {
            if (span.textContent) {
                highlightedTexts.push(span.textContent);
            }
        });

        return highlightedTexts;
    }

    // Utility method to scroll to first highlight
    scrollToFirstHighlight() {
        const firstHighlight = document.querySelector('.copilot-highlight');
        if (firstHighlight) {
            firstHighlight.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });
        }
    }
}

// Initialize highlight injection
new HighlightInject();
