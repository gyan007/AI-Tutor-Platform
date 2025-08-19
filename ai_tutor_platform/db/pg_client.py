import os
import psycopg2
from datetime import datetime
from typing import List, Dict, Any

# Environment variable for PostgreSQL URI
# Example: postgresql://user:password@host:port/database_name
# For Render, this will often be automatically set as DATABASE_URL
PG_URI = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/ai_tutor_db")

def get_db_connection():
    """Establishes and returns a new PostgreSQL connection."""
    try:
        conn = psycopg2.connect(PG_URI)
        return conn
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        raise

# Helper function to ensure database schema is set up (optional, but good for first run)
def setup_db_schema():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        sql_schema = """
        CREATE TABLE IF NOT EXISTS chat_history (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE, -- Optional: if you want email-based login/recovery
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS file_doubts (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            filename VARCHAR(255) NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            subject VARCHAR(255) NOT NULL,
            question TEXT NOT NULL,
            options TEXT[] NOT NULL, -- Array of text for options
            correct_answer VARCHAR(255) NOT NULL,
            user_answer VARCHAR(255) NOT NULL,
            is_correct BOOLEAN NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS user_progress (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            subject VARCHAR(255) NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            accuracy NUMERIC(5, 2) NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_chat_user_id ON chat_history (user_id);
        CREATE INDEX IF NOT EXISTS idx_file_user_id ON file_doubts (user_id);
        CREATE INDEX IF NOT EXISTS idx_quiz_user_id ON quiz_attempts (user_id);
        CREATE INDEX IF NOT EXISTS idx_progress_user_id ON user_progress (user_id);
        CREATE INDEX IF NOT EXISTS idx_progress_subject ON user_progress (subject);
        """
        cur.execute(sql_schema)
        conn.commit()
        print("Database schema ensured.")
    except Exception as e:
        print(f"Error setting up database schema: {e}")
        raise
    finally:
        if conn:
            conn.close()

# Call setup_db_schema once at application startup (e.g., in main.py or main_api.py)
# Or, prefer to run SQL scripts manually on your DB instance.

# ------------ Chat History ------------
def save_chat(user_id: str, question: str, answer: str):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO chat_history (user_id, question, answer) VALUES (%s, %s, %s)",
            (user_id, question, answer)
        )
        conn.commit()
    except Exception as e:
        print(f"Error saving chat: {e}")
        conn.rollback()
        raise
    finally:
        if conn:
            cur.close()
            conn.close()

# ------------ File-based Doubt ------------
def save_file_doubt(user_id: str, filename: str, question: str, answer: str):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO file_doubts (user_id, filename, question, answer) VALUES (%s, %s, %s, %s)",
            (user_id, filename, question, answer)
        )
        conn.commit()
    except Exception as e:
        print(f"Error saving file doubt: {e}")
        conn.rollback()
        raise
    finally:
        if conn:
            cur.close()
            conn.close()

# ------------ Quiz Answers ------------
def save_quiz_response(user_id: str, subject: str, quiz: List[Dict[str, Any]], user_answers: List[str]):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        for i, q in enumerate(quiz):
            # PostgreSQL array type (TEXT[]) needs a Python list
            options_list = q.get("options", [])
            correct_ans = q.get("answer", "").strip().lower()
            user_ans = user_answers[i].strip().lower() if user_answers[i] is not None else ""
            is_correct = correct_ans == user_ans

            cur.execute(
                "INSERT INTO quiz_attempts (user_id, subject, question, options, correct_answer, user_answer, is_correct) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (user_id, subject, q.get("question", ""), options_list, q.get("answer", ""), user_answers[i], is_correct)
            )
        conn.commit()
    except Exception as e:
        print(f"Error saving quiz response: {e}")
        conn.rollback()
        raise
    finally:
        if conn:
            cur.close()
            conn.close()

# ------------ User Progress ------------
def save_user_progress(user_id: str, subject: str, score: int, total: int):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        accuracy = round(score / total * 100, 2) if total > 0 else 0
        cur.execute(
            "INSERT INTO user_progress (user_id, subject, score, total, accuracy) VALUES (%s, %s, %s, %s, %s)",
            (user_id, subject, score, total, accuracy)
        )
        conn.commit()
    except Exception as e:
        print(f"Error saving user progress: {e}")
        conn.rollback()
        raise
    finally:
        if conn:
            cur.close()
            conn.close()

def get_user_progress(user_id: str):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, subject, score, total, accuracy, timestamp FROM user_progress WHERE user_id = %s ORDER BY timestamp ASC", (user_id,))
        rows = cur.fetchall()
        
        # Convert rows to list of dictionaries for compatibility with pandas/streamlit
        columns = [desc[0] for desc in cur.description]
        results = []
        for row in rows:
            results.append(dict(zip(columns, row)))
        return results
    except Exception as e:
        print(f"Error getting user progress: {e}")
        raise
    finally:
        if conn:
            cur.close()
            conn.close()

