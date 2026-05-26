from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage, MessageRole
from app.models.profile import UserProfile
from app.schemas.chat import ChatRequest, ChatSessionOut
from app.services.gemini_service import chat_with_coach
from app.utils.auth import get_current_user
from app.utils.helpers import from_json_str

router = APIRouter(prefix="/api/chat", tags=["Grooming Coach Chat"])


def _build_history(messages: list[ChatMessage]) -> list[dict]:
    """Convert DB messages to Gemini history format."""
    role_map = {MessageRole.user: "user", MessageRole.assistant: "model"}
    return [{"role": role_map[m.role], "parts": [m.content]} for m in messages]


@router.post("", response_model=dict, status_code=201)
def send_message(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message to the AuraCare Grooming Coach.
    Pass session_id to continue a conversation, or omit to start a new one.
    """
    # Get or create session
    if payload.session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == payload.session_id,
            ChatSession.user_id == current_user.id,
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found.")
    else:
        session = ChatSession(user_id=current_user.id, title=payload.message[:60])
        db.add(session)
        db.commit()
        db.refresh(session)

    # Build conversation history for Gemini
    existing_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    history = _build_history(existing_messages)

    # Get user profile context
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    profile_dict = {}
    if profile:
        profile_dict = {
            "skin_type": profile.skin_type,
            "hair_type": profile.hair_type,
            "skin_concerns": from_json_str(profile.skin_concerns) or [],
            "habit_score": profile.habit_score,
        }

    # Get AI response
    ai_response = chat_with_coach(payload.message, history, profile_dict)

    # Save both messages to DB
    user_msg = ChatMessage(session_id=session.id, role=MessageRole.user, content=payload.message)
    ai_msg = ChatMessage(session_id=session.id, role=MessageRole.assistant, content=ai_response)
    db.add_all([user_msg, ai_msg])

    # Update session title from first message
    if len(existing_messages) == 0:
        session.title = payload.message[:80]

    db.commit()
    db.refresh(user_msg)
    db.refresh(ai_msg)

    return {
        "session_id": session.id,
        "session_title": session.title,
        "user_message": {"id": user_msg.id, "content": user_msg.content, "created_at": user_msg.created_at},
        "ai_response": {"id": ai_msg.id, "content": ai_response, "created_at": ai_msg.created_at},
    }


@router.get("/sessions", response_model=list[dict])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all chat sessions for the current user."""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return [{"id": s.id, "title": s.title, "created_at": s.created_at, "updated_at": s.updated_at} for s in sessions]


@router.get("/sessions/{session_id}", response_model=ChatSessionOut)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a full chat session with all messages."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a chat session and all its messages."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    db.delete(session)
    db.commit()
