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
                
                case 'SEND_RAG_MESSAGE':
                    const ragResponse = await this.sendRAGToAgent(request);
                    sendResponse(ragResponse);
                    break;
                
                case 'GET_PAGE_CONTENT':
                    const content = await this.getPageContent(sender.tab.id);
                    sendResponse(content);
                    break;
                
                case 'SELECTED_TEXT':
                    await this.handleSelectedText(request, sender);
                    sendResponse({ success: true });
                    break;
                
                case 'PDF_TEXT_EXTRACTED':
                    await this.handlePDFText(request, sender);
                    sendResponse({ success: true });
                    break;
                
                case 'HIGHLIGHT_TEXT':
                    await this.highlightText(request, sender);
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
                    llm_provider: request.llm_provider,
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

    async sendRAGToAgent(request) {
        try {
            const response = await fetch(`${this.agentUrl}/rag/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: request.message,
                    model: request.llm_provider === 'local' ? 'local' : 'gpt-4',
                    provider: request.llm_provider,
                    top_k: 3,
                    use_legal_rag: true,
                    temperature: 0.7,
                    max_tokens: 1000
                })
            });

            if (!response.ok) {
                throw new Error(`Agent responded with status: ${response.status}`);
            }

            const data = await response.json();
            return {
                answer: data.answer,
                citations: data.citations,
                query: data.query,
                model: data.model,
                provider: data.provider
            };
        } catch (error) {
            console.error('Error communicating with RAG agent:', error);
            return {
                answer: 'Sorry, I cannot connect to the AI agent. Please make sure the agent is running.',
                citations: [],
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

    async handleSelectedText(request, sender) {
        console.log('Selected text received:', request.text);
        
        // Store selected text for sidebar access
        await chrome.storage.local.set({
            selectedText: request.text,
            selectedUrl: sender.tab.url,
            timestamp: Date.now()
        });
        
        // Notify sidebar if open
        chrome.runtime.sendMessage({
            type: 'TEXT_SELECTED',
            text: request.text,
            url: sender.tab.url
        });
    }

    async handlePDFText(request, sender) {
        console.log('PDF text extracted:', request.text.length, 'characters');
        
        // Store PDF text for sidebar access
        await chrome.storage.local.set({
            pdfText: request.text,
            pdfUrl: sender.tab.url,
            timestamp: Date.now()
        });
        
        // Notify sidebar if open
        chrome.runtime.sendMessage({
            type: 'PDF_TEXT_READY',
            text: request.text,
            url: sender.tab.url
        });
    }

    async highlightText(request, sender) {
        // Send highlight request to content script
        chrome.tabs.sendMessage(sender.tab.id, {
            type: 'HIGHLIGHT_SPANS',
            spans: request.spans
        });
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
        // Check if it's a PDF
        if (tab.url && tab.url.includes('.pdf')) {
            console.log('PDF detected:', tab.url);
        }
    }
}

// Initialize background script
new CopilotBackground();
