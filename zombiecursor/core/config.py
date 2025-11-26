"""
Core configuration management for ZombieCursor.
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=5051, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # LLM Configuration
    llm_host: str = Field(default="http://localhost:8007", env="LLM_HOST")
    llm_model: str = Field(default="llama2", env="LLM_MODEL")
    llm_timeout: int = Field(default=30, env="LLM_TIMEOUT")
    llm_max_tokens: int = Field(default=2048, env="LLM_MAX_TOKENS")
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    
    # Ollama Configuration (alternative)
    ollama_host: Optional[str] = Field(default=None, env="OLLAMA_HOST")
    ollama_model: Optional[str] = Field(default=None, env="OLLAMA_MODEL")
    
    # Project Configuration
    project_root: str = Field(default=".", env="PROJECT_ROOT")
    max_context_files: int = Field(default=50, env="MAX_CONTEXT_FILES")
    max_context_size: int = Field(default=3000, env="MAX_CONTEXT_SIZE")
    
    # Redis Configuration
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/zombiecursor.log", env="LOG_FILE")
    
    # Security
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    
    # Agent Configuration
    default_agent: str = Field(default="coder", env="DEFAULT_AGENT")
    enable_streaming: bool = Field(default=True, env="ENABLE_STREAMING")
    enable_memory: bool = Field(default=True, env="ENABLE_MEMORY")
    
    # Vector Store Configuration
    vector_store_path: str = Field(default="./vectorstores/data", env="VECTOR_STORE_PATH")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    
    # Tool Configuration
    enable_git_tool: bool = Field(default=True, env="ENABLE_GIT_TOOL")
    enable_python_tool: bool = Field(default=True, env="ENABLE_PYTHON_TOOL")
    enable_system_tool: bool = Field(default=True, env="ENABLE_SYSTEM_TOOL")
    python_timeout: int = Field(default=30, env="PYTHON_TIMEOUT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure log directory exists
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
        # Ensure vector store directory exists
        Path(self.vector_store_path).parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()