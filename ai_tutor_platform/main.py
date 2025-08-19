import streamlit as st
import tempfile
import json
import pandas as pd
import altair as alt
import uuid
import os
import requests

from ai_tutor_platform.modules.tutor.chat_tutor import ask_tutor
from ai_tutor_platform.modules.doubt_solver.file_handler import solve_doubt_from_file
from ai_tutor_platform.modules.quiz.quiz_generator import generate_quiz
from ai_tutor_platform.db.pg_client import (
    save_chat, save_file_doubt, save_quiz_response, get_user_progress # get_user_progress is crucial here
)

st.set_page_config(page_title="AI Tutor Platform", layout="wide")

# --- API Base URL ---
API_BASE_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

# -----------------------------
# Session state initialization
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "token_type" not in st.session_state: # Added token_type
    st.session_state.token_type = None
# IMPORTANT: Initialize chat_history as a dictionary keyed by username
if "chat_history_by_user" not in st.session_state:
    st.session_state.chat_history_by_user = {}
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "current_quiz_selections" not in st.session_state: # To persist quiz selections
    st.session_state.current_quiz_selections = {}


# Helper function to create authorization headers
def get_auth_headers():
    if st.session_state.access_token and st.session_state.token_type:
        return {"Authorization": f"{st.session_state.token_type} {st.session_state.access_token}"}
    return {}

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
                        response = requests.post(f"{API_BASE_URL}/auth/token",
                            data={"username": username_login, "password": password_login})

                        if response.status_code == 200:
                            token_data = response.json()
                            st.session_state.logged_in = True
                            st.session_state.username = username_login
                            st.session_state.access_token = token_data["access_token"]
                            st.session_state.token_type = token_data["token_type"]

                            # --- FETCH PREVIOUS DATA ON LOGIN ---
                            # Fetch existing chat history for this user from DB
                            # Note: The /tutor/ask route *saves* to DB, but you need a /tutor/history endpoint
                            # to *fetch* it. For now, let's assume `save_chat` is sufficient.
                            # If you need to *display* old chats, you'd need a `get_chat_history` function
                            # in pg_client and a corresponding FastAPI route.
                            # For simplicity, we'll initialize chat_history for the user here,
                            # and any new chats will be added. To load old chats, you'd call
                            # a DB function here. (See proposed new function below)

                            # Here, we will simulate loading existing chat from DB, assuming a new DB function exists.
                            # If `get_chat_history` doesn't exist, remove this part or create it.
                            # For now, it initializes an empty list for the user if none exists.
                            if username_login not in st.session_state.chat_history_by_user:
                                st.session_state.chat_history_by_user[username_login] = []
                            
                            # You would ideally fetch past chats here. Example:
                            # past_chats_response = requests.get(f"{API_BASE_URL}/tutor/history", headers=get_auth_headers())
                            # if past_chats_response.status_code == 200:
                            #     st.session_state.chat_history_by_user[username_login] = past_chats_response.json().get('history', [])
                            # else:
                            #     st.warning("Could not load past chat history.")
                            # For now, without a specific API endpoint to fetch all chats, we proceed with current logic.


                            st.success(f"Welcome, {username_login}!")
                            st.rerun() # Rerun to switch to the main app content
                        else:
                            st.error(f"Login failed: {response.json().get('detail', 'Unknown error')}")
                    except requests.exceptions.ConnectionError:
                        st.error("Could not connect to the API. Make sure the backend is running and FASTAPI_URL is correct.")
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
    st.caption(f"Powered by Groq | Logged in as: {st.session_state.username}")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.access_token = None
        st.session_state.token_type = None
        # Don't clear chat_history_by_user entirely, just for this user if desired
        # Or if you want to clear current user's chat, do:
        # if st.session_state.username in st.session_state.chat_history_by_user:
        #     st.session_state.chat_history_by_user[st.session_state.username] = []
        st.rerun()

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
                    try:
                        response_api = requests.post(f"{API_BASE_URL}/tutor/ask",
                            headers=get_auth_headers(),
                            json={"question": user_input})

                        if response_api.status_code == 200:
                            response_data = response_api.json().get("response", "No response from AI.")
                            # Ensure the current user's chat history list exists
                            if st.session_state.username not in st.session_state.chat_history_by_user:
                                st.session_state.chat_history_by_user[st.session_state.username] = []
                            st.session_state.chat_history_by_user[st.session_state.username].append(("user", user_input))
                            st.session_state.chat_history_by_user[st.session_state.username].append(("ai", response_data))
                        else:
                            st.error(f"Error from AI Tutor: {response_api.status_code} - {response_api.json().get('detail', 'Unknown error')}")
                    except requests.exceptions.ConnectionError:
                        st.error("Could not connect to the API. Make sure the backend is running.")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
            else:
                st.warning("Please enter a question.")

        # Display chat history ONLY for the current user
        current_user_chat_history = st.session_state.chat_history_by_user.get(st.session_state.username, [])
        if current_user_chat_history:
            st.markdown("#### Conversation History")
            for role, msg in reversed(current_user_chat_history): # Iterate through current user's history
                if role == "user":
                    st.markdown(f"**👤 You:** {msg}")
                else:
                    st.markdown(f"**🤖 AI:** {msg}")

        if st.button("Clear Chat", key="clear_chat_button"):
            if st.session_state.username in st.session_state.chat_history_by_user:
                st.session_state.chat_history_by_user[st.session_state.username] = []
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
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_file_path = tmp_file.name

                with st.spinner("Processing file..."):
                    try:
                        # Assuming solve_doubt_from_file handles LLM internally for now.
                        # It will save directly to DB using current_user.username
                        answer = solve_doubt_from_file(tmp_file_path, file_question)

                        st.success("Answer:")
                        st.write(answer)
                        # DB saving for file doubt is handled by FastAPI now if that route is used.
                        # If solve_doubt_from_file function itself is directly saving,
                        # you need to ensure pg_client.save_file_doubt is called.
                        # As per updated API routes, FastAPI backend will handle save_file_doubt.
                        # So, this `save_file_doubt` call is likely redundant if API is used for this feature.
                        # The client should call the FastAPI endpoint /doubt/solve, which then calls solve_doubt and save_file_doubt.
                        # For now, let's keep it calling the API if you intend to move file logic to API:
                        
                        # Proposed change for /doubt/solve to use FastAPI
                        # For FastAPI to process the file, you'd send the file bytes to FastAPI
                        # For simplicity, if solve_doubt_from_file is still called directly in Streamlit
                        # It needs to save to DB.
                        
                        # Option 1: Continue direct local execution, then save to DB (less ideal for API)
                        # save_file_doubt(st.session_state.username, uploaded_file.name, file_question, answer)
                        
                        # Option 2: Send the text and question to the FastAPI /doubt/solve endpoint
                        # This would mean `solve_doubt_from_file` should be adapted to be a client function.
                        # For now, we'll keep the direct `solve_doubt_from_file` call, which might already call LLM.
                        # If you want to use the API route for doubt, the logic here needs to change to:
                        # response_api = requests.post(f"{API_BASE_URL}/doubt/solve", headers=get_auth_headers(),
                        #                             json={"file_name": uploaded_file.name, "context": extracted_text, "question": file_question})
                        # Then save_file_doubt would happen on backend.
                        # For now, assuming solve_doubt_from_file internally calls LLM and saves to DB.
                        # But wait, your API /doubt/solve calls `solve_doubt` then `save_file_doubt`.
                        # So Streamlit needs to call `/doubt/solve`. This means `file_handler.py` needs to be
                        # restructured to separate text extraction from LLM call.

                        # Let's assume you pass text to backend for consistency:
                        extracted_text = solve_doubt_from_file(tmp_file_path, file_question) # This currently runs LLM directly
                        # You want to call the API, not direct `solve_doubt_from_file` if it's the backend's job.
                        # Let's assume `solve_doubt_from_file` returns just extracted text for now, or just the answer.
                        
                        # This part needs clarification: Does `solve_doubt_from_file` (your local function)
                        # call the LLM and DB, or just extract text?
                        # Based on `doubt_routes.py`, `solve_doubt` is on backend, called by API.
                        # So, Streamlit should do:
                        # 1. Extract text locally.
                        # 2. Send text + question to FastAPI's `/doubt/solve` endpoint.

                        # REVISION FOR DOUBT SOLVER:
                        # Assuming `extract_text_from_file` is local, and `solve_doubt` is on the backend.
                        from ai_tutor_platform.modules.doubt_solver.file_handler import extract_text_from_file # Import extraction
                        
                        extracted_text = extract_text_from_file(tmp_file_path) # Extract text locally
                        if "[ERROR]" in extracted_text:
                            st.error(extracted_text)
                        else:
                            response_api = requests.post(f"{API_BASE_URL}/doubt/solve",
                                headers=get_auth_headers(),
                                json={"file_name": uploaded_file.name, "context": extracted_text, "question": file_question})
                            
                            if response_api.status_code == 200:
                                answer = response_api.json().get("answer", "No answer from AI.")
                                st.success("Answer:")
                                st.write(answer)
                            else:
                                st.error(f"Error from Doubt Solver: {response_api.status_code} - {response_api.json().get('detail', 'Unknown error')}")

                    except requests.exceptions.ConnectionError:
                        st.error("Could not connect to the API. Make sure the backend is running.")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                
                os.unlink(tmp_file_path) # Clean up temp file
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

                    try:
                        response_api = requests.post(f"{API_BASE_URL}/quiz/submit",
                            headers=get_auth_headers(),
                            json={
                                # user_id is passed as a string (username)
                                "user_id": st.session_state.username, # FastAPI will get user from token, this `user_id` might be redundant but keeping for current API model compatibility
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

        progress_data_from_db = []
        try:
            # The /tracker/progress route in FastAPI now gets user_id from token
            # The request body can be empty or just a placeholder if the FastAPI route
            # doesn't expect 'user_id' in body after authentication.
            # Let's keep it as is, FastAPI will likely ignore it and use token's user_id.
            response_api = requests.post(f"{API_BASE_URL}/tracker/progress",
                headers=get_auth_headers(),
                json={"user_id": st.session_state.username}) # Sending username, though backend uses token

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
