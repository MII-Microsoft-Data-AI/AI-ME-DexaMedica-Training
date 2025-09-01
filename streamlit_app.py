"""
Multi-Agent Chat System - Streamlit Application

To customize company branding:
1. Change COMPANY_LOGO_URL to your company logo URL
2. Change COMPANY_NAME to your company name
3. Optionally update colors in the CSS styling below
"""

import os
import streamlit as st

# Import document processing utilities
from document_upload_cli.utils import init_index

# Load env
from dotenv import load_dotenv
load_dotenv()

# Import modular components
from utils.streamlit.config import *
from utils.streamlit.session import init_session_state
from utils.streamlit.ui.sidebar import page
from utils.streamlit.pages.agent_page import agent_page
from utils.streamlit.pages.upload_page import upload_page

@st.cache_resource
def install_dependencies():
    os.system('apt-get update')
    os.system('apt-get install -y ffmpeg')

if os.environ.get('CONTAINERIZE', '0') == '1':
    install_dependencies()


# Initialize session state
init_session_state()

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