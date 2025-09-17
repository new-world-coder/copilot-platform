// Background script for Copilot Platform Extension
class CopilotBackground {
    constructor() {
        this.agentUrl = 'http://localhost:8000';
        this.init();
    }

    init() {
        this.setupMessageListener();
        this.setupContextMenus();
        this.setupTabListener();
    }

    setupMessageListener() {
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            this.handleMessage(request, sender, sendResponse);
            return true; // Keep message channel open for async response
        });
    }

    async handleMessage(request, sender, sendResponse) {
        try {
            switch (request.type) {
                case 'SEND_MESSAGE':
                    const response = await this.sendToAgent(request);
                    sendResponse(response);
                    break;
                
                case 'GET_PAGE_CONTENT':
                    const content = await this.getPageContent(sender.tab.id);
                    sendResponse(content);
                    break;
                
                case 'CONTEXT_ACTION':
                    await this.handleContextAction(request, sender);
                    sendResponse({ success: true });
                    break;
                
                case 'PAGE_CHANGED':
                    await this.handlePageChange(request, sender);
                    sendResponse({ success: true });
                    break;
                
                default:
                    sendResponse({ error: 'Unknown message type' });
            }
        } catch (error) {
            console.error('Background script error:', error);
            sendResponse({ error: error.message });
        }
    }

    async sendToAgent(request) {
        try {
            const response = await fetch(`${this.agentUrl}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: request.message,
                    url: request.url,
                    timestamp: new Date().toISOString()
                })
            });

            if (!response.ok) {
                throw new Error(`Agent responded with status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error communicating with agent:', error);
            return {
                message: 'Sorry, I cannot connect to the AI agent. Please make sure the agent is running.',
                error: true
            };
        }
    }

    async getPageContent(tabId) {
        return new Promise((resolve) => {
            chrome.tabs.sendMessage(tabId, { type: 'GET_PAGE_CONTENT' }, (response) => {
                resolve(response || { error: 'Failed to get page content' });
            });
        });
    }

    async handleContextAction(request, sender) {
        const actions = {
            ask: `Can you explain this text: "${request.text}"`,
            summarize: `Please summarize this text: "${request.text}"`,
            translate: `Translate this text to English: "${request.text}"`,
            extract: `Extract the key points from this text: "${request.text}"`
        };

        const message = actions[request.action];
        if (message) {
            // Send to sidebar if open
            chrome.runtime.sendMessage({
                type: 'CONTEXT_MESSAGE',
                message: message,
                url: request.url
            });
        }
    }

    async handlePageChange(request, sender) {
        // Log page changes for analytics/debugging
        console.log('Page changed:', request.url, request.title);
        
        // Could send to agent for processing
        try {
            await fetch(`${this.agentUrl}/api/page-change`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: request.url,
                    title: request.title,
                    timestamp: new Date().toISOString()
                })
            });
        } catch (error) {
            console.error('Error reporting page change:', error);
        }
    }

    setupContextMenus() {
        // Create context menu items
        chrome.contextMenus.create({
            id: 'copilot-ask',
            title: 'Ask Copilot about this',
            contexts: ['selection']
        });

        chrome.contextMenus.create({
            id: 'copilot-summarize',
            title: 'Summarize with Copilot',
            contexts: ['selection']
        });

        chrome.contextMenus.create({
            id: 'copilot-translate',
            title: 'Translate with Copilot',
            contexts: ['selection']
        });

        // Handle context menu clicks
        chrome.contextMenus.onClicked.addListener((info, tab) => {
            this.handleContextMenuClick(info, tab);
        });
    }

    async handleContextMenuClick(info, tab) {
        const actions = {
            'copilot-ask': `Can you explain this text: "${info.selectionText}"`,
            'copilot-summarize': `Please summarize this text: "${info.selectionText}"`,
            'copilot-translate': `Translate this text to English: "${info.selectionText}"`
        };

        const message = actions[info.menuItemId];
        if (message) {
            // Open sidebar and send message
            await chrome.sidePanel.open({ tabId: tab.id });
            
            // Send message to sidebar
            setTimeout(() => {
                chrome.runtime.sendMessage({
                    type: 'CONTEXT_MESSAGE',
                    message: message,
                    url: tab.url
                });
            }, 500);
        }
    }

    setupTabListener() {
        // Listen for tab updates
        chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
            if (changeInfo.status === 'complete' && tab.url) {
                this.handleTabUpdate(tab);
            }
        });
    }

    async handleTabUpdate(tab) {
        // Could inject content script or notify agent
        console.log('Tab updated:', tab.url);
    }
}

// Initialize background script
new CopilotBackground();
