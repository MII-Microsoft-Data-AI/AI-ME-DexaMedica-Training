# Utils/Streamlit Module Documentation

This directory contains modularized Streamlit UI components and utilities for the Multi-Agent Chat System. The modularization separates UI concerns from the main application logic, making the codebase more maintainable and organized.

## 📁 Folder Structure

```
utils/streamlit/
├── README.md              # This documentation
├── __init__.py           # Package initialization
├── config.py             # Page configuration and styling
├── session.py            # Session state management
├── voice.py              # Voice-to-text functionality
├── document.py           # Document processing utilities
├── pages/                # Page-specific components
│   ├── __init__.py
│   ├── agent_page.py     # Agent chat interface
│   └── upload_page.py    # Document upload interface
└── ui/                   # Reusable UI components
    ├── __init__.py
    ├── chat_interface.py # Chat interface components
    └── sidebar.py        # Sidebar navigation
```

## 📋 Module Descriptions

### Core Modules

#### `config.py`
**Purpose**: Handles Streamlit page configuration and custom CSS styling.

**Key Features**:
- Page configuration (title, icon, layout)
- Company branding constants (logo, name, tagline)
- Custom CSS for improved UI styling
- Responsive design elements

**Usage**:
```python
from utils.streamlit.config import *

# This automatically applies page config and CSS when imported
```

#### `session.py`
**Purpose**: Manages Streamlit session state initialization and agent instances.

**Key Features**:
- Initializes all agent instances (Single, Multi-Agent, Hands-off)
- Sets up message history arrays
- Manages voice input state
- Recording state management

**Usage**:
```python
from utils.streamlit.session import init_session_state

init_session_state()  # Call once at app startup
```

#### `voice.py`
**Purpose**: Provides voice-to-text functionality using Azure Speech Services.

**Key Features**:
- Speech recognition from microphone
- Real-time streaming transcription
- Error handling for missing environment variables
- Thread-safe audio processing

**Dependencies**:
- `azure.cognitiveservices.speech`
- Environment variables: `SPEECH_KEY`, `SPEECH_ENDPOINT`

**Usage**:
```python
from utils.streamlit.voice import recognize_speech_from_microphone, queue_output_stt

# Start speech recognition
result = recognize_speech_from_microphone()
```

#### `document.py`
**Purpose**: Handles document processing operations for the upload functionality.

**Key Features**:
- Document upload and processing
- Progress tracking with callbacks
- Batch processing capabilities
- File type validation

**Dependencies**:
- `document_upload_cli.utils` (OCR, chunking, embedding)

**Usage**:
```python
from utils.streamlit.document import process_single_file, process_all_files

# Process individual file
process_single_file(uploaded_file)

# Process multiple files
process_all_files(uploaded_files_list)
```

### Pages Module (`pages/`)

#### `agent_page.py`
**Purpose**: Implements the main agent chat interface page.

**Key Features**:
- Agent selection (Single, Multi-Agent Triage, Hands-off)
- Chat history management
- Settings panel with export/import functionality
- Voice input integration
- Statistics display

**Usage**:
```python
from utils.streamlit.pages.agent_page import agent_page

# Call in main routing
if page == "Agent":
    agent_page()
```

#### `upload_page.py`
**Purpose**: Implements the document upload and processing page.

**Key Features**:
- File upload interface
- Document processing with progress bars
- Batch processing capabilities
- Environment variable validation
- File type support information

**Usage**:
```python
from utils.streamlit.pages.upload_page import upload_page

# Call in main routing
if page == "Upload":
    upload_page()
```

### UI Components Module (`ui/`)

#### `chat_interface.py`
**Purpose**: Provides reusable chat interface components.

**Key Features**:
- Message display with proper styling
- Voice input integration
- Real-time streaming text display
- Error handling and user feedback

**Usage**:
```python
from utils.streamlit.ui.chat_interface import clean_chat_interface

# Display chat interface
clean_chat_interface(agent, agent_name, messages_key, is_async)
```

#### `sidebar.py`
**Purpose**: Handles sidebar navigation and routing.

**Key Features**:
- Navigation menu with page selection
- Company branding display
- Page routing logic

**Usage**:
```python
from utils.streamlit.ui.sidebar import page

# Use the page variable for routing
if page == "Agent":
    # Show agent page
elif page == "Upload":
    # Show upload page
```

## 🔧 Integration with Main App

The main `streamlit_app.py` now imports and uses these modules:

```python
# Import modular components
from utils.streamlit.config import *
from utils.streamlit.session import init_session_state
from utils.streamlit.ui.sidebar import page
from utils.streamlit.pages.agent_page import agent_page
from utils.streamlit.pages.upload_page import upload_page

# Initialize session state
init_session_state()

# Main routing
if page == "Upload":
    upload_page()
elif page == "Agent":
    agent_page()
```

## 🎯 Benefits of Modularization

1. **Separation of Concerns**: UI logic is separated from business logic
2. **Maintainability**: Easier to modify individual components
3. **Reusability**: UI components can be reused across different pages
4. **Testing**: Each module can be tested independently
5. **Readability**: Main app file is much cleaner and focused
6. **Scalability**: Easy to add new pages or UI components

## 🔄 Migration Notes

- Original functionality is preserved
- All imports and dependencies remain the same
- Session state management is unchanged
- Page routing works identically
- Voice and document processing work as before

## 📝 Environment Variables Required

The following environment variables are required for full functionality:

- `SPEECH_KEY` - Azure Speech Services key
- `SPEECH_ENDPOINT` - Azure Speech Services endpoint
- `DOCUMENT_INTELLIGENCE_ENDPOINT` - Azure Document Intelligence endpoint
- `DOCUMENT_INTELLIGENCE_KEY` - Azure Document Intelligence key
- `OPENAI_KEY` - OpenAI API key
- `OPENAI_ENDPOINT` - OpenAI endpoint
- `AI_SEARCH_KEY` - Azure AI Search key
- `AI_SEARCH_ENDPOINT` - Azure AI Search endpoint
- `AI_SEARCH_INDEX` - Azure AI Search index name

## 🚀 Future Enhancements

This modular structure makes it easy to:
- Add new pages by creating files in `pages/`
- Create new UI components in `ui/`
- Extend voice functionality
- Add new document processing features
- Implement theme switching
- Add user authentication components

---

**Last Updated**: 2025-08-31
**Version**: 1.0
**Maintained by**: Kilo Code