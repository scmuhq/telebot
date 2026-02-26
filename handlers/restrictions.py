"""
Étape 8 — Restrictions dans le groupe principal.
Bloque stickers, images/photos, appels vocaux/vidéo pour les utilisateurs standards.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from config import MAIN_GROUP_ID, ADMIN_IDS
from database import get_certified_members

logger = logging.getLogger(__name__)


def _is_privileged(user_id: int) -> bool:
    """Check if user is admin or certified member."""
    if user_id in ADMIN_IDS:
        return True
    certified = get_certified_members()
    return any(m["user_id"] == user_id for m in certified)


async def block_restricted_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete stickers, photos, and other restricted content from non-privileged users."""
    msg = update.effective_message
    if not msg or not msg.from_user:
        return
    if msg.chat.id != MAIN_GROUP_ID:
        return
    if _is_privileged(msg.from_user.id):
        return

    # Check if message contains forbidden content
    is_sticker = msg.sticker is not None
    is_photo = msg.photo is not None and len(msg.photo) > 0
    is_video = msg.video is not None
    is_video_note = msg.video_note is not None
    is_animation = msg.animation is not None  # GIFs

    if is_sticker or is_photo or is_video or is_video_note or is_animation:
        try:
            await msg.delete()
            await context.bot.send_message(
                chat_id=MAIN_GROUP_ID,
                text=f"🚫 {msg.from_user.first_name}, les stickers, images et vidéos ne sont pas autorisés pour les membres standards.",
            )
        except Exception as e:
            logger.warning("Could not delete restricted content: %s", e)


def get_handlers() -> list:
    return [
        MessageHandler(
            filters.Chat(MAIN_GROUP_ID) & (
                filters.Sticker.ALL |
                filters.PHOTO |
                filters.VIDEO |
                filters.VIDEO_NOTE |
                filters.ANIMATION
            ),
            block_restricted_content,
        ),
    ]
