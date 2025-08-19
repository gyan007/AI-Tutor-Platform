import json
import re
from typing import List, Dict, Any # Kept Dict and Any for completeness, though QuizItem ensures specific types
from pydantic import BaseModel, ValidationError, field_validator, model_validator
# Update the import path for the LLM integration module
# If you renamed 'mistral_chain.py' to 'gemini_chain.py' or similar:
# from ai_tutor_platform.llm.gemini_chain import generate_response
# Otherwise, if you only changed its content but kept the filename:
from ai_tutor_platform.llm.mistral_chain import generate_response # This line is correct if filename not changed


class QuizItem(BaseModel):
    question: str
    options: List[str]
    answer: str

    @field_validator("options")
    def validate_options(cls, options):
        if not isinstance(options, list) or len(options) != 4:
            raise ValueError("There must be exactly 4 options.")
        return [opt.strip(" ,.:;\"") for opt in options]

    @model_validator(mode="after")
    def check_answer_in_options(self):
        answer_clean = self.answer.strip(" ,.:;\"").lower()
        options_clean = [opt.strip(" ,.:;\"").lower() for opt in self.options]
        if answer_clean not in options_clean:
            raise ValueError(f"Answer '{self.answer}' not found in options.")
        return self


def extract_json_array(text: str) -> str:
    # Remove code blocks
    text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()

    # Extract JSON array
    match = re.search(r'\[\s*{.*?}\s*\]', text, re.DOTALL)
    if not match:
        raise ValueError("No valid JSON array found in LLM output.")
    json_str = match.group(0)

    # Fix common formatting issues
    json_str = re.sub(r",\s*}", "}", json_str)
    json_str = re.sub(r",\s*]", "]", json_str)
    json_str = json_str.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    json_str = re.sub(r'"\s*"(.*?)"\s*"', r'"\1"', json_str)
    json_str = re.sub(r'\\(?![ntr"\\/bfu])', r'\\\\', json_str) # Escape backslashes correctly for JSON

    return json_str


def clean_dict_keys(data: list) -> list:
    cleaned = []
    for item in data:
        if isinstance(item, dict):
            cleaned_item = {k.strip(): v for k, v in item.items()}
            cleaned.append(cleaned_item)
    return cleaned


def parse_options(raw_options):
    if isinstance(raw_options, str):
        # Handle cases where options might be a single comma-separated string
        return [opt.strip() for opt in raw_options.split(",") if opt.strip()]
    elif isinstance(raw_options, list):
        # Ensure list items are strings and then strip them
        return [opt.strip(" ,.:;\"") for opt in raw_options if isinstance(opt, str)]
    return []


def generate_quiz(subject: str, num_questions: int = 5, max_retries: int = 3) -> list:
    # Enhanced prompt for Gemini to encourage robust JSON output
    prompt_template = (
        "Generate exactly {num} multiple-choice questions on the topic '{subject}'.\n"
        "Each question must have exactly 4 distinct options and one clearly correct answer.\n"
        "The correct answer must be one of the 4 options provided in the 'options' list.\n"
        "Ensure the 'answer' field matches one of the 'options' exactly.\n"
        "Respond with ONLY a valid JSON array. Do NOT include any introductory text, explanations, code blocks (like ```json), or markdown outside the JSON.\n"
        "Avoid emojis, LaTeX, or any other special characters not standard in plain text.\n"
        "Example JSON format:\n"
        "[\n"
        "  {{\n"
        "    \"question\": \"What is the capital of France?\",\n"
        "    \"options\": [\"London\", \"Berlin\", \"Paris\", \"Rome\"],\n"
        "    \"answer\": \"Paris\"\n"
        "  }}\n"
        "]"
    )

    valid_questions = []

    for attempt in range(max_retries):
        needed = num_questions - len(valid_questions)
        if needed <= 0:
            break

        prompt = prompt_template.format(subject=subject, num=needed)

        try:
            raw_output = generate_response(prompt)
            print(f"\n==== RAW LLM OUTPUT (Attempt {attempt + 1}) ====\n", raw_output)

            cleaned_json_str = extract_json_array(raw_output)
            print(f"\n==== CLEANED JSON (Attempt {attempt + 1}) ====\n", cleaned_json_str)

            quiz_data = json.loads(cleaned_json_str)
            quiz_data = clean_dict_keys(quiz_data)

            for i, item in enumerate(quiz_data):
                try:
                    question = item.get("question", "").strip()
                    raw_options = item.get("options", [])
                    answer = item.get("answer", "").strip()
                    options = parse_options(raw_options) # Use the helper for robustness

                    # Validate the QuizItem using the Pydantic model
                    quiz_item = QuizItem(question=question, options=options, answer=answer)

                    # Append only validated items
                    valid_questions.append({
                        "question": quiz_item.question,
                        "options": quiz_item.options,
                        "answer": quiz_item.answer # Already stripped/cleaned by Pydantic model
                    })

                    if len(valid_questions) >= num_questions:
                        break # Stop if we have enough valid questions
                except ValidationError as e:
                    print(f"⚠️ Skipped question from LLM output (index {i}) due to Pydantic validation error: {e}")
                except Exception as e:
                    print(f"⚠️ Skipped question from LLM output (index {i}) due to unexpected error: {e}")


        except ValueError as ve: # Catch specific ValueError from extract_json_array or json.loads
            print(f"💥 Error parsing LLM output (Attempt {attempt + 1}): {ve}. Raw: {raw_output[:200]}...")
        except Exception as e: # Catch other general errors from generate_response or other steps
            print(f"💥 General error in LLM generation process (Attempt {attempt + 1}): {e}")

    if not valid_questions:
        return [{
            "question": "[ERROR] No valid questions could be generated after multiple attempts. Please try a different topic or adjust LLM parameters.",
            "options": [],
            "answer": ""
        }]
    elif len(valid_questions) < num_questions:
        print(f"⚠️ WARNING: Only {len(valid_questions)} valid questions recovered out of {num_questions} requested.")
        # Return the partial list with a warning in the first item if less than requested
        return [{
            "question": f"[WARNING] Only {len(valid_questions)} valid questions could be generated out of {num_questions} requested.",
            "options": [],
            "answer": ""
        }] + valid_questions # Prepend warning and return the valid ones
    
    return valid_questions