import os
from dotenv import load_dotenv

load_dotenv()

# --- Bot Token ---
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# --- Group IDs ---
MAIN_GROUP_ID: int = int(os.getenv("MAIN_GROUP_ID", "0"))
BACKUP_GROUP_ID: int = int(os.getenv("BACKUP_GROUP_ID", "0"))

# --- Admin IDs ---
ADMIN_IDS: list[int] = [
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
]

# --- Channel Name ---
CHANNEL_NAME: str = os.getenv("CHANNEL_NAME", "MonCanal")

# --- CAPTCHA ---
CAPTCHA_TIMEOUT: int = int(os.getenv("CAPTCHA_TIMEOUT", "60"))

# --- Moderation ---
TEMP_BAN_DURATION: int = int(os.getenv("TEMP_BAN_DURATION", "3600"))  # 1 hour

# --- Blacklisted words ---
BLACKLISTED_WORDS: list[str] = [
    "cc",
    "scamma",
    "pack id",
]

# --- Database ---
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "bot_data.db")
