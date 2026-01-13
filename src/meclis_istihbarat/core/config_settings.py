import os
"""
Modern Configuration with Pydantic Settings
Replaces old config.py with type-safe, validated settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    # Database
    db_path: str = Field(default="meclis.db", description="SQLite database path")
    
    # CSV Data
    csv_path: str = Field(default="data/data.csv", description="CSV data file path")
    
    # Scraping Configuration
    max_tweets_per_user: int = Field(default=500, description="Maximum tweets to scrape per user")
    days_back: int = Field(default=90, description="Number of days to scrape back")
    
    # Ollama LLM
    ollama_url: str = Field(default="http://127.0.0.1:11434", description="Ollama API URL")
    ollama_model: str = Field(default="qwen2.5:3b", description="Default Ollama model")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_dir: str = Field(default="logs", description="Log files directory")
    
    # Browser Settings
    brave_path_windows: Optional[str] = Field(
        default=r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        description="Path to Brave browser on Windows"
    )
    
    def get_db_path(self) -> str:
        """Get absolute database path"""
        return os.path.abspath(self.db_path)
    
    def get_csv_path(self) -> str:
        """Get absolute CSV path"""
        return os.path.abspath(self.csv_path)
    
    def get_log_dir(self) -> str:
        """Get absolute log directory path"""
        return os.path.abspath(self.log_dir)


# Global settings instance
settings = Settings()

# Backward compatibility exports
DB_PATH = settings.db_path
CSV_PATH = settings.csv_path
MAX_TWEETS_PER_USER = settings.max_tweets_per_user
DAYS_BACK = settings.days_back
