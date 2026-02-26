"""
Étapes 2, 3, 4, 5 — /start → backup → CAPTCHA dans le bot → lien d'invitation.
"""

import logging
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)

from config import MAIN_GROUP_ID, BACKUP_GROUP_ID, CHANNEL_NAME, CAPTCHA_TIMEOUT
from database import add_bot_user, add_pending_captcha, get_pending_captcha, remove_pending_captcha

logger = logging.getLogger(__name__)

# Cache for the backup invite link
_backup_invite_cache: str | None = None


async def _get_backup_invite(context: ContextTypes.DEFAULT_TYPE) -> str:
    """Generate (or return cached) invite link for the backup group."""
    global _backup_invite_cache
    if _backup_invite_cache:
        return _backup_invite_cache

    invite = await context.bot.create_chat_invite_link(
        chat_id=BACKUP_GROUP_ID,
        name="backup_join",
        creates_join_request=False,
    )
    _backup_invite_cache = invite.invite_link
    return _backup_invite_cache


def _generate_captcha() -> tuple[str, int, list[int]]:
    """Return (question_text, correct_answer, [3 choices shuffled])."""
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    correct = a + b
    question = f"{a} + {b}"

    wrong = set()
    while len(wrong) < 2:
        w = correct + random.choice([-3, -2, -1, 1, 2, 3])
        if w != correct and w > 0:
            wrong.add(w)

    choices = list(wrong) + [correct]
    random.shuffle(choices)
    return question, correct, choices


# ─── Étape 1 : /start ────────────────────────────────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — welcome + instruction to join backup group."""
    user = update.effective_user
    if not user or not update.message:
        return

    add_bot_user(user.id, user.username, user.first_name)

    try:
        backup_url = await _get_backup_invite(context)
    except Exception as e:
        logger.error("Could not create backup invite link: %s", e)
        await update.message.reply_text(
            "⚠️ Impossible de générer le lien du groupe backup. Contacte un administrateur."
        )
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Rejoindre le groupe backup", url=backup_url)],
        [InlineKeyboardButton("✅ J'ai rejoint — Vérifier", callback_data="check_backup")],
    ])

    await update.message.reply_text(
        f"👋 Bienvenue sur le bot de **{CHANNEL_NAME} Group** !\n\n"
        f"Pour accéder au groupe principal, tu dois d'abord rejoindre "
        f"le **groupe backup**.\n\n"
        f"1️⃣ Clique sur le bouton ci-dessous pour rejoindre le groupe backup.\n"
        f"2️⃣ Une fois fait, clique sur **« J'ai rejoint — Vérifier »**.\n\n"
        f"⚠️ Tu ne pourras pas continuer sans avoir rejoint le groupe backup.",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


# ─── Étape 2 : Vérification backup → CAPTCHA ────────────────────────────────

async def check_backup_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Verify backup membership, then send CAPTCHA in DM."""
    query = update.callback_query
    if not query or not query.from_user:
        return
    await query.answer()

    user = query.from_user

    try:
        member = await context.bot.get_chat_member(BACKUP_GROUP_ID, user.id)
        is_member = member.status in ("member", "administrator", "creator")
    except Exception as e:
        logger.warning("Could not check backup membership for %s: %s", user.id, e)
        is_member = False

    if not is_member:
        try:
            backup_url = await _get_backup_invite(context)
        except Exception:
            backup_url = "https://t.me"

        await query.edit_message_text(
            "❌ Tu n'as pas encore rejoint le **groupe backup**.\n\n"
            "Rejoins-le d'abord, puis clique à nouveau sur le bouton.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Rejoindre le groupe backup", url=backup_url)],
                [InlineKeyboardButton("✅ J'ai rejoint — Vérifier", callback_data="check_backup")],
            ]),
        )
        return

    # Backup OK → Send CAPTCHA
    question, answer, choices = _generate_captcha()
    add_pending_captcha(user.id, answer)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(str(c), callback_data=f"captcha_{user.id}_{c}")
            for c in choices
        ]
    ])

    await query.edit_message_text(
        f"✅ Groupe backup rejoint !\n\n"
        f"🔒 **Étape suivante — CAPTCHA**\n\n"
        f"Combien font **{question}** ?\n\n"
        f"Choisis la bonne réponse ci-dessous :",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )

    # Schedule timeout
    context.job_queue.run_once(
        _captcha_timeout_dm,
        when=CAPTCHA_TIMEOUT,
        data={"user_id": user.id},
        name=f"captcha_timeout_{user.id}",
    )


# ─── Étape 3 : Réponse CAPTCHA → Lien d'invitation ──────────────────────────

async def captcha_answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle CAPTCHA answer in DM. If correct → send invite link."""
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()

    parts = query.data.split("_")  # captcha_{user_id}_{answer}
    if len(parts) != 3:
        return

    target_user_id = int(parts[1])
    chosen_answer = int(parts[2])

    if query.from_user.id != target_user_id:
        await query.answer("❌ Ce CAPTCHA n'est pas pour toi.", show_alert=True)
        return

    pending = get_pending_captcha(target_user_id)
    if not pending:
        await query.edit_message_text("⚠️ CAPTCHA expiré. Utilise /start pour recommencer.")
        return

    correct_answer = pending["answer"]
    remove_pending_captcha(target_user_id)

    # Cancel timeout
    jobs = context.job_queue.get_jobs_by_name(f"captcha_timeout_{target_user_id}")
    for job in jobs:
        job.schedule_removal()

    if chosen_answer == correct_answer:
        # Generate invite link
        try:
            invite = await context.bot.create_chat_invite_link(
                chat_id=MAIN_GROUP_ID,
                member_limit=1,
                name=f"invite_{target_user_id}",
            )
            invite_url = invite.invite_link
        except Exception as e:
            logger.error("Could not create invite link: %s", e)
            await query.edit_message_text(
                "⚠️ Erreur lors de la création du lien. Contacte un administrateur."
            )
            return

        await query.edit_message_text(
            f"✅ CAPTCHA réussi !\n\n"
            f"🔗 Voici ton **lien d'invitation unique** vers **{CHANNEL_NAME} Group** :\n"
            f"{invite_url}\n\n"
            f"⚠️ Ce lien est à usage unique et personnel. Ne le partage pas !",
            parse_mode="Markdown",
        )
    else:
        await query.edit_message_text(
            "❌ Mauvaise réponse.\n\n"
            "Utilise /start pour recommencer."
        )


async def _captcha_timeout_dm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle CAPTCHA timeout in DM."""
    data = context.job.data
    user_id = data["user_id"]

    pending = get_pending_captcha(user_id)
    if not pending:
        return

    remove_pending_captcha(user_id)

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="⏰ Temps écoulé pour le CAPTCHA.\n\nUtilise /start pour recommencer.",
        )
    except Exception:
        pass


def get_handlers() -> list:
    return [
        CommandHandler("start", start_command),
        CallbackQueryHandler(check_backup_callback, pattern="^check_backup$"),
        CallbackQueryHandler(captcha_answer_callback, pattern=r"^captcha_\d+_\d+$"),
    ]
