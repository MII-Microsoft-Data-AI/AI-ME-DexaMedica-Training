# Azure Function Semantic Kernel - Multi-Agent System

A comprehensive AI assistant platform built with **Azure Functions** and **FastAPI**, featuring multiple AI agents, document processing, real-time speech recognition, and a modern web interface.

## 🚀 Features

- **🤖 Multi-Agent AI System**: Single Agent, Multi-Agent (Triage), and Hands-Off Agent
- **📄 Document Upload & Processing**: PDF, DOCX, TXT with AI Search integration
- **🎤 Real-Time Speech Recognition**: WebRTC-based voice input with WebSocket streaming
- **💬 Modern Web Interface**: Responsive chatbot UI with separate chat rooms
- **🔄 Dual Deployment**: Both Azure Functions and FastAPI implementations
- **📊 Chat History Management**: Export/import with compression support
- **🔧 Agent State Management**: Persistent state across sessions

## 🛠️ Technology Stack

- **Backend**: Python 3.12, FastAPI, Azure Functions
- **AI Framework**: Microsoft Semantic Kernel
- **Speech Services**: Azure Speech Services with WebRTC
- **Document Processing**: Azure Document Intelligence + AI Search
- **Frontend**: HTML5, CSS3, JavaScript (WebRTC, WebSocket)
- **Database**: Azure AI Search for document indexing

## 📋 Prerequisites

- **Python 3.12+**
- **Azure Account** with the following services:
  - Azure OpenAI Service
  - Azure Speech Services  
  - Azure Document Intelligence
  - Azure AI Search
- **Node.js** (for Azure Functions development)

## ⚙️ Setup & Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd azure-function-semantic-kernel
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Copy `.env.example` to `.env` and configure your Azure services:

```env
# Container Environment (to deactivate some features)
CONTAINER_ENV=0 # "0"/"1" value

# Partner Name for Footer
PARTNER_NAME=Your Company Name

# Azure OpenAI
OPENAI_KEY=your_openai_key
OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Azure Speech Services
SPEECH_KEY=your_speech_key
SPEECH_ENDPOINT=https://your-region.api.cognitive.microsoft.com/

# Azure Document Intelligence
DOCUMENT_INTELLIGENCE_KEY=your_doc_intelligence_key
DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/

# Azure AI Search
AI_SEARCH_KEY=your_search_key
AI_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AI_SEARCH_INDEX=documents

# Azure Blob Storage
BLOB_STORAGE_CONNECTION_STRING=your_blob_storage_connection_string
BLOB_CONTAINER_NAME=your_container_name

# Azure AI Foundry (if applicable)
FOUNDRY_ENDPOINT=https://your-foundry-endpoint
FOUNDRY_AGENT_ID=registered_agent_id
```

## 🚀 Running the Application

### Option 1: FastAPI Development Server (Recommended)

```bash
# Start FastAPI server
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload
```

**Access Points:**
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Speech Test UI**: http://localhost:8000/speech/test-webrtc-ui

### Option 2: Azure Functions Local Development

```bash
# Start Azure Functions runtime
func start
```

**Access Points:**
- **API Base**: http://localhost:7071/api
- **Function endpoints**: http://localhost:7071/api/{endpoint}

## 🖥️ Web Interface Features

### 🤖 Multi-Agent Chat System
- **📚 Single Agent**: General-purpose assistant with tool integration
- **🎯 Multi-Agent (Triage)**: Intelligent request routing to specialized agents
- **🚀 Hands-Off Agent**: Autonomous workflow execution

### 💬 Chat Interface
- **Separate Chat Rooms**: Each agent maintains its own conversation history
- **Message Count Indicators**: Visual badges showing activity per agent
- **Real-time Messaging**: Instant responses with typing indicators
- **Chat History**: Persistent conversation storage per agent

### 📄 Document Upload
- **Drag & Drop**: Intuitive file upload interface
- **Supported Formats**: PDF, DOCX, TXT files
- **Progress Tracking**: Real-time upload status
- **AI Search Integration**: Automatic document indexing for agent queries

### 🎤 Voice Input
- **WebRTC Speech Recognition**: High-quality audio capture
- **Multi-language Support**: English, Indonesian, French, German, Spanish
- **Real-time Transcription**: Live speech-to-text conversion
- **Audio Visualization**: Visual feedback during recording
- **WebSocket Streaming**: Low-latency audio processing
## 🔧 Technical Architecture

### 🏗️ System Components

#### **1. Agent System**
```python
# Agent Types Available
single_agent/         # General-purpose AI assistant
├── agent.py         # Main agent implementation
├── prompt.py        # System prompts and instructions
└── plugins/         # Tool integrations (lights control, etc.)

multi_agent/         # Intelligent request triage system
├── agent.py         # Orchestrator with specialized sub-agents
├── agents/          # Specialized agent implementations
│   ├── document_agent/    # PDF/document processing specialist
│   ├── light_agent/       # IoT/smart home automation
│   └── orchestrator_agent/ # Request routing and coordination
└── common.py        # Shared utilities and configurations

hands_off_agent/     # Autonomous workflow execution
├── agent.py         # Advanced orchestration with minimal human input
├── agents/          # Same specialized agents as multi-agent
└── common.py        # Enhanced error handling and recovery
```

#### **2. Document Processing Pipeline**
```python
document_upload_cli/
├── utils.py         # Document parsing and chunking
└── __init__.py      # CLI interface for bulk uploads

# Document Flow:
# File Upload → Document Intelligence → Text Extraction → 
# Chunking → Embedding → Azure AI Search Index → Agent Queries
```

#### **3. Speech Recognition System**
```python
utils/fastapi/
└── azure_speech_streaming.py  # WebRTC + Azure Speech integration

# Speech Flow:
# Microphone → WebRTC Capture → WebSocket → Azure Speech → 
# Real-time Transcription → Agent Processing
```

### 🌐 API Endpoints

#### **FastAPI Endpoints**

**Core Endpoints:**
```http
GET  /                          # Main chatbot interface
GET  /chatbot                   # Alternative chatbot access
GET  /docs                      # Interactive API documentation
```

**Agent Interactions:**
```http
POST /chat/single               # Single agent conversation
POST /chat/multi                # Multi-agent triage system
POST /chat/hands-off            # Hands-off agent workflow

# Example Request:
{
    "message": "What documents do we have about machine learning?",
    "session_id": "user123",
    "context": {}
}
```

**Document Management:**
```http
POST /upload/document           # Upload and process documents
GET  /documents/search          # Search processed documents
POST /documents/batch-upload    # Bulk document processing

# Upload Example:
curl -X POST "http://localhost:8000/upload/document" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@document.pdf"
```

**Speech Recognition:**
```http
GET  /speech/test-webrtc-ui     # Speech recognition test interface
WS   /speech/websocket          # WebSocket for real-time speech

# WebSocket Connection:
const ws = new WebSocket('ws://localhost:8000/speech/websocket');
```

**Utility Endpoints:**
```http
GET  /health                    # System health check
GET  /status                    # Detailed system status
POST /chat/history/export       # Export chat history
POST /chat/history/import       # Import chat history
```

#### **Azure Functions Legacy Endpoints**

The following endpoints are maintained for backward compatibility:

## 🔄 WebSocket Features

### 💓 Ping/Pong Keepalive System
The application implements automatic connection health monitoring:

```javascript
// Client-side ping management
function startPingInterval() {
    pingInterval = setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
        }
    }, 2000); // Ping every 2 seconds
}

// Server automatically responds with pong
```

**Features:**
- **Automatic Reconnection**: Client automatically reconnects on connection loss
- **Health Monitoring**: Visual indicators for connection status
- **Timeout Management**: Configurable timeout periods for robust operation
- **Background Keepalive**: Maintains connections during idle periods

### 📡 Real-time Communication
```javascript
// WebSocket message handling
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'chat_response':
            displayMessage(data.message, 'ai');
            break;
        case 'transcription':
            updateTranscription(data.text);
            break;
        case 'pong':
            // Connection health confirmed
            break;
    }
};
```

## 🎨 Modern UI Design

### 🎯 Design Philosophy
- **Neutral Color Palette**: Professional gray tones for reduced eye strain
- **Responsive Layout**: Mobile-first design with desktop optimization
- **Accessibility**: WCAG 2.1 compliant with keyboard navigation
- **Modern UX**: Smooth animations and intuitive interactions

### 🎨 Color Scheme
```css
:root {
    --bg-color: #1a1a1a;           /* Deep charcoal background */
    --card-bg: #2a2a2a;           /* Card/panel backgrounds */
    --accent-color: #4a90e2;       /* Primary accent blue */
    --text-primary: #e0e0e0;       /* Primary text color */
    --text-secondary: #b0b0b0;     /* Secondary text color */
    --border-color: #404040;       /* Subtle borders */
    --success-color: #4caf50;      /* Success/positive actions */
    --warning-color: #ff9800;      /* Warnings/attention */
}
```

### 🧩 UI Components
- **Chat Bubbles**: Distinct styling for user/AI messages
- **Agent Switcher**: Tabbed interface with activity indicators
- **File Upload**: Drag-and-drop with progress visualization  
- **Voice Controls**: Recording status with audio visualization
- **Status Indicators**: Connection health and agent status

## 🚦 Error Handling & Recovery

### 🛡️ Robust Error Management
The system implements comprehensive error handling across all components:

```python
# Agent Error Recovery Example
async def chat_loop(self, message: str, session_id: str):
    try:
        # Main agent processing
        response = await self.process_message(message)
        return response
    except ValidationError as e:
        logger.error(f"Validation error in agent: {e}")
        # Automatic agent restart
        await self.restart_agent()
        return {"error": "Agent restarted due to validation error"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": "An unexpected error occurred"}
```

**Error Recovery Features:**
- **Automatic Agent Restart**: Agents restart on critical errors
- **Graceful Degradation**: Fallback responses when services are unavailable  
- **Connection Recovery**: WebSocket auto-reconnection with exponential backoff
- **Timeout Management**: Configurable timeouts prevent hanging operations
- **Comprehensive Logging**: Detailed error tracking for debugging

---

## 📊 Azure Functions API Reference (Legacy)

*The following endpoints are maintained for backward compatibility with existing integrations.*

### 🔧 Single Agent (Legacy Azure Functions)

**Chat with LLM:**
*Integrated tools available (refer to `single_agent/plugins.py`):*
- **Lamp Management**: Turn on/off lamps, get lamp IDs, search lamp details by name
- **Chat History**: Retrieve conversation history

```sh
$ curl --get --data-urlencode "chat=<your message>" http://localhost:7071/api/single/chat
```

### Check history
```sh
$ curl http://localhost:7071/api/single/history
```

### Export chat
```sh
$ curl http://localhost:7071/api/single/history/export
```

### Import chat
```sh
$ curl -X POST -d '{"data":"<your base64 data>"}' http://localhost:7071/api/single/history/import
```

### Export chat (compressed)
```sh
$ curl http://localhost:7071/api/single/history/export/compress
```

### Import chat (compressed)
```sh
$ curl -X POST -d '{"data":"<your base64 data>"}' http://localhost:7071/api/single/history/import/compress
```

### 🎯 Multi-Agent System (Legacy Azure Functions)

### Start the session
This will start a session to the multi-agent system.

```sh
$ curl -X POST -d '{"chat":"<your message>"}' http://localhost:7071/api/multi/chat/start
```

It will hang for waiting to return a response. But, it will not return until you finish the agent. You can open new terminal for contributing into the chat

### Send a message to the session
This will send a message to the multi-agent system.

```sh
$ curl -X POST -d '{"chat":"<your message>"}' http://localhost:7071/api/multi/chat
```

### Check history
```sh
$ curl http://localhost:7071/api/multi/history
```

### Export chat
```sh
$ curl http://localhost:7071/api/multi/history/export
```

### Import chat
```sh
$ curl -X POST -d '{"data":"<your base64 data>"}' http://localhost:7071/api/multi/history/import
```

### Export chat (compressed)
```sh
$ curl http://localhost:7071/api/multi/history/export/compress
```

### Import chat (compressed)
```sh
$ curl -X POST -d '{"data":"<your base64 data>"}' http://localhost:7071/api/multi/history/import/compress
```

### Export state
```sh
$ curl http://localhost:7071/api/multi/state/export
```

### Import state
```sh
$ curl -X POST --header "Content-Type: application/json" -d '<your state data>' http://localhost:7071/api/multi/state/import
```

### Export state (compressed)
```sh
$ curl http://localhost:7071/api/multi/state/export/compress
```

### Import state (compressed)
```sh
$ curl -X POST -d '{"data":"<your base64 data>"}' http://localhost:7071/api/multi/state/import/compress
```

---

## 📦 Additional Resources

### 🚀 Quick Start Guide
1. **Clone** → **Install Dependencies** → **Configure Environment** → **Run FastAPI**
2. **Open Browser** → http://localhost:8000 → **Start Chatting**
3. **Upload Documents** → **Try Voice Input** → **Switch Between Agents**

### 🔧 Development Tips
- **Hot Reload**: FastAPI automatically reloads on code changes
- **Debug Mode**: Set `DEBUG=True` in environment for detailed logging
- **API Testing**: Use http://localhost:8000/docs for interactive API testing
- **WebSocket Testing**: Use browser developer tools to monitor WebSocket traffic

### 📚 Further Reading
- [Microsoft Semantic Kernel Documentation](https://learn.microsoft.com/en-us/semantic-kernel/)
- [Azure OpenAI Service](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [WebRTC Specification](https://webrtc.org/)

### 🆘 Getting Help
- **Issues**: GitHub repository issues page
- **Discord**: Community discussion channels  
- **Stack Overflow**: Tag questions with `semantic-kernel` and `fastapi`
- **Azure Support**: For Azure service-specific issues

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Microsoft Semantic Kernel**: AI orchestration framework
- **Azure AI Services**: Cognitive services integration
- **FastAPI**: Modern Python web framework
- **WebRTC**: Real-time communication standards
- **Open Source Community**: Libraries and tools that make this possible

---

**🚀 Ready to explore AI-powered conversations with multiple agents, document intelligence, and real-time speech recognition!**

*Built with ❤️ using Microsoft Semantic Kernel, Azure AI Services, and modern web technologies.*