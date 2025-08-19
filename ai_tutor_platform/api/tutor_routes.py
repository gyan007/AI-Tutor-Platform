from fastapi import APIRouter, Depends # Added Depends
from pydantic import BaseModel
from ai_tutor_platform.modules.tutor.chat_tutor import ask_tutor
from ai_tutor_platform.db.pg_client import save_chat # Changed to pg_client
from ai_tutor_platform.api.auth_routes import get_current_user, User # Import User model and dependency

router = APIRouter()

class QuestionRequest(BaseModel):
    # user_id is no longer passed in the request body, but derived from the authenticated user
    question: str

@router.post("/ask")
# Add the dependency: current_user: User = Depends(get_current_user)
def handle_question(request: QuestionRequest, current_user: User = Depends(get_current_user)):
    response = ask_tutor(request.question)
    # Use current_user.username instead of a user_id from the request body
    save_chat(current_user.username, request.question, response)
    return {"response": response}
