from fastapi import APIRouter
from pydantic import BaseModel
from ai_tutor_platform.db.mongo_client import save_user_progress, get_user_progress

router = APIRouter()

class ScoreInput(BaseModel):
    user_id: str
    subject: str
    score: int
    total: int

class UserQuery(BaseModel):
    user_id: str

@router.post("/record")
def save_score(data: ScoreInput):
    save_user_progress(data.user_id, data.subject, data.score, data.total)
    return {"message": "Score recorded successfully."}

@router.post("/progress")
def fetch_progress(query: UserQuery):
    progress = get_user_progress(query.user_id)
    return {"progress": progress}
