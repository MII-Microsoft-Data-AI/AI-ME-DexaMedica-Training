#!/usr/bin/env python3
"""
FastAPI application equivalent to the Azure Functions app in function_app.py
"""
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import logging
import json
import os
import tempfile
import asyncio
import queue
import threading
import base64
import zlib
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import all the same dependencies as the Azure Functions app
from single_agent.agent import AgentSingleton
from multi_agent.agent import MultiAgent
from hands_off_agent.agent import HandsoffAgent

# Import document upload utilities
from document_upload_cli.utils import file_eligible, ocr, chunk_text, embed, upload_to_ai_search_studio, init_index, upload_to_blob, init_container

# Import speech streaming utilities
from utils.fastapi.azure_speech_streaming import AzureSpeechStreamingProcessor

from utils.history import chat_history_from_base64, chat_history_to_base64, chat_history_compress, chat_history_decompress
from utils.state import state_compress, state_decompress, state_to_base64, state_from_base64

# Load env
from dotenv import load_dotenv
load_dotenv()  # take environment variables

from semantic_kernel.utils.logging import setup_logging
setup_logging()
logging.getLogger("kernel").setLevel(logging.DEBUG)

# Initialize FastAPI app
app = FastAPI(
    title="Azure Function Semantic Kernel API",
    description="FastAPI equivalent of the Azure Functions semantic kernel application with document upload capabilities",
    version="1.0.0"
)

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

# Initialize agents (same as in function_app.py)
agent = AgentSingleton()
multi_agent = MultiAgent()
hands_off_agent = HandsoffAgent()

# Initialize search index and blob container for document uploads
try:
    init_index()
    init_container()
    logging.info("AI Search index and blob container initialized successfully")
except Exception as e:
    logging.warning(f"Failed to initialize AI Search index or blob container: {e}")
    logging.warning("Document upload functionality may not work properly")

# Pydantic models for request bodies
class ChatRequest(BaseModel):
    chat: str

class HelloRequest(BaseModel):
    name: Optional[str] = None

class ImportRequest(BaseModel):
    data: str

class DocumentUploadResponse(BaseModel):
    message: str
    file_name: str
    chunks_processed: int
    status: str

class SpeechWebSocketMessage(BaseModel):
    type: str  # "config", "audio", "start", "stop"
    data: Optional[str] = None  # base64 encoded audio data or config data
    language: Optional[str] = "en-US"

# Hello endpoint
@app.get("/")
async def root():
    """Root endpoint - serve the chatbot HTML file"""
    with open("utils/fastapi/chatbot_app.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/hello")
async def hello(name: Optional[str] = Query(None)):
    """Hello endpoint - equivalent to Azure Function hello route"""
    logging.info('FastAPI hello endpoint processed a request.')
    
    if name:
        return {"message": f"Hello, {name}. This HTTP triggered function executed successfully."}
    else:
        return {
            "message": "This HTTP triggered function executed successfully. Pass a name in the query string for a personalized response."
        }

@app.post("/hello")
async def hello_post(request: HelloRequest):
    """Hello endpoint - POST version"""
    logging.info('FastAPI hello POST endpoint processed a request.')
    
    if request.name:
        return {"message": f"Hello, {request.name}. This HTTP triggered function executed successfully."}
    else:
        return {
            "message": "This HTTP triggered function executed successfully. Pass a name in the request body for a personalized response."
        }

@app.get("/config/partner-name")
async def get_partner_name():
    """Get partner name from environment variable for footer display"""
    partner_name = os.getenv("PARTNER_NAME")
    return {"partnerName": partner_name}

# Document Upload Endpoints
@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document for AI search indexing"""
    logging.info('FastAPI document upload endpoint processed a request.')
    
    # Environment check
    required_envs = [
        "DOCUMENT_INTELLIGENCE_ENDPOINT",
        "DOCUMENT_INTELLIGENCE_KEY", 
        "OPENAI_KEY",
        "OPENAI_ENDPOINT",
        "AI_SEARCH_KEY",
        "AI_SEARCH_ENDPOINT",
        "AI_SEARCH_INDEX",
        "BLOB_STORAGE_CONNECTION_STRING"
    ]
    missing = [env for env in required_envs if not os.getenv(env)]
    if missing:
        raise HTTPException(
            status_code=500, 
            detail=f"Missing required environment variables: {', '.join(missing)}"
        )
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        try:
            # Write uploaded file to temporary file
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
            
            # Check if file is eligible for processing
            if not file_eligible(temp_file.name):
                raise HTTPException(
                    status_code=400, 
                    detail=f"File type not supported. Supported types: PDF, DOCX, TXT"
                )
            
            logging.info(f"Processing file: {file.filename}")
            
            # Upload file to blob storage first
            blob_name, blob_url = upload_to_blob(temp_file.name)
            logging.info(f"Processing file: {file.filename} - Blob Upload Done")
            
            # Process the document
            ocr_result = ocr(temp_file.name)
            logging.info(f"Processing file: {file.filename} - OCR Done")
            
            chunks = chunk_text(ocr_result)
            logging.info(f"Processing file: {file.filename} - Chunking Done, {len(chunks)} chunks created")
            
            # Upload chunks with threading for better performance
            def upload_chunk(i, text_chunk):
                logging.info(f"Processing file: {file.filename} - Uploading chunk {i+1}/{len(chunks)}")
                embeddings = embed(text_chunk)
                upload_to_ai_search_studio(i, file.filename, text_chunk, embeddings, blob_url, blob_name)
                logging.info(f"Processing file: {file.filename} - Uploaded chunk {i+1}/{len(chunks)}")
                return i
            
            logging.info(f"Processing file: {file.filename} - Starting Upload")
            
            uploaded_chunks = 0
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(upload_chunk, i, text_chunk) for i, text_chunk in enumerate(chunks)]
                for future in as_completed(futures):
                    try:
                        future.result()
                        uploaded_chunks += 1
                    except Exception as e:
                        logging.error(f"Error uploading chunk: {e}")
                        # Continue processing other chunks
                        pass
            
            logging.info(f"Processing file: {file.filename} - Upload Complete")
            
            return DocumentUploadResponse(
                message=f"Successfully processed and uploaded document: {file.filename}",
                file_name=file.filename,
                chunks_processed=uploaded_chunks,
                status="success"
            )
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logging.error(f"Error processing file {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing file: {str(e)}"
            )
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file.name)
            except OSError:
                pass

@app.get("/documents/supported-types")
async def get_supported_document_types():
    """Get list of supported document types for upload"""
    logging.info('FastAPI supported document types endpoint processed a request.')
    
    supported_types = {
        "supported_extensions": [".pdf", ".docx", ".txt"],
        "supported_mime_types": [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
            "text/plain"
        ],
        "description": "Supported document formats for upload and processing"
    }
    
    return supported_types

@app.post("/documents/init-index")
async def initialize_search_index():
    """Initialize the AI Search index and blob container for document storage"""
    logging.info('FastAPI init search index endpoint processed a request.')
    
    # Environment check
    required_envs = [
        "AI_SEARCH_KEY",
        "AI_SEARCH_ENDPOINT", 
        "AI_SEARCH_INDEX",
        "BLOB_STORAGE_CONNECTION_STRING"
    ]
    missing = [env for env in required_envs if not os.getenv(env)]
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing required environment variables: {', '.join(missing)}"
        )
    
    try:
        init_index()
        init_container()
        return {"message": "AI Search index and blob container initialized successfully", "status": "success"}
    except Exception as e:
        logging.error(f"Error initializing search index: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error initializing search index: {str(e)}"
        )

# Speech Recognition WebSocket Endpoints
@app.websocket("/speech/stream")
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

@app.get("/speech/test")
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

@app.get("/speech/test-ui", response_class=HTMLResponse)
async def speech_test_ui():
    """Serve the speech recognition test HTML page"""
    try:
        with open("speech_test.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Speech test UI not found")

# Single Agent Endpoints
@app.get("/single/chat")
async def single_chat(chat: str = Query(...)):
    """Single agent chat endpoint - GET version"""
    logging.info('FastAPI single chat endpoint processed a request.')
    
    if not chat:
        raise HTTPException(status_code=400, detail="No chat message provided.")

    response = await agent.chat(chat)
    return {"response": response}

@app.get("/single/history")
async def single_history():
    """Get single agent chat history"""
    logging.info('FastAPI single history endpoint processed a request.')

    history = agent.get_history()
    all_messages = []

    for message in history.messages:
        all_messages.append(f"{message.role}: {message.content}")

    if len(all_messages) == 0:
        return {"message": "No chat history available."}

    return {"history": "\n".join(all_messages)}

@app.get("/single/history/export")
async def single_history_export():
    """Export single agent chat history as base64"""
    logging.info('FastAPI single history export endpoint processed a request.')

    history = agent.get_history()
    history_base64 = chat_history_to_base64(history)

    return {"data": history_base64}

@app.post("/single/history/import")
async def single_history_import(request: ImportRequest):
    """Import single agent chat history from base64"""
    logging.info('FastAPI single history import endpoint processed a request.')

    if not request.data:
        raise HTTPException(status_code=400, detail="No base64 data provided.")

    history = chat_history_from_base64(request.data)
    if not history:
        raise HTTPException(status_code=400, detail="Invalid base64 data.")

    agent.set_history(history)

    return {"message": "Successfully updating chat history."}

@app.get("/single/history/export/compress")
async def single_history_export_compress():
    """Export single agent chat history as compressed base64"""
    logging.info('FastAPI single history export compress endpoint processed a request.')

    history = agent.get_history()
    history_base64 = chat_history_compress(history)

    return {"data": history_base64}

@app.post("/single/history/import/compress")
async def single_history_import_decompress(request: ImportRequest):
    """Import single agent chat history from compressed base64"""
    logging.info('FastAPI single history import decompress endpoint processed a request.')

    if not request.data:
        raise HTTPException(status_code=400, detail="No base64 data provided.")

    history = chat_history_decompress(request.data)
    if not history:
        raise HTTPException(status_code=400, detail="Invalid base64 data.")

    agent.set_history(history)

    return {"message": "Successfully updating chat history."}

# Multi Agent Endpoints
@app.post("/multi/chat")
async def multi_chat(request: ChatRequest):
    """Multi agent chat endpoint"""
    logging.info('FastAPI multi chat endpoint processed a request.')

    if not request.chat:
        raise HTTPException(status_code=400, detail="No chat message provided in the request body.")

    try:
        response = multi_agent.chat(request.chat)
        return {"response": response}
    except Exception as e:
        logging.error(f"Error sending message to multi-agent: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending message to multi-agent. {str(e)}")

@app.get("/multi/history")
async def multi_history():
    """Get multi agent chat history"""
    logging.info('FastAPI multi history endpoint processed a request.')

    history = multi_agent.get_history()
    all_messages = [f"{message.role}: {message.content}" for message in history]

    if not all_messages:
        return {"message": "No chat history available."}

    return {"history": "\n".join(all_messages)}

@app.get("/multi/history/export")
async def multi_history_export():
    """Export multi agent chat history as base64"""
    logging.info('FastAPI multi history export endpoint processed a request.')

    history = multi_agent.get_history()
    history_base64 = chat_history_to_base64(history)

    return {"data": history_base64}

@app.post("/multi/history/import")
async def multi_history_import(request: ImportRequest):
    """Import multi agent chat history from base64"""
    logging.info('FastAPI multi history import endpoint processed a request.')

    if not request.data:
        raise HTTPException(status_code=400, detail="No base64 data provided.")

    history = chat_history_from_base64(request.data)
    if not history:
        raise HTTPException(status_code=400, detail="Invalid base64 data.")

    multi_agent.set_history(history)

    return {"message": "Successfully updating chat history."}

@app.get("/multi/history/export/compress")
async def multi_history_export_compress():
    """Export multi agent chat history as compressed base64"""
    logging.info('FastAPI multi history export compress endpoint processed a request.')

    history = multi_agent.get_history()
    history_base64 = chat_history_compress(history)

    return {"data": history_base64}

@app.post("/multi/history/import/compress")
async def multi_history_import_decompress(request: ImportRequest):
    """Import multi agent chat history from compressed base64"""
    logging.info('FastAPI multi history import decompress endpoint processed a request.')

    if not request.data:
        raise HTTPException(status_code=400, detail="No base64 data provided.")

    history = chat_history_decompress(request.data)
    if not history:
        raise HTTPException(status_code=400, detail="Invalid base64 data.")

    multi_agent.set_history(history)

    return {"message": "Successfully updating chat history."}

# Hands-off Agent Endpoints
@app.post("/handsoff/chat")
async def handsoff_chat(request: ChatRequest):
    """Hands-off agent chat endpoint"""
    logging.info('FastAPI handsoff chat endpoint processed a request.')

    if not request.chat:
        raise HTTPException(status_code=400, detail="No chat message provided in the request body.")

    try:
        response = hands_off_agent.chat(request.chat)
        return {"response": response}
    except Exception as e:
        logging.error(f"Error sending message to hands-off agent: {e}")
        
        # Try to restart the agent on certain errors
        if "pydantic_core._pydantic_core.ValidationError" in str(e) or "ValidationError" in str(e):
            try:
                logging.info("Attempting to restart hands-off agent due to validation error...")
                hands_off_agent.restart_agent()
                # Try the request again after restart
                response = hands_off_agent.chat(request.chat)
                return {"response": response}
            except Exception as restart_error:
                logging.error(f"Error even after restarting hands-off agent: {restart_error}")
                return {"response": f"The hands-off agent encountered an error and couldn't recover. Please try again later. Error: {str(restart_error)}"}
        
        raise HTTPException(status_code=500, detail=f"Error sending message to hands-off agent. {str(e)}")

@app.get("/handsoff/history")
async def handsoff_history():
    """Get hands-off agent chat history"""
    logging.info('FastAPI handsoff history endpoint processed a request.')

    history = hands_off_agent.get_history()
    all_messages = [f"{message.role}: {message.content}" for message in history]

    if not all_messages:
        return {"message": "No chat history available."}

    return {"history": "\n".join(all_messages)}

@app.get("/handsoff/history/export")
async def handsoff_history_export():
    """Export hands-off agent chat history as base64"""
    logging.info('FastAPI handsoff history export endpoint processed a request.')

    history = hands_off_agent.get_history()
    history_base64 = chat_history_to_base64(history)

    return {"data": history_base64}

@app.post("/handsoff/history/import")
async def handsoff_history_import(request: ImportRequest):
    """Import hands-off agent chat history from base64"""
    logging.info('FastAPI handsoff history import endpoint processed a request.')

    if not request.data:
        raise HTTPException(status_code=400, detail="No base64 data provided.")

    history = chat_history_from_base64(request.data)
    if not history:
        raise HTTPException(status_code=400, detail="Invalid base64 data.")

    hands_off_agent.set_history(history)

    return {"message": "Successfully updating chat history."}

@app.get("/handsoff/history/export/compress")
async def handsoff_history_export_compress():
    """Export hands-off agent chat history as compressed base64"""
    logging.info('FastAPI handsoff history export compress endpoint processed a request.')

    history = hands_off_agent.get_history()
    history_base64 = chat_history_compress(history)

    return {"data": history_base64}

@app.post("/handsoff/history/import/compress")
async def handsoff_history_import_decompress(request: ImportRequest):
    """Import hands-off agent chat history from compressed base64"""
    logging.info('FastAPI handsoff history import decompress endpoint processed a request.')

    if not request.data:
        raise HTTPException(status_code=400, detail="No base64 data provided.")

    history = chat_history_decompress(request.data)
    if not history:
        raise HTTPException(status_code=400, detail="Invalid base64 data.")

    hands_off_agent.set_history(history)

    return {"message": "Successfully updating chat history."}

@app.get("/handsoff/state/export")
async def handsoff_state_export():
    """Export hands-off agent state as base64"""
    logging.info('FastAPI handsoff state export endpoint processed a request.')

    state = await hands_off_agent.get_state()
    base64 = state_to_base64(state)

    return {"data": base64}

@app.post("/handsoff/state/import")
async def handsoff_state_import(request: ImportRequest):
    """Import hands-off agent state from base64"""
    logging.info('FastAPI handsoff state import endpoint processed a request.')

    if not request.data:
        raise HTTPException(status_code=400, detail="No base64 data provided.")

    state = state_from_base64(request.data)
    if not state:
        raise HTTPException(status_code=400, detail="Invalid base64 data.")

    hands_off_agent.set_state(state)

    return {"message": "Successfully updating agent state."}

@app.get("/handsoff/state/export/compress")
async def handsoff_state_export_compress():
    """Export hands-off agent state as compressed base64"""
    logging.info('FastAPI handsoff state export compress endpoint processed a request.')

    state_str = hands_off_agent.get_state()
    state_dict = json.loads(state_str)
    state_base64 = state_compress(state_dict)

    return {"data": state_base64}

@app.post("/handsoff/state/import/compress")
async def handsoff_state_import_compress(request: ImportRequest):
    """Import hands-off agent state from compressed base64"""
    logging.info('FastAPI handsoff state import compress endpoint processed a request.')

    if not request.data:
        raise HTTPException(status_code=400, detail="No base64 data provided.")

    state_dict = state_decompress(request.data)
    if not state_dict:
        raise HTTPException(status_code=400, detail="Invalid base64 data.")

    state_str = json.dumps(state_dict)
    hands_off_agent.set_state(state_str)

    return {"message": "Successfully updating agent state."}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "FastAPI Semantic Kernel API is running"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to the FastAPI Semantic Kernel API",
        "version": "1.0.0",
        "features": [
            "Single Agent Chat",
            "Multi Agent Chat", 
            "Hands-off Agent Chat",
            "Document Upload & Processing",
            "Real-time Speech Recognition (WebSocket + WebRTC)",
            "Chat History Import/Export",
            "Agent State Management"
        ],
        "speech_test_ui": {
            "websocket": "/speech/test-ui",
            "webrtc": "/speech/test-webrtc-ui"
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
