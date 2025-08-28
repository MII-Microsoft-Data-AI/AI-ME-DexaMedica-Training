# FastAPI Version

This folder contains a FastAPI equivalent of the Azure Functions app (`function_app.py`).

## Files

- `fastapi_app.py` - Main FastAPI application with all the same endpoints as the Azure Functions version
- `run_fastapi.py` - Startup script to run the FastAPI app with development settings

## Installation

Install the additional FastAPI dependencies:

```bash
pip install fastapi uvicorn pydantic
```

Or install from the updated requirements.txt:

```bash
pip install -r requirements.txt
```

## Running the FastAPI App

### Option 1: Using the startup script
```bash
python run_fastapi.py
```

### Option 2: Using uvicorn directly
```bash
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Running from within Python
```bash
python fastapi_app.py
```

The app will be available at `http://localhost:8000`

## API Documentation

FastAPI automatically generates interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoint Mapping

The FastAPI version maintains the same endpoint structure as the Azure Functions version:

| Azure Functions Route | FastAPI Endpoint | Method | Description |
|----------------------|------------------|--------|-------------|
| `/api/hello` | `/hello` | GET/POST | Hello world endpoint |
| `/api/single/chat` | `/single/chat` | GET | Single agent chat (query param) |
| `/api/single/history` | `/single/history` | GET | Get single agent history |
| `/api/single/history/export` | `/single/history/export` | GET | Export single agent history |
| `/api/single/history/import` | `/single/history/import` | POST | Import single agent history |
| `/api/single/history/export/compress` | `/single/history/export/compress` | GET | Export compressed single agent history |
| `/api/single/history/import/compress` | `/single/history/import/compress` | POST | Import compressed single agent history |
| `/api/multi/chat/start` | `/multi/chat/start` | POST | Start multi-agent chat |
| `/api/multi/chat` | `/multi/chat` | POST | Send message to multi-agent |
| `/api/multi/history` | `/multi/history` | GET | Get multi-agent history |
| `/api/multi/history/export` | `/multi/history/export` | GET | Export multi-agent history |
| `/api/multi/history/import` | `/multi/history/import` | POST | Import multi-agent history |
| `/api/multi/history/export/compress` | `/multi/history/export/compress` | GET | Export compressed multi-agent history |
| `/api/multi/history/import/compress` | `/multi/history/import/compress` | POST | Import compressed multi-agent history |

## Key Differences from Azure Functions

1. **Request Handling**: FastAPI uses Pydantic models for request body validation instead of manual JSON parsing
2. **Error Handling**: Uses FastAPI's `HTTPException` instead of returning error responses
3. **Response Format**: Some endpoints return JSON objects instead of plain text for better structure
4. **Documentation**: Automatic OpenAPI/Swagger documentation generation
5. **Development**: Built-in reload functionality for development
6. **Validation**: Automatic request/response validation with detailed error messages

## Testing

You can test the endpoints using curl, just like with the Azure Functions version:

```bash
# Hello endpoint
curl http://localhost:8000/hello?name=World

# Single agent chat
curl "http://localhost:8000/single/chat?chat=Hello"

# Multi-agent start
curl -X POST -H "Content-Type: application/json" -d '{"chat":"What can you do?"}' http://localhost:8000/multi/chat/start

# Multi-agent chat
curl -X POST -H "Content-Type: application/json" -d '{"chat":"Tell me a joke"}' http://localhost:8000/multi/chat
```
