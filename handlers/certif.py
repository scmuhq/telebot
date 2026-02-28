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


# Sections du staff avec leurs membres par défaut
STAFF_SECTIONS = [
    ("Développeur 👨🏽‍💻", ["@jbsshi"]),
    ("C*C 💳", []),
    ("Formation 📵", ["@socrate_vbv"]),
    ("NL/DB 📇", ["@Silentleadsbot"]),
    ("Exchanger ™️", []),
]

# Mapping des noms de rôle vers les noms de section (pour matcher /addcertif)
ROLE_TO_SECTION = {
    "développeur": "Développeur 👨🏽‍💻",
    "dev": "Développeur 👨🏽‍💻",
    "c*c": "C*C 💳",
    "cc": "C*C 💳",
    "formation": "Formation 📵",
    "nl/db": "NL/DB 📇",
    "nl": "NL/DB 📇",
    "db": "NL/DB 📇",
    "exchanger": "Exchanger ™️",
}


def _build_certif_text() -> str:
    """Construit le message /certif dynamiquement avec les membres de la BDD."""
    members = get_certified_members()

    # Grouper les membres dynamiques par section
    dynamic_by_section: dict[str, list[str]] = {}
    for m in members:
        role_lower = m["role"].lower().strip()
        section_name = ROLE_TO_SECTION.get(role_lower)
        if section_name:
            name = f"@{m['username']}" if m["username"] else m["first_name"] or str(m["user_id"])
            dynamic_by_section.setdefault(section_name, []).append(name)

    lines = ["𝑺𝑻𝑨𝑭𝑭 𝑪𝑬𝑹𝑻𝑰𝑭𝑰𝑬́ 𝑫𝑬 𝑳𝑨 𝑷𝑰𝑹𝑬́𝑬", "___", ""]

    for section_name, defaults in STAFF_SECTIONS:
        lines.append(f"ω {section_name}")
        # Membres par défaut + membres dynamiques
        all_members = defaults + dynamic_by_section.get(section_name, [])
        if all_members:
            for name in all_members:
                lines.append(f"—> {name} ✅")
        else:
            lines.append("—>")
        lines.append("")

    return "\n".join(lines).rstrip()


async def certif_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /certif — Affiche le staff certifié.
    Accessible à tous les utilisateurs.
    """
    msg = update.effective_message
    if not msg:
        return

    await msg.reply_text(_build_certif_text())


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
        f"✅ {target.first_name} a été ajouté(e) comme {role}.",
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
