from pydantic import BaseModel
from typing import Optional
import json


class AIPromptsRequest(BaseModel):
    """Request model with three AI prompts"""
    ai1: str
    ai2: str
    ai3: str
    
    def to_stringified_json(self) -> str:
        """Convert the request to a stringified JSON"""
        return json.dumps(self.model_dump(), ensure_ascii=False)
    
    def get_all_prompts(self) -> list[str]:
        """Get all prompts as a list"""
        return [self.ai1, self.ai2, self.ai3]


class PromptRequest(BaseModel):
    """Request model for custom prompts"""
    prompt: str
    system_message: Optional[str] = None


class SummarizeRequest(BaseModel):
    """Request model for text summarization"""
    text: str


class ResponseModel(BaseModel):
    """Generic response model"""
    result: str
