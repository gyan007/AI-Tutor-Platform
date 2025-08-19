from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from ai_tutor_platform.api import (
    tutor_routes,
    quiz_routes,
    doubt_routes,
    tracker_routes
)
# Update this import from mongo_client to pg_client
# from ai_tutor_platform.db.pg_client import setup_db_schema # <-- ADDED if you want to run schema setup from API

app = FastAPI(
    title="AI Tutoring Platform",
    description="A FastAPI-powered tutoring platform using LangChain and Google Gemini.",
    version="1.0.0"
)

# Optional: Run schema setup once at API startup (e.g., in a development environment)
# In production on Render, you'd usually create the database and run these scripts once manually.
# @app.on_event("startup")
# async def startup_event():
#     try:
#         setup_db_schema()
#     except Exception as e:
#         print(f"Failed to set up database schema on API startup: {e}")

# Optional: Redirect root to Streamlit UI
@app.get("/", include_in_schema=False)
def redirect_to_ui():
    return RedirectResponse(url="http://localhost:8501")

# Include API routes
app.include_router(tutor_routes.router, prefix="/tutor", tags=["Tutor"])
app.include_router(quiz_routes.router, prefix="/quiz", tags=["Quiz"])
app.include_router(doubt_routes.router, prefix="/doubt", tags=["Doubt Solver"])
app.include_router(tracker_routes.router, prefix="/tracker", tags=["Progress Tracker"])
