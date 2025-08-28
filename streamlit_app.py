"""
Multi-Agent Chat System - Streamlit Application

To customize company branding:
1. Change COMPANY_LOGO_URL to your company logo URL
2. Change COMPANY_NAME to your company name
3. Optionally update colors in the CSS styling below
"""

import streamlit as st
import asyncio
import base64
import json
import os
from io import BytesIO

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

# Load env
from dotenv import load_dotenv
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Multi-Agent Chat System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Company logo/image configuration
COMPANY_LOGO_URL = "https://www.astabyte.com/assets/astabyte-white.svg"  # Change this URL later
COMPANY_NAME = "Astabyte"  # Change this name later
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

init_session_state()

# Sidebar navigation - simplified
st.sidebar.image(COMPANY_LOGO_URL, width=200)
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
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(COMPANY_LOGO_URL, width=150)
    with col2:
        st.title("📁 Document Upload")
        st.markdown(f'<p class="company-info">{COMPANY_NAME} - Multi-Agent System</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="company-info">{COMPANY_TAGLINE}</p>', unsafe_allow_html=True)
    
    st.markdown("Upload documents to be processed by the document search agent.")
    st.markdown("---")
    
    # Upload instructions
    st.info("📝 **Instructions:** Upload PDF, DOCX, or TXT files. The documents will be processed and made available for the document search agent to query.")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose document files",
        type=['pdf', 'docx', 'txt'],
        accept_multiple_files=True,
        help="Upload PDF, DOCX, or TXT files for document processing"
    )
    
    if uploaded_files:
        st.subheader("📋 Uploaded Files:")
        
        for uploaded_file in uploaded_files:
            with st.expander(f"📄 {uploaded_file.name} ({uploaded_file.type})"):
                # File details
                file_details = {
                    "Filename": uploaded_file.name,
                    "FileType": uploaded_file.type,
                    "FileSize": f"{uploaded_file.size:,} bytes"
                }
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.json(file_details)
                
                with col2:
                    st.markdown("**Actions:**")
                    if st.button(f"🔄 Process", key=f"process_{uploaded_file.name}"):
                        # Here you would integrate with document_input functionality
                        with st.spinner(f"Processing {uploaded_file.name}..."):
                            # Placeholder for document processing
                            # You can integrate with document_input.split_and_upload here
                            st.success(f"✅ {uploaded_file.name} processed successfully!")
                    
                    if st.button(f"📥 Download", key=f"download_{uploaded_file.name}"):
                        st.info("Download functionality will be implemented with document processing pipeline")
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



# Clean chat interface focused on conversation
def clean_chat_interface(agent, agent_name, messages_key, is_async=True):
    # Chat messages container with proper styling
    chat_container = st.container()
    with chat_container:
        for message in st.session_state[messages_key]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input at the bottom
    if prompt := st.chat_input(f"Message {agent_name}..."):
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
        
        # Quick actions
        st.markdown("### ⚙️ Quick Actions")
        col1, col2 = st.columns(2)
        with col1:
            show_settings = st.button("Settings", help="Show management options")
        with col2:
            if st.button("Clear Chat", help="Clear current conversation"):
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
    if page == "Upload":
        upload_page()
    elif page == "Agent":
        agent_page()

if __name__ == "__main__":
    main()
