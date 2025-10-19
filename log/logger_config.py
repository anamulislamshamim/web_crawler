# logger_config.py
import logging
import io

# Create a shared in-memory stream
log_stream = io.StringIO()

# Define formatter
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Create handlers
stream_handler = logging.StreamHandler(log_stream)
stream_handler.setFormatter(formatter)

file_handler = logging.FileHandler("crawler_daily.log")
file_handler.setFormatter(formatter)

# Configure the root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

# Prevent duplicate logs
logger.propagate = False

def get_logger(name: str = None):
    """Return a named logger (module-specific)."""
    return logging.getLogger(name)

def get_in_memory_logs() -> str:
    """Return all current in-memory logs as text."""
    return log_stream.getvalue()