from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any, Optional
import uvicorn
import json
from pathlib import Path
import aiofiles
import logging

from ..core.orchestrator import AIOrchestrator
from ..core.config import ConfigManager

app = FastAPI(
    title="Enterprise AI Orchestration Platform",
    description="A sophisticated AI platform that orchestrates multiple AI models and services",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize configuration and orchestrator
config = ConfigManager()
orchestrator = AIOrchestrator()

@app.on_event("startup")
async def startup_event():
    """Initialize models and services on startup"""
    success = await orchestrator.initialize_models()
    if not success:
        logging.error("Failed to initialize models")
        raise RuntimeError("Failed to initialize AI models")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models": orchestrator.get_model_status()
    }

@app.post("/api/v1/process/text")
async def process_text(
    text: str,
    task_type: str,
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """Process text using specified AI model"""
    try:
        result = await orchestrator.process_text(text, task_type)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/process/image")
async def process_image(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """Process image using vision model"""
    try:
        # Save uploaded file
        file_path = Path("data/interim") / file.filename
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        # Process image
        result = await orchestrator.process_image(str(file_path))
        
        # Clean up
        file_path.unlink()
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/models/status")
async def get_model_status(
    token: str = Depends(oauth2_scheme)
) -> Dict[str, bool]:
    """Get status of all models"""
    return orchestrator.get_model_status()

if __name__ == "__main__":
    api_config = config.get_api_config()
    uvicorn.run(
        "main:app",
        host=api_config["host"],
        port=api_config["port"],
        reload=api_config["debug"]
    ) 