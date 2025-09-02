#!/usr/bin/env python3
"""
FastAPI application equivalent to the Azure Functions app in function_app.py
"""
from fastapi import FastAPI
import logging

# Import route modules
from utils.fastapi.routes.core import router as core_router
from utils.fastapi.routes.agents import single_router, multi_router, handsoff_router, foundry_router
from utils.fastapi.routes.documents import router as documents_router
from utils.fastapi.routes.speech import router as speech_router
from utils.fastapi.routes.lights import router as lights_router

# Load env
from dotenv import load_dotenv
load_dotenv()  # take environment variables

from semantic_kernel.utils.logging import setup_logging
setup_logging()
logging.getLogger("kernel").setLevel(logging.DEBUG)

# Initialize FastAPI app
app = FastAPI(
    title="Azure Function Semantic Kernel API",
    description="""
    FastAPI equivalent of the Azure Functions semantic kernel application with comprehensive features:
    
    🤖 **AI Agents**: Single, Multi, and Hands-off agent chat capabilities
    📄 **Document Processing**: Upload and process documents for AI search indexing  
    🗣️ **Speech Recognition**: Real-time speech-to-text via WebSocket
    💡 **Smart Light Control**: Complete REST API for controlling smart lights
    💾 **State Management**: Import/export chat history and agent states
    
    ## Smart Light Control Features
    - List all available lights with current states
    - Search for lights by name
    - Control individual lights (on/off/toggle)
    - Bulk operations (all on/off)
    - System statistics and monitoring
    """,
    version="1.0.0",
    tags_metadata=[
        {
            "name": "Core",
            "description": "Basic application functionality including health checks and configuration.",
        },
        {
            "name": "Lights",
            "description": "Smart light control operations. Manage individual lights or control all lights simultaneously.",
        },
        {
            "name": "Single Agent",
            "description": "Single agent chat interactions and history management.",
        },
        {
            "name": "Multi Agent",
            "description": "Multi-agent system chat interactions and history management.",
        },
        {
            "name": "Hands-off Agent",
            "description": "Autonomous hands-off agent interactions with state management.",
        },
        {
            "name": "Foundry Agent",
            "description": "Azure AI Foundry agent with streaming chat capabilities.",
        },
        {
            "name": "Documents",
            "description": "Document upload, processing, and AI search indexing operations.",
        },
        {
            "name": "Speech",
            "description": "Real-time speech recognition via WebSocket connections.",
        },
    ]
)

# Include all route modules
app.include_router(core_router)
app.include_router(lights_router)
app.include_router(single_router)
app.include_router(multi_router)  
app.include_router(handsoff_router)
app.include_router(foundry_router)
app.include_router(documents_router)
app.include_router(speech_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
