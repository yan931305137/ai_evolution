import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Disable ChromaDB Telemetry to prevent timeouts
os.environ["ANONYMIZED_TELEMETRY"] = "False"
# Set HuggingFace endpoint mirror for China users
if "HF_ENDPOINT" not in os.environ:
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

class Config:
    """Simple configuration manager for OpenClaw-Local."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._config = {}
            cls._instance._loaded = False
        return cls._instance

    def load(self, config_path: str = "config/config.yaml"):
        """Load configuration from YAML file."""
        path = Path(config_path)
        if not path.exists():
            # Try looking relative to the package root if running from elsewhere
            root_path = Path(__file__).parent.parent
            path = root_path / config_path
            
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found at {path}")
            
        with open(path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

            # Override sensitive configs with environment variables if available
            if os.getenv("LLM_API_KEY"):
                if "llm" not in self._config: self._config["llm"] = {}
                self._config["llm"]["api_key"] = os.getenv("LLM_API_KEY")
            
            if os.getenv("LLM_BASE_URL"):
                if "llm" not in self._config: self._config["llm"] = {}
                self._config["llm"]["base_url"] = os.getenv("LLM_BASE_URL")

            if os.getenv("LLM_MODEL_NAME"):
                if "llm" not in self._config: self._config["llm"] = {}
                self._config["llm"]["model_name"] = os.getenv("LLM_MODEL_NAME")

            self._loaded = True
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation for nested keys)."""
        if not self._loaded:
            self.load()
            
        keys = key.split(".")
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    @property
    def llm_config(self) -> Dict[str, Any]:
        return self.get("llm", {})

    @property
    def db_config(self) -> Dict[str, Any]:
        return self.get("database", {})

# Global instance
cfg = Config()
