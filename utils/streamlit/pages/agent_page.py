import streamlit as st
import asyncio
import json

# Import utilities
from utils.history import (
    chat_history_to_base64, chat_history_from_base64,
    chat_history_compress, chat_history_decompress
)
from utils.state import (
    state_to_base64, state_from_base64,
    state_compress, state_decompress
)

# Import config
from ..config import COMPANY_LOGO_URL, COMPANY_NAME, COMPANY_TAGLINE

import queue

# Import voice functionality
from ..voice.voice import recognize_speech_from_microphone, queue_output_stt, speech_key, speech_endpoint,  create_streaming_voice_interface, stop_recognition_signal

# Import UI components
from ..ui.chat_interface import clean_chat_interface

def start_recording():
    stop_recognition_signal.clear()
    st.session_state.recording = True
    st.session_state.chat_input = ""
    st.rerun()

def stop_recording():
    st.session_state.recording = False
    stop_recognition_signal.set()
    st.rerun()

def update_chat_input(text: str):
    st.session_state.chat_input = text
    st.rerun()


def agent_page():
    # Minimal header
    st.title("🤖 AI Chat Assistant")


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
        if speech_key and speech_endpoint:
            st.success("🎤 Voice input enabled")
            
            # Voice interface mode selector
            voice_mode = st.selectbox(
                "Voice Input Mode",
                ["Basic (Click to Record)", "Streaming (Real-time)"],
                index=0,
                help="Choose between basic microphone recording or real-time WebRTC streaming"
            )
            
        else:
            st.warning("🎤 Voice input disabled\n\nSet SPEECH_KEY and SPEECH_ENDPOINT environment variables to enable voice-to-text functionality.")
            voice_mode = None

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

    # Voice interface section
    if speech_key and speech_endpoint and 'voice_mode' in locals():
        # Check if user selected streaming mode
        if voice_mode == "Streaming (Real-time)":
            st.markdown("#### 🎤 Real-time Voice Input")
            
            # Create streaming voice interface
            voice_interface = create_streaming_voice_interface(key=f"voice-{agent_choice.lower().replace(' ', '-')}", on_start=start_recording, on_stop=stop_recording)
            if not st.session_state.recording:
                if st.button("🎤 Record", help="Click to start voice input", key=f"voice_btn_{messages_key}", use_container_width=True):
                    start_recording()
            # Render the streaming interface
            voice_interface.render_interface(st.session_state.recording)

        if voice_mode == "Basic (Click to Record)":
            # Voice input controls
            st.markdown("### 🎤 Voice Input")
            if not st.session_state.recording:
                if st.button("🎤 Record", help="Click to start voice input", key=f"voice_btn_{messages_key}", use_container_width=True):
                    start_recording()
            else:
                recognize_speech_from_microphone()
    
    if st.session_state.recording:
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

        st.write_stream(stream_stt())

    # Chat interface
    clean_chat_interface(selected_agent, agent_choice, messages_key, is_async)

    # Settings panel (collapsible)
    if show_settings:
        with st.expander("⚙️ Management Settings", expanded=False):
            tab1, tab2, tab3 = st.tabs(["📊 History", "💾 Export/Import", " Stats"])

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