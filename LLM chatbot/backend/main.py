import os
from typing import Literal

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models import Conversation, Message
from datetime import datetime


# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")


# Initialize Gemini
client = genai.Client(api_key=api_key)


# Initialize FastAPI
app = FastAPI(title="Gemini AI Chat")


# Allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# -------------------------
# Pydantic request/response models
# -------------------------

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: int


class SavedMessage(BaseModel):
    role: Literal["user", "assistant"]
    text: str


class ConversationHistory(BaseModel):
    conversation_id: int
    messages: list[SavedMessage]

class ConversationSummary(BaseModel):
    id: int
    title: str
    created_at: datetime


# -------------------------
# Chat endpoint
# -------------------------

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    # Step 1: Find an existing conversation or create one.
    try:
        if request.conversation_id is None:
            conversation = Conversation(
                title=request.message[:60]
            )

            db.add(conversation)
            db.flush()

        else:
            conversation = (
                db.query(Conversation)
                .filter(
                    Conversation.id == request.conversation_id
                )
                .first()
            )

            if conversation is None:
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found.",
                )

        conversation_id = conversation.id

        # Step 2: Load the latest 20 saved messages.
        previous_messages = (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation_id
            )
            .order_by(Message.id.desc())
            .limit(20)
            .all()
        )

        # Restore chronological order.
        previous_messages.reverse()

        # Step 3: Save the user's new message.
        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
        )

        db.add(user_message)
        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        print(f"Database error: {type(e).__name__}: {e}")

        raise HTTPException(
            status_code=500,
            detail="Could not save or load the conversation.",
        )

    # Step 4: Build Gemini's conversation context.
    contents = []

    for item in previous_messages:
        role = "user" if item.role == "user" else "model"

        contents.append(
            {
                "role": role,
                "parts": [{"text": item.content}],
            }
        )

    # Include the current message exactly once.
    contents.append(
        {
            "role": "user",
            "parts": [{"text": request.message}],
        }
    )

    # Step 5: Generate the AI response.
    try:
        response = await client.aio.models.generate_content(
            model="gemini-3.6-flash",
            contents=contents,
        )

        if not response.text:
            raise HTTPException(
                status_code=502,
                detail="The AI returned no text response.",
            )

    except HTTPException:
        raise

    except Exception as e:
        print(f"Gemini API error: {type(e).__name__}: {e}")

        raise HTTPException(
            status_code=502,
            detail="Gemini could not complete the request.",
        )

    # Step 6: Save Gemini's response in PostgreSQL.
    try:
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=response.text,
        )

        db.add(assistant_message)
        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Database error: {type(e).__name__}: {e}")

        raise HTTPException(
            status_code=500,
            detail="The AI replied, but the response could not be saved.",
        )

    # Step 7: Return the reply and conversation ID.
    return ChatResponse(
        reply=response.text,
        conversation_id=conversation_id,
    )


# -------------------------
# Retrieve conversation history
# -------------------------

@app.get(
    "/conversations/{conversation_id}",
    response_model=ConversationHistory,
)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
):
    # Step 1: Find the conversation.
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id
        )
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    # Step 2: Retrieve its messages in chronological order.
    messages = (
        db.query(Message)
        .filter(
            Message.conversation_id == conversation_id
        )
        .order_by(Message.id.asc())
        .all()
    )

    # Step 3: Return the history in a frontend-friendly format.
    return ConversationHistory(
        conversation_id=conversation.id,
        messages=[
            SavedMessage(
                role=message.role,
                text=message.content,
            )
            for message in messages
        ],
    )
@app.get(
    "/conversations",
    response_model=list[ConversationSummary],
)
def list_conversations(
    db: Session = Depends(get_db),
):
    conversations = (
        db.query(Conversation)
        .order_by(Conversation.id.desc())
        .all()
    )

    return conversations


# -------------------------
# Database write test endpoint
# -------------------------

@app.post("/test-db-write")
def test_db_write(
    db: Session = Depends(get_db),
):
    conversation = Conversation(
        title="Database connection test"
    )

    db.add(conversation)
    db.flush()

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content="My favourite programming language is Python.",
    )

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content="I'll use Python as the example language.",
    )

    db.add_all([user_message, assistant_message])
    db.commit()
    db.refresh(conversation)

    return {
        "message": "Conversation and messages saved successfully",
        "conversation_id": conversation.id,
        "saved_messages": 2,
    }