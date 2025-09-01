"""
FastAPI utilities package
Contains utilities specifically designed for FastAPI integration
"""

from .azure_speech_streaming import AzureSpeechStreamingProcessor, get_speech_config

__all__ = ['AzureSpeechStreamingProcessor', 'get_speech_config']
