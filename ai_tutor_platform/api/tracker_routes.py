from fastapi import APIRouter, Depends # Added Depends
from pydantic import BaseModel
from ai_tutor_platform.db.pg_client import save_user_progress, get_user_progress # Changed to pg_client
from ai_tutor_platform.api.auth_routes import get_current_user, User # Import User model and dependency

router = APIRouter()

class ScoreInput(BaseModel):
    # user_id is no longer passed in the request body
    subject: str
    score: int
    total: int

# No need for UserQuery if user_id is always from authenticated user
# class UserQuery(BaseModel):
#     user_id: str

@router.post("/record")
# Protect this route
def save_score(data: ScoreInput, current_user: User = Depends(get_current_user)):
    # Use current_user.username for saving user progress
    save_user_progress(current_user.username, data.subject, data.score, data.total)
    return {"message": "Score recorded successfully."}

@router.post("/progress")
# Protect this route
# No request body needed, user_id comes from authentication
def fetch_progress(current_user: User = Depends(get_current_user)):
    # Use current_user.username for fetching progress
    progress = get_user_progress(current_user.username)
    return {"progress": progress}
