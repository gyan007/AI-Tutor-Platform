from fastapi import APIRouter, Depends # Added Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from ai_tutor_platform.modules.quiz.quiz_generator import generate_quiz
from ai_tutor_platform.db.pg_client import save_quiz_response # Changed to pg_client
from ai_tutor_platform.api.auth_routes import get_current_user, User # Import User model and dependency

router = APIRouter()

class QuizRequest(BaseModel):
    topic: str
    num_questions: int = 5

class QuizSubmission(BaseModel):
    # user_id is no longer passed in the request body for the authenticated user
    subject: str
    questions: List[Dict[str, Any]]
    user_answers: List[str]

@router.post("/generate")
# Protect this route
def create_quiz(request: QuizRequest, current_user: User = Depends(get_current_user)):
    # The current_user is available here if needed, but generate_quiz doesn't use user_id
    result = generate_quiz(request.topic, request.num_questions)
    return {"quiz": result}

@router.post("/submit")
# Protect this route
def submit_quiz(submission: QuizSubmission, current_user: User = Depends(get_current_user)):
    correct_count = 0
    detailed_results = []

    for q, user_ans in zip(submission.questions, submission.user_answers):
        is_correct = user_ans.strip().lower() == q["answer"].strip().lower()
        if is_correct:
            correct_count += 1
        detailed_results.append({
            "question": q["question"],
            "correct_answer": q["answer"],
            "user_answer": user_ans,
            "is_correct": is_correct
        })

    # Use current_user.username for saving the quiz response
    save_quiz_response(current_user.username, submission.subject, submission.questions, submission.user_answers)

    return {
        "score": correct_count,
        "total": len(submission.questions),
        "details": detailed_results
    }
