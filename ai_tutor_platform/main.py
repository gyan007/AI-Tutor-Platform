import streamlit as st
import tempfile
import json
import pandas as pd
import altair as alt
import uuid
import os
import requests # <-- ADDED for making API calls

from ai_tutor_platform.modules.tutor.chat_tutor import ask_tutor
from ai_tutor_platform.modules.doubt_solver.file_handler import solve_doubt_from_file
from ai_tutor_platform.modules.quiz.quiz_generator import generate_quiz
from ai_tutor_platform.db.pg_client import ( # Changed to pg_client
    save_chat, save_file_doubt, save_quiz_response, save_user_progress, get_user_progress
    # No setup_db_schema call here, assume manual schema setup
)

st.set_page_config(page_title="AI Tutor Platform", layout="wide")

# -----------------------------
# Session state initialization
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {} # Now store history per user
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
# No score_history session state, will fetch directly from DB for current user
if "user_id" not in st.session_state:
    # This was a UUID, now it will be the username or None if not logged in
    st.session_state.user_id = None # Set to None, will be replaced by username on login

# --- API Base URL ---
# In production, this would be your deployed FastAPI URL (e.g., https://your-api-url.onrender.com)
API_BASE_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

# ------------------
# Login/Signup Section (Before main app content)
# ------------------
if not st.session_state.logged_in:
    st.subheader("Welcome to AI Tutor Platform")
    auth_tab1, auth_tab2 = st.tabs(["Login", "Signup"])

    with auth_tab1:
        with st.form("login_form"):
            st.write("Login")
            username_login = st.text_input("Username", key="username_login")
            password_login = st.text_input("Password", type="password", key="password_login")
            submit_login = st.form_submit_button("Login")

            if submit_login:
                if username_login and password_login:
                    try:
                        # FastAPI expects x-www-form-urlencoded for OAuth2PasswordRequestForm
                        response = requests.post(f"{API_BASE_URL}/auth/token",
                            data={"username": username_login, "password": password_login})
                        
                        if response.status_code == 200:
                            token_data = response.json()
                            st.session_state.logged_in = True
                            st.session_state.username = username_login
                            st.session_state.access_token = token_data["access_token"]
                            st.session_state.token_type = token_data["token_type"]
                            # Load user-specific chat history
                            st.session_state.chat_history[username_login] = [] # Initialize or load from DB if stored per session
                            st.success(f"Welcome, {username_login}!")
                            st.rerun()
                        else:
                            st.error(f"Login failed: {response.json().get('detail', 'Unknown error')}")
                    except requests.exceptions.ConnectionError:
                        st.error("Could not connect to the API. Make sure the backend is running.")
                    except Exception as e:
                        st.error(f"An error occurred during login: {e}")
                else:
                    st.warning("Please enter both username and password.")

    with auth_tab2:
        with st.form("signup_form"):
            st.write("Signup")
            username_signup = st.text_input("New Username", key="username_signup")
            password_signup = st.text_input("New Password", type="password", key="password_signup")
            email_signup = st.text_input("Email (Optional)", key="email_signup")
            submit_signup = st.form_submit_button("Signup")

            if submit_signup:
                if username_signup and password_signup:
                    try:
                        response = requests.post(f"{API_BASE_URL}/auth/signup",
                            json={"username": username_signup, "password": password_signup, "email": email_signup})
                        
                        if response.status_code == 200:
                            st.success(f"User {username_signup} registered successfully! Please login.")
                        else:
                            st.error(f"Signup failed: {response.json().get('detail', 'Unknown error')}")
                    except requests.exceptions.ConnectionError:
                        st.error("Could not connect to the API. Make sure the backend is running.")
                    except Exception as e:
                        st.error(f"An error occurred during signup: {e}")
                else:
                    st.warning("Please enter a username and password.")
else: # User is logged in, show main app content

    st.title("🎓 AI Tutor Platform")
    st.caption(f"Powered by Groq | Logged in as: {st.session_state.username}") # Display logged-in user

    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.access_token = None
        st.session_state.chat_history = {} # Clear chat history on logout
        st.rerun()

    # Create headers for authenticated API calls
    def get_auth_headers():
        if st.session_state.access_token:
            return {"Authorization": f"{st.session_state.token_type} {st.session_state.access_token}"}
        return {}

    # ------------------
    # Tabs Declaration
    # ------------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "💬 Chat Tutor",
        "📂 Doubt from File",
        "✍️ Quiz Generator",
        "📈 Progress Tracker"
    ])

    # ----------------------------
    # ✨ Tab 1: Chat Tutor
    # ----------------------------
    with tab1:
        st.subheader("Chat with your AI Tutor")
        user_input = st.text_input("Ask something:", key="chat_input")

        if st.button("Send", key="send_chat"):
            if user_input.strip():
                with st.spinner("Thinking..."):
                    # Call the FastAPI backend endpoint for chat
                    try:
                        # Assuming your FastAPI /tutor/ask route expects JSON body and uses dependency
                        response_api = requests.post(f"{API_BASE_URL}/tutor/ask",
                            headers=get_auth_headers(),
                            json={"question": user_input})
                        
                        if response_api.status_code == 200:
                            response_data = response_api.json().get("response", "No response from AI.")
                            if st.session_state.username not in st.session_state.chat_history:
                                st.session_state.chat_history[st.session_state.username] = []
                            st.session_state.chat_history[st.session_state.username].append(("user", user_input))
                            st.session_state.chat_history[st.session_state.username].append(("ai", response_data))
                            # DB saving is handled by the FastAPI backend
                        else:
                            st.error(f"Error from AI Tutor: {response_api.status_code} - {response_api.json().get('detail', 'Unknown error')}")
                    except requests.exceptions.ConnectionError:
                        st.error("Could not connect to the API. Make sure the backend is running.")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
            else:
                st.warning("Please enter a question.")

        # Display chat history for the current user
        if st.session_state.username and st.session_state.username in st.session_state.chat_history:
            if st.session_state.chat_history[st.session_state.username]:
                st.markdown("#### Conversation History")
                for role, msg in reversed(st.session_state.chat_history[st.session_state.username]):
                    if role == "user":
                        st.markdown(f"**👤 You:** {msg}")
                    else:
                        st.markdown(f"**🤖 AI:** {msg}")

        if st.button("Clear Chat", key="clear_chat_button"):
            if st.session_state.username in st.session_state.chat_history:
                st.session_state.chat_history[st.session_state.username] = []
            st.rerun()

    # ----------------------------
    # 📁 Tab 2: Doubt Solver from File
    # ----------------------------
    with tab2:
        st.subheader("Upload File and Ask a Question")
        uploaded_file = st.file_uploader("Choose file (PDF, TXT, JPG, PNG)", type=["pdf", "txt", "jpg", "jpeg", "png"])
        file_question = st.text_input("What is your question about this file?", key="file_q")

        if st.button("Solve Doubt"):
            if uploaded_file and file_question.strip():
                # Use tempfile to securely save and access the uploaded file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_file_path = tmp_file.name

                with st.spinner("Processing file..."):
                    try:
                        # For file uploads, it's easier to send directly to backend if backend handles file.
                        # OR, you can process file locally then send text to backend.
                        # Current design has Streamlit extracting text, so let's stick to that for now
                        # and then call FastAPI with context.
                        # If FastAPI needs the raw file, you'd send it as multipart/form-data.

                        # Call the local solve_doubt_from_file function as it extracts text
                        answer = solve_doubt_from_file(tmp_file_path, file_question)
                        
                        # Assuming solve_doubt_from_file does NOT call the DB directly anymore
                        # and instead returns the answer, and DB saving is via FastAPI.
                        # The original file_handler.py calls generate_response directly.
                        # If you want to use the FastAPI route, you'd need to adapt.
                        # For simplicity, if solve_doubt_from_file already calls LLM, we save directly:
                        # For now, let's keep the direct call to solve_doubt_from_file
                        # and then save the info to DB via pg_client.
                        # Note: If you want to use the API for file_doubt, FastAPI needs to handle file uploads.
                        # For current simplicity, let's assume solve_doubt_from_file is local LLM call
                        # that already interacts with `ai_tutor_platform.llm.mistral_chain`.

                        st.success("Answer:")
                        st.write(answer)
                        # Save file doubt to DB directly (as solve_doubt_from_file doesn't know about user_id from token)
                        # This means your save_file_doubt needs to be updated in pg_client to only take user_id as string
                        save_file_doubt(st.session_state.username, uploaded_file.name, file_question, answer) # <-- CHANGED
                    except Exception as e:
                        st.error(f"An error occurred processing your file: {e}")
                
                # Clean up the temporary file after processing
                os.unlink(tmp_file_path)

            else:
                st.warning("Please upload a file and enter a question.")

    # ----------------------------
    # 📝 Tab 3: Quiz Generator
    # ----------------------------
    with tab3:
        st.subheader("📝 Generate a Subject Quiz")

        subject = st.selectbox("Select a subject:", ["Math", "Science", "History", "Geography", "English"], key="quiz_subject_select")
        num_questions = st.slider("Number of questions:", min_value=1, max_value=10, value=3, key="quiz_num_questions_slider")

        if st.button("Generate Quiz", key="generate_quiz_button"):
            with st.spinner("Generating quiz..."):
                try:
                    # Call FastAPI backend for quiz generation
                    response_api = requests.post(f"{API_BASE_URL}/quiz/generate",
                        headers=get_auth_headers(),
                        json={"topic": subject, "num_questions": num_questions})
                    
                    if response_api.status_code == 200:
                        quiz = response_api.json().get("quiz", [])
                        if quiz and "question" in quiz[0] and "[ERROR]" in quiz[0]["question"]:
                            st.error(quiz[0]["question"])
                            st.session_state.quiz_questions = []
                            st.session_state.quiz_submitted = False
                        else:
                            st.session_state.quiz_questions = quiz
                            st.session_state.quiz_submitted = False
                            # Clear previous quiz selections for a new quiz
                            st.session_state.current_quiz_selections = {f"quiz_q_{i}": None for i in range(len(st.session_state.quiz_questions))}
                    else:
                        st.error(f"Error generating quiz: {response_api.status_code} - {response_api.json().get('detail', 'Unknown error')}")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the API. Make sure the backend is running.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

        if st.session_state.quiz_questions:
            if not st.session_state.quiz_submitted:
                st.subheader("📚 Answer the Questions")
                
                if "current_quiz_selections" not in st.session_state:
                    st.session_state.current_quiz_selections = {f"quiz_q_{i}": None for i in range(len(st.session_state.quiz_questions))}

                for i, q in enumerate(st.session_state.quiz_questions):
                    st.markdown(f"**Q{i + 1}: {q['question']}**")
                    options = q["options"]
                    
                    if not isinstance(options, list) or len(options) != 4 or not all(isinstance(opt, str) for opt in options):
                        st.error(f"Invalid options for Q{i+1}. Please regenerate quiz. Raw options: {options}")
                        continue

                    selected_option = st.radio(
                        f"Your answer for Q{i + 1}:",
                        options,
                        index=options.index(st.session_state.current_quiz_selections[f"quiz_q_{i}"]) if st.session_state.current_quiz_selections[f"quiz_q_{i}"] in options else None,
                        key=f"quiz_q_{i}"
                    )
                    st.session_state.current_quiz_selections[f"quiz_q_{i}"] = selected_option


                if st.button("Submit Quiz", key="submit_quiz_button"):
                    user_answers = [st.session_state.current_quiz_selections[f"quiz_q_{i}"] for i in range(len(st.session_state.quiz_questions))]

                    # Call FastAPI backend for quiz submission
                    try:
                        response_api = requests.post(f"{API_BASE_URL}/quiz/submit",
                            headers=get_auth_headers(),
                            json={
                                "user_id": st.session_state.username, # Pass username
                                "subject": subject,
                                "questions": st.session_state.quiz_questions,
                                "user_answers": user_answers
                            })
                        
                        if response_api.status_code == 200:
                            submission_results = response_api.json()
                            st.session_state.quiz_submitted = True
                            
                            st.markdown("### 📊 Results:")
                            for detail in submission_results["details"]:
                                st.markdown(f"**Q: {detail['question']}**")
                                if detail['is_correct']:
                                    st.success(f"✅ Your answer: **{detail['user_answer']}**")
                                else:
                                    st.error(f"❌ Your answer: **{detail['user_answer']}**")
                                    st.info(f"✅ Correct answer: **{detail['correct_answer']}**")
                                st.markdown("---")
                            
                            st.success(f"🏁 Final Score: **{submission_results['score']} / {submission_results['total']}**")
                            # No need to save to session state score_history now, always fetch from DB
                        else:
                            st.error(f"Error submitting quiz: {response_api.status_code} - {response_api.json().get('detail', 'Unknown error')}")
                    except requests.exceptions.ConnectionError:
                        st.error("Could not connect to the API. Make sure the backend is running.")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
            else:
                st.info("Quiz already submitted. Generate a new quiz to continue.")

    # ----------------------------
    # 📊 Tab 4: Progress Tracker
    # ----------------------------
    with tab4:
        st.subheader("Quiz Performance Over Time")

        # Call FastAPI backend for progress
        progress_data_from_db = []
        try:
            response_api = requests.post(f"{API_BASE_URL}/tracker/progress",
                headers=get_auth_headers(),
                json={"user_id": st.session_state.username}) # Pass username
            
            if response_api.status_code == 200:
                progress_data_from_db = response_api.json().get("progress", [])
            else:
                st.error(f"Error fetching progress: {response_api.status_code} - {response_api.json().get('detail', 'Unknown error')}")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the API to fetch progress.")
        except Exception as e:
            st.error(f"An error occurred fetching progress: {e}")

        if progress_data_from_db:
            df = pd.DataFrame(progress_data_from_db)
            df['accuracy'] = df['accuracy'].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values(by='timestamp')

            chart_overall = alt.Chart(df).mark_line(point=True).encode(
                x=alt.X('timestamp:T', title="Date of Quiz"),
                y=alt.Y('accuracy:Q', title="Accuracy (%)", scale=alt.Scale(domain=[0, 100])),
                color=alt.Color('subject:N', title="Subject"),
                tooltip=[
                    alt.Tooltip('timestamp:T', title='Date'),
                    'subject',
                    'score',
                    'total',
                    alt.Tooltip('accuracy:Q', format='.2f', title='Accuracy (%)')
                ]
            ).properties(
                title="Overall Quiz Accuracy Trend"
            ).interactive()

            st.altair_chart(chart_overall, use_container_width=True)

            avg_accuracy_by_subject = df.groupby('subject')['accuracy'].mean().reset_index()
            chart_subject_avg = alt.Chart(avg_accuracy_by_subject).mark_bar().encode(
                x=alt.X('subject:N', title="Subject"),
                y=alt.Y('accuracy:Q', title="Average Accuracy (%)", scale=alt.Scale(domain=[0, 100])),
                tooltip=['subject', alt.Tooltip('accuracy:Q', format='.2f', title='Avg Accuracy (%)')]
            ).properties(
                title="Average Accuracy Per Subject"
            ).interactive()

            st.altair_chart(chart_subject_avg, use_container_width=True)

            st.markdown("#### Raw Progress Data")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Take some quizzes to track your progress! Your progress data will appear here.")
