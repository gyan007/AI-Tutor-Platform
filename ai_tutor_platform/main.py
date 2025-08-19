import streamlit as st
import tempfile
import json
import pandas as pd
import altair as alt
import uuid
import os

from ai_tutor_platform.modules.tutor.chat_tutor import ask_tutor
from ai_tutor_platform.modules.doubt_solver.file_handler import solve_doubt_from_file
from ai_tutor_platform.modules.quiz.quiz_generator import generate_quiz

# Update this import from mongo_client to pg_client
from ai_tutor_platform.db.pg_client import ( # <-- CHANGED
    save_chat, save_file_doubt, save_quiz_response, save_user_progress, get_user_progress,
    setup_db_schema # <-- ADDED if you want to run schema setup from app
)

st.set_page_config(page_title="AI Tutor Platform", layout="wide")


# -----------------------------
# Session state initialization
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "score_history" not in st.session_state:
    st.session_state.score_history = []
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

st.title("🎓 AI Tutor Platform") # Updated emoji for title
# Update the caption to reflect the use of Gemini
st.caption("Powered by GROQ")

# ------------------
# Tabs Declaration
# ------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "💬 Chat Tutor", # Updated emoji
    "📂 Doubt from File", # Updated emoji
    "✍️ Quiz Generator", # Updated emoji
    "📈 Progress Tracker" # Updated emoji
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
                response = ask_tutor(user_input)
                st.session_state.chat_history.append(("user", user_input))
                st.session_state.chat_history.append(("ai", response))
                # Call to save chat to DB
                save_chat(st.session_state.user_id, user_input, response)
        else:
            st.warning("Please enter a question.")

    if st.session_state.chat_history:
        st.markdown("#### Conversation History")
        # Display chat history in reverse order to show latest messages at the bottom
        for role, msg in reversed(st.session_state.chat_history):
            if role == "user":
                st.markdown(f"**👤 You:** {msg}") # Updated emoji
            else:
                st.markdown(f"**🤖 AI:** {msg}") # Updated emoji

    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun() # Use st.rerun() to clear chat input and history display immediately

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
                answer = solve_doubt_from_file(tmp_file_path, file_question)
            
            # Clean up the temporary file after processing
            os.unlink(tmp_file_path)

            st.success("Answer:")
            st.write(answer)
            # Call to save file doubt to DB
            save_file_doubt(st.session_state.user_id, uploaded_file.name, file_question, answer)
        else:
            st.warning("Please upload a file and enter a question.")

# ----------------------------
# 📝 Tab 3: Quiz Generator
# ----------------------------
with tab3:
    st.subheader("📝 Generate a Subject Quiz") # Updated emoji

    subject = st.selectbox("Select a subject:", ["Math", "Science", "History", "Geography", "English"], key="quiz_subject_select") # Added key
    num_questions = st.slider("Number of questions:", min_value=1, max_value=10, value=3, key="quiz_num_questions_slider") # Added key

    if st.button("Generate Quiz", key="generate_quiz_button"): # Added key
        with st.spinner("Generating quiz..."):
            quiz = generate_quiz(subject, num_questions)

            # Check for error message returned by generate_quiz
            if quiz and "question" in quiz[0] and "[ERROR]" in quiz[0]["question"]:
                st.error(quiz[0]["question"])
                st.session_state.quiz_questions = [] # Clear previous questions on error
                st.session_state.quiz_submitted = False
            else:
                st.session_state.quiz_questions = quiz
                st.session_state.quiz_submitted = False # Reset submission status for new quiz

            # Only show raw output if quiz generation was successful or for debugging purposes
            # st.markdown("#### 🛠️ Raw Quiz Output (Debugging)")
            # st.code(json.dumps(quiz, indent=2), language="json")


    if st.session_state.quiz_questions:
        if not st.session_state.quiz_submitted: # Only show quiz if not submitted yet
            st.subheader("📚 Answer the Questions") # Updated emoji
            user_answers = []
            
            # Use a dictionary to store user selections to handle re-renders more robustly
            if "current_quiz_selections" not in st.session_state:
                st.session_state.current_quiz_selections = {f"quiz_q_{i}": None for i in range(len(st.session_state.quiz_questions))}


            for i, q in enumerate(st.session_state.quiz_questions):
                st.markdown(f"**Q{i + 1}: {q['question']}**")
                options = q["options"]
                
                # Check if options are valid (e.g., list of 4 strings)
                if not isinstance(options, list) or len(options) != 4 or not all(isinstance(opt, str) for opt in options):
                    st.error(f"Invalid options for Q{i+1}. Please regenerate quiz. Raw options: {options}")
                    # You might want to break or handle this more gracefully, e.g., clear quiz_questions
                    continue

                # Use a unique key for each radio button, pre-select if already answered
                selected_option = st.radio(
                    f"Your answer for Q{i + 1}:", 
                    options, 
                    index=options.index(st.session_state.current_quiz_selections[f"quiz_q_{i}"]) if st.session_state.current_quiz_selections[f"quiz_q_{i}"] in options else None,
                    key=f"quiz_q_{i}" # Use the same key as stored in session state
                )
                st.session_state.current_quiz_selections[f"quiz_q_{i}"] = selected_option


            if st.button("Submit Quiz", key="submit_quiz_button"): # Added key
                # Collect user answers from session state after submission button is pressed
                user_answers = [st.session_state.current_quiz_selections[f"quiz_q_{i}"] for i in range(len(st.session_state.quiz_questions))]

                st.session_state.quiz_submitted = True
                score = 0
                total_questions = len(st.session_state.quiz_questions)

                st.markdown("### 📊 Results:")

                # Loop through quiz questions and user answers to display results
                for i, q in enumerate(st.session_state.quiz_questions):
                    question_text = q.get("question", f"Question {i + 1}")
                    correct_answer = q.get("answer", "").strip().lower()
                    user_answer = user_answers[i] if user_answers[i] is not None else "" # Handle unselected answers
                    user_answer_cleaned = user_answer.strip().lower()

                    st.markdown(f"**Q{i + 1}: {question_text}**")

                    if not user_answer:
                        st.warning("❗ You did not select an answer.")
                    elif user_answer_cleaned == correct_answer:
                        st.success(f"✅ Your answer: **{user_answer}**")
                        score += 1
                    else:
                        st.error(f"❌ Your answer: **{user_answer}**")
                        st.info(f"✅ Correct answer: **{q.get('answer', 'N/A')}**") # Show original case of correct answer

                    st.markdown("---")

                st.success(f"🏁 Final Score: **{score} / {total_questions}**")

                # Save quiz response to DB
                save_quiz_response(
                    st.session_state.user_id,
                    subject,
                    st.session_state.quiz_questions,
                    user_answers
                )

                # Save user progress to DB
                save_user_progress(
                    st.session_state.user_id,
                    subject,
                    score,
                    total_questions
                )

                # Append to session state for progress tracker (if needed for immediate display)
                st.session_state.score_history.append({
                    "subject": subject,
                    "score": score,
                    "total": total_questions,
                    "accuracy": round(score / total_questions * 100, 2) if total_questions > 0 else 0
                })
        else: # If quiz has been submitted, just display results (or hide quiz)
            st.info("Quiz already submitted. Generate a new quiz to continue.")
            # You might want to re-display the results here, or just let the user generate a new quiz.
            # For simplicity, if submitted, just show info. The progress tracker will have the score.

# ----------------------------
# 📊 Tab 4: Progress Tracker
# ----------------------------
with tab4:
    st.subheader("Quiz Performance Over Time")

    # Fetch fresh progress data from DB
    progress_data_from_db = get_user_progress(st.session_state.user_id)
    
    if progress_data_from_db:
        # Create DataFrame from fetched data
        df = pd.DataFrame(progress_data_from_db)
        df['accuracy'] = df['accuracy'].astype(float)
        
        # Ensure 'timestamp' is datetime for better charting options
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        # Sort by timestamp to show progress over time correctly
        df = df.sort_values(by='timestamp')

        # Create a line chart for overall accuracy trend
        chart_overall = alt.Chart(df).mark_line(point=True).encode(
            x=alt.X('timestamp:T', title="Date of Quiz"), # Use timestamp for x-axis
            y=alt.Y('accuracy:Q', title="Accuracy (%)", scale=alt.Scale(domain=[0, 100])), # Scale Y to 0-100
            color=alt.Color('subject:N', title="Subject"), # Color lines by subject
            tooltip=[
                alt.Tooltip('timestamp:T', title='Date'),
                'subject',
                'score',
                'total',
                alt.Tooltip('accuracy:Q', format='.2f', title='Accuracy (%)')
            ]
        ).properties(
            title="Overall Quiz Accuracy Trend"
        ).interactive() # Make chart interactive for zooming/panning

        st.altair_chart(chart_overall, use_container_width=True)

        # Optionally, display a bar chart for average accuracy per subject
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

