# Copilot Platform

An AI-powered productivity platform that combines a Chrome extension with a desktop agent to provide intelligent assistance across web browsing, document processing, and task management.

## 🏗️ Architecture

The platform consists of several interconnected components:

- **Chrome Extension** (`extension/`) - Browser-based UI and content interaction
- **Desktop Agent** (`agent/`) - Python FastAPI backend service
- **Reusable Libraries** (`libs/`) - Common utilities for PDF processing, web search, task extraction, etc.
- **Vertical-Specific Code** (`verticals/`) - Domain-specific implementations (e.g., legal)
- **RAG System** (`rag/`) - Embedding, indexing, and retrieval components
- **LLM Connectors** (`llm/`) - Integration with various language models
- **Tests** (`tests/`) - Unit tests and integration tests

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+ (for extension development)
- Chrome browser
- OpenAI API key (or Anthropic API key)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd copilot-platform
```

### 2. Setup Desktop Agent

```bash
cd agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create environment file:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

### 3. Run the Agent

```bash
python main.py
```

The agent will start on `http://localhost:8000`

### 4. Install Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" and select the `extension/` directory
4. The extension icon should appear in your browser toolbar

### 5. Test the Setup

1. Open any webpage
2. Click the extension icon to open the sidebar
3. Try asking a question or using one of the quick actions

## 📁 Project Structure

```
copilot-platform/
├── extension/                 # Chrome extension
│   ├── manifest.json         # Extension manifest
│   ├── sidebar.html          # Main sidebar UI
│   ├── sidebar.css           # Sidebar styles
│   ├── sidebar.js            # Sidebar functionality
│   ├── content.js            # Content script
│   ├── content.css           # Content script styles
│   ├── background.js         # Background script
│   ├── popup.html            # Extension popup
│   └── popup.js              # Popup functionality
├── agent/                    # Python FastAPI backend
│   ├── main.py               # Application entry point
│   ├── requirements.txt      # Python dependencies
│   ├── core/                 # Core application modules
│   │   ├── config.py         # Configuration settings
│   │   ├── database.py       # Database setup
│   │   ├── llm_client.py     # LLM client wrapper
│   │   └── task_manager.py   # Task management
│   ├── routers/              # API route handlers
│   │   ├── health.py         # Health check endpoints
│   │   ├── chat.py           # Chat endpoints
│   │   └── tasks.py          # Task endpoints
│   ├── models/               # Data models
│   └── services/             # Business logic services
├── libs/                     # Reusable libraries
│   ├── pdf_utils.py          # PDF processing utilities
│   ├── web_search.py         # Web search functionality
│   ├── task_extraction.py    # Task extraction from text
│   ├── dom_observer.py       # DOM change observation
│   └── utils.py              # General utilities
├── verticals/                # Domain-specific code
│   └── legal/                # Legal domain
│       ├── contract_analyzer.py
│       ├── legal_document_processor.py
│       ├── compliance_checker.py
│       └── case_law_search.py
├── rag/                      # RAG components
│   ├── embedding_service.py  # Text embedding service
│   ├── vector_store.py       # Vector database
│   └── retrieval_service.py  # Document retrieval
├── llm/                      # LLM connectors
│   ├── openai_client.py      # OpenAI integration
│   ├── anthropic_client.py   # Anthropic integration
│   └── llm_factory.py        # LLM client factory
├── tests/                    # Unit tests
│   ├── test_libs.py          # Library tests
│   ├── test_agent.py         # Agent tests
│   └── test_extension.py     # Extension tests
└── README.md                 # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `agent/` directory:

```env
# Server Configuration
HOST=localhost
PORT=8000
DEBUG=false

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4

# Database Configuration
DATABASE_URL=sqlite:///./copilot.db

# RAG Configuration
EMBEDDING_MODEL=text-embedding-ada-002
VECTOR_STORE_PATH=./data/vector_store

# Security
SECRET_KEY=your_secret_key_here
```

### Extension Configuration

The extension automatically connects to the agent running on `localhost:8000`. To change this:

1. Edit `extension/background.js`
2. Update the `agentUrl` variable
3. Reload the extension in Chrome

## 🛠️ Development

### Running Tests

```bash
cd agent
python -m pytest tests/ -v
```

### Code Formatting

```bash
# Format Python code
black agent/ libs/ verticals/ rag/ llm/ tests/
isort agent/ libs/ verticals/ rag/ llm/ tests/

# Lint Python code
flake8 agent/ libs/ verticals/ rag/ llm/ tests/
```

### Extension Development

The extension uses vanilla JavaScript and CSS. For development:

1. Make changes to extension files
2. Go to `chrome://extensions/`
3. Click the refresh icon on the extension
4. Test your changes

## 📚 API Documentation

### Agent Endpoints

#### Health Check
- `GET /health/` - Basic health check
- `GET /health/detailed` - Detailed health check with component status

#### Chat
- `POST /api/chat` - Send message to AI agent
- `POST /api/chat/stream` - Stream chat response

#### Tasks
- `POST /api/tasks` - Create new task
- `GET /api/tasks/{task_id}` - Get task status
- `GET /api/tasks` - List recent tasks

### Extension API

The extension communicates with the agent via Chrome runtime messages:

```javascript
// Send message to agent
chrome.runtime.sendMessage({
    type: 'SEND_MESSAGE',
    message: 'Your message here',
    url: window.location.href
});

// Get page content
chrome.runtime.sendMessage({
    type: 'GET_PAGE_CONTENT'
});
```

## 🔌 Extending the Platform

### Adding New Verticals

1. Create a new directory under `verticals/`
2. Implement domain-specific processors and analyzers
3. Add tests in `tests/test_verticals.py`
4. Update the main agent to include your vertical

### Adding New LLM Providers

1. Create a new client in `llm/`
2. Implement the required interface methods
3. Update `llm_factory.py` to include your provider
4. Add configuration options

### Adding New Libraries

1. Create your module in `libs/`
2. Follow the existing patterns for error handling and logging
3. Add comprehensive tests
4. Update `libs/__init__.py` to export your module

## 🐛 Troubleshooting

### Common Issues

**Extension not connecting to agent:**
- Ensure the agent is running on `localhost:8000`
- Check browser console for errors
- Verify CORS settings in the agent

**Agent not starting:**
- Check Python version (3.8+ required)
- Verify all dependencies are installed
- Check environment variables are set correctly

**LLM API errors:**
- Verify API keys are correct and have sufficient credits
- Check rate limits and quotas
- Ensure network connectivity

### Debug Mode

Enable debug mode by setting `DEBUG=true` in your `.env` file. This will:
- Enable detailed logging
- Show stack traces for errors
- Enable hot reloading for development

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📞 Support

For questions and support:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

---

**Happy coding! 🚀**
