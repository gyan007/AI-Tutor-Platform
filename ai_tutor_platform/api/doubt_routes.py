from fastapi import APIRouter
from pydantic import BaseModel
from ai_tutor_platform.modules.doubt_solver.file_handler import solve_doubt
from ai_tutor_platform.db.pg_client import save_file_doubt

router = APIRouter()

class DoubtRequest(BaseModel):
    user_id: str
    file_name: str
    context: str
    question: str

@router.post("/solve")
def solve_doubt_from_file(request: DoubtRequest):
    result = solve_doubt(request.context, request.question)
    save_file_doubt(request.user_id, request.file_name, request.question, result)
    return {"answer": result}

