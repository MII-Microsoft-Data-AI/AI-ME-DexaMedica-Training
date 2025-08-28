# Streamlit Multi-Agent Chat Application

This Streamlit application provides a web interface for interacting with multiple AI agents powered by Semantic Kernel and Azure OpenAI.

## Features

- **Document Upload**: Upload and process PDF, DOCX, and TXT files
- **Multi-Agent Chat**: Three different agent types:
  - Single Agent: Simple chat with smart home capabilities
  - Multi-Agent Triage: Orchestrated multi-agent system
  - Multi-Agent Hands-off: Advanced handoff orchestration
- **Chat History Management**: Export, import, and manage chat histories
- **State Management**: Export and import agent states (for supported agents)
- **Company Branding**: Customizable logo and company information

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up Environment Variables

Create a `.env` file with your Azure OpenAI credentials:

```env
OPENAI_KEY=your_openai_key
OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
```

### 3. Run the Application

**Option 1: Using the run script**
```bash
python run_streamlit.py
```

**Option 2: Direct streamlit command**
```bash
streamlit run streamlit_app.py
```

The application will be available at `http://localhost:8501`

## Customization

### Company Branding

To customize the company branding, edit the following variables in `streamlit_app.py`:

```python
# Company logo/image configuration
COMPANY_LOGO_URL = "https://your-company-logo-url.com/logo.png"
COMPANY_NAME = "Your Company Name"
COMPANY_TAGLINE = "Your Company Tagline"
```

### Styling

Custom CSS can be modified in the `st.markdown()` section with custom styles.

## Usage

### Upload Page
- Upload documents (PDF, DOCX, TXT)
- Process files for document search integration
- View file details and manage uploads

### Agent Page
- **Single Agent Tab**: Chat with a simple AI agent with smart home capabilities
- **Multi-Agent Triage Tab**: Interact with orchestrated multi-agent system  
- **Multi-Agent Hands-off Tab**: Use advanced handoff orchestration system

### History Management
- Export chat history (regular or compressed format)
- Import previous chat sessions
- Clear chat history
- Download history as text files

### State Management (Hands-off Agent)
- Export agent state for persistence
- Import previous agent states
- Support for compressed state formats

## Architecture

The application integrates with:
- `single_agent.agent.AgentSingleton`: Simple chat agent
- `multi_agent.agent.MultiAgent`: Multi-agent triage system  
- `hands_off_agent.agent.HandsoffAgent`: Handoff orchestration system
- `document_input`: Document processing pipeline (integration ready)

## Troubleshooting

1. **Import Errors**: Make sure all dependencies are installed
2. **Agent Errors**: Check your `.env` file has correct Azure OpenAI credentials
3. **Port Issues**: Change port in `run_streamlit.py` if 8501 is occupied
4. **State/History Issues**: Ensure proper base64 format for import operations

## Development

The application is structured with:
- Modular agent interfaces
- Session state management for chat history
- Async/sync agent support
- Error handling and user feedback
- Responsive UI with custom styling

To extend the application:
1. Add new agent types by following existing patterns
2. Extend document processing integration
3. Add new export/import formats
4. Customize UI components and styling
