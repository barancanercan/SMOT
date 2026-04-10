"""
Application Configuration - Pydantic Settings
Single source of truth for all configuration
"""
from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project paths
BACKEND_DIR = Path(__file__).parent.parent.parent  # backend/
ROOT_DIR = BACKEND_DIR.parent  # sam/

# Data directory - use environment variable or default to relative path
_data_dir_env = os.environ.get("DATA_DIR")
if _data_dir_env:
    DATA_DIR = Path(_data_dir_env)
else:
    # Check if we're in production (Render) or development
    if os.environ.get("ENVIRONMENT") == "production":
        DATA_DIR = BACKEND_DIR / "data"  # Inside backend for Render
    else:
        DATA_DIR = ROOT_DIR / "data"  # Outside backend for local dev

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Environment
    environment: str = Field(default="development", description="Environment (development/production)")
    debug: bool = Field(default=True, description="Debug mode")

    # API
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_prefix: str = Field(default="/api/v1", description="API prefix")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001,https://stratejik-analiz-merkezi.vercel.app",
        description="Allowed CORS origins (comma separated) - NO WILDCARDS in production"
    )

    # Security
    secret_key: str = Field(
        default="sam-dev-secret-key-change-in-production",
        description="Secret key for JWT encoding - MUST change in production"
    )
    access_token_expire_minutes: int = Field(default=30, description="JWT token expiration time")

    # Database
    database_url: str = Field(
        default=f"sqlite:///{DATA_DIR}/sam.db",
        description="Database connection URL"
    )

    # Legacy SQLite path (for backward compatibility)
    db_path: str = Field(default=str(DATA_DIR / "sam.db"), description="SQLite database path")

    # CSV Data
    csv_path: str = Field(default=str(DATA_DIR / "data.csv"), description="CSV data file path")

    # ChromaDB
    chroma_path: str = Field(default=str(ROOT_DIR / "chroma_db"), description="ChromaDB storage path")

    # Scraping Configuration
    max_tweets_per_user: int = Field(default=500, description="Maximum tweets to scrape per user")
    days_back: int = Field(default=90, description="Number of days to scrape back")
    scrape_timeout: int = Field(default=30, description="Scraping timeout in seconds")

    # LLM Configuration
    llm_provider: str = Field(default="openai", description="LLM provider (openai or ollama)")

    # OpenAI LLM
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-3.5-turbo", description="OpenAI model (gpt-3.5-turbo recommended for speed/cost)")
    openai_chat_model: str = Field(default="gpt-4o", description="OpenAI model for chat classification (gpt-4o recommended)")
    openai_timeout: int = Field(default=60, description="OpenAI request timeout in seconds")

    # Ollama LLM (fallback)
    ollama_url: str = Field(default="http://127.0.0.1:11434", description="Ollama API URL")
    ollama_model: str = Field(default="qwen2.5:3b", description="Default Ollama model")
    ollama_fallback_model: str = Field(default="llama3.2:1b", description="Fallback Ollama model")
    ollama_timeout: int = Field(default=300, description="LLM request timeout in seconds")

    # Embedding
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Sentence transformer model")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_dir: str = Field(default=str(BACKEND_DIR / "logs"), description="Log files directory")

    # Browser Settings (for scraping)
    brave_path_windows: str | None = Field(
        default=r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        description="Path to Brave browser on Windows"
    )
    brave_path_linux: str | None = Field(
        default="/usr/bin/brave-browser",
        description="Path to Brave browser on Linux"
    )
    headless_browser: bool = Field(default=False, description="Run browser in headless mode")

    # Cache
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    report_cache_hours: int = Field(default=168, description="Report cache duration in hours")

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"

    def get_browser_path(self) -> str | None:
        """Get browser path based on OS"""
        import platform
        if platform.system() == "Windows":
            return self.brave_path_windows
        return self.brave_path_linux


# Global settings instance
settings = Settings()

# Backward compatibility exports
DB_PATH = settings.db_path
CSV_PATH = settings.csv_path
MAX_TWEETS_PER_USER = settings.max_tweets_per_user
DAYS_BACK = settings.days_back
