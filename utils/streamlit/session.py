import streamlit as st

# Import agents
from single_agent.agent import AgentSingleton
from multi_agent.agent import MultiAgent
from hands_off_agent.agent import HandsoffAgent

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