import os
from dotenv import load_dotenv

load_dotenv()

# Load environment variables and validate them
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_CHANNEL = int(os.getenv("DB_CHANNEL"))
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL"))
FORCE_SUB = os.getenv("FORCE_SUB", "0")  # Default to "0" if not set
AUTO_DELETE_TIME = int(os.getenv("AUTO_DELETE_TIME", 10)) * 60  # Default to 10 minutes if not set
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(',')))

def validate_config():
    required_vars = ['BOT_TOKEN', 'DB_CHANNEL', 'LOG_CHANNEL', 'AUTO_DELETE_TIME', 'ADMIN_IDS']
    for var in required_vars:
        if os.getenv(var) is None:
            raise ValueError(f"Environment variable {var} is not set.")

validate_config()
