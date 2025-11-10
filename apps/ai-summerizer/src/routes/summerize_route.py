from fastapi import APIRouter, HTTPException
from ..services.summerize_service import summarize_service
from ..dtos.response_dto import PromptRequest, SummarizeRequest, ResponseModel, AIPromptsRequest

router = APIRouter(prefix="/api/summarize", tags=["summarize"])


@router.post("/invoke", response_model=ResponseModel)
async def invoke_gemini_prompt(request: PromptRequest):
    """
    Invoke Gemini with a custom prompt
    
    Args:
        request: Contains the prompt and optional system message
        
    Returns:
        The generated response from Gemini
    """
    try:
        result = await summarize_service.invoke_prompt(
            prompt=request.prompt,
            system_message=request.system_message
        )
        return ResponseModel(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-prompts", response_model=ResponseModel)
async def summarize_ai_prompts(request: AIPromptsRequest):
    """
    Receive three AI prompts (ai1, ai2, ai3), stringify the JSON, 
    and summarize all three prompts into a single comprehensive response
    
    Args:
        request: Contains ai1, ai2, ai3 prompt strings
        
    Returns:
        A single summarized response combining all three prompts
    """
    try:
        result = await summarize_service.summarize_ai_prompts(ai_prompts=request)
        return ResponseModel(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text", response_model=ResponseModel)
async def summarize_text(request: SummarizeRequest):
    """
    Summarize the provided text using Gemini
    
    Args:
        request: Contains the text to summarize
        
    Returns:
        A summary of the text
    """
    try:
        result = await summarize_service.summarize_text(text=request.text)
        return ResponseModel(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Check if the summarize service is healthy
    """
    try:
        # Simple check to verify the service is initialized
        if summarize_service.model:
            return {"status": "healthy", "message": "Gemini service is running"}
        else:
            raise HTTPException(status_code=503, detail="Gemini service not initialized")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
