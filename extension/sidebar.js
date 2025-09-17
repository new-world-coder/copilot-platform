class CopilotSidebar {
    constructor() {
        this.messagesContainer = document.getElementById('messages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkConnection();
        this.loadSettings();
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

        // Tool button actions
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                this.handleToolAction(action);
            });
        });

        // Settings button
        document.getElementById('settingsBtn').addEventListener('click', () => {
            this.openSettings();
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
            // Send message to background script
            const response = await chrome.runtime.sendMessage({
                type: 'SEND_MESSAGE',
                message: message,
                url: await this.getCurrentTabUrl()
            });

            // Add assistant response to UI
            this.addMessage(response.message, 'assistant');
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

    async handleToolAction(action) {
        const actions = {
            summarize: 'Summarize the current page content',
            extract: 'Extract key data from this page',
            analyze: 'Analyze the content structure and patterns',
            translate: 'Translate this page to English'
        };

        const message = actions[action];
        if (message) {
            this.messageInput.value = message;
            this.sendMessage();
        }
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

    loadSettings() {
        chrome.storage.sync.get(['copilotSettings'], (result) => {
            const settings = result.copilotSettings || {};
            // Apply settings to UI
            console.log('Loaded settings:', settings);
        });
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
