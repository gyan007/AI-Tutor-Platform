from fastapi import APIRouter, Depends # Added Depends
from pydantic import BaseModel
from ai_tutor_platform.modules.doubt_solver.file_handler import solve_doubt
from ai_tutor_platform.db.pg_client import save_file_doubt # Changed to pg_client
from ai_tutor_platform.api.auth_routes import get_current_user, User # Import User model and dependency

router = APIRouter()

class DoubtRequest(BaseModel):
    # user_id is no longer passed in the request body
    file_name: str
    context: str
    question: str

@router.post("/solve")
# Protect this route
def solve_doubt_from_file(request: DoubtRequest, current_user: User = Depends(get_current_user)):
    result = solve_doubt(request.context, request.question)
    # Use current_user.username for saving the file doubt
    save_file_doubt(current_user.username, request.file_name, request.question, result)
    return {"answer": result}
