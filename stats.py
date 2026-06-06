import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.database import get_stats
from config import BRANDING, BRANDING_LINE

logger = logging.getLogger(__name__)

BACK_KB = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="nav:menu")]])


def build_stats_text(stats: dict) -> str:
    return (
        f"<b>{BRANDING}</b>\n"
        f"<code>{BRANDING_LINE}</code>\n\n"
        "📊 <b>Bot Statistics</b>\n\n"
        f"👥 <b>Total Users:</b> {stats['total_users']:,}\n"
        f"📁 <b>Total Files Processed:</b> {stats['total_files']:,}\n"
        f"💎 <b>Premium Users:</b> {stats['premium_users']:,}\n"
        f"📅 <b>Today's Activity:</b> {stats['today_activity']:,}\n\n"
        f"<code>{BRANDING_LINE}</code>"
    )


async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = get_stats()
    text = build_stats_text(stats)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=BACK_KB)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=BACK_KB)
