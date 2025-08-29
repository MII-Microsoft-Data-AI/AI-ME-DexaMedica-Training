#!/usr/bin/env python3
"""
FastAPI application equivalent to the Azure Functions app in function_app.py
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import logging
import json
from typing import Optional

# Import all the same dependencies as the Azure Functions app
from single_agent.agent import AgentSingleton
from multi_agent.agent import MultiAgent
from hands_off_agent.agent import HandsoffAgent

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
    description="FastAPI equivalent of the Azure Functions semantic kernel application",
    version="1.0.0"
)

# Initialize agents (same as in function_app.py)
agent = AgentSingleton()
multi_agent = MultiAgent()
hands_off_agent = HandsoffAgent()

# Pydantic models for request bodies
class ChatRequest(BaseModel):
    chat: str

class HelloRequest(BaseModel):
    name: Optional[str] = None

class ImportRequest(BaseModel):
    data: str

# Hello endpoint
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
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
