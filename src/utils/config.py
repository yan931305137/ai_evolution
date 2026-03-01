import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

import logging

# Load environment variables from .env file
load_dotenv()

# Initialize logger (using getLogger to avoid circular dependency if setup_logger is used)
# Note: Logger setup should happen in the main entry point
logger = logging.getLogger(__name__)

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
            # Try with src/ prefix
            root_path = Path(__file__).parent.parent
            path = root_path / "src" / config_path
            
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
            
            # 环境变量覆盖provider设置（如果需要强制覆盖配置文件）
            if os.getenv("LLM_PROVIDER"):
                if "llm" not in self._config: self._config["llm"] = {}
                self._config["llm"]["provider"] = os.getenv("LLM_PROVIDER")

            # GitHub Configuration from Environment Variables
            self._load_github_config_from_env()
            
            # Evolution CI/CD Configuration from Environment Variables
            self._load_evolution_cicd_config_from_env()
            
            # LangSmith Configuration
            self._load_langsmith_config_from_env()
            
            # Load additional config files
            self._load_additional_configs()

            self._loaded = True
    
    def _load_github_config_from_env(self):
        """从环境变量加载 GitHub 配置"""
        github_config = self._config.get("github", {})
        
        if os.getenv("GITHUB_TOKEN"):
            github_config["token"] = os.getenv("GITHUB_TOKEN")
        if os.getenv("GITHUB_OWNER"):
            github_config["owner"] = os.getenv("GITHUB_OWNER")
        if os.getenv("GITHUB_REPO"):
            github_config["repo"] = os.getenv("GITHUB_REPO")
        
        if github_config:
            self._config["github"] = github_config
    
    def _load_evolution_cicd_config_from_env(self):
        """从环境变量加载进化 CI/CD 配置"""
        # 确保 self_evolution 配置存在
        if "self_evolution" not in self._config:
            self._config["self_evolution"] = {}
        
        evolution_config = self._config["self_evolution"]
        
        # 确保 cicd 子配置存在
        if "cicd" not in evolution_config:
            evolution_config["cicd"] = {}
        
        cicd_config = evolution_config["cicd"]
        
        # 从环境变量读取配置
        if os.getenv("EVOLUTION_CICD_ENABLED"):
            cicd_config["enabled"] = os.getenv("EVOLUTION_CICD_ENABLED").lower() == "true"
        if os.getenv("EVOLUTION_CICD_AUTO_TRIGGER"):
            cicd_config["auto_trigger"] = os.getenv("EVOLUTION_CICD_AUTO_TRIGGER").lower() == "true"
        if os.getenv("EVOLUTION_CICD_BRANCH"):
            cicd_config["branch"] = os.getenv("EVOLUTION_CICD_BRANCH")
        if os.getenv("EVOLUTION_CICD_CREATE_PR"):
            cicd_config["create_pr"] = os.getenv("EVOLUTION_CICD_CREATE_PR").lower() == "true"
        if os.getenv("EVOLUTION_CICD_AUTO_MERGE"):
            cicd_config["auto_merge"] = os.getenv("EVOLUTION_CICD_AUTO_MERGE").lower() == "true"
        if os.getenv("EVOLUTION_CICD_WORKFLOW"):
            cicd_config["workflow"] = os.getenv("EVOLUTION_CICD_WORKFLOW")
            
    def _load_langsmith_config_from_env(self):
        """从环境变量加载 LangSmith 配置"""
        if "langsmith" not in self._config:
            self._config["langsmith"] = {}
            
        langsmith_config = self._config["langsmith"]
        
        # LangSmith 环境变量
        if os.getenv("LANGCHAIN_TRACING_V2"):
            langsmith_config["tracing"] = os.getenv("LANGCHAIN_TRACING_V2").lower() == "true"
        if os.getenv("LANGCHAIN_API_KEY"):
            langsmith_config["api_key"] = os.getenv("LANGCHAIN_API_KEY")
        if os.getenv("LANGCHAIN_PROJECT"):
            langsmith_config["project"] = os.getenv("LANGCHAIN_PROJECT")
        if os.getenv("LANGCHAIN_ENDPOINT"):
            langsmith_config["endpoint"] = os.getenv("LANGCHAIN_ENDPOINT")
            
    def _load_additional_configs(self):
        """加载额外的配置文件"""
        additional_configs = [
            "config/github_cicd.yaml",
        ]
        
        for config_file in additional_configs:
            path = Path(config_file)
            if not path.exists():
                # 尝试从项目根目录查找
                root_path = Path(__file__).parent.parent
                path = root_path / config_file
            
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        additional_config = yaml.safe_load(f)
                        if additional_config:
                            # 合并配置
                            self._deep_merge(self._config, additional_config)
                            logger.info(f"[Config] Loaded additional config: {config_file}")
                except Exception as e:
                    logger.warning(f"[Config] Warning: Failed to load {config_file}: {e}")
    
    def _deep_merge(self, base: dict, override: dict) -> dict:
        """深度合并两个字典"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base
            
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
    def llm_provider(self) -> str:
        """获取LLM提供商"""
        # 环境变量优先级最高
        env_provider = os.getenv("LLM_PROVIDER")
        if env_provider:
            return env_provider
        return self.get("llm.provider", "coze")
    
    @property
    def brain_config(self) -> Dict[str, Any]:
        """获取Brain配置"""
        return self.get("llm.brain", {})

    @property
    def db_config(self) -> Dict[str, Any]:
        return self.get("database", {})

    @property
    def langsmith_config(self) -> Dict[str, Any]:
        """获取 LangSmith 配置"""
        return self.get("langsmith", {})

# Global instance
cfg = Config()
