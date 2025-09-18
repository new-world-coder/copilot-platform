/**
 * Watermark Remover Content Script
 * Removes "Made with Emergent" watermark from the page
 */
debugger; // Breakpoint for debugging

(function() {
    'use strict';

    // Function to remove watermark
    function removeWatermark() {
        // Look for the specific watermark div
        const watermarkSelectors = [
            'div[style*="flex-direction: row"]',
            'div[style*="width: 20px; height: 20px"]',
            'img[src*="avatars.githubusercontent.com/in/1201222"]',
            'p:contains("Made with Emergent")'
        ];

        let removed = false;

        // Try different selectors to find the watermark
        watermarkSelectors.forEach(selector => {
            try {
                const elements = document.querySelectorAll(selector);
                elements.forEach(element => {
                    // Check if this element contains the watermark text or image
                    if (element.textContent && element.textContent.includes('Made with Emergent')) {
                        element.remove();
                        removed = true;
                        console.log('Removed watermark element:', element);
                    } else if (element.querySelector && element.querySelector('img[src*="avatars.githubusercontent.com/in/1201222"]')) {
                        element.remove();
                        removed = true;
                        console.log('Removed watermark element with GitHub avatar:', element);
                    } else if (element.querySelector && element.querySelector('p:contains("Made with Emergent")')) {
                        element.remove();
                        removed = true;
                        console.log('Removed watermark element with text:', element);
                    }
                });
            } catch (e) {
                // Ignore selector errors
            }
        });

        // Also check for elements with specific styling that matches the watermark
        const allDivs = document.querySelectorAll('div');
        allDivs.forEach(div => {
            const style = div.getAttribute('style') || '';
            if (style.includes('flex-direction: row') && 
                style.includes('align-items: center') &&
                div.querySelector('img[src*="avatars.githubusercontent.com"]') &&
                div.textContent.includes('Made with Emergent')) {
                div.remove();
                removed = true;
                console.log('Removed watermark div with specific styling:', div);
            }
        });

        return removed;
    }

    // Function to remove watermark from dynamically added content
    function removeWatermarkFromNewContent() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // Check if the added node contains watermark
                        if (node.textContent && node.textContent.includes('Made with Emergent')) {
                            node.remove();
                            console.log('Removed dynamically added watermark:', node);
                        }
                        
                        // Check child elements
                        const watermarkElements = node.querySelectorAll('*');
                        watermarkElements.forEach(element => {
                            if (element.textContent && element.textContent.includes('Made with Emergent')) {
                                element.remove();
                                console.log('Removed watermark from child element:', element);
                            }
                        });
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    // Remove watermark immediately
    if (removeWatermark()) {
        console.log('Watermark removed on page load');
    }

    // Set up observer for dynamically added content
    if (document.body) {
        removeWatermarkFromNewContent();
    } else {
        // Wait for body to be available
        document.addEventListener('DOMContentLoaded', () => {
            removeWatermark();
            removeWatermarkFromNewContent();
        });
    }

    // Also remove watermark after a delay to catch late-loading content
    setTimeout(() => {
        removeWatermark();
    }, 1000);

    // Remove watermark every 5 seconds to catch any persistent watermarks
    setInterval(() => {
        removeWatermark();
    }, 5000);

})();
