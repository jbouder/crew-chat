"""FastAPI application for the crew chat backend."""

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents import process_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Crew Chat API",
    description="An agentic chatbot API powered by CrewAI and AWS Bedrock",
    version="1.0.0",
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Request model for chat messages."""

    message: str


class ChatResponse(BaseModel):
    """Response model for chat messages."""

    response: str


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {"status": "healthy", "message": "Crew Chat API is running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message through the CrewAI agent."""
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        response = await process_message(request.message)
        return ChatResponse(response=response)
    except ValueError as e:
        logger.warning("Invalid input: %s", e)
        raise HTTPException(status_code=400, detail="Invalid message format")
    except ConnectionError as e:
        logger.error("Connection error to LLM service: %s", e)
        raise HTTPException(
            status_code=503, detail="Service temporarily unavailable. Please try again."
        )
    except Exception as e:
        logger.exception("Unexpected error processing message")
        raise HTTPException(
            status_code=500, detail="An error occurred processing your message."
        )


if __name__ == "__main__":
    import uvicorn

    from config import settings

    uvicorn.run(app, host=settings.host, port=settings.port)
