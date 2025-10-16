import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "book_crawler")

# Crawler configuration
SITE_KEY = os.getenv("SITE_KEY", "books_toscrape")

# Scheduler configuration
SCHEDULER_TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "UTC")
SCHEDULER_RUN_TIME = os.getenv("SCHEDULER_RUN_TIME", "")  # e.g., "02:00"
SCHEDULER_INTERVAL_MINUTES = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", 1440))

# API key name
API_KEY_NAME = os.getenv("API_KEY_NAME", "")