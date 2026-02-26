"""
Étape 11 — /certif : afficher et gérer la liste des membres certifiés.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config import ADMIN_IDS, CHANNEL_NAME
from database import (
    get_certified_members,
    add_certified_member,
    remove_certified_member,
)

logger = logging.getLogger(__name__)


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def certif_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /certif — Affiche la liste des membres certifiés et du staff.
    Accessible à tous les utilisateurs.
    """
    msg = update.effective_message
    if not msg:
        return

    members = get_certified_members()

    if not members:
        await msg.reply_text(
            f"📋 **Staff & Membres certifiés — {CHANNEL_NAME}**\n\n"
            f"Aucun membre certifié pour le moment.",
            parse_mode="Markdown",
        )
        return

    lines = [f"📋 **Staff & Membres certifiés — {CHANNEL_NAME}**\n"]
    for m in members:
        name = m["username"] or m["first_name"] or str(m["user_id"])
        display = f"@{name}" if m["username"] else f"[{m['first_name']}](tg://user?id={m['user_id']})"
        lines.append(f"• {display} — _{m['role']}_")

    await msg.reply_text("\n".join(lines), parse_mode="Markdown")


async def addcertif_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /addcertif <rôle> — Ajoute un membre certifié (répondre à un message).
    Réservé aux admins.
    """
    msg = update.effective_message
    if not msg or not msg.from_user:
        return
    if not _is_admin(msg.from_user.id):
        await msg.reply_text("❌ Commande réservée aux administrateurs.")
        return

    if not msg.reply_to_message or not msg.reply_to_message.from_user:
        await msg.reply_text(
            "⚠️ Réponds au message d'un utilisateur.\n"
            "Usage : `/addcertif Rôle optionnel`",
            parse_mode="Markdown",
        )
        return

    target = msg.reply_to_message.from_user
    role = " ".join(context.args) if context.args else "Membre certifié"

    add_certified_member(target.id, target.username, target.first_name, role)
    await msg.reply_text(
        f"✅ {target.first_name} a été ajouté(e) comme **{role}**.",
        parse_mode="Markdown",
    )


async def removecertif_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /removecertif — Retire un membre certifié (répondre à un message).
    Réservé aux admins.
    """
    msg = update.effective_message
    if not msg or not msg.from_user:
        return
    if not _is_admin(msg.from_user.id):
        await msg.reply_text("❌ Commande réservée aux administrateurs.")
        return

    if not msg.reply_to_message or not msg.reply_to_message.from_user:
        await msg.reply_text("⚠️ Réponds au message d'un utilisateur pour le retirer de la liste.")
        return

    target = msg.reply_to_message.from_user
    remove_certified_member(target.id)
    await msg.reply_text(f"✅ {target.first_name} a été retiré(e) de la liste des certifiés.")


def get_handlers() -> list:
    return [
        CommandHandler("certif", certif_command),
        CommandHandler("addcertif", addcertif_command),
        CommandHandler("removecertif", removecertif_command),
    ]
