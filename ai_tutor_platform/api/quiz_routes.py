from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from ai_tutor_platform.modules.quiz.quiz_generator import generate_quiz
from ai_tutor_platform.db.mongo_client import save_quiz_response


router = APIRouter()

class QuizRequest(BaseModel):
    topic: str
    num_questions: int = 5

class QuizSubmission(BaseModel):
    user_id: str
    subject: str
    questions: List[Dict[str, Any]]
    user_answers: List[str]

@router.post("/generate")
def create_quiz(request: QuizRequest):
    result = generate_quiz(request.topic, request.num_questions)
    return {"quiz": result}

@router.post("/submit")
def submit_quiz(submission: QuizSubmission):
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

    save_quiz_response(submission.user_id, submission.subject, submission.questions, submission.user_answers)

    return {
        "score": correct_count,
        "total": len(submission.questions),
        "details": detailed_results
    }
