document.addEventListener('DOMContentLoaded', async () => {
    const openSidebarBtn = document.getElementById('openSidebar');
    const summarizePageBtn = document.getElementById('summarizePage');
    const extractDataBtn = document.getElementById('extractData');
    const status = document.getElementById('status');

    // Check agent connection
    try {
        const response = await fetch('http://localhost:8000/health');
        status.textContent = response.ok ? 'Agent Connected' : 'Agent Offline';
        status.style.color = response.ok ? 'green' : 'red';
    } catch {
        status.textContent = 'Agent Offline';
        status.style.color = 'red';
    }

    // Open sidebar
    openSidebarBtn.addEventListener('click', async () => {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        await chrome.sidePanel.open({ tabId: tab.id });
        window.close();
    });

    // Summarize page
    summarizePageBtn.addEventListener('click', async () => {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        await chrome.sidePanel.open({ tabId: tab.id });
        chrome.runtime.sendMessage({
            type: 'CONTEXT_MESSAGE',
            message: 'Please summarize this page',
            url: tab.url
        });
        window.close();
    });

    // Extract data
    extractDataBtn.addEventListener('click', async () => {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        await chrome.sidePanel.open({ tabId: tab.id });
        chrome.runtime.sendMessage({
            type: 'CONTEXT_MESSAGE',
            message: 'Extract key data from this page',
            url: tab.url
        });
        window.close();
    });
});
