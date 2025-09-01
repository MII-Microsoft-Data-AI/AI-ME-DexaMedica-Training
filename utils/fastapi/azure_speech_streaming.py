"""
Azure Speech Services Streaming Module for FastAPI

Handles continuous speech recognition with streaming audio input.
Provides real-time transcription with intermediate and final results.
Optimized for FastAPI WebSocket integration.
"""

import os
import logging
import queue
import threading
from typing import Optional, Dict, List, Callable

import azure.cognitiveservices.speech as speechsdk

import pydub
import io

logger = logging.getLogger(__name__)


def get_speech_config(language: str = "en-US") -> tuple[Optional[speechsdk.SpeechConfig], Optional[str]]:
    """
    Get Azure Speech Services configuration
    
    Args:
        language: Speech recognition language code
        
    Returns:
        tuple: (SpeechConfig object, error message if any)
    """
    speech_key = os.environ.get('SPEECH_KEY')
    speech_endpoint = os.environ.get('SPEECH_ENDPOINT')
    
    if not speech_key or not speech_endpoint:
        return None, "Missing SPEECH_KEY or SPEECH_ENDPOINT environment variables"
    
    try:
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            endpoint=speech_endpoint
        )
        speech_config.speech_recognition_language = language
        speech_config.enable_dictation()
        return speech_config, None
    except Exception as e:
        return None, f"Error creating speech config: {str(e)}"


class AzureSpeechStreamingProcessor:
    """
    Handles Azure Speech Services streaming integration for continuous recognition
    Optimized for FastAPI WebSocket usage
    """
    
    def __init__(self, language: str = "en-US", queue_output: Optional[queue.Queue] = None):
        """
        Initialize Azure Speech streaming processor
        
        Args:
            language: Speech recognition language
            queue_output: Optional queue to output recognition results
        """
        self.language = language
        self.speech_config = None
        self.recognizer = None
        self.audio_stream = None
        self.is_running = False
        self.error_message = None
        self.queue_output = queue_output
        
    def initialize(self) -> bool:
        """
        Initialize the speech recognizer
        
        Returns:
            bool: True if initialization successful
        """
        self.speech_config, error_msg = get_speech_config(self.language)
        if not self.speech_config:
            self.error_message = error_msg
            return False
            
        return self.setup_recognizer()
    
    def setup_recognizer(self) -> bool:
        """
        Setup the speech recognizer with custom audio stream
        
        Returns:
            bool: True if setup successful
        """
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
            self.error_message = f"Failed to setup recognizer: {e}"
            return False
    
    def _on_recognizing(self, evt):
        """Handle intermediate recognition results"""
        print("Recognizing result:", evt.result.text)
        logger.debug(f"Recognizing: {evt.result.text}")
        if evt.result.text:
            result = {
                "finish": False,
                "type": "recognizing",
                "text": evt.result.text,
                "confidence": None,
                "timestamp": threading.current_thread().ident
            }
            if self.queue_output:
                self.queue_output.put(result)
    
    def _on_recognized(self, evt):
        """Handle final recognition results"""
        print("Recognized result:", evt.result.text)
        logger.debug(f"Recognized: {evt.result.text}")
        if evt.result.text:
            # Try to extract confidence score if available
            confidence = None
            try:
                if hasattr(evt.result, 'json'):
                    import json
                    result_json = json.loads(evt.result.json)
                    if 'NBest' in result_json and len(result_json['NBest']) > 0:
                        confidence = result_json['NBest'][0].get('Confidence', None)
            except:
                pass
                
            result = {
                "finish": True,
                "type": "recognized",
                "text": evt.result.text,
                "confidence": confidence,
                "timestamp": threading.current_thread().ident
            }
            if self.queue_output:
                self.queue_output.put(result)
    
    def _on_session_started(self, evt):
        print("Starting session:", evt)
        """Handle session start"""
        logger.info("Speech recognition session started")
    
    def _on_session_stopped(self, evt):
        """Handle session stop"""
        print("Session stop:", evt)
        logger.info("Speech recognition session stopped")
        self.is_running = False
    
    def _on_canceled(self, evt):
        """Handle cancellation"""
        print("Recognition canceled:", evt)
        logger.warning(f"Speech recognition canceled: {evt}")
        self.is_running = False
        if hasattr(evt, 'error_details'):
            self.error_message = f"Recognition canceled: {evt.error_details}"
    
    def start_continuous_recognition(self) -> bool:
        """
        Start continuous speech recognition
        
        Returns:
            bool: True if started successfully
        """
        if not self.recognizer:
            self.error_message = "Recognizer not initialized"
            return False
            
        if self.is_running:
            return True  # Already running
            
        try:
            logger.info("Starting continuous speech recognition...")
            self.recognizer.start_continuous_recognition_async()
            self.is_running = True
            self.error_message = None
            logger.info("Speech recognition started successfully")
            return True
        except Exception as e:
            error_msg = f"Failed to start recognition: {str(e)}"
            logger.error(error_msg)
            self.error_message = error_msg
            return False
    
    def stop_continuous_recognition(self):
        """Stop continuous speech recognition"""
        if self.recognizer and self.is_running:
            try:
                self.recognizer.stop_continuous_recognition()
            except Exception as e:
                logger.error(f"Error stopping recognition: {e}")
            finally:
                self.is_running = False
    
    def push_audio_data(self, audio_data: bytes):
        """
        Push audio data to the recognizer
        
        Args:
            audio_data: Audio data in 16kHz mono 16-bit PCM format
        """
        if self.audio_stream and self.is_running:
            try:
                logger.debug(f"Pushing audio data of length: {len(audio_data)} bytes")
                print("Pushing audio data of length:", len(audio_data))
                self.audio_stream.write(audio_data)
            except Exception as e:
                print(f"Failed to push audio data: {e}")
                logger.error(f"Failed to push audio data: {e}")
    
    def update_language(self, language: str) -> bool:
        """
        Update recognition language
        
        Args:
            language: New language code
            
        Returns:
            bool: True if updated successfully
        """
        if self.is_running:
            self.stop_continuous_recognition()
            
        self.language = language
        if self.speech_config:
            self.speech_config.speech_recognition_language = language
            return True
        return False
    
    def get_status(self) -> Dict:
        """
        Get current processor status
        
        Returns:
            Dict: Status information
        """
        return {
            "is_running": self.is_running,
            "language": self.language,
            "error_message": self.error_message,
            "has_recognizer": self.recognizer is not None
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_continuous_recognition()
        if self.audio_stream:
            try:
                self.audio_stream.close()
            except:
                pass
        self.audio_stream = None
        self.recognizer = None

    def convert_audio_webm(self, data: bytes) -> bytes:
        """
        Convert WebM audio frames to format suitable for Azure Speech Services for Websocket, WebM/Opus format
             
        Returns:
            bytes: Audio data in 16kHz mono 16-bit PCM format
        """
        if not data:
            return b''
        
        try:
            webm_segment = pydub.AudioSegment.from_file(io.BytesIO(data), codec="opus")
            webm_segment = webm_segment.set_frame_rate(16000) \
                                        .set_channels(1) \
                                        .set_sample_width(2) # 2 bytes = 16 bits

            return webm_segment.raw_data
        except Exception as e:
            print(f"Failed to convert audio: {e}")
            logger.error(f"Failed to convert audio: {e}")
            return b''
        
    def convert_audio_webrtc(self, data: bytes) -> bytes:
        """
        Convert WebRTC audio frames to format suitable for Azure Speech Services
        
        WebRTC sends raw PCM16 data at 16kHz mono, which is exactly what Azure Speech Services expects.
        No conversion needed, just return the data as-is.
             
        Returns:
            bytes: Audio data in 16kHz mono 16-bit PCM format
        """
        if not data:
            return b''
        
        try:
            # WebRTC already provides PCM16 16kHz mono data
            # Azure Speech Services expects exactly this format
            logger.debug(f"WebRTC audio data received: {len(data)} bytes")
            return data
        except Exception as e:
            logger.error(f"Failed to process WebRTC audio: {e}")
            return b''
    
    def convert_audio(self, data: bytes, format_type: str = "webm") -> bytes:
        """
        Convert audio data to format suitable for Azure Speech Services
        
        Args:
            data: Raw audio data
            format_type: Audio format type ("webm", "webrtc", "pcm16")
            
        Returns:
            bytes: Audio data in 16kHz mono 16-bit PCM format
        """
        if not data:
            return b''
        
        if format_type.lower() in ["webrtc", "pcm16"]:
            return self.convert_audio_webrtc(data)
        elif format_type.lower() == "webm":
            return self.convert_audio_webm(data)
        else:
            logger.warning(f"Unknown audio format: {format_type}, treating as WebRTC/PCM16")
            return self.convert_audio_webrtc(data)