from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import uvicorn
from contextlib import asynccontextmanager

from rag_engine import FIHRulesEngine
from logger import get_logger

logger = get_logger(__name__)

# Global engine instance
engine: Optional[FIHRulesEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the RAG engine on startup."""
    global engine
    try:
        logger.info("Initializing FIH Rules Engine...")
        engine = FIHRulesEngine()
        logger.info("Engine initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize engine: {e}", exc_info=True)
        # We don't raise here to allow the health check to return 503 instead of crashing
    yield
    # Cleanup if needed

app = FastAPI(title="FIH Rules API", lifespan=lifespan)

# CORS Configuration
# Create a list of allowed origins. In production, this should be specific.
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Security ---
API_KEY = os.getenv("API_KEY", "dev-secret-key")

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# --- Data Models ---

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: str
    history: List[Message] = []

class SourceDoc(BaseModel):
    page_content: str
    metadata: Dict[str, Any]

class ChatResponse(BaseModel):
    answer: str
    standalone_query: str
    variant: str
    source_docs: List[SourceDoc]

# --- Endpoints ---

@app.get("/health")
async def health_check():
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    return {"status": "healthy", "service": "fih-rules-api"}

@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
async def chat(request: ChatRequest):
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not ready")
    
    try:
        # Convert Pydantic models to dicts/tuples expected by engine
        history_list = [(m.role, m.content) for m in request.history]
        
        result = engine.query(request.query, history=history_list)
        
        # Transform result for response
        # engine.query returns dict with keys: answer, standalone_query, variant, source_docs
        # source_docs are LangChain Documents, need to convert to Pydantic
        
        source_docs_data = [
            SourceDoc(page_content=doc.page_content, metadata=doc.metadata) 
            for doc in result["source_docs"]
        ]
        
        return ChatResponse(
            answer=result["answer"],
            standalone_query=result["standalone_query"],
            variant=result["variant"],
            source_docs=source_docs_data
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/evals/latest", dependencies=[Depends(verify_api_key)])
async def get_latest_evals():
    """Return the latest evaluation results (placeholder for now)."""
    # TODO: Read from a persistent JSON file or DB table
    return {
        "timestamp": "2023-10-27T10:00:00Z",
        "metrics": {
            "accuracy": 0.85,
            "retrieval_hit_rate": 0.92,
            "latency_p95": 1.2
        }
    }

# Serve React static files (Production)
# This assumes the build output is copied to 'static' folder (see Dockerfile.public)
from fastapi.staticfiles import StaticFiles
if os.path.exists("static"):
    logger.info("Serving static files from 'static' directory")
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
