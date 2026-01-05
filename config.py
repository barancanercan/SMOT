"""
Configuration file - Tüm constants burada
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# PATHS
# ============================================================================
DB_PATH = "meclis.db"

# ============================================================================
# API CONFIGURATION
# ============================================================================
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b-instruct-q4_K_M"

# ============================================================================
# CREDENTIALS (from .env)
# ============================================================================
X_USER = os.getenv("X_USERNAME", "default_user")
X_PASS = os.getenv("X_PASSWORD", "default_pass")

# ============================================================================
# ANALYSIS QUESTIONS
# ============================================================================
QUESTIONS = [
    "Bu üyenin ana gündemleri neler?",
    "Hangi konularda en çok tweet atıyor?",
    "Son ayda ne hakkında konuşmaya başladı?",
]

# ============================================================================
# UI CONFIGURATION
# ============================================================================
UI_HOST = "127.0.0.1"
UI_PORT = 7860
