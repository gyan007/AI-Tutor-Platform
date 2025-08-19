import os
from langchain_groq import ChatGroq # Correct import for Groq
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from ai_tutor_platform.config.configuration import config_instance # Import the config instance

class LLMChainWrapper:
    def __init__(self):
        # Load API key and model name from the centralized config
        groq_api_key = config_instance.get_groq_api_key
        groq_model_name = config_instance.get_groq_model_name

        # Ensure API key is available
        if not groq_api_key: # Check for empty string or None
            raise ValueError("Groq API key is not set. Please set it in .streamlit/secrets.toml or config.ini for local dev.")

        # Initialize ChatGroq with the API key and chosen model
        self.llm = ChatGroq(
            temperature=0.7, # Default temperature, can be made configurable if needed
            groq_api_key=groq_api_key,
            model_name=groq_model_name
        )
        
        # Define a flexible prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an AI tutor designed to help students learn and solve problems."),
            ("user", "{question}")
        ])
        
        # Combine the prompt and LLM into a chain
        self.chain = self.prompt_template | self.llm

    def generate_response(self, prompt: str) -> str:
        """
        Generates a raw string response from the LLM without formatting (no markdown or code blocks).
        """
        try:
            response = self.chain.invoke({"question": prompt})
            return response.content.strip()
        except Exception as e:
            return f"[ERROR] {str(e)}"
