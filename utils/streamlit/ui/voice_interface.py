"""
Voice Interface UI Components

Provides Streamlit UI components for voice input and real-time transcription display.
Handles voice interface controls, status indicators, and transcription visualization.
"""

import streamlit as st
import time
from typing import Dict, List, Optional


# Language options for speech recognition
LANGUAGE_OPTIONS = {
    "English (US)": "en-US",
    "English (UK)": "en-GB", 
    "Spanish": "es-ES",
    "French": "fr-FR",
    "German": "de-DE",
    "Italian": "it-IT",
    "Portuguese": "pt-BR",
    "Japanese": "ja-JP",
    "Korean": "ko-KR",
    "Chinese (Simplified)": "zh-CN",
    "Indonesian": "id-ID"
}

# Custom CSS for voice interface
VOICE_INTERFACE_CSS = """
<style>
    .voice-status-box {
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
        text-align: center;
        font-weight: 500;
    }
    .status-connected {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .status-disconnected {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .status-processing {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    .transcription-display {
        background-color: #f8f9fa;
        border: 2px solid #dee2e6;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        min-height: 60px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.5;
    }
    .transcription-interim {
        color: #6c757d;
        font-style: italic;
    }
    .transcription-final {
        color: #212529;
        font-weight: 500;
    }
    .voice-controls {
        display: flex;
        gap: 10px;
        justify-content: center;
        margin: 15px 0;
    }
    .confidence-indicator {
        font-size: 0.8em;
        color: #6c757d;
        margin-top: 5px;
    }
</style>
"""


def init_voice_session_state():
    """Initialize voice-related session state variables"""
    if 'voice_transcription_history' not in st.session_state:
        st.session_state.voice_transcription_history = []
    if 'voice_current_transcription' not in st.session_state:
        st.session_state.voice_current_transcription = ""
    if 'voice_interim_transcription' not in st.session_state:
        st.session_state.voice_interim_transcription = ""
    if 'voice_is_listening' not in st.session_state:
        st.session_state.voice_is_listening = False
    if 'voice_selected_language' not in st.session_state:
        st.session_state.voice_selected_language = "English (US)"
    if 'voice_app_mode' not in st.session_state:
        st.session_state.voice_app_mode = "Audio Only"


def render_voice_interface_css():
    """Render CSS styles for voice interface"""
    st.markdown(VOICE_INTERFACE_CSS, unsafe_allow_html=True)


def render_voice_configuration_sidebar():
    """
    Render voice configuration options in sidebar
    
    Returns:
        Dict: Configuration settings
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎤 Voice Settings")
    
    # Language selection
    selected_language = st.sidebar.selectbox(
        "Recognition Language",
        list(LANGUAGE_OPTIONS.keys()),
        index=list(LANGUAGE_OPTIONS.keys()).index(st.session_state.voice_selected_language),
        key="voice_language_selector"
    )
    st.session_state.voice_selected_language = selected_language
    
    # Advanced settings
    with st.sidebar.expander("🔧 Advanced Settings"):
        show_interim_results = st.checkbox(
            "Show interim results", 
            value=True, 
            help="Display real-time transcription as you speak"
        )
        
        auto_clear_transcription = st.checkbox(
            "Auto-clear after sending", 
            value=True,
            help="Automatically clear transcription after sending to chat"
        )
        
        transcription_timeout = st.slider(
            "Transcription timeout (seconds)",
            min_value=1,
            max_value=10,
            value=3,
            help="How long to wait for final transcription"
        )
    
    # Clear history button
    if st.sidebar.button("🗑️ Clear Voice History", use_container_width=True):
        st.session_state.voice_transcription_history = []
        st.session_state.voice_current_transcription = ""
        st.session_state.voice_interim_transcription = ""
        st.rerun()
    
    return {
        "language": LANGUAGE_OPTIONS[selected_language],
        "language_display": selected_language,
        "show_interim": show_interim_results,
        "auto_clear": auto_clear_transcription,
        "timeout": transcription_timeout
    }


def render_connection_status(webrtc_status: Dict, speech_status: Dict):
    """
    Render connection status indicators
    
    Args:
        webrtc_status: WebRTC connection status
        speech_status: Azure Speech Services status
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if webrtc_status.get("connected", False):
            st.markdown(
                '<div class="voice-status-box status-connected">🟢 WebRTC Connected</div>',
                unsafe_allow_html=True
            )
        else:
            status_text = webrtc_status.get("status_text", "🔴 WebRTC Disconnected")
            st.markdown(
                f'<div class="voice-status-box status-disconnected">{status_text}</div>',
                unsafe_allow_html=True
            )
    
    with col2:
        if speech_status.get("is_running", False):
            st.markdown(
                '<div class="voice-status-box status-processing">🎤 Listening</div>',
                unsafe_allow_html=True
            )
        elif speech_status.get("error_message"):
            st.markdown(
                '<div class="voice-status-box status-disconnected">❌ Speech Error</div>',
                unsafe_allow_html=True
            )
        elif not speech_status.get("has_recognizer", False):
            st.markdown(
                '<div class="voice-status-box status-disconnected">🔧 Not Initialized</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="voice-status-box status-disconnected">⏸️ Not Listening</div>',
                unsafe_allow_html=True
            )
    
    with col3:
        language_display = speech_status.get("language", "Unknown")
        st.markdown(
            f'<div class="voice-status-box status-connected">🌐 {language_display}</div>',
            unsafe_allow_html=True
        )
    
    # Show error message if any
    if speech_status.get("error_message"):
        st.error(f"**Speech Recognition Error:** {speech_status['error_message']}")
        
    # Show WebRTC error if any
    if not webrtc_status.get("connected", False) and webrtc_status.get("state") == "no_context":
        st.warning("⚠️ WebRTC context not available. Make sure to click START to establish connection.")


def render_transcription_display(config: Dict):
    """
    Render real-time transcription display
    
    Args:
        config: Voice interface configuration
    """
    st.subheader("📝 Live Transcription")
    
    # Current transcription display
    display_text = ""
    
    if st.session_state.voice_interim_transcription and config.get("show_interim", True):
        display_text = f'<span class="transcription-interim">{st.session_state.voice_interim_transcription}</span>'
    
    if st.session_state.voice_current_transcription:
        if display_text:
            display_text += "<br>"
        display_text += f'<span class="transcription-final">{st.session_state.voice_current_transcription}</span>'
    
    if not display_text:
        display_text = '<span class="transcription-interim">Listening for speech...</span>'
    
    st.markdown(
        f'<div class="transcription-display">{display_text}</div>',
        unsafe_allow_html=True
    )
    
    # Action buttons for transcription
    if st.session_state.voice_current_transcription:
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("📋 Copy", help="Copy transcription to clipboard"):
                st.code(st.session_state.voice_current_transcription)
        
        with col2:
            if st.button("💬 Send to Chat", help="Send transcription to chat input"):
                return st.session_state.voice_current_transcription
        
        with col3:
            if st.button("🗑️ Clear Current", help="Clear current transcription"):
                st.session_state.voice_current_transcription = ""
                st.session_state.voice_interim_transcription = ""
                st.rerun()
    
    return None


def render_transcription_history():
    """Render transcription history in an expandable section"""
    if st.session_state.voice_transcription_history:
        with st.expander(f"📚 Voice History ({len(st.session_state.voice_transcription_history)} items)", expanded=False):
            for i, entry in enumerate(reversed(st.session_state.voice_transcription_history[-10:])):
                timestamp = entry.get("timestamp", "Unknown")
                text = entry.get("text", "")
                confidence = entry.get("confidence")
                
                st.markdown(f"**{i+1}.** {text}")
                if confidence:
                    st.markdown(f"<div class='confidence-indicator'>Confidence: {confidence:.2f}</div>", 
                              unsafe_allow_html=True)
                st.markdown("---")


def update_transcription(result: Dict):
    """
    Update transcription based on recognition result
    
    Args:
        result: Recognition result from Azure Speech Services
    """
    if result["type"] == "recognizing":
        # Update interim transcription
        st.session_state.voice_interim_transcription = result["text"]
        
    elif result["type"] == "recognized":
        # Update final transcription
        final_text = result["text"].strip()
        if final_text:
            st.session_state.voice_current_transcription = final_text
            st.session_state.voice_interim_transcription = ""
            
            # Add to history
            history_entry = {
                "text": final_text,
                "timestamp": time.strftime("%H:%M:%S"),
                "confidence": result.get("confidence")
            }
            st.session_state.voice_transcription_history.append(history_entry)
            
            # Keep only last 50 entries
            if len(st.session_state.voice_transcription_history) > 50:
                st.session_state.voice_transcription_history = st.session_state.voice_transcription_history[-50:]


def get_voice_input_for_chat() -> Optional[str]:
    """
    Get voice input text for chat integration
    
    Returns:
        Optional[str]: Transcribed text if available
    """
    if st.session_state.voice_current_transcription:
        text = st.session_state.voice_current_transcription
        # Clear after getting (if auto-clear is enabled)
        # This would be controlled by the main interface
        return text
    return None


def render_voice_interface_info():
    """Render information about voice interface capabilities"""
    with st.expander("ℹ️ Voice Interface Help", expanded=False):
        st.markdown("""
        **Voice Interface Features:**
        
        🎤 **Real-time Speech Recognition**
        - Uses Azure Cognitive Services for accurate transcription
        - Supports multiple languages
        - Shows both interim and final results
        
        🌐 **WebRTC Integration**  
        - Direct browser audio capture
        - No additional software needed
        - Works on desktop and mobile browsers
        
        📝 **Transcription Management**
        - View real-time transcription
        - Copy text to clipboard
        - Send directly to chat
        - Maintain transcription history
        
        ⚙️ **Configuration Options**
        - Language selection
        - Audio/Video modes
        - Advanced recognition settings
        
        **Required Environment Variables:**
        - `SPEECH_KEY`: Azure Speech Services API key
        - `SPEECH_ENDPOINT`: Azure Speech Services endpoint
        - `TWILIO_ACCOUNT_SID` (optional): For better WebRTC connectivity
        - `TWILIO_AUTH_TOKEN` (optional): For better WebRTC connectivity
        """)
