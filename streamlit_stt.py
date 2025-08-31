"""
Real-time Speech-to-Text using Azure Cognitive Services and streamlit-webrtc

This application demonstrates real-time speech recognition using:
1. Azure Speech Services for accurate speech-to-text conversion
2. streamlit-webrtc for capturing audio directly from the browser
3. Custom audio processing pipeline for seamless integration

Requirements:
- SPEECH_KEY: Azure Speech Services API key
- SPEECH_ENDPOINT: Azure Speech Services endpoint
- Optional: TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN for better WebRTC connectivity
"""

import asyncio
import logging
import os
import queue
import threading
import time
import tempfile
import io
from collections import deque
from pathlib import Path
from typing import List, Optional

import av
import numpy as np
import pydub
import streamlit as st
from twilio.rest import Client
import azure.cognitiveservices.speech as speechsdk

from streamlit_webrtc import WebRtcMode, webrtc_streamer

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Set page configuration
st.set_page_config(
    page_title="Real-time Speech-to-Text",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        padding: 1rem 0;
        border-bottom: 2px solid #f0f2f6;
        margin-bottom: 2rem;
    }
    .status-box {
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .status-listening {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .status-processing {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    .status-error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .transcription-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 20px;
        margin: 10px 0;
        min-height: 100px;
        font-family: monospace;
    }
    .confidence-meter {
        background-color: #e9ecef;
        border-radius: 10px;
        height: 20px;
        overflow: hidden;
    }
    .confidence-bar {
        height: 100%;
        background-color: #28a745;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    if 'transcription_history' not in st.session_state:
        st.session_state.transcription_history = []
    if 'current_transcription' not in st.session_state:
        st.session_state.current_transcription = ""
    if 'is_listening' not in st.session_state:
        st.session_state.is_listening = False
    if 'confidence_scores' not in st.session_state:
        st.session_state.confidence_scores = []

init_session_state()

# Azure Speech Services configuration
def get_speech_config():
    """Get Azure Speech Services configuration"""
    speech_key = os.environ.get('SPEECH_KEY')
    speech_endpoint = os.environ.get('SPEECH_ENDPOINT')
    
    if not speech_key or not speech_endpoint:
        return None, "Missing SPEECH_KEY or SPEECH_ENDPOINT environment variables"
    
    try:
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            endpoint=speech_endpoint
        )
        # Set language (can be made configurable)
        speech_config.speech_recognition_language = "en-US"
        speech_config.enable_dictation()
        return speech_config, None
    except Exception as e:
        return None, f"Error creating speech config: {str(e)}"

# WebRTC configuration
@st.cache_data
def get_ice_servers():
    """Get ICE servers for WebRTC connection"""
    try:
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    except KeyError:
        logger.warning(
            "Twilio credentials are not set. Fallback to a free STUN server from Google."
        )
        return [{"urls": ["stun:stun.l.google.com:19302"]}]

    if not account_sid or not auth_token:
        return [{"urls": ["stun:stun.l.google.com:19302"]}]

    try:
        client = Client(account_sid, auth_token)
        token = client.tokens.create()
        return token.ice_servers
    except Exception as e:
        logger.warning(f"Failed to get Twilio ICE servers: {e}")
        return [{"urls": ["stun:stun.l.google.com:19302"]}]

class AzureSpeechProcessor:
    """Handles Azure Speech Services integration"""
    
    def __init__(self, speech_config):
        self.speech_config = speech_config
        self.recognizer = None
        self.audio_stream = None
        self.results_queue = queue.Queue()
        self.is_running = False
        
    def setup_recognizer(self):
        """Setup the speech recognizer with custom audio stream"""
        try:
            # Create a push audio input stream
            self.audio_stream = speechsdk.audio.PushAudioInputStream()
            audio_config = speechsdk.audio.AudioConfig(stream=self.audio_stream)
            
            # Create recognizer
            self.recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Connect event handlers
            self.recognizer.recognizing.connect(self._on_recognizing)
            self.recognizer.recognized.connect(self._on_recognized)
            self.recognizer.session_started.connect(self._on_session_started)
            self.recognizer.session_stopped.connect(self._on_session_stopped)
            self.recognizer.canceled.connect(self._on_canceled)
            
            return True
        except Exception as e:
            logger.error(f"Failed to setup recognizer: {e}")
            return False
    
    def _on_recognizing(self, evt):
        """Handle intermediate recognition results"""
        if evt.result.text:
            self.results_queue.put({
                "type": "recognizing",
                "text": evt.result.text,
                "confidence": None
            })
    
    def _on_recognized(self, evt):
        """Handle final recognition results"""
        if evt.result.text:
            self.results_queue.put({
                "type": "recognized",
                "text": evt.result.text,
                "confidence": evt.result.json if hasattr(evt.result, 'json') else None
            })
    
    def _on_session_started(self, evt):
        """Handle session start"""
        logger.info("Speech recognition session started")
    
    def _on_session_stopped(self, evt):
        """Handle session stop"""
        logger.info("Speech recognition session stopped")
        self.is_running = False
    
    def _on_canceled(self, evt):
        """Handle cancellation"""
        logger.warning(f"Speech recognition canceled: {evt}")
        self.is_running = False
    
    def start_continuous_recognition(self):
        """Start continuous speech recognition"""
        if self.recognizer:
            self.recognizer.start_continuous_recognition()
            self.is_running = True
            return True
        return False
    
    def stop_continuous_recognition(self):
        """Stop continuous speech recognition"""
        if self.recognizer:
            self.recognizer.stop_continuous_recognition()
            self.is_running = False
    
    def push_audio_data(self, audio_data):
        """Push audio data to the recognizer"""
        if self.audio_stream and self.is_running:
            try:
                self.audio_stream.write(audio_data)
            except Exception as e:
                logger.error(f"Failed to push audio data: {e}")
    
    def get_results(self):
        """Get recognition results from queue"""
        results = []
        try:
            while True:
                result = self.results_queue.get_nowait()
                results.append(result)
        except queue.Empty:
            pass
        return results

def convert_audio_for_azure(audio_frames):
    """Convert WebRTC audio frames to format suitable for Azure Speech Services"""
    if not audio_frames:
        return b''
    
    try:
        # Combine all audio frames
        sound_chunk = pydub.AudioSegment.empty()
        for audio_frame in audio_frames:
            sound = pydub.AudioSegment(
                data=audio_frame.to_ndarray().tobytes(),
                sample_width=audio_frame.format.bytes,
                frame_rate=audio_frame.sample_rate,
                channels=len(audio_frame.layout.channels),
            )
            sound_chunk += sound
        
        if len(sound_chunk) > 0:
            # Convert to 16kHz mono 16-bit PCM (required by Azure Speech Services)
            sound_chunk = sound_chunk.set_channels(1).set_frame_rate(16000)
            sound_chunk = sound_chunk.set_sample_width(2)  # 16-bit
            return sound_chunk.raw_data
        
        return b''
    except Exception as e:
        logger.error(f"Failed to convert audio: {e}")
        return b''

def main():
    """Main application"""
    st.title("🎤 Real-time Speech-to-Text")
    st.markdown("**Powered by Azure Cognitive Services & WebRTC**")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Language selection
        language_options = {
            "English (US)": "en-US",
            "English (UK)": "en-GB",
            "Spanish": "es-ES",
            "French": "fr-FR",
            "German": "de-DE",
            "Italian": "it-IT",
            "Portuguese": "pt-BR",
            "Japanese": "ja-JP",
            "Korean": "ko-KR",
            "Chinese (Simplified)": "zh-CN"
        }
        
        selected_language = st.selectbox(
            "Recognition Language",
            list(language_options.keys()),
            index=0
        )
        
        # Mode selection
        app_mode = st.selectbox(
            "Application Mode",
            ["Audio Only", "Audio + Video"]
        )
        
        # WebRTC settings
        st.subheader("🌐 Connection")
        show_webrtc_logs = st.checkbox("Show WebRTC Logs", False)
        
        # Clear history button
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.transcription_history = []
            st.session_state.current_transcription = ""
            st.rerun()
    
    # Check Azure Speech Services configuration
    speech_config, error_msg = get_speech_config()
    
    if not speech_config:
        st.error(f"❌ **Configuration Error:** {error_msg}")
        st.info("Please set the following environment variables:")
        st.code("""
SPEECH_KEY=your_azure_speech_key
SPEECH_ENDPOINT=your_azure_speech_endpoint
        """)
        return
    
    # Update language in speech config
    speech_config.speech_recognition_language = language_options[selected_language]
    
    # Create Azure Speech processor
    speech_processor = AzureSpeechProcessor(speech_config)
    
    if not speech_processor.setup_recognizer():
        st.error("❌ Failed to setup Azure Speech recognizer")
        return
    
    st.success("✅ Azure Speech Services configured successfully")
    
    # Audio processing queue for threading
    frames_deque_lock = threading.Lock()
    frames_deque: deque = deque([])
    
    async def queued_audio_frames_callback(frames: List[av.AudioFrame]) -> List[av.AudioFrame]:
        """Callback to handle incoming audio frames"""
        with frames_deque_lock:
            frames_deque.extend(frames)
        
        # Return empty frames to avoid echo
        new_frames = []
        for frame in frames:
            input_array = frame.to_ndarray()
            new_frame = av.AudioFrame.from_ndarray(
                np.zeros(input_array.shape, dtype=input_array.dtype),
                layout=frame.layout.name,
            )
            new_frame.sample_rate = frame.sample_rate
            new_frames.append(new_frame)
        
        return new_frames
    
    # Configure WebRTC based on mode
    if app_mode == "Audio Only":
        webrtc_ctx = webrtc_streamer(
            key="speech-to-text-audio",
            mode=WebRtcMode.SENDONLY,
            audio_receiver_size=1024,
            rtc_configuration={"iceServers": get_ice_servers()},
            media_stream_constraints={"video": False, "audio": True},
            async_processing=True,
        )
    else:
        webrtc_ctx = webrtc_streamer(
            key="speech-to-text-video",
            mode=WebRtcMode.SENDRECV,
            queued_audio_frames_callback=queued_audio_frames_callback,
            rtc_configuration={"iceServers": get_ice_servers()},
            media_stream_constraints={"video": True, "audio": True},
            async_processing=True,
        )
    
    # Status indicators
    col1, col2, col3 = st.columns(3)
    with col1:
        connection_status = st.empty()
    with col2:
        listening_status = st.empty()
    with col3:
        processing_status = st.empty()
    
    # Transcription display area
    st.subheader("📝 Live Transcription")
    current_text = st.empty()
    
    # Historical transcriptions
    if st.session_state.transcription_history:
        with st.expander("📚 Transcription History", expanded=False):
            for i, entry in enumerate(reversed(st.session_state.transcription_history[-10:])):
                st.text(f"{i+1}. {entry}")
    
    # Main processing loop
    if not webrtc_ctx.state.playing:
        connection_status.markdown("🔴 **Disconnected**")
        listening_status.markdown("⏸️ **Not Listening**")
        processing_status.markdown("💤 **Idle**")
        current_text.markdown("*Click 'Start' to begin speech recognition...*")
        return
    
    connection_status.markdown("🟢 **Connected**")
    listening_status.markdown("🎤 **Listening**")
    
    # Start Azure Speech recognition
    if speech_processor.start_continuous_recognition():
        processing_status.markdown("🔄 **Processing**")
    else:
        processing_status.markdown("❌ **Error**")
        st.error("Failed to start speech recognition")
        return
    
    # Audio processing thread
    def process_audio_frames():
        """Process audio frames in a separate thread"""
        while webrtc_ctx.state.playing:
            audio_frames = []
            
            if app_mode == "Audio Only":
                if webrtc_ctx.audio_receiver:
                    try:
                        audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=0.1)
                    except queue.Empty:
                        continue
            else:
                with frames_deque_lock:
                    while len(frames_deque) > 0:
                        frame = frames_deque.popleft()
                        audio_frames.append(frame)
            
            if audio_frames:
                # Convert audio for Azure Speech Services
                audio_data = convert_audio_for_azure(audio_frames)
                if audio_data:
                    speech_processor.push_audio_data(audio_data)
            
            time.sleep(0.01)  # Small delay to prevent excessive CPU usage
    
    # Start audio processing thread
    audio_thread = threading.Thread(target=process_audio_frames, daemon=True)
    audio_thread.start()
    
    # Main display loop
    display_text = ""
    
    while webrtc_ctx.state.playing:
        # Get recognition results
        results = speech_processor.get_results()
        
        for result in results:
            if result["type"] == "recognizing":
                # Show intermediate results
                display_text = f"*{result['text']}*"
                current_text.markdown(f"**Current:** {display_text}")
            
            elif result["type"] == "recognized":
                # Show final results
                final_text = result['text']
                if final_text.strip():
                    display_text = final_text
                    current_text.markdown(f"**Final:** {display_text}")
                    
                    # Add to history
                    st.session_state.transcription_history.append(final_text)
                    st.session_state.current_transcription = final_text
                    
                    # Keep only last 50 entries
                    if len(st.session_state.transcription_history) > 50:
                        st.session_state.transcription_history = st.session_state.transcription_history[-50:]
        
        if not display_text:
            current_text.markdown("*Listening for speech...*")
        
        time.sleep(0.1)
    
    # Cleanup
    speech_processor.stop_continuous_recognition()
    connection_status.markdown("🔴 **Disconnected**")
    listening_status.markdown("⏸️ **Stopped**")
    processing_status.markdown("💤 **Idle**")

if __name__ == "__main__":
    # Set up logging
    DEBUG = os.environ.get("DEBUG", "false").lower() not in ["false", "no", "0"]
    
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)7s from %(name)s in %(pathname)s:%(lineno)d: %(message)s",
        force=True,
    )
    
    logger.setLevel(level=logging.DEBUG if DEBUG else logging.INFO)
    
    # Streamlit WebRTC logger
    st_webrtc_logger = logging.getLogger("streamlit_webrtc")
    st_webrtc_logger.setLevel(logging.DEBUG if DEBUG else logging.WARNING)
    
    # Run main application
    main()
