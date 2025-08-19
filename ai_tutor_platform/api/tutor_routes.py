from fastapi import APIRouter
from pydantic import BaseModel
from ai_tutor_platform.modules.tutor.chat_tutor import ask_tutor
from ai_tutor_platform.db.mongo_client import save_chat

router = APIRouter()

class QuestionRequest(BaseModel):
    user_id: str
    question: str

@router.post("/ask")
def handle_question(request: QuestionRequest):
    response = ask_tutor(request.question)
    save_chat(request.user_id, request.question, response)
    return {"response": response}
