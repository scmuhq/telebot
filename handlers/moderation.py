"""
Étapes 9 & 10 — Modération automatique (blacklist) + commandes admin.
"""

import logging
import re
from datetime import datetime, timedelta, timezone

from telegram import Update, ChatPermissions
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import (
    MAIN_GROUP_ID,
    ADMIN_IDS,
    BLACKLISTED_WORDS,
    TEMP_BAN_DURATION,
)
from database import add_warning, get_warning_count

logger = logging.getLogger(__name__)

# Build regex pattern from blacklisted words (word boundaries, case-insensitive)
_blacklist_pattern = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in BLACKLISTED_WORDS) + r")\b",
    re.IGNORECASE,
)


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _get_target_user_id(update: Update) -> int | None:
    """Extract target user from reply or @mention."""
    msg = update.effective_message
    if not msg:
        return None

    # If replying to a message, use that user
    if msg.reply_to_message and msg.reply_to_message.from_user:
        return msg.reply_to_message.from_user.id

    # If mentioning @user, try entities
    if msg.entities:
        for entity in msg.entities:
            if entity.type == "text_mention" and entity.user:
                return entity.user.id

    return None


# ─── Blacklist auto-moderation ────────────────────────────────────────────────

async def blacklist_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete messages containing blacklisted words and temp-ban the user."""
    msg = update.effective_message
    if not msg or not msg.text or not msg.from_user:
        return
    if msg.chat.id != MAIN_GROUP_ID:
        return
    if _is_admin(msg.from_user.id):
        return  # Don't filter admins

    if _blacklist_pattern.search(msg.text):
        user = msg.from_user
        # Delete the message
        try:
            await msg.delete()
        except Exception as e:
            logger.warning("Could not delete blacklisted message: %s", e)

        # Temp ban (1 hour)
        until = datetime.now(timezone.utc) + timedelta(seconds=TEMP_BAN_DURATION)
        try:
            await context.bot.ban_chat_member(
                chat_id=MAIN_GROUP_ID,
                user_id=user.id,
                until_date=until,
            )
        except Exception as e:
            logger.error("Could not temp-ban user %s: %s", user.id, e)

        try:
            await context.bot.send_message(
                chat_id=MAIN_GROUP_ID,
                text=(
                    f"🚫 Message supprimé — mot interdit détecté.\n"
                    f"L'utilisateur [{user.first_name}](tg://user?id={user.id}) "
                    f"a été banni temporairement (1 heure)."
                ),
                parse_mode="Markdown",
            )
        except Exception:
            pass


# ─── /ban ─────────────────────────────────────────────────────────────────────

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/ban — Ban a user (reply or @mention)."""
    msg = update.effective_message
    if not msg or not msg.from_user:
        return
    if msg.chat.id != MAIN_GROUP_ID:
        return
    if not _is_admin(msg.from_user.id):
        await msg.reply_text("❌ Commande réservée aux administrateurs.")
        return

    target = _get_target_user_id(update)
    if not target:
        await msg.reply_text("⚠️ Réponds à un message ou mentionne un utilisateur.\nUsage : /ban (en réponse à un message)")
        return

    try:
        await context.bot.ban_chat_member(MAIN_GROUP_ID, target)
        await msg.reply_text(f"✅ Utilisateur banni.")
    except Exception as e:
        await msg.reply_text(f"❌ Erreur : {e}")


# ─── /mute ────────────────────────────────────────────────────────────────────

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/mute — Mute a user."""
    msg = update.effective_message
    if not msg or not msg.from_user:
        return
    if msg.chat.id != MAIN_GROUP_ID:
        return
    if not _is_admin(msg.from_user.id):
        await msg.reply_text("❌ Commande réservée aux administrateurs.")
        return

    target = _get_target_user_id(update)
    if not target:
        await msg.reply_text("⚠️ Réponds à un message ou mentionne un utilisateur.\nUsage : /mute (en réponse à un message)")
        return

    muted_permissions = ChatPermissions(
        can_send_messages=False,
        can_send_audios=False,
        can_send_documents=False,
        can_send_photos=False,
        can_send_videos=False,
        can_send_video_notes=False,
        can_send_voice_notes=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
    )

    try:
        await context.bot.restrict_chat_member(MAIN_GROUP_ID, target, permissions=muted_permissions)
        await msg.reply_text(f"🔇 Utilisateur muté.")
    except Exception as e:
        await msg.reply_text(f"❌ Erreur : {e}")


# ─── /unmute ──────────────────────────────────────────────────────────────────

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/unmute — Unmute a user (restore standard permissions)."""
    msg = update.effective_message
    if not msg or not msg.from_user:
        return
    if msg.chat.id != MAIN_GROUP_ID:
        return
    if not _is_admin(msg.from_user.id):
        await msg.reply_text("❌ Commande réservée aux administrateurs.")
        return

    target = _get_target_user_id(update)
    if not target:
        await msg.reply_text("⚠️ Réponds à un message ou mentionne un utilisateur.\nUsage : /unmute (en réponse à un message)")
        return

    standard_permissions = ChatPermissions(
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
    )

    try:
        await context.bot.restrict_chat_member(MAIN_GROUP_ID, target, permissions=standard_permissions)
        await msg.reply_text(f"🔊 Utilisateur démuté.")
    except Exception as e:
        await msg.reply_text(f"❌ Erreur : {e}")


# ─── /warn ────────────────────────────────────────────────────────────────────

async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/warn — Warn a user. 3 warnings => ban."""
    msg = update.effective_message
    if not msg or not msg.from_user:
        return
    if msg.chat.id != MAIN_GROUP_ID:
        return
    if not _is_admin(msg.from_user.id):
        await msg.reply_text("❌ Commande réservée aux administrateurs.")
        return

    target = _get_target_user_id(update)
    if not target:
        await msg.reply_text("⚠️ Réponds à un message ou mentionne un utilisateur.\nUsage : /warn (en réponse à un message)")
        return

    reason = " ".join(context.args) if context.args else None
    count = add_warning(target, msg.from_user.id, reason)

    if count >= 3:
        try:
            await context.bot.ban_chat_member(MAIN_GROUP_ID, target)
            await msg.reply_text(f"⚠️ Avertissement #{count} — L'utilisateur a atteint 3 avertissements et a été **banni**.", parse_mode="Markdown")
        except Exception as e:
            await msg.reply_text(f"❌ Erreur lors du ban : {e}")
    else:
        reason_text = f"\nRaison : {reason}" if reason else ""
        await msg.reply_text(f"⚠️ Avertissement #{count}/3 donné à l'utilisateur.{reason_text}")


def get_handlers() -> list:
    return [
        # Blacklist filter — must run on ALL text messages in the group
        MessageHandler(
            filters.Chat(MAIN_GROUP_ID) & filters.TEXT & ~filters.COMMAND,
            blacklist_filter,
        ),
        CommandHandler("ban", ban_command),
        CommandHandler("mute", mute_command),
        CommandHandler("unmute", unmute_command),
        CommandHandler("warn", warn_command),
    ]
