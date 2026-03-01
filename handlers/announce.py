"""
Étape 7 — Annonces via le bot (envoi en MP à tous les utilisateurs ayant fait /start).
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config import ADMIN_IDS, MAIN_GROUP_ID
from database import get_all_bot_users

logger = logging.getLogger(__name__)


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def announce_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /announce <message>
    Envoie le message en MP à tous les utilisateurs ayant lancé /start.
    Réservé aux admins. Peut être utilisé en privé ou dans le groupe.
    """
    msg = update.effective_message
    if not msg or not msg.from_user:
        return
    if not _is_admin(msg.from_user.id):
        await msg.reply_text("❌ Commande réservée aux administrateurs.")
        return

    if not context.args:
        await msg.reply_text(
            "⚠️ Usage : `/announce Votre message d'annonce ici`",
            parse_mode="Markdown",
        )
        return

    announcement_text = " ".join(context.args)
    users = get_all_bot_users()

    success = 0
    failed = 0

    status_msg = await msg.reply_text(f"📤 Envoi de l'annonce à {len(users)} utilisateur(s)...")

    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user["user_id"],
                text=f"📢 **Annonce — {msg.from_user.first_name}** :\n\n{announcement_text}",
                parse_mode="Markdown",
            )
            success += 1
        except Exception as e:
            logger.debug("Could not send announcement to %s: %s", user["user_id"], e)
            failed += 1

    await status_msg.edit_text(
        f"✅ Annonce envoyée !\n"
        f"• Succès : {success}\n"
        f"• Échecs : {failed} (utilisateurs ayant bloqué le bot ou compte supprimé)"
    )


async def msg_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /msg <message>
    Le bot envoie le message dans le groupe principal en son nom.
    Réservé aux admins. La commande d'origine est supprimée.
    """
    msg = update.effective_message
    if not msg or not msg.from_user:
        return
    if not _is_admin(msg.from_user.id):
        await msg.reply_text("❌ Commande réservée aux administrateurs.")
        return

    if not context.args:
        await msg.reply_text("⚠️ Usage : `/msg Votre message ici`", parse_mode="Markdown")
        return

    text = " ".join(context.args)

    # Supprimer la commande d'origine
    try:
        await msg.delete()
    except Exception:
        pass

    # Envoyer le message en tant que bot dans le groupe
    try:
        await context.bot.send_message(
            chat_id=MAIN_GROUP_ID,
            text=text,
        )
    except Exception as e:
        logger.error("Could not send /msg: %s", e)


def get_handlers() -> list:
    return [
        CommandHandler("announce", announce_command),
        CommandHandler("msg", msg_command),
    ]
