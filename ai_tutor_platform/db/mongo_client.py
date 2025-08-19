from pymongo import MongoClient
from datetime import datetime

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["ai_tutor_platform_db"]

# ------------ Tab 1: Chat History ------------
def save_chat(user_id: str, question: str, answer: str):
    db.chat_history.insert_one({
        "user_id": user_id,
        "question": question,
        "answer": answer,
        "timestamp": datetime.utcnow()
    })

# ------------ Tab 2: File-based Doubt ------------
def save_file_doubt(user_id: str, filename: str, question: str, answer: str):
    db.file_doubts.insert_one({
        "user_id": user_id,
        "filename": filename,
        "question": question,
        "answer": answer,
        "timestamp": datetime.utcnow()
    })

# ------------ Tab 3: Quiz Answers ------------
def save_quiz_response(user_id: str, subject: str, quiz: list, user_answers: list):
    for i, q in enumerate(quiz):
        db.quiz_attempts.insert_one({
            "user_id": user_id,
            "subject": subject,
            "question": q["question"],
            "options": q["options"],
            "correct_answer": q["answer"],
            "user_answer": user_answers[i],
            "is_correct": q["answer"].strip().lower() == user_answers[i].strip().lower(),
            "timestamp": datetime.utcnow()
        })

# ------------ Tab 4: User Progress ------------
def save_user_progress(user_id: str, subject: str, score: int, total: int):
    db.user_progress.insert_one({
        "user_id": user_id,
        "subject": subject,
        "score": score,
        "total": total,
        "accuracy": round(score / total * 100, 2),
        "timestamp": datetime.utcnow()
    })

def get_user_progress(user_id: str):
    return list(db.user_progress.find({"user_id": user_id}))

