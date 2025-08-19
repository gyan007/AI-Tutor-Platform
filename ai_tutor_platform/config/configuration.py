import configparser
import os

class Config:
    def __init__(self):
        # Construct the path to config.ini relative to the current file
        # This assumes config.ini is in ai_tutor_platform/data/
        # base_path will be C:\Users\gyant\Desktop\ai_tutor_platform\ai_tutor_platform
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_path, "data", "config.ini")

        self.config = configparser.ConfigParser()
        # Read the configuration file. If it doesn't exist, the config object will be empty.
        self.config.read(config_path)

    def get_llm_model(self):
        # Get LLM model from config.ini, default to "gemini-pro"
        return self.config["GENERAL"].get("llm_model", "gemini-pro")

    def get_temperature(self):
        # Get temperature from config.ini, default to 0.7, ensure it's a float
        return float(self.config["GENERAL"].get("temperature", "0.7"))

    def get_api_base(self):
        # Get API base URL from config.ini, default to Gemini's standard endpoint
        # Remove the markdown link formatting from the default string
        return self.config["GENERAL"].get("api_base", "https://generativelanguage.googleapis.com/")

    def get_api_key(self):
        # Prioritize fetching the API key from environment variables (GOOGLE_API_KEY)
        # If not found in environment, then try to get it from config.ini
        # If still not found, return None or an empty string, letting the LLM client handle the error
        api_key_env = os.getenv("GOOGLE_API_KEY")
        if api_key_env:
            return api_key_env
        else:
            return self.config["GENERAL"].get("api_key", None) # Default to None if not found