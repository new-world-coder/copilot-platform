class CopilotSidebar {
    constructor() {
        this.messagesContainer = document.getElementById('messages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        this.llmProvider = document.getElementById('llmProvider');
        
        this.selectedTextInfo = document.getElementById('selectedTextInfo');
        this.selectedTextPreview = document.getElementById('selectedTextPreview');
        this.pdfTextInfo = document.getElementById('pdfTextInfo');
        this.pdfTextPreview = document.getElementById('pdfTextPreview');
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkConnection();
        this.loadSettings();
        this.loadContext();
    }

    setupEventListeners() {
        // Send message on button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter key (but allow Shift+Enter for new lines)
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // LLM provider change
        this.llmProvider.addEventListener('change', () => {
            this.saveSettings();
        });

        // Settings button
        document.getElementById('settingsBtn').addEventListener('click', () => {
            this.openSettings();
        });

        // Listen for messages from background script
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            this.handleBackgroundMessage(request);
        });
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        // Add user message to UI
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.sendButton.disabled = true;

        try {
            // Send message to background script with RAG enabled
            const response = await chrome.runtime.sendMessage({
                type: 'SEND_RAG_MESSAGE',
                message: message,
                url: await this.getCurrentTabUrl(),
                llm_provider: this.llmProvider.value,
                use_rag: true
            });

            // Add assistant response to UI with citations
            this.addMessageWithCitations(response.answer, response.citations, 'assistant');
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
        } finally {
            this.sendButton.disabled = false;
            this.messageInput.focus();
        }
    }

    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const p = document.createElement('p');
        p.textContent = content;
        messageDiv.appendChild(p);
        
        this.messagesContainer.appendChild(messageDiv);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    addMessageWithCitations(content, citations, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        // Add main answer
        const p = document.createElement('p');
        p.textContent = content;
        messageDiv.appendChild(p);
        
        // Add citations if available
        if (citations && citations.length > 0) {
            const citationsDiv = document.createElement('div');
            citationsDiv.className = 'citations';
            
            const citationsHeader = document.createElement('div');
            citationsHeader.className = 'citations-header';
            citationsHeader.textContent = `📚 Sources (${citations.length})`;
            citationsDiv.appendChild(citationsHeader);
            
            citations.forEach((citation, index) => {
                const citationItem = document.createElement('div');
                citationItem.className = 'citation-item';
                
                const citationTitle = document.createElement('div');
                citationTitle.className = 'citation-title';
                citationTitle.textContent = `${index + 1}. ${citation.source}`;
                citationItem.appendChild(citationTitle);
                
                const citationMeta = document.createElement('div');
                citationMeta.className = 'citation-meta';
                citationMeta.innerHTML = `
                    <span class="citation-type">${citation.document_type || 'Document'}</span>
                    <span class="citation-score">Score: ${citation.similarity_score.toFixed(3)}</span>
                `;
                citationItem.appendChild(citationMeta);
                
                const citationPreview = document.createElement('div');
                citationPreview.className = 'citation-preview';
                citationPreview.textContent = citation.text_preview;
                citationItem.appendChild(citationPreview);
                
                // Add click handler to expand/collapse
                citationItem.addEventListener('click', () => {
                    citationItem.classList.toggle('expanded');
                });
                
                citationsDiv.appendChild(citationItem);
            });
            
            messageDiv.appendChild(citationsDiv);
        }
        
        this.messagesContainer.appendChild(messageDiv);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    handleBackgroundMessage(request) {
        switch (request.type) {
            case 'TEXT_SELECTED':
                this.showSelectedText(request.text);
                break;
            case 'PDF_TEXT_READY':
                this.showPDFText(request.text);
                break;
            case 'CONTEXT_MESSAGE':
                this.messageInput.value = request.message;
                this.sendMessage();
                break;
        }
    }

    showSelectedText(text) {
        this.selectedTextPreview.textContent = text.length > 100 ? 
            text.substring(0, 100) + '...' : text;
        this.selectedTextInfo.style.display = 'block';
    }

    showPDFText(text) {
        this.pdfTextPreview.textContent = text.length > 100 ? 
            text.substring(0, 100) + '...' : text;
        this.pdfTextInfo.style.display = 'block';
    }

    async getCurrentTabUrl() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            return tab?.url || '';
        } catch (error) {
            console.error('Error getting current tab URL:', error);
            return '';
        }
    }

    async checkConnection() {
        try {
            // Check if agent is running
            const response = await fetch('http://localhost:8000/health');
            if (response.ok) {
                this.updateStatus('connected', 'Connected');
            } else {
                this.updateStatus('error', 'Agent Offline');
            }
        } catch (error) {
            this.updateStatus('error', 'Agent Offline');
        }
    }

    updateStatus(status, text) {
        this.statusDot.className = `status-dot ${status}`;
        this.statusText.textContent = text;
    }

    async loadSettings() {
        try {
            const result = await chrome.storage.sync.get(['copilotSettings']);
            const settings = result.copilotSettings || {};
            
            if (settings.llmProvider) {
                this.llmProvider.value = settings.llmProvider;
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    async saveSettings() {
        try {
            const settings = {
                llmProvider: this.llmProvider.value
            };
            
            await chrome.storage.sync.set({ copilotSettings: settings });
        } catch (error) {
            console.error('Error saving settings:', error);
        }
    }

    async loadContext() {
        try {
            const result = await chrome.storage.local.get(['selectedText', 'pdfText']);
            
            if (result.selectedText) {
                this.showSelectedText(result.selectedText);
            }
            
            if (result.pdfText) {
                this.showPDFText(result.pdfText);
            }
        } catch (error) {
            console.error('Error loading context:', error);
        }
    }

    openSettings() {
        // Open settings popup or navigate to settings page
        chrome.runtime.openOptionsPage();
    }
}

// Initialize sidebar when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CopilotSidebar();
});
