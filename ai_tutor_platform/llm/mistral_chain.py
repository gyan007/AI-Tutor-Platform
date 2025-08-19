from langchain_google_genai import ChatGoogleGenerativeAI # <<<--- THIS IS THE CORRECT IMPORT
from langchain.schema import HumanMessage
from ai_tutor_platform.config.configuration import Config

lobj_config = Config()

def get_gemini_llm():
    return ChatGoogleGenerativeAI(
        model=lobj_config.get_llm_model(),
        temperature=lobj_config.get_temperature(),
    )
def generate_response(prompt: str) -> str:
    """
    Generates a raw string response from the LLM without formatting (no markdown or code blocks).
    """
    llm = get_gemini_llm()

    messages = [
        HumanMessage(content=f"{prompt}")
    ]

    try:
        response = llm.invoke(messages)
        cleaned = response.content.strip()

        # Keep the cleaning logic as Gemini models can also output markdown/code blocks
        if cleaned.startswith("```"):
            # Remove triple backticks and optional 'json'
            cleaned = cleaned.lstrip("`").lstrip("json").strip()
            cleaned = cleaned.rstrip("`").strip()

        return cleaned
    except Exception as e:
        return f"[ERROR] {str(e)}"