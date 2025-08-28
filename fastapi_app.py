from fastapi import FastAPI, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import logging
import json
from typing import Optional

from single_agent.agent import AgentSingleton
from multi_agent.agent import MultiAgent

from utils.history import chat_history_from_base64, chat_history_to_base64, chat_history_compress, chat_history_decompress
from utils.state import state_compress, state_decompress, state_to_base64, state_from_base64

# Load env
from dotenv import load_dotenv
load_dotenv()  # take environment variables

from semantic_kernel.utils.logging import setup_logging
setup_logging()
logging.getLogger("kernel").setLevel(logging.DEBUG)

# Pydantic models for request bodies
class ChatRequest(BaseModel):
    chat: str

class HistoryImportRequest(BaseModel):
    data: str

class StateImportRequest(BaseModel):
    data: str

# Initialize FastAPI app
app = FastAPI(
    title="Semantic Kernel Multi-Agent API",
    description="FastAPI equivalent of Azure Functions app with single and multi-agent chat capabilities",
    version="1.0.0"
)

# Initialize agents
agent = AgentSingleton()
multi_agent = MultiAgent()

@app.get("/hello")
async def hello(name: Optional[str] = None):
    """Hello endpoint that accepts name as query parameter"""
    if name:
        return {"message": f"Hello, {name}. This HTTP triggered function executed successfully."}
    else:
        return {
            "message": "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response."
        }

@app.post("/hello")
async def hello_post(name: Optional[str] = None):
    """Hello endpoint that accepts name in request body"""
    if name:
        return {"message": f"Hello, {name}. This HTTP triggered function executed successfully."}
    else:
        return {
            "message": "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response."
        }

# Single Agent Endpoints
@app.get("/single/chat", response_class=PlainTextResponse)
async def single_chat(chat: str):
    """Single agent chat endpoint with query parameter"""
    logging.info('FastAPI single chat function processed a request.')
    
    if not chat:
        raise HTTPException(status_code=400, detail="No chat message provided.")
    
    response = await agent.chat(chat)
    return response

@app.get("/single/history", response_class=PlainTextResponse)
async def single_history():
    """Get single agent chat history"""
    logging.info('FastAPI single history function processed a request.')
    
    history = agent.get_history()
    all_messages = []
    
    for message in history.messages:
        all_messages.append(f"{message.role}: {message.content}")
    
    if len(all_messages) == 0:
        return "No chat history available."
    
    return "\n".join(all_messages)

@app.get("/single/history/export", response_class=PlainTextResponse)
async def single_history_export():
    """Export single agent chat history as base64"""
    logging.info('FastAPI single history export function processed a request.')
    
    history = agent.get_history()
    history_base64 = chat_history_to_base64(history)
    
    return history_base64

@app.post("/single/history/import", response_class=PlainTextResponse)
async def single_history_import(request: HistoryImportRequest):
    """Import single agent chat history from base64"""
    logging.info('FastAPI single history import function processed a request.')
    
    if not request.data:
        raise HTTPException(status_code=400, detail="No base64 data provided.")
    
    history = chat_history_from_base64(request.data)
    if not history:
        raise HTTPException(status_code=400, detail="Invalid base64 data.")
    
    agent.set_history(history)
    
    return "Successfully updating chat history."

@app.get("/single/history/export/compress", response_class=PlainTextResponse)
async def single_history_export_compress():
    """Export single agent chat history as compressed base64"""
    logging.info('FastAPI single history export compress function processed a request.')
    
    history = agent.get_history()
    history_base64 = chat_history_compress(history)
    
    return history_base64

@app.post("/single/history/import/compress", response_class=PlainTextResponse)
async def single_history_import_decompress(request: HistoryImportRequest):
    """Import single agent chat history from compressed base64"""
    logging.info('FastAPI single history import decompress function processed a request.')
    
    if not request.data:
        raise HTTPException(status_code=400, detail="No base64 data provided.")
    
    history = chat_history_decompress(request.data)
    if not history:
        raise HTTPException(status_code=400, detail="Invalid base64 data.")
    
    agent.set_history(history)
    
    return "Successfully updating chat history."

# Multi Agent Endpoints
@app.post("/multi/chat", response_class=PlainTextResponse)
async def multi_chat(request: ChatRequest):
    """Send message to multi-agent"""
    logging.info('FastAPI multi_chat function processed a request.')
    
    if not request.chat:
        raise HTTPException(status_code=400, detail="No chat message provided in the request body.")
    
    try:
        return multi_agent.chat(request.chat)
    except Exception as e:
        logging.error(f"Error sending message to multi-agent: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending message to multi-agent. {str(e)}")

@app.get("/multi/history", response_class=PlainTextResponse)
async def multi_history():
    """Get multi-agent chat history"""
    logging.info('FastAPI multi_history function processed a request.')
    
    history = multi_agent.get_history()
    all_messages = [f"{message.role}: {message.content}" for message in history]
    
    if not all_messages:
        return "No chat history available."
    
    return "\n".join(all_messages)

@app.get("/multi/history/export", response_class=PlainTextResponse)
async def multi_history_export():
    """Export multi-agent chat history as base64"""
    logging.info('FastAPI multi_history_export function processed a request.')
    
    history = multi_agent.get_history()
    history_base64 = chat_history_to_base64(history)
    
    return history_base64

@app.post("/multi/history/import", response_class=PlainTextResponse)
async def multi_history_import(request: HistoryImportRequest):
    """Import multi-agent chat history from base64"""
    logging.info('FastAPI multi_history_import function processed a request.')
    
    if not request.data:
        raise HTTPException(status_code=400, detail="No base64 data provided.")
    
    history = chat_history_from_base64(request.data)
    if not history:
        raise HTTPException(status_code=400, detail="Invalid base64 data.")
    
    multi_agent.set_history(history)
    
    return "Successfully updating chat history."

@app.get("/multi/history/export/compress", response_class=PlainTextResponse)
async def multi_history_export_compress():
    """Export multi-agent chat history as compressed base64"""
    logging.info('FastAPI multi_history_export_compress function processed a request.')
    
    history = multi_agent.get_history()
    history_base64 = chat_history_compress(history)
    
    return history_base64

@app.post("/multi/history/import/compress", response_class=PlainTextResponse)
async def multi_history_import_decompress(request: HistoryImportRequest):
    """Import multi-agent chat history from compressed base64"""
    logging.info('FastAPI multi_history_import_decompress function processed a request.')
    
    if not request.data:
        raise HTTPException(status_code=400, detail="No base64 data provided.")
    
    history = chat_history_decompress(request.data)
    if not history:
        raise HTTPException(status_code=400, detail="Invalid base64 data.")
    
    multi_agent.set_history(history)
    
    return "Successfully updating chat history."

# Commented out state management endpoints (same as in original)
# @app.get("/multi/state/export", response_class=PlainTextResponse)
# async def multi_state_export():
#     """Export multi-agent state as base64"""
#     logging.info('FastAPI multi_state_export function processed a request.')
    
#     state = await multi_agent.get_state()
#     base64 = state_to_base64(state)
    
#     return base64

# @app.post("/multi/state/import", response_class=PlainTextResponse)
# async def multi_state_import(request: StateImportRequest):
#     """Import multi-agent state from base64"""
#     logging.info('FastAPI multi_state_import function processed a request.')
    
#     if not request.data:
#         raise HTTPException(status_code=400, detail="No base64 data provided.")
    
#     state = state_from_base64(request.data)
#     if not state:
#         raise HTTPException(status_code=400, detail="Invalid base64 data.")
    
#     multi_agent.set_state(state)
    
#     return "Successfully updating agent state."

# @app.get("/multi/state/export/compress", response_class=PlainTextResponse)
# async def multi_state_export_compress():
#     """Export multi-agent state as compressed base64"""
#     logging.info('FastAPI multi_state_export_compress function processed a request.')
    
#     state_str = multi_agent.get_state()
#     state_dict = json.loads(state_str)
#     state_base64 = state_compress(state_dict)
    
#     return state_base64

# @app.post("/multi/state/import/compress", response_class=PlainTextResponse)
# async def multi_state_import_compress(request: StateImportRequest):
#     """Import multi-agent state from compressed base64"""
#     logging.info('FastAPI multi_state_import_compress function processed a request.')
    
#     if not request.data:
#         raise HTTPException(status_code=400, detail="No base64 data provided.")
    
#     state_dict = state_decompress(request.data)
#     if not state_dict:
#         raise HTTPException(status_code=400, detail="Invalid base64 data.")
    
#     state_str = json.dumps(state_dict)
#     multi_agent.set_state(state_str)
    
#     return "Successfully updating agent state."

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
