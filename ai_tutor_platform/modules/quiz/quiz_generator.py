import json
import re
from typing import List, Dict, Any
from pydantic import BaseModel, ValidationError, field_validator, model_validator
from ai_tutor_platform.llm.mistral_chain import generate_response

# Re-define QuizItem, extract_json_array, clean_dict_keys, parse_options if they are within this file's scope
# Assuming they are defined in the same file as generate_quiz as per your previous context.

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
    # Remove common LLM non-JSON elements like code blocks.
    # Updated regex to be more robust for potential surrounding text.
    # It attempts to find the first JSON array.
    
    # Attempt to remove code block markers first
    text = re.sub(r"```(?:json)?", "", text, flags=re.DOTALL).strip()

    # Look for a top-level JSON array
    match = re.search(r'\[\s*\{.*?\}\s*\]', text, re.DOTALL)
    if not match:
        # If a full array isn't found, try to find a list of objects
        # This might capture partial output but could be useful for debugging
        match = re.search(r'(\[\s*\{.*?\}\s*(?:,\s*\{.*?\}\s*)*\])', text, re.DOTALL)
        if not match:
            # If still no array, try to find individual objects and wrap them (risky)
            # This is a last resort to try and salvage something
            objects = re.findall(r'\{\s*".*?":\s*".*?".*?\}', text, re.DOTALL)
            if objects:
                text = f"[{','.join(objects)}]" # Wrap found objects in an array
                match = re.search(r'\[\s*\{.*?\}\s*\]', text, re.DOTALL)
                if not match: return "" # Still no valid array
            else:
                return "" # No JSON-like structure found at all

    json_str = match.group(0) if match else "" # Ensure json_str is empty if no match

    # Fix common formatting issues
    json_str = re.sub(r",\s*}", "}", json_str)
    json_str = re.sub(r",\s*]", "]", json_str)
    json_str = json_str.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    # This regex attempts to fix escaped quotes that might be doubled or malformed.
    # More aggressively, it handles some common LLM quirks, but can be brittle.
    json_str = re.sub(r'(?<!\\)"(?!\\)', r'\"', json_str) # Escape unescaped double quotes that are not part of valid JSON structure. (This might be too aggressive)
    json_str = re.sub(r"\\\"", r'"', json_str) # Correct already escaped quotes
    json_str = re.sub(r'\\(?![ntr"\\/bfu])', r'\\\\', json_str) # Escape backslashes correctly for JSON

    # Add a check for empty string or non-JSON-like string after cleaning
    if not json_str.strip() or not (json_str.strip().startswith('[') and json_str.strip().endswith(']')):
        print(f"DEBUG: extract_json_array returning empty/malformed after cleaning. Final string: '{json_str}'")
        return "" # Return empty string if it's clearly not a JSON array

    return json_str

def clean_dict_keys(data: list) -> list:
    cleaned = []
    for item in data:
        if isinstance(item, dict):
            cleaned_item = {k.strip(): v for k, v in item.items()}
            cleaned.append(cleaned_item)
        else: # Handle cases where LLM might return non-dict items in array
            print(f"⚠️ Skipped non-dictionary item in quiz_data: {item}")
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
            print(f"\n==== RAW LLM OUTPUT (Attempt {attempt + 1}) ====\n'{raw_output}'") # Added quotes for visibility of empty/whitespace

            if not raw_output.strip(): # Check for empty or whitespace-only response early
                print(f"💥 LLM returned empty or whitespace-only response on Attempt {attempt + 1}. Retrying...")
                continue # Skip to next attempt

            cleaned_json_str = extract_json_array(raw_output)
            print(f"\n==== CLEANED JSON (Attempt {attempt + 1}) ====\n'{cleaned_json_str}'") # Added quotes for visibility

            if not cleaned_json_str.strip(): # Check if cleaning resulted in empty string
                print(f"💥 No valid JSON array could be extracted from LLM output on Attempt {attempt + 1}. Retrying...")
                continue # Skip to next attempt

            try:
                quiz_data = json.loads(cleaned_json_str)
                if not isinstance(quiz_data, list): # Ensure it's a list at the top level
                    raise ValueError("JSON parsed but not a list of questions.")
            except json.JSONDecodeError as jde:
                print(f"💥 json.loads failed (Attempt {attempt + 1}): {jde}. Cleaned JSON was: '{cleaned_json_str[:200]}...'")
                continue # Skip to next attempt

            quiz_data = clean_dict_keys(quiz_data)

            for i, item in enumerate(quiz_data):
                try:
                    # Defensive parsing for required fields
                    question = item.get("question")
                    raw_options = item.get("options")
                    answer = item.get("answer")

                    if not question or not raw_options or not answer:
                        raise ValueError("Missing 'question', 'options', or 'answer' field in quiz item.")

                    question = question.strip()
                    answer = answer.strip()
                    options = parse_options(raw_options)

                    # Validate the QuizItem using the Pydantic model
                    quiz_item = QuizItem(question=question, options=options, answer=answer)

                    # Append only validated items
                    valid_questions.append({
                        "question": quiz_item.question,
                        "options": quiz_item.options,
                        "answer": quiz_item.answer
                    })

                    if len(valid_questions) >= num_questions:
                        break # Stop if we have enough valid questions
                except ValidationError as e:
                    print(f"⚠️ Skipped question from LLM output (index {i}) due to Pydantic validation error: {e}. Item: {item}")
                except ValueError as e: # Catch value errors from parsing or missing fields
                    print(f"⚠️ Skipped question from LLM output (index {i}) due to data format error: {e}. Item: {item}")
                except Exception as e:
                    print(f"⚠️ Skipped question from LLM output (index {i}) due to unexpected error during item processing: {e}. Item: {item}")


        except ValueError as ve: # Catch specific ValueError from extract_json_array or json.loads
            print(f"💥 Error in LLM output processing (Attempt {attempt + 1}): {ve}. Raw: '{raw_output[:200]}...'")
        except Exception as e: # Catch other general errors from generate_response or other steps
            print(f"💥 General error in LLM generation process (Attempt {attempt + 1}): {e}. Raw output: '{raw_output[:200]}...'")

    if not valid_questions:
        print(f"❌ Failed to generate any valid questions after {max_retries} attempts for '{subject}'.")
        return [{
            "question": "[ERROR] No valid questions could be generated after multiple attempts. Please try a different topic or adjust LLM parameters.",
            "options": [],
            "answer": ""
        }]
    elif len(valid_questions) < num_questions:
        print(f"⚠️ WARNING: Only {len(valid_questions)} valid questions recovered out of {num_questions} requested for '{subject}'.")
        return [{
            "question": f"[WARNING] Only {len(valid_questions)} valid questions could be generated out of {num_questions} requested.",
            "options": [],
            "answer": ""
        }] + valid_questions

    return valid_questions
