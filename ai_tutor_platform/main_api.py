from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from ai_tutor_platform.api import (
    tutor_routes,
    quiz_routes,
    doubt_routes,
    tracker_routes,
    auth_routes # <-- ADD THIS IMPORT
)
from ai_tutor_platform.api.auth_routes import get_current_user, User # <-- Import user for dependency

# Assuming setup_db_schema is defined in pg_client.py and imported.
# It's better to run initial schema creation manually in production.
# from ai_tutor_platform.db.pg_client import setup_db_schema

app = FastAPI(
    title="AI Tutoring Platform",
    description="A FastAPI-powered tutoring platform using LangChain and Groq API.",
    version="1.0.0"
)

# Optional: Redirect root to Streamlit UI
@app.get("/", include_in_schema=False)
def redirect_to_ui():
    return RedirectResponse(url="http://localhost:8501")

# Include Authentication Routes (no authentication needed for these)
app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])

# Include Protected API Routes
# Add `dependencies=[Depends(get_current_user)]` to protect these routes
# The user object returned by get_current_user will be passed to the route handlers if needed
app.include_router(tutor_routes.router, prefix="/tutor", tags=["Tutor"], dependencies=[Depends(get_current_user)])
app.include_router(quiz_routes.router, prefix="/quiz", tags=["Quiz"], dependencies=[Depends(get_current_user)])
app.include_router(doubt_routes.router, prefix="/doubt", tags=["Doubt Solver"], dependencies=[Depends(get_current_user)])
app.include_router(tracker_routes.router, prefix="/tracker", tags=["Progress Tracker"], dependencies=[Depends(get_current_user)])
