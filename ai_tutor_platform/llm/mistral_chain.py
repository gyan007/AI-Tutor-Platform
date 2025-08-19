import os
from langchain_groq import ChatGroq # Correct import for Groq
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough # For chaining in newer LangChain versions if needed, or stick to LLMChain
# If you are using LangChain 0.2.x+ and prefer the new LCEL syntax directly
# from langchain_core.output_parsers import StrOutputParser

from ai_tutor_platform.config.configuration import config_instance # Import the config instance

class LLMChainWrapper:
    def __init__(self):
        # Load API key and model name from the centralized config
        groq_api_key = config_instance.get_groq_api_key() # <-- Call the method
        groq_model_name = config_instance.get_groq_model_name() # <-- Call the method
        temperature = config_instance.get_temperature() # Get temperature from config

        # Ensure API key is available
        if not groq_api_key: # Check for empty string or None
            raise ValueError("Groq API key is not set. Please set the GROQ_API_KEY environment variable.")

        # Initialize ChatGroq with the API key and chosen model
        self.llm = ChatGroq(
            temperature=temperature, # Use configured temperature
            groq_api_key=groq_api_key,
            model_name=groq_model_name
        )
        
        # Define a flexible prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are an AI tutor designed to help students learn and solve problems."),
            ("user", "{question}")
        ])
        
        # Combine the prompt and LLM into a chain
        # Using LCEL (LangChain Expression Language) for robust chaining
        self.chain = self.prompt_template | self.llm # | StrOutputParser() if you want to explicitly parse to string

    def generate_response(self, prompt: str) -> str:
        """
        Generates a raw string response from the LLM without formatting (no markdown or code blocks).
        """
        try:
            response = self.chain.invoke({"question": prompt})
            # LangChain 0.2.x+ returns AIMessage objects, access content via .content
            return response.content.strip()
        except Exception as e:
            return f"[ERROR] {str(e)}"

# Make an instance globally available if other modules import generate_response directly
llm_wrapper_instance = LLMChainWrapper()
generate_response = llm_wrapper_instance.generate_response
