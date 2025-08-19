from pathlib import Path
import fitz
import pytesseract
from PIL import Image
from ai_tutor_platform.llm.mistral_chain import generate_response 

def solve_doubt(context: str, question: str) -> str:
    """
    Uses provided file content (`context`) to answer a specific question.
    """
    if not context.strip() or not question.strip():
        return "Both file content and question must be provided."

    prompt = (
        f"Here is the context from the user's uploaded file:\n\n"
        f"{context}\n\n"
        f"Based on the above, answer the following question:\n{question}"
    )

    try:
        return generate_response(prompt)
    except Exception as e:
        return f"[ERROR] {str(e)}"


def extract_text_from_file(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    elif ext in [".png", ".jpg", ".jpeg"]:
        return extract_text_from_image(file_path)
    else:
        return "[ERROR] Unsupported file format."


def extract_text_from_pdf(file_path: str) -> str:
    try:
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text.strip()
    except Exception as e:
        return f"[ERROR reading PDF] {str(e)}"


def extract_text_from_txt(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"[ERROR reading TXT] {str(e)}"


def extract_text_from_image(file_path: str) -> str:
    try:
        img = Image.open(file_path)
        return pytesseract.image_to_string(img)
    except Exception as e:
        return f"[ERROR OCR image] {str(e)}"


def solve_doubt_from_file(file_path: str, question: str) -> str:
    context = extract_text_from_file(file_path)
    if context.startswith("[ERROR"):
        return context

    if not context.strip() or not question.strip():
        return "Both file content and question must be provided."

    prompt = (
        f"Here is the content extracted from the uploaded file:\n\n"
        f"{context}\n\n"
        f"Based on this content, answer the following question:\n{question}"
    )

    try:
        return generate_response(prompt)
    except Exception as e:
        return f"[ERROR LLM] {str(e)}"