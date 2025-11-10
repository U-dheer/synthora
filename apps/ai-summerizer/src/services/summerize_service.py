import os
import json
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage

from src.constansts.summerize_systemPromt import SYSTEM_PROMPT
from ..dtos.response_dto import AIPromptsRequest

# Load environment variables
load_dotenv()

class SummarizeService:
    def __init__(self):
        """Initialize the Gemini model"""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        os.environ["GOOGLE_API_KEY"] = self.api_key
        self.model = init_chat_model("google_genai:gemini-2.5-flash-lite")
    
    async def invoke_prompt(self, prompt: str, system_message: str = None) -> str:
        """
        Invoke Gemini with a prompt and return the result
        
        Args:
            prompt: The user prompt to send to Gemini
            system_message: Optional system message to set context
            
        Returns:
            The generated response from Gemini
        """
        try:
            messages = []
            
            if system_message:
                messages.append(SystemMessage(content=system_message))
            
            messages.append(HumanMessage(content=prompt))
            
            response = self.model.invoke(messages)
            return response.content
        
        except Exception as e:
            raise Exception(f"Error invoking Gemini: {str(e)}")
    
    async def summarize_ai_prompts(self, ai_prompts: AIPromptsRequest) -> str:
        """
        Take three AI prompts (ai1, ai2, ai3), stringify the JSON, and summarize all three prompts into a single response
        
        Args:
            ai_prompts: AIPromptsRequest containing ai1, ai2, ai3 prompts
            
        Returns:
            A single summarized response combining insights from all three prompts
        """
        try:
            # Stringify the JSON
            stringified_json = ai_prompts.to_stringified_json()
            
            # Create a comprehensive prompt for summarization
            system_message = SYSTEM_PROMPT
            
            user_prompt = f"""Here are three prompts in JSON format:
{stringified_json}

Please analyze these three prompts and provide a single, comprehensive response that addresses all of them together. 
Synthesize the information and provide a cohesive answer."""
            
            response = await self.invoke_prompt(user_prompt, system_message)
            return response
        
        except Exception as e:
            raise Exception(f"Error summarizing AI prompts: {str(e)}")
    
    async def summarize_text(self, text: str) -> str:
        """
        Summarize the given text using Gemini
        
        Args:
            text: The text to summarize
            
        Returns:
            A summary of the text
        """
        system_message = "You are a helpful assistant that provides concise and accurate summaries of text."
        prompt = f"Please summarize the following text:\n\n{text}"
        
        return await self.invoke_prompt(prompt, system_message)

# Singleton instance
summarize_service = SummarizeService()
