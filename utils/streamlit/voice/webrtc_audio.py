"""
WebRTC Audio Processing Module

Handles WebRTC audio streaming and processing for real-time speech recognition.
Provides audio format conversion and frame management for Azure Speech Services.
"""

import os
import logging
import queue
import threading
import time
from collections import deque
from typing import List, Optional, Callable

import av
import numpy as np
import pydub
import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer
from twilio.rest import Client

logger = logging.getLogger(__name__)

@st.cache_data
def get_ice_servers():
    """Get ICE servers for WebRTC connection with Twilio fallback"""
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


def convert_audio_for_azure(audio_frames: List[av.AudioFrame]) -> bytes:
    """
    Convert WebRTC audio frames to format suitable for Azure Speech Services
    
    Args:
        audio_frames: List of WebRTC audio frames
        
    Returns:
        bytes: Audio data in 16kHz mono 16-bit PCM format
    """
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


class WebRTCAudioProcessor:
    """
    Handles WebRTC audio streaming and processing
    """
    
    def __init__(self, audio_callback: Optional[Callable[[bytes], None]] = None, on_start: Optional[Callable[[], None]] = None, on_stop: Optional[Callable[[], None]] = None, stop_signal: Optional[threading.Event] = None):
        """
        Initialize WebRTC audio processor
        
        Args:
            audio_callback: Optional callback function to handle processed audio data
        """
        self.audio_callback = audio_callback
        self.frames_deque_lock = threading.Lock()
        self.frames_deque: deque = deque([])
        self.is_processing = False
        self.processing_thread = None

        self.on_start = on_start
        self.on_stop = on_stop
        self.stop_signal = stop_signal
        
    def setup_webrtc_streamer(self, key: str) -> object:
        """
        Setup WebRTC streamer based on mode
        
        Args:
            key: Unique key for the WebRTC streamer
            mode: Either "audio_only" or "audio_video"
            
        Returns:
            WebRTC context object
        """
        webrtc_ctx = webrtc_streamer(
            key=f"{key}-audio-only",
            mode=WebRtcMode.SENDONLY,
            audio_receiver_size=1024,
            rtc_configuration={"iceServers": get_ice_servers()},
            media_stream_constraints={"video": False, "audio": True},
            async_processing=True,
            desired_playing_state=True
        )
        return webrtc_ctx
    
    async def _queued_audio_frames_callback(self, frames: List[av.AudioFrame]) -> List[av.AudioFrame]:
        """Callback to handle incoming audio frames for audio+video mode"""
        with self.frames_deque_lock:
            self.frames_deque.extend(frames)
        
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
    
    def start_audio_processing(self, webrtc_ctx):
        """
        Start audio processing in a separate thread
        
        Args:
            webrtc_ctx: WebRTC context object
            mode: Audio processing mode
        """
        if self.processing_thread and self.processing_thread.is_alive():
            return
            
        self.is_processing = True
        self.processing_thread = threading.Thread(
            target=self._process_audio_frames,
            args=(webrtc_ctx, self.on_start, self.on_stop, self.stop_signal),
            daemon=True
        )
        self.processing_thread.start()
    
    def stop_audio_processing(self):
        """Stop audio processing"""
        self.is_processing = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
        if self.on_stop:
            self.on_stop()
    
    def _process_audio_frames(self, webrtc_ctx, on_start: Optional[Callable[[], None]] = None, on_stop: Optional[Callable[[], None]] = None, stop_signal: Optional[threading.Event] = None):
        """Process audio frames in a separate thread"""
        if on_start:
            on_start()

        while self.is_processing and webrtc_ctx.state.playing and (stop_signal is None or not stop_signal.is_set()):
            audio_frames = []
            
            if webrtc_ctx.audio_receiver:
                try:
                    audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=0.1)
                except queue.Empty:
                    continue

            if audio_frames and self.audio_callback:
                # Convert audio for Azure Speech Services
                print("Converting audio frames for Azure...")
                audio_data = convert_audio_for_azure(audio_frames)
                print(f"Converted audio data length: {len(audio_data)} bytes")
                if audio_data:
                    self.audio_callback(audio_data)
            
            time.sleep(0.01)  # Small delay to prevent excessive CPU usage
        
        if on_stop:
            on_stop()
    
    def get_connection_status(self, webrtc_ctx) -> dict:
        """
        Get WebRTC connection status
        
        Args:
            webrtc_ctx: WebRTC context object
            
        Returns:
            dict: Status information
        """
        if not webrtc_ctx:
            return {
                "connected": False,
                "listening": False,
                "status_text": "🔴 No WebRTC Context",
                "state": "no_context"
            }
            
        if not webrtc_ctx.state.playing:
            return {
                "connected": False,
                "listening": False,
                "status_text": "🔴 Disconnected",
                "state": "disconnected"
            }
        
        return {
            "connected": True,
            "listening": True,
            "status_text": "🟢 Connected & Listening",
            "state": "connected"
        }
