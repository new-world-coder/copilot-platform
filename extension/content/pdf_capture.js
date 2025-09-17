// PDF capture content script for Copilot Platform Extension
class PDFCapture {
    constructor() {
        this.isPDF = false;
        this.pdfText = '';
        this.init();
    }

    init() {
        this.checkIfPDF();
        this.setupMessageListener();
        
        if (this.isPDF) {
            this.extractPDFText();
        }
    }

    checkIfPDF() {
        // Check if current page is a PDF
        this.isPDF = window.location.href.includes('.pdf') || 
                    document.contentType === 'application/pdf' ||
                    document.querySelector('embed[type="application/pdf"]') ||
                    document.querySelector('object[type="application/pdf"]');
        
        console.log('PDF detected:', this.isPDF);
    }

    setupMessageListener() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            switch (request.type) {
                case 'EXTRACT_PDF_TEXT':
                    this.extractPDFText();
                    sendResponse({ success: true });
                    break;
                case 'GET_PDF_TEXT':
                    sendResponse({ text: this.pdfText });
                    break;
                default:
                    sendResponse({ error: 'Unknown message type' });
            }
        });
    }

    async extractPDFText() {
        try {
            if (!this.isPDF) {
                console.log('Not a PDF page');
                return;
            }

            // Method 1: Try to extract from PDF.js viewer
            const pdfText = await this.extractFromPDFJS();
            
            if (pdfText) {
                this.pdfText = pdfText;
                this.sendPDFText();
                return;
            }

            // Method 2: Try to extract from embedded PDF
            const embeddedText = await this.extractFromEmbedded();
            
            if (embeddedText) {
                this.pdfText = embeddedText;
                this.sendPDFText();
                return;
            }

            // Method 3: Fallback to page text (limited effectiveness)
            const pageText = this.extractFromPageText();
            if (pageText) {
                this.pdfText = pageText;
                this.sendPDFText();
            }

        } catch (error) {
            console.error('Error extracting PDF text:', error);
        }
    }

    async extractFromPDFJS() {
        try {
            // Check if PDF.js is available
            if (typeof window.PDFViewerApplication !== 'undefined') {
                const pdfViewer = window.PDFViewerApplication.pdfViewer;
                const currentPage = pdfViewer.currentPageNumber;
                const page = await pdfViewer.getPageView(currentPage - 1);
                
                if (page && page.textLayer) {
                    return page.textLayer.textContent;
                }
            }

            // Try alternative PDF.js access
            if (typeof window.pdfjsLib !== 'undefined') {
                // This would require more complex PDF.js integration
                console.log('PDF.js library detected but extraction not implemented');
            }

            return null;
        } catch (error) {
            console.error('Error extracting from PDF.js:', error);
            return null;
        }
    }

    async extractFromEmbedded() {
        try {
            // Look for embedded PDF elements
            const embed = document.querySelector('embed[type="application/pdf"]');
            const object = document.querySelector('object[type="application/pdf"]');
            
            if (embed || object) {
                // For embedded PDFs, we can only extract limited text
                // This is a stub implementation
                console.log('Embedded PDF detected - full text extraction not available');
                return null;
            }

            return null;
        } catch (error) {
            console.error('Error extracting from embedded PDF:', error);
            return null;
        }
    }

    extractFromPageText() {
        try {
            // Extract text from the page (works for some PDF viewers)
            const textContent = document.body.innerText;
            
            // Filter out common PDF viewer UI elements
            const filteredText = textContent
                .split('\n')
                .filter(line => {
                    const trimmed = line.trim();
                    return trimmed.length > 0 && 
                           !trimmed.match(/^\d+\s*$/) && // Page numbers
                           !trimmed.includes('PDF') &&
                           !trimmed.includes('Zoom') &&
                           !trimmed.includes('Page');
                })
                .join('\n');

            return filteredText.length > 100 ? filteredText : null;
        } catch (error) {
            console.error('Error extracting from page text:', error);
            return null;
        }
    }

    sendPDFText() {
        if (this.pdfText && this.pdfText.length > 0) {
            chrome.runtime.sendMessage({
                type: 'PDF_TEXT_EXTRACTED',
                text: this.pdfText,
                url: window.location.href,
                timestamp: new Date().toISOString()
            });
        }
    }

    // Stub function for PDF.js integration
    async initializePDFJS() {
        // This would be implemented with proper PDF.js integration
        console.log('PDF.js initialization stub');
        
        // Example of what this might look like:
        /*
        const pdfjsLib = await import('pdfjs-dist/build/pdf');
        const pdf = await pdfjsLib.getDocument(window.location.href).promise;
        
        let fullText = '';
        for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const textContent = await page.getTextContent();
            const pageText = textContent.items.map(item => item.str).join(' ');
            fullText += pageText + '\n';
        }
        
        return fullText;
        */
    }
}

// Initialize PDF capture
new PDFCapture();
