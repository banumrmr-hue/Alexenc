import logging
import io
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import ContextTypes
from database.database import get_or_create_user, increment_user_files, get_user
from utils.helpers import require_not_banned, require_membership, can_process
from utils.progress import animate_progress
from modules.shortpy import run_shortpy
from modules.logic_changer import run_logic_changer
from modules.expiry_injector import run_expiry_injector
from modules.obfuxtreme import run_obfuxtreme
from config import BRANDING, BRANDING_LINE

logger = logging.getLogger(__name__)

BACK_KB = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="nav:menu")]])

SELECT_TEXT = (
    f"<b>{BRANDING}</b>\n"
    f"<code>{BRANDING_LINE}</code>\n\n"
    "💎 <b>Premium Combo</b>\n\n"
    "Full protection pipeline:\n\n"
    "<code>✂️ Short Py\n"
    "    ↓\n"
    "🧠 Logic Changer\n"
    "    ↓\n"
    "🔐 Expiry Inject\n"
    "    ↓\n"
    "⚡ ObfuXtreme</code>\n\n"
    "📁 <b>Please upload your <code>.py</code> file now.</b>\n\n"
    f"<code>{BRANDING_LINE}</code>"
)

DATE_PROMPT_TEXT = (
    f"<b>{BRANDING}</b>\n"
    f"<code>{BRANDING_LINE}</code>\n\n"
    "💎 <b>Premium Combo</b>\n\n"
    "📅 <b>Enter the expiry date for Expiry Inject:</b>\n\n"
    "<b>Format:</b> <code>YYYY-MM-DD</code>\n"
    "<b>Example:</b> <code>2026-12-31</code>\n\n"
    f"<code>{BRANDING_LINE}</code>"
)

NOT_PREMIUM_TEXT = (
    f"<b>{BRANDING}</b>\n"
    f"<code>{BRANDING_LINE}</code>\n\n"
    "💎 <b>Premium Combo</b>\n\n"
    "⛔ This module requires a <b>Premium</b> plan.\n\n"
    "Premium benefits:\n"
    "• Unlimited daily usage\n"
    "• Access to Premium Combo\n"
    "• Priority processing\n\n"
    "Contact an admin to upgrade your account.\n\n"
    f"<code>{BRANDING_LINE}</code>"
)


@require_not_banned
@require_membership
async def combo_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    db_user = get_or_create_user(user.id, user.username, user.first_name)

    if not db_user["is_premium"]:
        await query.message.edit_text(NOT_PREMIUM_TEXT, parse_mode="HTML", reply_markup=BACK_KB)
        return

    context.user_data["module"] = "combo"
    context.user_data["awaiting_file"] = True
    context.user_data.pop("combo_source", None)
    context.user_data.pop("combo_filename", None)
    await query.message.edit_text(SELECT_TEXT, parse_mode="HTML", reply_markup=BACK_KB)


@require_not_banned
async def combo_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    doc = update.message.document
    db_user = get_or_create_user(user.id, user.username, user.first_name)

    if not db_user["is_premium"]:
        await update.message.reply_text(NOT_PREMIUM_TEXT, parse_mode="HTML", reply_markup=BACK_KB)
        return

    ok, reason = can_process(user.id)
    if not ok:
        await update.message.reply_text(f"<b>{BRANDING}</b>\n\n{reason}", parse_mode="HTML")
        return

    tg_file = await context.bot.get_file(doc.file_id)
    raw = await tg_file.download_as_bytearray()
    source = raw.decode("utf-8")

    context.user_data["combo_source"] = source
    context.user_data["combo_filename"] = doc.file_name
    context.user_data["awaiting_date"] = True
    context.user_data.pop("awaiting_file", None)

    await update.message.reply_text(
        DATE_PROMPT_TEXT,
        parse_mode="HTML",
        reply_markup=ForceReply(selective=True),
    )


@require_not_banned
async def combo_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    date_str = update.message.text.strip()

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        await update.message.reply_text(
            f"<b>{BRANDING}</b>\n\n"
            "❌ Invalid format. Use <code>YYYY-MM-DD</code>\n"
            "Example: <code>2026-12-31</code>",
            parse_mode="HTML",
        )
        return

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text(
            f"<b>{BRANDING}</b>\n\n❌ Invalid date. Please check and try again.",
            parse_mode="HTML",
        )
        return

    source = context.user_data.get("combo_source")
    filename = context.user_data.get("combo_filename", "output.py")

    if not source:
        await update.message.reply_text(
            f"<b>{BRANDING}</b>\n\n❌ No file found. Please restart with 💎 Premium Combo.",
            parse_mode="HTML",
            reply_markup=BACK_KB,
        )
        return

    status_msg = await update.message.reply_text(
        f"<b>{BRANDING}</b>\n\n⚡ Starting Premium Combo Pipeline...", parse_mode="HTML"
    )

    try:
        final_step = await animate_progress(status_msg, "combo", delay=0.8)

        code = source
        code = run_shortpy(code)
        code = run_logic_changer(code)
        code = run_expiry_injector(code, date_str)
        code = run_obfuxtreme(code)

        await status_msg.edit_text(f"<b>{BRANDING}</b>\n\n{final_step}", parse_mode="HTML")

        base_name = filename.replace(".py", "")
        out_name = f"Alex_PremiumProtected_{base_name}.py"
        out_bytes = io.BytesIO(code.encode("utf-8"))
        out_bytes.name = out_name

        increment_user_files(user.id)
        context.user_data.pop("combo_source", None)
        context.user_data.pop("combo_filename", None)
        context.user_data.pop("awaiting_date", None)
        context.user_data.pop("module", None)

        await update.message.reply_document(
            document=out_bytes,
            filename=out_name,
            caption=(
                f"<b>{BRANDING}</b>\n\n"
                "✅ <b>Premium Combo complete!</b>\n"
                f"📁 File: <code>{out_name}</code>\n"
                f"📅 Expires: <code>{date_str}</code>\n\n"
                "Pipeline applied:\n"
                "<code>✂️ Short Py → 🧠 Logic Changer → 🔐 Expiry Inject → ⚡ ObfuXtreme</code>\n\n"
                f"<code>{BRANDING_LINE}</code>"
            ),
            parse_mode="HTML",
            reply_markup=BACK_KB,
        )
        await status_msg.delete()

    except Exception as e:
        logger.error(f"Premium Combo error for {user.id}: {e}")
        await status_msg.edit_text(
            f"<b>{BRANDING}</b>\n\n❌ Error: <code>{e}</code>",
            parse_mode="HTML",
            reply_markup=BACK_KB,
        )
