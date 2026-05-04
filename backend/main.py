from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
import os
from dotenv import load_dotenv

from agent import HRAssistant

load_dotenv()

app  = FastAPI(
  title="AI HR Assistant API",
  description="LangChain-powered HR assistant with RAG + SQL tools",
  version="1.0.0"
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:5174", "http://localhost:3000"],
  allow_credentials= True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# ── Session store ─────────────────────────────────────────────────────────────
# Each session_id maps to one HRAssistant instance with its own memory.
sessions : dict[str, HRAssistant] ={}

# ── Request / Response models ─────────────────────────────────────────────────
class ChatRequest(BaseModel):
  message: str
  session_id: Optional[str] = None   # if None, we create a new session
  employee_id: Optional[int] = None  

class ChatResponse(BaseModel):
    response: str
    session_id: str  

class SessionResponse(BaseModel):
    message: str
    session_id: str

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    """Quick check that the API is alive — React polls this on startup."""
    return {"status" : "ok" , "active_sessions": len(sessions)}

@app.post("/chat", response_model= ChatResponse)
def chat(request: ChatRequest):
    """
    Main endpoint. Accepts a message, returns the agent's response.
    Creates a new session if session_id is not provided.
    """
    session_id = request.session_id or str(uuid.uuid4())

    if(session_id not in sessions):
        sessions[session_id] = HRAssistant()
    
    assistant = sessions[session_id]

    # Prepend employee context if this is the first message
    message=request.message
    if request.employee_id and len(assistant.chat_history)==0:
        message= f"[Employee ID: {request.employee_id}] {message}"
    try:
        response = assistant.chat(message)
        return ChatResponse(response=response, session_id=session_id)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )
    
@app.post("/reset-session", response_model=SessionResponse)
def reset_session(session_id: str):
    """
    Clears conversation history for a session.
    Called when user clicks 'New Conversation' in the frontend.
    """
    if session_id in sessions:
         del sessions[session_id]

    new_session_id= str(uuid.uuid4())
    sessions[new_session_id] = HRAssistant()

    return SessionResponse(
        message="Session reset successfully",
        session_id=new_session_id
    )

@app.get("/session/{session_id}/history")
def get_history(session_id: str):
    """
    Returns the conversation history for a session.
    Useful for the frontend to restore chat on page refresh.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    assistant =sessions[session_id]
    history =[]

    for msg in assistant.chat_history:
        history.append({
            "role" : "user" if msg.__class__.__name__ == "HumanMessage" else "assistant",
            "content": msg.content
        })

    return {"session_id": session_id, "history": history}