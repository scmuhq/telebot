"""
Bot Telegram principal — point d'entrée.
Regroupe onboarding, sécurité, CAPTCHA, modération et annonces.
"""

import logging

from telegram.ext import ApplicationBuilder

from config import BOT_TOKEN
from database import init_db

# Import handlers
from handlers import start, captcha, moderation, announce, certif, restrictions

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    # Initialize database
    init_db()
    logger.info("Database initialized.")

    # Build application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register all handlers
    for handler in start.get_handlers():
        app.add_handler(handler)

    for handler in captcha.get_handlers():
        app.add_handler(handler)

    # Moderation handlers — blacklist filter must have lower group to run first
    for handler in moderation.get_handlers():
        app.add_handler(handler, group=1)

    for handler in restrictions.get_handlers():
        app.add_handler(handler, group=2)

    for handler in announce.get_handlers():
        app.add_handler(handler)

    for handler in certif.get_handlers():
        app.add_handler(handler)

    logger.info("Bot started — polling...")
    app.run_polling(
        allowed_updates=[
            "message",
            "callback_query",
            "chat_member",
        ],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
