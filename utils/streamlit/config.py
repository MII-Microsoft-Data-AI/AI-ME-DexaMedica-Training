import streamlit as st

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