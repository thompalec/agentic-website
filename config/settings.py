import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Browser settings
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
SLOW_MO = int(os.getenv("SLOW_MO", "50"))

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Website URLs
EXPEDIA_URL = os.getenv("EXPEDIA_URL", "https://www.expedia.com/")

# Timeout settings
NAVIGATION_TIMEOUT = int(os.getenv("NAVIGATION_TIMEOUT", "30000"))
ACTION_TIMEOUT = int(os.getenv("ACTION_TIMEOUT", "10000"))
