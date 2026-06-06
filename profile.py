import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.database import get_or_create_user
from utils.helpers import require_not_banned, plan_badge
from config import BRANDING, BRANDING_LINE

logger = logging.getLogger(__name__)

BACK_KB = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="nav:menu")]])


def build_profile_text(user, db_user: dict) -> str:
    plan = plan_badge(bool(db_user["is_premium"]))
    return (
        f"<b>{BRANDING}</b>\n"
        f"<code>{BRANDING_LINE}</code>\n\n"
        "👤 <b>Your Profile</b>\n\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"👤 <b>Name:</b> {user.first_name or 'N/A'}\n"
        f"📅 <b>Join Date:</b> {db_user['join_date']}\n"
        f"📦 <b>Plan:</b> {plan}\n"
        f"📁 <b>Files Today:</b> {db_user['files_today']}\n"
        f"📊 <b>Total Files:</b> {db_user['files_total']}\n\n"
        f"<code>{BRANDING_LINE}</code>"
    )


@require_not_banned
async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_or_create_user(user.id, user.username, user.first_name)
    text = build_profile_text(user, db_user)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=BACK_KB)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=BACK_KB)
