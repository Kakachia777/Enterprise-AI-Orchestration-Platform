from typing import Dict, Any, List, Optional
import logging
from pathlib import Path
import json
from datetime import datetime

from transformers import pipeline
from sentence_transformers import SentenceTransformer
import torch
from langchain import OpenAI
import mlflow

from .config import ConfigManager

class AIOrchestrator:
    def __init__(self):
        self.config = ConfigManager()
        self.models: Dict[str, Any] = {}
        self.embeddings_model = None
        self._setup_logging()
        self._initialize_mlflow()
        
    def _setup_logging(self):
        logging_config = self.config.get_config()["logging"]
        logging.basicConfig(
            level=logging_config["level"],
            format=logging_config["format"],
            filename=logging_config["file"]
        )
        self.logger = logging.getLogger(__name__)

    def _initialize_mlflow(self):
        mlflow_config = self.config.get_config()["mlflow"]
        mlflow.set_tracking_uri(mlflow_config["tracking_uri"])
        mlflow.set_experiment(mlflow_config["experiment_name"])

    async def initialize_models(self):
        """Initialize all AI models based on configuration"""
        try:
            # Initialize GPT-4o integration
            gpt_config = self.config.get_model_config("gpt4o")
            self.models["gpt4o"] = OpenAI(
                model_name=gpt_config["model_name"],
                temperature=gpt_config["temperature"]
            )

            # Initialize Vision Model
            vision_config = self.config.get_model_config("vision")
            self.models["vision"] = pipeline(
                "object-detection",
                model=vision_config["model_name"]
            )

            # Initialize Embeddings Model
            embeddings_config = self.config.get_model_config("embeddings")
            self.embeddings_model = SentenceTransformer(
                embeddings_config["model_name"],
                cache_folder=embeddings_config["cache_dir"]
            )

            self.logger.info("All models initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing models: {str(e)}")
            return False

    async def process_text(self, text: str, task_type: str) -> Dict[str, Any]:
        """Process text using specified AI model"""
        try:
            with mlflow.start_run():
                mlflow.log_param("task_type", task_type)
                mlflow.log_param("input_length", len(text))

                if task_type == "gpt4o":
                    response = await self._process_with_gpt4o(text)
                elif task_type == "embeddings":
                    response = self._get_embeddings(text)
                else:
                    raise ValueError(f"Unknown task type: {task_type}")

                mlflow.log_metrics({"processing_time": response.get("processing_time", 0)})
                return response
        except Exception as e:
            self.logger.error(f"Error processing text: {str(e)}")
            return {"error": str(e)}

    async def process_image(self, image_path: str) -> Dict[str, Any]:
        """Process image using vision model"""
        try:
            with mlflow.start_run():
                mlflow.log_param("task_type", "vision")
                mlflow.log_artifact(image_path)

                start_time = datetime.now()
                results = self.models["vision"](image_path)
                processing_time = (datetime.now() - start_time).total_seconds()

                mlflow.log_metrics({
                    "processing_time": processing_time,
                    "detected_objects": len(results)
                })

                return {
                    "results": results,
                    "processing_time": processing_time
                }
        except Exception as e:
            self.logger.error(f"Error processing image: {str(e)}")
            return {"error": str(e)}

    async def _process_with_gpt4o(self, text: str) -> Dict[str, Any]:
        """Process text using GPT-4o"""
        start_time = datetime.now()
        response = self.models["gpt4o"].generate(text)
        processing_time = (datetime.now() - start_time).total_seconds()

        return {
            "response": response,
            "processing_time": processing_time
        }

    def _get_embeddings(self, text: str) -> Dict[str, Any]:
        """Get embeddings for text"""
        start_time = datetime.now()
        embeddings = self.embeddings_model.encode(text)
        processing_time = (datetime.now() - start_time).total_seconds()

        return {
            "embeddings": embeddings.tolist(),
            "processing_time": processing_time
        }

    def get_model_status(self) -> Dict[str, bool]:
        """Get status of all initialized models"""
        return {
            "gpt4o": "gpt4o" in self.models,
            "vision": "vision" in self.models,
            "embeddings": self.embeddings_model is not None
        } 