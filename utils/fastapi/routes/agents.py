"""
Agent API Routes
================

FastAPI routes for AI agent interactions (Single, Multi, Hands-off, and Foundry agents).
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import logging
import json
import os

# Import agents
from single_agent.agent import AgentSingleton
from multi_agent.agent import MultiAgent
from hands_off_agent.agent import HandsoffAgent
from foundry_agent.agent import FoundryAgent

# Import utilities
from utils.history import chat_history_from_base64, chat_history_to_base64, chat_history_compress, chat_history_decompress
from utils.state import state_compress, state_decompress, state_to_base64, state_from_base64

# Initialize agents
agent = AgentSingleton()
multi_agent = MultiAgent()
hands_off_agent = HandsoffAgent()
foundry_agent = FoundryAgent()
try:
    
    logging.info("Foundry Agent initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize Foundry Agent: {e}")
    foundry_agent = None

# Pydantic models
class ChatRequest(BaseModel):
    chat: str

class ImportRequest(BaseModel):
    data: str

# Single Agent Router
single_router = APIRouter(prefix="/single", tags=["Single Agent"])

@single_router.get("/chat")
async def single_chat(chat: str = Query(...)):
    """Single agent chat endpoint - GET version"""
    logging.info('FastAPI single chat endpoint processed a request.')
    
    if not chat:
        raise HTTPException(status_code=400, detail="No chat message provided.")

    response = await agent.chat(chat)
    return {"response": response}

@single_router.get("/history")
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

@single_router.get("/history/export")
async def single_history_export():
    """Export single agent chat history as base64"""
    logging.info('FastAPI single history export endpoint processed a request.')

    history = agent.get_history()
    history_base64 = chat_history_to_base64(history)

    return {"data": history_base64}

@single_router.post("/history/import")
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

@single_router.get("/history/export/compress")
async def single_history_export_compress():
    """Export single agent chat history as compressed base64"""
    logging.info('FastAPI single history export compress endpoint processed a request.')

    history = agent.get_history()
    history_base64 = chat_history_compress(history)

    return {"data": history_base64}

@single_router.post("/history/import/compress")
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

# Multi Agent Router
multi_router = APIRouter(prefix="/multi", tags=["Multi Agent"])

@multi_router.post("/chat")
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

@multi_router.get("/history")
async def multi_history():
    """Get multi agent chat history"""
    logging.info('FastAPI multi history endpoint processed a request.')

    history = multi_agent.get_history()
    all_messages = [f"{message.role}: {message.content}" for message in history]

    if not all_messages:
        return {"message": "No chat history available."}

    return {"history": "\n".join(all_messages)}

@multi_router.get("/history/export")
async def multi_history_export():
    """Export multi agent chat history as base64"""
    logging.info('FastAPI multi history export endpoint processed a request.')

    history = multi_agent.get_history()
    history_base64 = chat_history_to_base64(history)

    return {"data": history_base64}

@multi_router.post("/history/import")
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

@multi_router.get("/history/export/compress")
async def multi_history_export_compress():
    """Export multi agent chat history as compressed base64"""
    logging.info('FastAPI multi history export compress endpoint processed a request.')

    history = multi_agent.get_history()
    history_base64 = chat_history_compress(history)

    return {"data": history_base64}

@multi_router.post("/history/import/compress")
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

# Hands-off Agent Router
handsoff_router = APIRouter(prefix="/handsoff", tags=["Hands-off Agent"])

@handsoff_router.post("/chat")
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

@handsoff_router.get("/history")
async def handsoff_history():
    """Get hands-off agent chat history"""
    logging.info('FastAPI handsoff history endpoint processed a request.')

    history = hands_off_agent.get_history()
    all_messages = [f"{message.role}: {message.content}" for message in history]

    if not all_messages:
        return {"message": "No chat history available."}

    return {"history": "\n".join(all_messages)}

@handsoff_router.get("/history/export")
async def handsoff_history_export():
    """Export hands-off agent chat history as base64"""
    logging.info('FastAPI handsoff history export endpoint processed a request.')

    history = hands_off_agent.get_history()
    history_base64 = chat_history_to_base64(history)

    return {"data": history_base64}

@handsoff_router.post("/history/import")
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

@handsoff_router.get("/history/export/compress")
async def handsoff_history_export_compress():
    """Export hands-off agent chat history as compressed base64"""
    logging.info('FastAPI handsoff history export compress endpoint processed a request.')

    history = hands_off_agent.get_history()
    history_base64 = chat_history_compress(history)

    return {"data": history_base64}

@handsoff_router.post("/history/import/compress")
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

@handsoff_router.get("/state/export")
async def handsoff_state_export():
    """Export hands-off agent state as base64"""
    logging.info('FastAPI handsoff state export endpoint processed a request.')

    state = await hands_off_agent.get_state()
    base64 = state_to_base64(state)

    return {"data": base64}

@handsoff_router.post("/state/import")
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

@handsoff_router.get("/state/export/compress")
async def handsoff_state_export_compress():
    """Export hands-off agent state as compressed base64"""
    logging.info('FastAPI handsoff state export compress endpoint processed a request.')

    state_str = hands_off_agent.get_state()
    state_dict = json.loads(state_str)
    state_base64 = state_compress(state_dict)

    return {"data": state_base64}

@handsoff_router.post("/state/import/compress")
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

# Foundry Agent Router
foundry_router = APIRouter(prefix="/foundry", tags=["Foundry Agent"])

@foundry_router.post("/chat")
async def foundry_chat(request: ChatRequest):
    """Foundry agent streaming chat endpoint"""
    logging.info('FastAPI foundry chat endpoint processed a request.')

    if not foundry_agent:
        raise HTTPException(status_code=503, detail="Foundry Agent is not available. Check configuration.")

    if not request.chat:
        raise HTTPException(status_code=400, detail="No chat message provided in the request body.")

    import queue
    import threading
    
    def generate_response():
        """Generator function for real-time streaming response"""
        try:
            # Create a queue for real-time chunk streaming
            chunk_queue = queue.Queue()
            
            # Start streaming in a separate thread
            def run_streaming():
                foundry_agent.stream_chat_async(request.chat, chunk_queue)
            
            thread = threading.Thread(target=run_streaming)
            thread.start()
            
            # Stream chunks as they arrive
            while True:
                try:
                    # Get chunk from queue with timeout
                    chunk = chunk_queue.get(timeout=30)  # 30 second timeout
                    
                    if chunk == "[[DONE]]":
                        break
                    elif chunk.startswith("ERROR:"):
                        yield f"data: {json.dumps({'error': chunk[6:]})}\n\n"
                        break
                    else:
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                        
                except queue.Empty:
                    # Timeout - send keepalive
                    yield f"data: {json.dumps({'keepalive': True})}\n\n"
                    continue
                except Exception as e:
                    logging.error(f"Error getting chunk from queue: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    break
            
            # Wait for thread to complete
            thread.join(timeout=5)
            
            # Send completion signal
            yield f"data: {json.dumps({'chunk': '[[DONE]]'})}\n\n"
            
        except Exception as e:
            logging.error(f"Error in foundry chat streaming: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/plain; charset=utf-8"
        }
    )

@foundry_router.get("/new-chat")
async def foundry_new_chat():
    """Start a new chat thread for Foundry agent"""
    logging.info('FastAPI foundry new-chat endpoint processed a request.')

    if not foundry_agent:
        raise HTTPException(status_code=503, detail="Foundry Agent is not available. Check configuration.")

    try:
        foundry_agent.new_chat()
        return {"message": "New chat thread created successfully"}
    except Exception as e:
        logging.error(f"Error creating new foundry chat thread: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating new chat thread: {str(e)}")

@foundry_router.get("/status")
async def foundry_status():
    """Get Foundry agent status"""
    logging.info('FastAPI foundry status endpoint processed a request.')
    
    return {
        "available": foundry_agent is not None,
        "thread_id": foundry_agent.thread.id if foundry_agent else None
    }
