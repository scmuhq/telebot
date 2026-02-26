"""
Permissions + message de bienvenue quand un utilisateur rejoint le groupe.
Le CAPTCHA est géré dans start.py (dans le bot DM).
"""

import logging

from telegram import (
    Update,
    ChatPermissions,
)
from telegram.ext import (
    ContextTypes,
    ChatMemberHandler,
)

from config import MAIN_GROUP_ID, CHANNEL_NAME

logger = logging.getLogger(__name__)

# Permissions standard (no stickers/photos/videos)
STANDARD_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_audios=False,
    can_send_documents=True,
    can_send_photos=False,
    can_send_videos=False,
    can_send_video_notes=False,
    can_send_voice_notes=True,
    can_send_polls=True,
    can_send_other_messages=False,
    can_add_web_page_previews=True,
    can_change_info=False,
    can_invite_users=False,
    can_pin_messages=False,
)


async def on_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """When a user joins the main group, apply standard restricted permissions silently."""
    if not update.chat_member:
        return

    chat = update.chat_member.chat
    if chat.id != MAIN_GROUP_ID:
        return

    new = update.chat_member.new_chat_member
    old = update.chat_member.old_chat_member

    if old.status not in ("left", "kicked", "banned"):
        return
    if new.status not in ("member", "restricted"):
        return

    user = new.user
    if user.is_bot:
        return

    # Apply standard permissions + welcome message
    try:
        await context.bot.restrict_chat_member(
            chat_id=MAIN_GROUP_ID,
            user_id=user.id,
            permissions=STANDARD_PERMISSIONS,
        )
    except Exception as e:
        logger.error("Could not set permissions for new member %s: %s", user.id, e)

    # Welcome message
    mention = f"[{user.first_name}](tg://user?id={user.id})"
    try:
        await context.bot.send_message(
            chat_id=MAIN_GROUP_ID,
            text=f"🎉 **Bienvenue {mention} sur {CHANNEL_NAME} Group** !",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error("Could not send welcome message for %s: %s", user.id, e)


def get_handlers() -> list:
    return [
        ChatMemberHandler(on_new_member, ChatMemberHandler.CHAT_MEMBER),
    ]
