import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Logs directory
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class CustomLogger:
    _instance = None

    @staticmethod
    def get_logger(name: str = "SMOT"):
        """
        Get a configured logger instance.
        If a logger with the given name already exists, it returns it.
        Otherwise, it configures a new one.
        """
        logger = logging.getLogger(name)

        # If logger already has handlers, assume it's configured
        if logger.handlers:
            return logger

        logger.setLevel(logging.INFO)

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        logger.addHandler(console_handler)

        # File Handler (Rotating)
        file_path = os.path.join(LOG_DIR, "app.log")
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=10*1024*1024, # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        logger.addHandler(file_handler)

        return logger

# Global accessor
def get_logger(name: str = "SMOT"):
    return CustomLogger.get_logger(name)
