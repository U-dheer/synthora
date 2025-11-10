from fastapi import FastAPI
import uvicorn
from src.routes.summerize_route import router as summarize_router

app = FastAPI(
    title="AI Summarizer API",
    description="API for text summarization using Gemini",
    version="0.0.1"
)

# Include routers
app.include_router(summarize_router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to AI Summarizer API",
        "docs": "/docs",
        "endpoints": {
            "summarize_ai_prompts": "/api/summarize/ai-prompts",
            "summarize_text": "/api/summarize/text",
            "invoke_prompt": "/api/summarize/invoke",
            "health_check": "/api/summarize/health"
        }
    }

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
