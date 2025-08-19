from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any 
from ai_tutor_platform.db.pg_client import save_quiz_response, save_user_progress  
from ai_tutor_platform.api.auth_routes import get_current_user, User
from ai_tutor_platform.modules.quiz.quiz_generator import generate_quiz

router = APIRouter()

class QuizRequest(BaseModel):
    topic: str
    num_questions: int = 5

class QuizSubmission(BaseModel):
    subject: str
    questions: List[Dict[str, Any]]
    user_answers: List[str]

@router.post("/generate") 
def create_quiz(request: QuizRequest, current_user: User = Depends(get_current_user)):
    result = generate_quiz(request.topic, request.num_questions)
    return {"quiz": result}

@router.post("/submit") 
def submit_quiz(submission: QuizSubmission, current_user: User = Depends(get_current_user)):
    correct_count = 0
    detailed_results = []
    total_questions = len(submission.questions)  

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
 
    save_quiz_response(current_user.username, submission.subject, submission.questions, submission.user_answers)
 
    save_user_progress(
        user_id=current_user.username,  
        subject=submission.subject,
        score=correct_count,
        total=total_questions
    )

    return {
        "score": correct_count,
        "total": total_questions,
        "details": detailed_results
    }

