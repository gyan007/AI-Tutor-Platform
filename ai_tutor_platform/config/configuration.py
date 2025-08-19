import configparser
import os

class Config:
    def __init__(self):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_path, "data", "config.ini")

        self.config = configparser.ConfigParser()
        self.config.read(config_path)

    def get_llm_model(self):
        # This can be used as a generic LLM model name, e.g., for general context
        return self.config["GENERAL"].get("llm_model", "llama3-8b-8192") # Default to a common Groq model

    def get_temperature(self):
        return float(self.config["GENERAL"].get("temperature", "0.7"))

    def get_api_base(self):
        # This might not be strictly needed for Groq as `ChatGroq` handles it internally,
        # but keep it if other LLM clients might use it.
        return self.config["GENERAL"].get("api_base", "https://api.groq.com/openai/v1")

    def get_groq_api_key(self): # Renamed for clarity to match Groq usage
        # Prioritize fetching the API key from environment variables (GROQ_API_KEY)
        # If not found, then try to get it from config.ini (less secure for production)
        api_key_env = os.getenv("GROQ_API_KEY") # <-- Use GROQ_API_KEY environment variable
        if api_key_env:
            return api_key_env
        else:
            return self.config["GENERAL"].get("api_key", None) # Fallback to config.ini for dev

    def get_groq_model_name(self): # Added specific method for Groq model name
        # Prioritize environment variable for model name, or fallback to config.ini
        model_name_env = os.getenv("GROQ_MODEL_NAME") # <-- Use GROQ_MODEL_NAME environment variable
        if model_name_env:
            return model_name_env
        else:
            return self.config["GENERAL"].get("llm_model", "llama3-8b-8192") # Fallback to config.ini, use a Groq model default

# Create a single instance of the Config class to be imported throughout the app
config_instance = Config()
