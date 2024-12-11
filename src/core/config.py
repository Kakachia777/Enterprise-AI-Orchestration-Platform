from pathlib import Path
import yaml
from typing import Dict, Any
import os

class ConfigManager:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
        with open(config_path, "r") as f:
            self._config = yaml.safe_load(f)
        
        # Override with environment variables if they exist
        self._override_from_env()

    def _override_from_env(self):
        for key in self._config.keys():
            env_key = f"EAOP_{key.upper()}"
            if env_key in os.environ:
                self._config[key] = os.environ[env_key]

    def get_config(self) -> Dict[str, Any]:
        return self._config

    def get_api_config(self) -> Dict[str, Any]:
        return self._config.get("api", {})

    def get_model_config(self, model_type: str) -> Dict[str, Any]:
        return self._config.get("models", {}).get(model_type, {})

    def get_database_config(self, db_type: str) -> Dict[str, Any]:
        return self._config.get("database", {}).get(db_type, {})

    def get_monitoring_config(self) -> Dict[str, Any]:
        return self._config.get("monitoring", {})

    def get_security_config(self) -> Dict[str, Any]:
        return self._config.get("security", {}) 