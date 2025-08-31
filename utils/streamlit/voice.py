import os
import streamlit as st
import queue
from threading import Thread

# Azure Speech SDK for voice-to-text
import azure.cognitiveservices.speech as speechsdk

# Queue for streaming STT results
queue_output_stt = queue.Queue()

# Voice input section
speech_key = os.environ.get('SPEECH_KEY')
speech_endpoint = os.environ.get('SPEECH_ENDPOINT')

# Voice-to-text functionality using Azure Speech Services
def recognize_speech_from_microphone():
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
    speech_config.speech_recognition_language = "id-ID"  # Change language as needed

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

    thread = Thread(target=_main_thread_)
    thread.start()