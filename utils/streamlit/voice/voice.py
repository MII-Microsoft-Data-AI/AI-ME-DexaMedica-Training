import os
import streamlit as st
import queue
import threading
from typing import Optional, Dict, Any, Callable

# Azure Speech SDK for voice-to-text
import azure.cognitiveservices.speech as speechsdk

# Import streaming components
from .webrtc_audio import WebRTCAudioProcessor, get_ice_servers
from .azure_speech_streaming import AzureSpeechStreamingProcessor, get_speech_config
from ..ui.voice_interface import (
    init_voice_session_state, render_voice_interface_css,
    render_voice_configuration_sidebar, render_connection_status,
    update_transcription, get_voice_input_for_chat, 
)

# Queue for streaming STT results (backward compatibility)
queue_output_stt = queue.Queue()

# Signal for stopping the recognition thread
stop_recognition_signal = threading.Event()

# Voice input section
speech_key = os.environ.get('SPEECH_KEY')
speech_endpoint = os.environ.get('SPEECH_ENDPOINT')


# Voice-to-text functionality using Azure Speech Services
def recognize_speech_from_microphone(language: str = "id-ID") -> Dict[str, Any]:
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
    speech_config.speech_recognition_language = language  # Change language as needed

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

    thread = threading.Thread(target=_main_thread_)
    thread.start()


class StreamingVoiceInterface:
    """
    Streaming voice interface using WebRTC and Azure Speech Services
    """
    
    def __init__(self, key: str = "voice-interface", on_start: Optional[Callable[[], None]] = None, on_stop: Optional[Callable[[], None]] = None):
        """
        Initialize streaming voice interface
        
        Args:
            key: Unique key for WebRTC components
        """
        self.key = key
        self.webrtc_processor = None
        self.speech_processor = None
        self.config = {}
        self.webrtc_ctx = None
        self.queue_output = queue_output_stt  # For backward compatibility
        self.stop_signal = stop_recognition_signal

        self.on_start = on_start
        self.on_stop = on_stop
        
    def initialize(self) -> bool:
        """
        Initialize the streaming voice interface
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Initialize session state
            init_voice_session_state()
            
            # Render CSS
            render_voice_interface_css()
            
            # Get configuration from sidebar
            self.config = render_voice_configuration_sidebar()
            
            # Initialize speech processor
            if not self.speech_processor:
                self.speech_processor = AzureSpeechStreamingProcessor(
                    language=self.config["language"],
                    queue_output=self.queue_output
                )
                
                if not self.speech_processor.initialize():
                    return False
                    
            # Initialize WebRTC processor
            if not self.webrtc_processor:
                self.webrtc_processor = WebRTCAudioProcessor(
                    audio_callback=self.speech_processor.push_audio_data,
                    on_start=self.on_start,
                    on_stop=self.on_stop,
                )
            
            return True
        except Exception as e:
            st.error(f"Initialization error: {str(e)}")
            return False
    
    def _on_speech_result(self, result: Dict):
        """Handle speech recognition results"""
        update_transcription(result)
    
    def render_interface(self, active: bool = False) -> Optional[str]:
        """
        Render the streaming voice interface
        
        Returns:
            Optional[str]: Transcribed text for chat if user clicked "Send to Chat"
        """
        # Initialize session state
        init_voice_session_state()
        
        # Render CSS
        render_voice_interface_css()
        
        # Get configuration from sidebar
        self.config = render_voice_configuration_sidebar()
        
        # Initialize speech processor if not already done
        if not self.speech_processor:
            self.speech_processor = AzureSpeechStreamingProcessor(
                language=self.config["language"],
                queue_output=self.queue_output
            )
            
            if not self.speech_processor.initialize():
                st.error(f"❌ Failed to initialize Azure Speech Services: {self.speech_processor.error_message}")
                return None
        
        # Initialize WebRTC processor if not already done
        if not self.webrtc_processor:
            self.webrtc_processor = WebRTCAudioProcessor(
                audio_callback=self.speech_processor.push_audio_data,
                on_start=self.on_start,
                on_stop=self.on_stop,
                stop_signal=self.stop_signal
            )
            
        if not active:
            return
        
        self.webrtc_ctx = self.webrtc_processor.setup_webrtc_streamer(self.key)
        self.speech_processor.start_continuous_recognition()
        self.webrtc_processor.start_audio_processing(self.webrtc_ctx)
    
    def get_transcribed_text(self) -> Optional[str]:
        """
        Get current transcribed text
        
        Returns:
            Optional[str]: Current transcription
        """
        return get_voice_input_for_chat()
    
    def clear_transcription(self):
        """Clear current transcription"""
        st.session_state.voice_current_transcription = ""
        st.session_state.voice_interim_transcription = ""
    
    def cleanup(self):
        """Cleanup resources"""
        if self.speech_processor:
            self.speech_processor.cleanup()
        if self.webrtc_processor:
            self.webrtc_processor.stop_audio_processing()

def create_streaming_voice_interface(key: str = "voice-interface", on_start: Optional[Callable[[], None]] = None, on_stop: Optional[Callable[[], None]] = None) -> StreamingVoiceInterface:
    """
    Create or get existing streaming voice interface instance
    
    Args:
        key: Unique key for WebRTC components
        on_start: Optional callback when recording starts
        on_stop: Optional callback when recording stops
        
    Returns:
        StreamingVoiceInterface: The voice interface instance
    """
    return StreamingVoiceInterface(key=key, on_start=on_start, on_stop=on_stop)