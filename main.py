
import os
import logging
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing. Check your .env file.")

client = genai.Client(api_key=api_key)

MODEL = "gemini-3.8-flash"

SYSTEM_PROMPT = (
    "You are a friendly, context-aware AI assistant. "
    "Give clear, accurate, beginner-friendly answers. "
    "Use earlier messages in the same conversation when relevant. "
    "If you are unsure about something, say so rather than inventing facts."
)

MAX_HISTORY_MESSAGES = 10

app = FastAPI(
    title="Context-Aware AI Chatbot",
    description="A multi-turn chatbot powered by Google Gemini.",
    version="3.1.0",
)

conversation_histories: dict[str, list[dict[str, str]]] = {}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str


@app.get("/")
def home():
    return {
        "message": "Context-Aware AI Chatbot API is running.",
        "provider": "Google Gemini",
        "model": MODEL,
        "chat_endpoint": "/chat",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    conversation_id = request.conversation_id or str(uuid4())

    if conversation_id not in conversation_histories:
        conversation_histories[conversation_id] = []

    history = conversation_histories[conversation_id]
    history_limit = MAX_HISTORY_MESSAGES - (MAX_HISTORY_MESSAGES % 2)
    recent_history = history[-history_limit:]

    gemini_history = []

    for message in recent_history:
        role = "user" if message["role"] == "user" else "model"

        gemini_history.append(
            types.Content(
                role=role,
                parts=[types.Part(text=message["content"])],
            )
        )

    try:
        chat_session = client.chats.create(
            model=MODEL,
            history=gemini_history,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                automatic_function_calling=(
                    types.AutomaticFunctionCallingConfig(disable=True)
                ),
            ),
        )

        response = chat_session.send_message(message=request.message)
        reply = response.text

        if not reply or not reply.strip():
            raise HTTPException(
                status_code=502,
                detail="Gemini returned an empty response.",
            )

        history.extend([
            {"role": "user", "content": request.message},
            {"role": "assistant", "content": reply},
        ])

        conversation_histories[conversation_id] = history[-history_limit:]

        logger.info("Chat response generated successfully.")

        return ChatResponse(
            reply=reply,
            conversation_id=conversation_id,
        )

    except HTTPException:
        raise

    except errors.APIError as error:
        status_code = getattr(error, "code", 502)
        logger.error("Gemini API error: HTTP %s - %s", status_code, error)

        if status_code == 429:
            raise HTTPException(
                status_code=429,
                detail="Gemini quota or rate limit reached. Check your API usage.",
            ) from error

        if status_code in (401, 403):
            raise HTTPException(
                status_code=502,
                detail="Gemini authentication or access error. Check your API key.",
            ) from error

        if status_code == 408:
            raise HTTPException(
                status_code=504,
                detail="Gemini request timed out. Please retry.",
            ) from error

        raise HTTPException(
            status_code=502,
            detail=f"Gemini API request failed (HTTP {status_code}).",
        ) from error

    except Exception as error:
        logger.exception("Unexpected error while processing chat request.")

        raise HTTPException(
            status_code=500,
            detail="An unexpected server error occurred. Check the backend terminal.",
        ) from error
