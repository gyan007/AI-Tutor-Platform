from ai_tutor_platform.llm.mistral_chain import generate_response

def ask_tutor(question: str) -> str:
    """
    Takes a user's question and gets a response from the LLM.
    """
    if not question or not question.strip():
        return "Please enter a valid question."

    try:
        return generate_response(question)
    except Exception as e:
        return f"An error occurred while processing your question: {str(e)}"