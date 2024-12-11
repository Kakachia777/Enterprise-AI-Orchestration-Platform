import pytest
from unittest.mock import Mock, patch
import asyncio
from datetime import datetime

from src.core.orchestrator import AIOrchestrator
from src.core.config import ConfigManager

@pytest.fixture
def orchestrator():
    with patch('src.core.orchestrator.ConfigManager') as mock_config:
        mock_config.return_value.get_config.return_value = {
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "test.log"
            },
            "mlflow": {
                "tracking_uri": "http://localhost:5000",
                "experiment_name": "test_experiment"
            }
        }
        yield AIOrchestrator()

@pytest.mark.asyncio
async def test_initialize_models(orchestrator):
    """Test model initialization"""
    with patch.object(orchestrator, 'models', {}):
        success = await orchestrator.initialize_models()
        assert success is True
        assert "gpt4o" in orchestrator.models
        assert "vision" in orchestrator.models
        assert orchestrator.embeddings_model is not None

@pytest.mark.asyncio
async def test_process_text_gpt4o(orchestrator):
    """Test GPT-4o text processing"""
    mock_response = {"response": "Test response", "processing_time": 0.5}
    
    with patch.object(orchestrator, '_process_with_gpt4o') as mock_process:
        mock_process.return_value = mock_response
        result = await orchestrator.process_text("Test input", "gpt4o")
        
        assert result == mock_response
        mock_process.assert_called_once_with("Test input")

@pytest.mark.asyncio
async def test_process_text_embeddings(orchestrator):
    """Test text embeddings processing"""
    mock_embeddings = [0.1, 0.2, 0.3]
    
    with patch.object(orchestrator, '_get_embeddings') as mock_process:
        mock_process.return_value = {
            "embeddings": mock_embeddings,
            "processing_time": 0.1
        }
        result = await orchestrator.process_text("Test input", "embeddings")
        
        assert "embeddings" in result
        assert result["embeddings"] == mock_embeddings
        mock_process.assert_called_once_with("Test input")

@pytest.mark.asyncio
async def test_process_image(orchestrator):
    """Test image processing"""
    mock_results = [
        {"label": "person", "confidence": 0.95, "bbox": [0, 0, 100, 100]}
    ]
    
    with patch.dict(orchestrator.models, {"vision": Mock()}):
        orchestrator.models["vision"].return_value = mock_results
        result = await orchestrator.process_image("test_image.jpg")
        
        assert "results" in result
        assert result["results"] == mock_results
        assert "processing_time" in result

def test_get_model_status(orchestrator):
    """Test model status checking"""
    with patch.dict(orchestrator.models, {
        "gpt4o": Mock(),
        "vision": Mock()
    }):
        orchestrator.embeddings_model = Mock()
        status = orchestrator.get_model_status()
        
        assert status["gpt4o"] is True
        assert status["vision"] is True
        assert status["embeddings"] is True

@pytest.mark.asyncio
async def test_process_text_invalid_type(orchestrator):
    """Test processing text with invalid task type"""
    with pytest.raises(ValueError):
        await orchestrator.process_text("Test input", "invalid_type") 