"""
Multi-Agent Chat System - Streamlit Application

To customize company branding:
1. Change COMPANY_LOGO_URL to your company logo URL
2. Change COMPANY_NAME to your company name
3. Optionally update colors in the CSS styling below
"""

import os

if os.environ.get('CONTAINERIZE', '0') == '1':
    # Install libasound2-dev for audio support in Docker
    os.system('sudo apt-get update')
    os.system('sudo apt-get install -y libasound2-dev')

import streamlit as st
import asyncio
import json
import tempfile

import queue

from threading import Thread

# Azure Speech SDK for voice-to-text
import azure.cognitiveservices.speech as speechsdk

# Import agents
from single_agent.agent import AgentSingleton
from multi_agent.agent import MultiAgent
from hands_off_agent.agent import HandsoffAgent

# Import utilities
from utils.history import (
    chat_history_to_base64, chat_history_from_base64,
    chat_history_compress, chat_history_decompress
)
from utils.state import (
    state_to_base64, state_from_base64,
    state_compress, state_decompress
)

# Import document processing utilities
from document_upload_cli.utils import (
    file_eligible, ocr, chunk_text, embed, upload_to_ai_search_studio, init_index
)

# Load env
from dotenv import load_dotenv
load_dotenv()

# Queue for streaming STT results
queue_output_stt = queue.Queue()

# Voice input section
speech_key = os.environ.get('SPEECH_KEY')
speech_endpoint = os.environ.get('SPEECH_ENDPOINT')

# Set page configuration
st.set_page_config(
    page_title="Multi-Agent Chat System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Company logo/image configuration
COMPANY_LOGO_URL = "https://d1csarkz8obe9u.cloudfront.net/posterpreviews/company-logo-design-template-e089327a5c476ce5c70c74f7359c5898_screen.jpg?ts=1672291305"  # Change this URL later
COMPANY_NAME = "Company Sample"  # Change this name later
COMPANY_TAGLINE = "Powered by Semantic Kernel & Azure OpenAI"  # Change this tagline later

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        padding: 1rem 0;
        border-bottom: 2px solid #f0f2f6;
        margin-bottom: 2rem;
    }
    .company-info {
        color: #666;
        font-style: italic;
        font-size: 0.9rem;
    }
    /* Clean chat styling */
    .stChatMessage {
        margin-bottom: 1rem;
    }
    /* Hide streamlit branding in main area */
    .stApp > header {
        background-color: transparent;
    }
    .stApp > .main > .block-container {
        padding-top: 2rem;
        max-width: 800px;
    }
    /* Sidebar styling */
    .css-1d391kg {
        padding-top: 2rem;
    }
    
    /* Voice button styling */
    .voice-recording {
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
        100% {
            opacity: 1;
        }
    }
            
    .reportview-container {
        margin-top: -2em;
    }
    #MainMenu {visibility: hidden;}
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    #stDecoration {display:none;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'single_agent' not in st.session_state:
        st.session_state.single_agent = AgentSingleton()
    if 'multi_agent' not in st.session_state:
        st.session_state.multi_agent = MultiAgent()
    if 'handsoff_agent' not in st.session_state:
        st.session_state.handsoff_agent = HandsoffAgent()
    if 'single_messages' not in st.session_state:
        st.session_state.single_messages = []
    if 'multi_messages' not in st.session_state:
        st.session_state.multi_messages = []
    if 'handsoff_messages' not in st.session_state:
        st.session_state.handsoff_messages = []
    if 'recording' not in st.session_state:
        st.session_state.recording = False
    if 'voice_input_text' not in st.session_state:
        st.session_state.voice_input_text = ""
    if 'voice_input_streaming' not in st.session_state:
        st.session_state.voice_input_streaming = ""


init_session_state()

# Voice-to-text functionality using Azure Speech Services
def recognize_speech_from_microphone():
    """
    Recognize speech from microphone using Azure Speech Services
    Returns the recognized text or error message
    """
    # Check for required environment variables
    speech_key = os.environ.get('SPEECH_KEY')
    speech_endpoint = os.environ.get('SPEECH_ENDPOINT')
    
    if not speech_key or not speech_endpoint:
        return {
            "success": False,
            "text": "",
            "error": "Missing SPEECH_KEY or SPEECH_ENDPOINT environment variables"
        }
    
    # Configure speech recognition
    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key, 
        endpoint=speech_endpoint
    )
    speech_config.speech_recognition_language = "id-ID"  # Change language as needed
    
    # Configure audio input
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, 
        audio_config=audio_config
    )

    def _thread_recognizing_(evt, queue_out: queue.Queue):
        queue_out.put({
            "finish": False,
            "text": evt.result.text
        })

    def _thread_recognize_(evt, queue_out: queue.Queue):
        queue_out.put({
            "finish": True,
            "text": evt.result.text
        })

    speech_recognizer.recognizing.connect(lambda evt: _thread_recognizing_(evt, queue_output_stt))
    speech_recognizer.recognized.connect(lambda evt: _thread_recognize_(evt, queue_output_stt))
    
    # Perform speech recognition
    def _main_thread_():
        speech_recognizer.recognize_once()

    thread = Thread(target=_main_thread_)
    thread.start()

# Document processing function
def process_document(uploaded_file, progress_callback=None):
    """
    Process an uploaded document through OCR, chunking, embedding, and upload to AI Search
    """
    try:
        # Check environment variables
        required_envs = [
            "DOCUMENT_INTELLIGENCE_ENDPOINT",
            "DOCUMENT_INTELLIGENCE_KEY",
            "OPENAI_KEY",
            "OPENAI_ENDPOINT",
            "AI_SEARCH_KEY",
            "AI_SEARCH_ENDPOINT",
            "AI_SEARCH_INDEX"
        ]
        missing = [env for env in required_envs if not os.getenv(env)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        # Save uploaded file to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            temp_file_path = tmp_file.name
        
        try:
            # Check if file is eligible
            if not file_eligible(temp_file_path):
                raise ValueError(f"File type not supported: {uploaded_file.type}")
            
            if progress_callback:
                progress_callback(10, "Starting OCR processing...")
            
            # Perform OCR
            ocr_result = ocr(temp_file_path)
            
            if progress_callback:
                progress_callback(30, "OCR complete, chunking text...")
            
            # Chunk the text
            chunks = chunk_text(ocr_result)
            
            if progress_callback:
                progress_callback(40, f"Text chunked into {len(chunks)} pieces, starting upload...")
            
            # Process chunks sequentially
            for i, text_chunk in enumerate(chunks):
                if progress_callback:
                    progress = 40 + (i + 1) / len(chunks) * 50
                    progress_callback(progress, f"Processing chunk {i+1}/{len(chunks)}...")
                
                # Generate embeddings and upload
                embeddings = embed(text_chunk)
                upload_to_ai_search_studio(i, uploaded_file.name, text_chunk, embeddings)
            
            if progress_callback:
                progress_callback(100, "Upload complete!")
            
            return {
                "success": True,
                "message": f"Successfully processed {uploaded_file.name}",
                "chunks_processed": len(chunks),
                "total_characters": len(ocr_result)
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        return {
            "success": False,
            "message": f"Error processing {uploaded_file.name}: {str(e)}",
            "chunks_processed": 0,
            "total_characters": 0
        }

# Sidebar navigation - simplified
st.sidebar.image(COMPANY_LOGO_URL)
st.sidebar.title(f"{COMPANY_NAME}")
st.sidebar.markdown("---")

# Navigation
page = st.sidebar.selectbox("📍 Navigation", ["🤖 Agent", "📁 Upload"])

# Convert display names back to simple names for routing
page_mapping = {
    "🤖 Agent": "Agent",
    "📁 Upload": "Upload"
}
page = page_mapping[page]

# Upload Page
def upload_page():
    # Header with company branding
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(COMPANY_LOGO_URL)
    with col2:
        st.title("📁 Document Upload")
        st.markdown(f'<p class="company-info">{COMPANY_NAME} - Multi-Agent System</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="company-info">{COMPANY_TAGLINE}</p>', unsafe_allow_html=True)
    
    st.markdown("Upload documents to be processed by the document search agent.")
    st.markdown("---")
    
    # Check environment variables
    required_envs = [
        "DOCUMENT_INTELLIGENCE_ENDPOINT",
        "DOCUMENT_INTELLIGENCE_KEY", 
        "OPENAI_KEY",
        "OPENAI_ENDPOINT",
        "AI_SEARCH_KEY",
        "AI_SEARCH_ENDPOINT",
        "AI_SEARCH_INDEX"
    ]
    missing_envs = [env for env in required_envs if not os.getenv(env)]
    
    if missing_envs:
        st.error(f"❌ **Missing Environment Variables:** {', '.join(missing_envs)}")
        st.markdown("Please configure the required environment variables to enable document upload functionality.")
        return
    
    # Upload instructions
    st.info("📝 **Instructions:** Upload PDF, DOCX, or TXT files. The documents will be processed using OCR, chunked, embedded, and uploaded to Azure AI Search for the document search agent to query.")
    
    # Initialize AI Search index button
    if st.button("🔧 Initialize AI Search Index", help="Initialize or update the AI Search index"):
        with st.spinner("Initializing AI Search index..."):
            try:
                init_index()
                st.success("✅ AI Search index initialized successfully!")
            except Exception as e:
                st.error(f"❌ Failed to initialize index: {str(e)}")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose document files",
        type=['pdf', 'docx', 'txt'],
        accept_multiple_files=True,
        help="Upload PDF, DOCX, or TXT files for document processing"
    )
    
    if uploaded_files:
        st.subheader("📋 Uploaded Files:")
        
        # Process all files button
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("� Process All Files", help="Process all uploaded files at once"):
                process_all_files(uploaded_files)
        
        with col2:
            clear_files = st.button("🗑️ Clear All", help="Clear all uploaded files")
            if clear_files:
                st.rerun()
        
        # Individual file processing
        for uploaded_file in uploaded_files:
            with st.expander(f"📄 {uploaded_file.name} ({uploaded_file.type}) - {uploaded_file.size:,} bytes"):
                # File details
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**File:** {uploaded_file.name}")
                    st.markdown(f"**Type:** {uploaded_file.type}")
                    st.markdown(f"**Size:** {uploaded_file.size:,} bytes")
                    
                    # Check if file is eligible
                    file_extension = uploaded_file.name.split('.')[-1].lower()
                    eligible_extensions = ['pdf', 'docx', 'txt']
                    
                    if file_extension in eligible_extensions:
                        st.success("✅ File type supported")
                    else:
                        st.warning("⚠️ File type may not be fully supported")
                
                with col2:
                    st.markdown("**Actions:**")
                    
                    # Process individual file
                    if st.button(f"� Process", key=f"process_{uploaded_file.name}"):
                        process_single_file(uploaded_file)
    else:
        st.markdown("### 🎯 No files uploaded yet")
        st.markdown("Use the file uploader above to get started with document processing.")
        
        # Example of supported file types
        st.markdown("### 📚 Supported File Types")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**📄 PDF**\n- Research papers\n- Reports\n- Documentation")
        with col2:
            st.markdown("**📝 DOCX**\n- Word documents\n- Proposals\n- Manuscripts")
        with col3:
            st.markdown("**📋 TXT**\n- Plain text files\n- Code documentation\n- Notes")
    
    # Add footer at bottom of sidebar for upload page
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"""
        <div style="text-align: center; color: #666; font-size: 0.8rem; padding: 10px 0;">
            © 2025 {COMPANY_NAME}<br>
            All rights reserved<br>
            <small>{COMPANY_TAGLINE}</small>
        </div>
        """, unsafe_allow_html=True)


def process_single_file(uploaded_file):
    """Process a single uploaded file"""
    # Create progress bar and status container
    progress_bar = st.progress(0)
    status_text = st.empty()
    result_container = st.empty()
    
    def update_progress(progress, message):
        progress_bar.progress(progress / 100)
        status_text.text(message)
    
    # Process the file
    result = process_document(uploaded_file, update_progress)
    
    # Show results
    with result_container.container():
        if result["success"]:
            st.success(f"✅ {result['message']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Chunks Created", result["chunks_processed"])
            with col2:
                st.metric("Characters Processed", f"{result['total_characters']:,}")
        else:
            st.error(f"❌ {result['message']}")
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()


def process_all_files(uploaded_files):
    """Process all uploaded files sequentially"""
    st.markdown("### 🚀 Processing All Files")
    
    overall_progress = st.progress(0)
    overall_status = st.empty()
    
    results = []
    total_files = len(uploaded_files)
    
    for i, uploaded_file in enumerate(uploaded_files):
        overall_status.text(f"Processing file {i+1}/{total_files}: {uploaded_file.name}")
        
        # Create individual progress for this file
        st.markdown(f"**Processing:** {uploaded_file.name}")
        file_progress = st.progress(0)
        file_status = st.empty()
        
        def update_progress(progress, message):
            file_progress.progress(progress / 100)
            file_status.text(message)
        
        # Process the file
        result = process_document(uploaded_file, update_progress)
        results.append(result)
        
        # Show individual result
        if result["success"]:
            st.success(f"✅ {uploaded_file.name}: {result['chunks_processed']} chunks processed")
        else:
            st.error(f"❌ {uploaded_file.name}: {result['message']}")
        
        # Update overall progress
        overall_progress.progress((i + 1) / total_files)
        
        # Clean up individual progress bars
        file_progress.empty()
        file_status.empty()
    
    # Show final summary
    overall_status.text("All files processed!")
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Files", total_files)
    with col2:
        st.metric("Successful", len(successful))
    with col3:
        st.metric("Failed", len(failed))
    with col4:
        total_chunks = sum(r["chunks_processed"] for r in successful)
        st.metric("Total Chunks", total_chunks)
    
    if failed:
        with st.expander("❌ Failed Files", expanded=True):
            for result in failed:
                st.error(result["message"])



# Clean chat interface focused on conversation
def clean_chat_interface(agent, agent_name, messages_key, is_async=True):
    # Chat messages container with proper styling
    chat_container = st.container()
    with chat_container:
        for message in st.session_state[messages_key]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


    if speech_key and speech_endpoint:
        # Voice input controls
        st.markdown("### 🎤 Voice Input")
        if not st.session_state.recording:
            if st.button("🎤 Record", help="Click to start voice input", key=f"voice_btn_{messages_key}", use_container_width=True):
                st.session_state.recording = True
                st.rerun()
        else:
            def stream_stt():
                final_text = ""
                while True:
                    try:
                        item = queue_output_stt.get(timeout=0.1)

                        # Get the Difference between final_text and item["text"]
                        len_final = len(final_text)
                        new_text = ""
                        if len(item["text"]) > len_final:
                            new_text = item["text"][len_final:]
                        yield new_text
                        final_text = item["text"]
                        if item["finish"]:
                            break
                    except queue.Empty:
                        continue
                st.session_state.chat_input = final_text
                st.session_state.recording = False
                st.rerun()

            with st.spinner("Listening..."):
                recognize_speech_from_microphone()
                if st.session_state.recording:
                    st.write_stream(stream_stt())

    # Regular chat input (always available)
    if prompt := st.chat_input(f"Type your message to {agent_name}...", key="chat_input", ):
        # Add user message to chat history
        st.session_state[messages_key].append({"role": "user", "content": prompt})
        
        # Get assistant response
        with st.spinner("Thinking..."):
            try:
                if is_async:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    response = loop.run_until_complete(agent.chat(prompt))
                    loop.close()
                else:
                    response = agent.chat(prompt)
                
                st.session_state[messages_key].append({"role": "assistant", "content": response})
                st.rerun()
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state[messages_key].append({"role": "assistant", "content": error_msg})
                st.rerun()


# Agent Page - Clean and focused on chat
def agent_page():
    # Minimal header
    st.title("🤖 AI Chat Assistant")
    
    # Agent selection in sidebar instead of main area
    with st.sidebar:
        st.markdown("### 🎯 Choose Agent")
        agent_choice = st.selectbox(
            "Agent Type:",
            ["Single Agent", "Multi-Agent Triage", "Multi-Agent Hands-off"],
            help="Select the type of agent you want to interact with",
            label_visibility="collapsed"
        )
        
        # Quick agent info
        agent_descriptions = {
            "Single Agent": "🏠 Smart home assistant",
            "Multi-Agent Triage": "🎭 Multi-agent system",
            "Multi-Agent Hands-off": "🤝 Advanced handoff system"
        }
        st.info(agent_descriptions[agent_choice])
        
        # Voice feature status
        speech_key = os.environ.get('SPEECH_KEY')
        speech_endpoint = os.environ.get('SPEECH_ENDPOINT')
        if speech_key and speech_endpoint:
            st.success("🎤 Voice input enabled")
        else:
            st.warning("🎤 Voice input disabled\n\nSet SPEECH_KEY and SPEECH_ENDPOINT environment variables to enable voice-to-text functionality.")
        
        # Quick actions
        st.markdown("### ⚙️ Quick Actions")
        col1, col2 = st.columns(2)
        with col1:
            show_settings = st.button("Settings", help="Show management options", use_container_width=True)
        with col2:
            if st.button("Clear Chat", help="Clear current conversation", use_container_width=True):
                # Clear the appropriate message history
                if agent_choice == "Single Agent":
                    st.session_state.single_messages = []
                elif agent_choice == "Multi-Agent Triage":
                    st.session_state.multi_messages = []
                else:
                    st.session_state.handsoff_messages = []
                st.rerun()
    
    # Map agent choice to actual agents and session keys
    agent_mapping = {
        "Single Agent": (st.session_state.single_agent, "single_messages", True),
        "Multi-Agent Triage": (st.session_state.multi_agent, "multi_messages", False),
        "Multi-Agent Hands-off": (st.session_state.handsoff_agent, "handsoff_messages", False)
    }
    
    selected_agent, messages_key, is_async = agent_mapping[agent_choice]
    
    # Main chat interface - clean and centered
    st.markdown(f"### 💬 Chatting with {agent_choice}")
    
    # Chat interface
    clean_chat_interface(selected_agent, agent_choice, messages_key, is_async)
    
    # Settings panel (collapsible)
    if show_settings:
        with st.expander("⚙️ Management Settings", expanded=False):
            tab1, tab2, tab3 = st.tabs(["📊 History", "💾 Export/Import", "� Stats"])
            
            with tab1:
                col1, col2, col3 = st.columns(3)
                with col1:
                    # Generate history data for download
                    try:
                        history = selected_agent.get_history()
                        history_base64 = chat_history_to_base64(history)
                        st.download_button(
                            "📤 Export History",
                            data=history_base64,
                            file_name=f"{agent_choice.lower().replace(' ', '_')}_history.txt",
                            mime="text/plain",
                            help="Download chat history as a text file"
                        )
                    except Exception as e:
                        st.error(f"Cannot export history: {str(e)}")
                
                with col2:
                    uploaded_history = st.file_uploader("📥 Import History", type=['txt'], help="Upload a previously exported history file")
                    if uploaded_history:
                        try:
                            history_data = uploaded_history.read().decode()
                            history = chat_history_from_base64(history_data)
                            selected_agent.set_history(history)
                            st.session_state[messages_key] = []
                            st.success("History imported!")
                            st.rerun()
                        except Exception as e:
                            try:
                                # Try compressed format as fallback
                                history = chat_history_decompress(history_data)
                                selected_agent.set_history(history)
                                st.session_state[messages_key] = []
                                st.success("Compressed history imported!")
                                st.rerun()
                            except:
                                st.error(f"Import failed: {str(e)}")
                
                with col3:
                    if st.button("🗑️ Clear All History", help="Clear all chat history for this agent"):
                        if hasattr(selected_agent, 'clear_history'):
                            selected_agent.clear_history()
                        else:
                            from semantic_kernel.contents.chat_history import ChatHistory
                            selected_agent.set_history(ChatHistory())
                        st.session_state[messages_key] = []
                        st.success("History cleared!")
                        st.rerun()
            
            with tab2:
                if agent_choice == "Multi-Agent Hands-off":
                    st.markdown("**Agent State Management**")
                    col1, col2 = st.columns(2)
                    with col1:
                        # Generate state data for download
                        try:
                            if asyncio.iscoroutinefunction(selected_agent.get_state):
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                state = loop.run_until_complete(selected_agent.get_state())
                                loop.close()
                            else:
                                state = selected_agent.get_state()
                            
                            state_base64 = state_to_base64(state)
                            st.download_button(
                                "📤 Export State",
                                data=state_base64,
                                file_name=f"handsoff_agent_state.txt",
                                mime="text/plain",
                                help="Download agent state for backup or transfer"
                            )
                        except Exception as e:
                            st.error(f"Cannot export state: {str(e)}")
                    
                    with col2:
                        uploaded_state = st.file_uploader("📥 Import State", type=['txt'], help="Upload a previously exported state file")
                        if uploaded_state:
                            try:
                                state_data = uploaded_state.read().decode()
                                state = state_from_base64(state_data)
                                selected_agent.set_state(state)
                                st.success("State imported!")
                            except Exception as e:
                                try:
                                    # Try compressed format as fallback
                                    state = state_decompress(state_data)
                                    if isinstance(state, dict):
                                        state = json.dumps(state)
                                    selected_agent.set_state(state)
                                    st.success("Compressed state imported!")
                                except:
                                    st.error(f"State import failed: {str(e)}")
                else:
                    st.info("State management is only available for Multi-Agent Hands-off")
            
            with tab3:
                message_count = len(st.session_state[messages_key])
                if message_count > 0:
                    user_msgs = len([m for m in st.session_state[messages_key] if m["role"] == "user"])
                    assistant_msgs = len([m for m in st.session_state[messages_key] if m["role"] == "assistant"])
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Messages", message_count)
                    with col2:
                        st.metric("Your Messages", user_msgs)
                    with col3:
                        st.metric("AI Responses", assistant_msgs)
                else:
                    st.info("No messages yet. Start chatting to see statistics!")
    
    # Add footer at bottom of sidebar for agent page
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"""
        <div style="text-align: center; color: #666; font-size: 0.8rem; padding: 10px 0;">
            © 2025 {COMPANY_NAME}<br>
            All rights reserved<br>
            <small>{COMPANY_TAGLINE}</small>
        </div>
        """, unsafe_allow_html=True)

# Main app routing
def main():
    # Initialize AI Search index on startup (only once per session)
    if 'index_initialized' not in st.session_state:
        try:
            # Check if we have the required environment variables
            required_envs = [
                "DOCUMENT_INTELLIGENCE_ENDPOINT",
                "DOCUMENT_INTELLIGENCE_KEY",
                "OPENAI_KEY", 
                "OPENAI_ENDPOINT",
                "AI_SEARCH_KEY",
                "AI_SEARCH_ENDPOINT",
                "AI_SEARCH_INDEX"
            ]
            missing = [env for env in required_envs if not os.getenv(env)]
            
            if not missing:
                init_index()
                st.session_state.index_initialized = True
            else:
                st.session_state.index_initialized = False
        except Exception as e:
            st.session_state.index_initialized = False
            # Don't show error on startup, will be shown in upload page if needed
    
    if page == "Upload":
        upload_page()
    elif page == "Agent":
        agent_page()

if __name__ == "__main__":
    main()
