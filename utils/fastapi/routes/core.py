"""
Core API Routes
===============

FastAPI routes for basic application functionality (hello, config, health, root).
"""

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import logging
import os

# Initialize router
router = APIRouter(tags=["Core"])

# Pydantic models
class HelloRequest(BaseModel):
    name: Optional[str] = None

@router.get("/")
async def root():
    """Root endpoint - serve the chatbot HTML file"""
    try:
        with open("utils/fastapi/chatbot_app.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
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
                "Agent State Management",
                "Smart Light Control API"
            ],
            "light_api": {
                "description": "Complete REST API for smart light control",
                "endpoints": {
                    "list_lights": "GET /lights - Get all lights",
                    "search_light": "GET /lights/search/{name} - Find light by name",
                    "get_light": "GET /lights/{id} - Get light details",
                    "update_light": "PUT /lights/{id}/state - Control light on/off",
                    "toggle_light": "POST /lights/{id}/toggle - Toggle light state",
                    "all_on": "POST /lights/all/on - Turn all lights on",
                    "all_off": "POST /lights/all/off - Turn all lights off",
                    "statistics": "GET /lights/stats - Get system statistics"
                }
            },
            "speech_test_ui": {
                "websocket": "/speech/test-ui",
                "webrtc": "/speech/test-webrtc-ui"
            },
            "docs": "/docs",
            "redoc": "/redoc"
        }

@router.get("/hello")
async def hello(name: Optional[str] = Query(None)):
    """Hello endpoint - equivalent to Azure Function hello route"""
    logging.info('FastAPI hello endpoint processed a request.')
    
    if name:
        return {"message": f"Hello, {name}. This HTTP triggered function executed successfully."}
    else:
        return {
            "message": "This HTTP triggered function executed successfully. Pass a name in the query string for a personalized response."
        }

@router.post("/hello")
async def hello_post(request: HelloRequest):
    """Hello endpoint - POST version"""
    logging.info('FastAPI hello POST endpoint processed a request.')
    
    if request.name:
        return {"message": f"Hello, {request.name}. This HTTP triggered function executed successfully."}
    else:
        return {
            "message": "This HTTP triggered function executed successfully. Pass a name in the request body for a personalized response."
        }

@router.get("/config/partner-name")
async def get_partner_name():
    """Get partner name from environment variable for footer display"""
    partner_name = os.getenv("PARTNER_NAME")
    return {"partnerName": partner_name}

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "FastAPI Semantic Kernel API is running"}
