# 🎓 AI Tutor Platform

An intelligent AI tutoring platform built with FastAPI, Streamlit, LangChain, and Groq, with user authentication and progress tracking powered by **PostgreSQL**.

## 🚀 Features

  * **ChatGPT-style AI Tutor** (`/tutor/ask`): Engage in natural language conversations with an AI assistant for learning and doubt clarification.
  * **Auto-generated MCQ Quizzes** (`/quiz/generate`): Generate subject-wise multiple-choice quizzes with configurable numbers of questions.
  * **File-based Doubt Solving** (`/doubt/solve`): Upload documents (PDFs, TXT, images) and ask questions directly related to their content.
  * **User Authentication (Sign Up/Login)**: Securely register and log in to personalized accounts.
  * **Personalized Progress Tracking** (`/tracker/*`): Track your quiz scores and performance over time, accessible only to logged-in users.
  * **Persistent Chat History**: Previous conversations are saved and loaded for logged-in users.

## ⚙️ Tech Stack

  * **FastAPI**: A modern, fast (high-performance) web framework for building the backend API.
  * **Streamlit**: The framework for creating the interactive web-based user interface.
  * **LangChain**: A framework for developing applications powered by large language models.
  * **Groq**: Provides fast inference for large language models (Llama 3, Mixtral) used for tutoring and quiz generation.
  * **PostgreSQL**: A powerful open-source relational database for storing user data, chat history, quiz attempts, and progress.
  * **Psycopg2-binary**: The PostgreSQL adapter for Python.
  * **Passlib (bcrypt)**: Used for secure password hashing and verification.
  * **Python-jose**: (For JWT) Recommended for secure token generation and validation in `auth_routes.py`.
  * **Pydantic**: Data validation and settings management.
  * **Pandas & Altair**: For data manipulation and interactive visualizations in the progress tracker.
  * **PyMuPDF (fitz) & Pillow + PyTesseract**: For text extraction from PDF and image files for the doubt solver.

-----

## 🏁 Running the App Locally

To run this project on your local machine without Docker, you'll need Python, PostgreSQL, and Tesseract OCR installed.

1.  **Prerequisites**:

      * **Python 3.8+**: Install from [python.org](https://www.python.org/).
      * **PostgreSQL**: Install a PostgreSQL server locally (e.g., via [PostgreSQL Downloads](https://www.postgresql.org/download/) or a tool like [PgAdmin](https://www.pgadmin.org/)).
      * **Tesseract OCR Engine**: Install Tesseract OCR for your operating system.
          * **Windows**: Download installer from [Tesseract-OCR GitHub](https://github.com/UB-Mannheim/tesseract/wiki).
          * **macOS**: `brew install tesseract`
          * **Linux (Debian/Ubuntu)**: `sudo apt-get install tesseract-ocr`
          * Ensure Tesseract is added to your system's PATH.

2.  **Clone the Repository**:

    ```bash
    git clone https://github.com/gyan007/AI-Tutor-Platform.git
    cd AI-Tutor-Platform
    ```

3.  **Create and Activate a Virtual Environment**:

    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

4.  **Install Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

    *Make sure your `requirements.txt` is up-to-date with all the libraries listed in the "Tech Stack" section.*

5.  **Create `.env` file**: In the root directory of the project, create a file named `.env` and add your API keys and secrets. This file is ignored by Git and keeps your secrets safe.

    ```ini
    # .env
    # Groq API Key for LLM access
    GROQ_API_KEY=sk_your_groq_api_key_here

    # Database connection string for local PostgreSQL
    DATABASE_URL=postgresql://user:password@localhost:5432/your_local_db_name

    # Secret key for JWT token signing (FastAPI backend)
    SECRET_KEY=your_long_random_secret_for_jwt_signing

    # Streamlit secret for session state management
    STREAMLIT_SECRET_KEY=your_long_random_streamlit_secret
    ```

    *Replace placeholders with your actual keys and desired database credentials (user/password/db name for your local PostgreSQL instance).*

6.  **Update `ai_tutor_platform/data/config.ini`**:
    This file primarily serves as a fallback or for non-sensitive defaults. Ensure it aligns with your environment.

    ```ini
    # ai_tutor_platform/data/config.ini
    [GENERAL]
    llm_model = llama3-8b-8192  ; Default Groq model
    temperature = 0.7
    api_base = https://api.groq.com/openai/v1
    ; api_key = YOUR_GROQ_API_KEY_HERE ; Keep this commented or as placeholder for security
    ```

7.  **Initialize Local Database Schema**:

      * Start your local PostgreSQL server.
      * Connect to your local database (e.g., using `psql` or PgAdmin) and run the `CREATE TABLE` and `CREATE INDEX` SQL scripts for `users`, `chat_history`, `file_doubts`, `quiz_attempts`, and `user_progress`. (These scripts were provided in previous responses).

8.  **Run FastAPI Backend**:
    Open a new terminal window, activate your virtual environment, navigate to the project root, and run:

    ```bash
    export PYTHONPATH=$PYTHONPATH:./ai_tutor_platform # For Linux/macOS
    # On Windows: set PYTHONPATH=%PYTHONPATH%;.\ai_tutor_platform
    uvicorn ai_tutor_platform.main_api:app --host 0.0.0.0 --port 8000 --reload
    ```

      * The `--reload` flag is useful for local development, automatically restarting the server when code changes.

9.  **Run Streamlit Frontend**:
    Open another new terminal window, activate your virtual environment, navigate to the project root, and run:

    ```bash
    export PYTHONPATH=$PYTHONPATH:./ai_tutor_platform # For Linux/macOS
    # On Windows: set PYTHONPATH=%PYTHONPATH%;.\ai_tutor_platform
    streamlit run ai_tutor_platform/main.py --server.port 8501
    ```

10. **Access the Application**:

      * **Streamlit UI**: Open your web browser and navigate to `http://localhost:8501`
      * **FastAPI Docs**: Open your web browser and navigate to `http://localhost:8000/docs` (for API documentation)

-----

## ☁️ Deployment to Cloud

Deploying this multi-service application involves separate considerations for each component on cloud platforms. We'll outline deployment to **Render** (for FastAPI & PostgreSQL) and **Streamlit Community Cloud** (for Streamlit frontend).

### 1\. PostgreSQL Database

  * **Recommended**: **Render PostgreSQL** (or other managed PostgreSQL services like ElephantSQL, Railway, Supabase).
      * Sign up for [Render.com](https://render.com/).
      * Create a new **PostgreSQL** database service on Render. Choose a free-tier instance for testing.
      * Once provisioned, note the **Internal Database URL** (for other Render services) and **External Connection String (psql)** (for local `psql` access).
      * **Initialize Database Schema**: Use the External Connection String to connect to your Render PostgreSQL database via `psql` from your local machine and run all your `CREATE TABLE` and `CREATE INDEX` SQL scripts once.

### 2\. FastAPI Backend

  * **Recommended**: **Render.com** (as a Web Service).
      * On Render, create a new **Web Service**.
      * Connect to your GitHub repository.
      * **Root Directory**: Set this to `.` (assuming your `ai_tutor_platform` directory is at the root of your Git repo).
      * **Runtime**: Select `Python 3`.
      * **Build Command**: `pip install -r requirements.txt`
          * **Note**: If using PyTesseract for image OCR, you'll need the Tesseract OCR engine installed. Render's standard Python runtime does *not* include this. You might need to add a build step to install it if allowed, or consider using a `Dockerfile` for more control over system dependencies.
      * **Start Command**:
        ```bash
        export PYTHONPATH=$PYTHONPATH:./ai_tutor_platform && uvicorn ai_tutor_platform.main_api:app --host 0.0.0.0 --port $PORT
        ```
      * **Environment Variables**:
          * `GROQ_API_KEY`: Your Groq API key (from Groq Console).
          * `DATABASE_URL`: The **Internal Database URL** of your deployed Render PostgreSQL database.
          * `SECRET_KEY`: A long, random, and securely generated string for JWT token signing.

### 3\. Streamlit Frontend

  * **Recommended**: **Streamlit Community Cloud** (`share.streamlit.io`).
      * Your Streamlit app's code (`ai_tutor_platform/main.py`) must be in a **public GitHub repository**.

      * **`.streamlit/secrets.toml`**: Create a `.streamlit` directory in your repository root and add `secrets.toml`. This file is private to Streamlit Cloud and should contain your sensitive keys:

        ```ini
        # .streamlit/secrets.toml
        # Groq API Key for LLM access (if Streamlit still makes direct LLM calls or passes it)
        GROQ_API_KEY = "sk_your_real_groq_api_key_from_groq"

        # Streamlit secret for session state management (must be long and random)
        STREAMLIT_SECRET_KEY = "your_long_random_string_for_streamlit_session_state"

        # Public URL of your deployed FastAPI backend on Render
        FASTAPI_URL = "https://your-deployed-fastapi-app-name.onrender.com"
        ```

      * **Deploy**: Go to Streamlit Community Cloud, click "New app", select your repository and the main file (`ai_tutor_platform/main.py`), and deploy.

-----

This revised `README.md` now correctly reflects your non-Docker local setup and the specific Render/Streamlit Cloud deployment paths. Remember to replace all placeholder values with your actual credentials and URLs before pushing to GitHub.
