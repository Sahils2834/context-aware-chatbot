
import os
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import (
    OpenAI,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
)
from pydantic import BaseModel, Field

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError(
        "OPENAI_API_KEY is missing. Check your .env file."
    )

client = OpenAI(
    api_key=api_key,
    timeout=60.0,
    max_retries=2,
)

app = FastAPI(
    title="Context-Aware AI Chatbot",
    description="A multi-turn chatbot powered by OpenAI.",
    version="2.0.0",
)

MODEL = "gpt-4.1-mini"

SYSTEM_PROMPT = (
    "You are a friendly, context-aware AI assistant. "
    "Give clear, accurate, beginner-friendly answers. "
    "Remember details from earlier messages in the same conversation. "
    "If you are unsure about something, say so rather than inventing facts."
)

conversation_histories = {}

MAX_HISTORY_MESSAGES = 10


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    conversation_id = request.conversation_id or str(uuid4())

    if conversation_id not in conversation_histories:
        conversation_histories[conversation_id] = []

    history = conversation_histories[conversation_id]

    messages = history[-MAX_HISTORY_MESSAGES:] + [
        {"role": "user", "content": request.message}
    ]

    try:
        response = client.responses.create(
            model=MODEL,
            instructions=SYSTEM_PROMPT,
            input=messages,
        )

        reply = response.output_text

        if not reply or not reply.strip():
            raise HTTPException(
                status_code=502,
                detail="The AI model returned an empty response.",
            )

        history.extend([
            {"role": "user", "content": request.message},
            {"role": "assistant", "content": reply},
        ])

        conversation_histories[conversation_id] = (
            history[-MAX_HISTORY_MESSAGES:]
        )

        return ChatResponse(
            reply=reply,
            conversation_id=conversation_id,
        )

    except RateLimitError as error:
        raise HTTPException(
            status_code=429,
            detail=(
                "OpenAI rate limit or quota reached. "
                "Check your API billing, credits, and usage limits."
            ),
        ) from error

    except APITimeoutError as error:
        raise HTTPException(
            status_code=504,
            detail="The OpenAI request timed out. Please try again.",
        ) from error

    except APIConnectionError as error:
        raise HTTPException(
            status_code=503,
            detail="Could not connect to OpenAI. Check your connection.",
        ) from error

    except APIStatusError as error:
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI returned an API error (HTTP {error.status_code}).",
        ) from error

    except HTTPException:
        raise
