from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from ai_tutor_platform.api import (
    tutor_routes,
    quiz_routes,
    doubt_routes,
    tracker_routes
)

app = FastAPI(
    title="AI Tutoring Platform",
    # Update the description to reflect the use of Gemini
    description="A FastAPI-powered tutoring platform using LangChain and Google Gemini.",
    version="1.0.0"
)

# Optional: Redirect root to Streamlit UI
@app.get("/", include_in_schema=False)
def redirect_to_ui():
    return RedirectResponse(url="http://localhost:8501")

# Include API routes
app.include_router(tutor_routes.router, prefix="/tutor", tags=["Tutor"])
app.include_router(quiz_routes.router, prefix="/quiz", tags=["Quiz"])
app.include_router(doubt_routes.router, prefix="/doubt", tags=["Doubt Solver"])
app.include_router(tracker_routes.router, prefix="/tracker", tags=["Progress Tracker"])