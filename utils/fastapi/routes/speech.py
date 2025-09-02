"""
Speech API Routes
================

FastAPI routes for speech recognition and WebSocket operations.
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import logging
import json
import os
import asyncio
import queue
import threading
import base64
import zlib

# Import speech streaming utilities
from utils.fastapi.azure_speech_streaming import AzureSpeechStreamingProcessor

# Initialize router
router = APIRouter(prefix="/speech", tags=["Speech"])

# Compression utilities for audio data
def compress_base64(data: str) -> str:
    """Compress base64 encoded data using zlib"""
    try:
        # Decode base64 to bytes
        decoded_data = base64.b64decode(data)
        
        # Compress using zlib
        compressed_data = zlib.compress(decoded_data)
        
        # Encode back to base64
        compressed_base64 = base64.b64encode(compressed_data).decode('utf-8')
        
        compression_ratio = (1 - len(compressed_data) / len(decoded_data)) * 100
        logging.debug(f"Compression ratio: {compression_ratio:.1f}% ({len(decoded_data)} -> {len(compressed_data)} bytes)")
        
        return compressed_base64
    except Exception as e:
        logging.error(f"Error compressing data: {e}")
        return data  # Return original data if compression fails

def decompress_base64(data: str) -> str:
    """Decompress zlib compressed base64 encoded data"""
    try:
        # Decode base64 to bytes
        compressed_data = base64.b64decode(data)
        
        # Decompress using zlib
        decompressed_data = zlib.decompress(compressed_data)
        
        # Encode back to base64
        decompressed_base64 = base64.b64encode(decompressed_data).decode('utf-8')
        
        return decompressed_base64
    except Exception as e:
        logging.error(f"Error decompressing data: {e}")
        return data  # Return original data if decompression fails

@router.websocket("/stream")
async def websocket_speech_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time speech recognition
    
    Protocol:
    1. Client connects and sends config message: {"type": "config", "language": "en-US"}
    2. Client sends start message: {"type": "start"}
    3. Client sends audio chunks: {"type": "audio", "data": "base64_encoded_pcm_audio"}
    4. Server responds with recognition results: {"finish": false/true, "text": "...", "type": "recognizing/recognized"}
    5. Client sends stop message: {"type": "stop"}
    """
    await websocket.accept()
    logging.info("WebSocket connection established for speech recognition")
    
    speech_processor = None
    results_queue = queue.Queue()
    stop_event = threading.Event()
    audio_bytes_frames = []
    
    async def send_recognition_results(websocket: WebSocket, results_queue: queue.Queue, stop_event: threading.Event):
        """Background task to send recognition results to client"""
        while not stop_event.is_set():
            try:
                # Get results from queue with timeout
                if not results_queue.empty():
                    result = results_queue.get()
                    await websocket.send_json(result)
                await asyncio.sleep(0.1)  # Small delay to prevent high CPU usage
            except Exception as e:
                logging.error(f"Error sending recognition results: {e}")
                break
    
    background_task = None
    
    try:
        async for message in websocket.iter_text():
            try:
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "config":
                    # Initialize speech processor with language
                    language = data.get("language", "en-US")
                    
                    # Check required environment variables
                    speech_key = os.environ.get('SPEECH_KEY')
                    speech_endpoint = os.environ.get('SPEECH_ENDPOINT')
                    
                    if not speech_key or not speech_endpoint:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Missing SPEECH_KEY or SPEECH_ENDPOINT environment variables"
                        })
                        continue
                    
                    speech_processor = AzureSpeechStreamingProcessor(
                        language=language, 
                        queue_output=results_queue
                    )
                    
                    if not speech_processor.initialize():
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Failed to initialize speech recognizer: {speech_processor.error_message}"
                        })
                        continue
                    
                    await websocket.send_json({
                        "type": "config_success",
                        "message": f"Speech recognizer initialized for language: {language}"
                    })
                    
                elif msg_type == "start":
                    with results_queue.mutex:
                        results_queue.queue.clear()
                    audio_bytes_frames = []
                    if not speech_processor:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Speech processor not initialized. Send config message first."
                        })
                        continue
                    
                    if speech_processor.start_continuous_recognition():

                        def __thread_recognition__(websocket: WebSocket, results_queue: queue.Queue, stop_event: threading.Event):
                            print("Thread recognition started")
                            try:
                                asyncio.run(send_recognition_results(websocket, results_queue, stop_event))
                            except Exception as e:
                                logging.error(f"Error in recognition thread: {e}")

                        # Start background task to send results
                        stop_event.clear()
                        background_task = threading.Thread(
                            target=__thread_recognition__,
                            args=(websocket, results_queue, stop_event),
                            daemon=True
                        )
                        background_task.start()
                        
                        await websocket.send_json({
                            "type": "start_success",
                            "message": "Speech recognition started"
                        })
                    else:
                        await websocket.send_json({
                            "type": "error", 
                            "message": f"Failed to start recognition: {speech_processor.error_message}"
                        })
                
                elif msg_type == "audio":
                    if not speech_processor or not speech_processor.is_running:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Speech recognition not running. Send start message first."
                        })
                        continue
                    
                    audio_data = data.get("data")
                    audio_format = data.get("format", "webm")  # Default to webm for backward compatibility
                    is_compressed = data.get("compressed", False)  # Check if data is compressed
                    
                    if audio_data:
                        try:
                            logging.debug(f"Received audio chunk of size: {len(audio_data)} elem, format: {audio_format}, compressed: {is_compressed}")
                            # Handle compressed data
                            if is_compressed:
                                logging.debug("Decompressing audio data...")
                                audio_data = decompress_base64(audio_data)
                                logging.debug("Audio data decompressed successfully")
                            
                            # Decode base64 audio data
                            audio_bytes = base64.b64decode(audio_data)
                            audio_bytes_frames.append(audio_bytes)
                            
                            # Use the new convert_audio method with format detection
                            audio_data_bytes = speech_processor.convert_audio(audio_bytes, audio_format)
                            speech_processor.push_audio_data(audio_data_bytes)
                        except Exception as e:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Failed to process audio data: {str(e)}"
                            })
                
                elif msg_type == "stop":
                    if speech_processor:
                        speech_processor.stop_continuous_recognition()
                        stop_event.set()
                        
                        if background_task:
                            try:
                                background_task.join()
                            except asyncio.CancelledError:
                                pass
                    
                    audio_bytes_frames = []
                    with results_queue.mutex:
                        results_queue.queue.clear()
                    await websocket.send_json({
                        "type": "stop_success",
                        "message": "Speech recognition stopped"
                    })
                
                elif msg_type == "ping":
                    # Respond to ping with pong to keep connection alive
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": data.get("timestamp", "")
                    })
                
                else:
                    with results_queue.mutex:
                        results_queue.queue.clear()
                    audio_bytes_frames = []
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {msg_type}"
                    })
                    
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logging.error(f"Error processing WebSocket message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                })
    
    except WebSocketDisconnect:
        logging.info("WebSocket disconnected")
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        # Cleanup
        stop_event.set()
        if background_task:
            try:
                background_task.join()
            except (RuntimeError, AttributeError):
                pass
        
        if speech_processor:
            speech_processor.cleanup()
        
        logging.info("WebSocket connection closed and cleaned up")

@router.get("/test")
async def speech_test():
    """Test endpoint to check if speech services are configured"""
    logging.info('FastAPI speech test endpoint processed a request.')
    
    speech_key = os.environ.get('SPEECH_KEY')
    speech_endpoint = os.environ.get('SPEECH_ENDPOINT')
    
    if not speech_key or not speech_endpoint:
        return {
            "configured": False,
            "message": "Missing SPEECH_KEY or SPEECH_ENDPOINT environment variables",
            "required_env_vars": ["SPEECH_KEY", "SPEECH_ENDPOINT"]
        }
    
    try:
        # Test speech configuration
        from utils.fastapi.azure_speech_streaming import get_speech_config
        config, error = get_speech_config()
        if error:
            return {
                "configured": False,
                "message": f"Speech configuration error: {error}"
            }
        
        return {
            "configured": True,
            "message": "Speech services configured successfully",
            "websocket_url": "/speech/stream"
        }
    except Exception as e:
        return {
            "configured": False,
            "message": f"Error testing speech configuration: {str(e)}"
        }

@router.get("/test-ui", response_class=HTMLResponse)
async def speech_test_ui():
    """Serve the speech recognition test HTML page"""
    try:
        with open("speech_test.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Speech test UI not found")
