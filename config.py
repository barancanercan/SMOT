"""
Configuration file - Tüm constants burada
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# PATHS
# ============================================================================
DB_PATH = "meclis.db"
CSV_PATH = "data/data.csv"

# ============================================================================
# SCRAPING CONFIGURATION
# ============================================================================
MAX_TWEETS_PER_USER = 500
DAYS_BACK = 90