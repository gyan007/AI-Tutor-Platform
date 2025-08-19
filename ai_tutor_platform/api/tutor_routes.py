from fastapi import APIRouter, Depends # Added Depends
from pydantic import BaseModel
from ai_tutor_platform.modules.tutor.chat_tutor import ask_tutor
from ai_tutor_platform.api.auth_routes import get_current_user, User # Import User model and dependency
from ai_tutor_platform.db.pg_client import save_chat, get_chat_history

router = APIRouter()

class QuestionRequest(BaseModel): 
    question: str

@router.post("/ask")
def handle_question(request: QuestionRequest, current_user: User = Depends(get_current_user)):
    response = ask_tutor(request.question)
    save_chat(current_user.username, request.question, response)
    return {"response": response}

@router.get("/history")  
def get_chat_history_for_user(current_user: User = Depends(get_current_user)):
    history = get_chat_history(current_user.username)
    formatted_history = []
    for role, message in history:
        formatted_history.append({"role": role, "message": message})
    return {"history": formatted_history}

