import logging
import io
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import ContextTypes
from database.database import get_or_create_user, increment_user_files
from utils.helpers import require_not_banned, require_membership, can_process
from utils.progress import animate_progress
from modules.expiry_injector import run_expiry_injector
from config import BRANDING, BRANDING_LINE

logger = logging.getLogger(__name__)

BACK_KB = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="nav:menu")]])

SELECT_TEXT = (
    f"<b>{BRANDING}</b>\n"
    f"<code>{BRANDING_LINE}</code>\n\n"
    "🔐 <b>Expiry Inject</b>\n\n"
    "Injects time-based expiry protection:\n"
    "• Detects expiry date\n"
    "• Blocks execution after expiry\n"
    "• Checks debugger presence\n"
    "• Verifies code integrity\n"
    "• Prevents time rollback\n\n"
    "📁 <b>Please upload your <code>.py</code> file now.</b>\n\n"
    f"<code>{BRANDING_LINE}</code>"
)

DATE_PROMPT_TEXT = (
    f"<b>{BRANDING}</b>\n"
    f"<code>{BRANDING_LINE}</code>\n\n"
    "🔐 <b>Expiry Inject</b>\n\n"
    "📅 <b>Enter the expiry date:</b>\n\n"
    "<b>Format:</b> <code>YYYY-MM-DD</code>\n"
    "<b>Example:</b> <code>2026-12-31</code>\n\n"
    f"<code>{BRANDING_LINE}</code>"
)


@require_not_banned
@require_membership
async def expiry_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["module"] = "expiry"
    context.user_data["awaiting_file"] = True
    context.user_data.pop("expiry_source", None)
    context.user_data.pop("expiry_filename", None)
    await query.message.edit_text(SELECT_TEXT, parse_mode="HTML", reply_markup=BACK_KB)


@require_not_banned
async def expiry_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    doc = update.message.document

    ok, reason = can_process(user.id)
    if not ok:
        await update.message.reply_text(f"<b>{BRANDING}</b>\n\n{reason}", parse_mode="HTML")
        return

    tg_file = await context.bot.get_file(doc.file_id)
    raw = await tg_file.download_as_bytearray()
    source = raw.decode("utf-8")

    context.user_data["expiry_source"] = source
    context.user_data["expiry_filename"] = doc.file_name
    context.user_data["awaiting_date"] = True
    context.user_data.pop("awaiting_file", None)

    await update.message.reply_text(
        DATE_PROMPT_TEXT,
        parse_mode="HTML",
        reply_markup=ForceReply(selective=True),
    )


@require_not_banned
async def expiry_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    source = context.user_data.get("expiry_source")
    filename = context.user_data.get("expiry_filename", "output.py")

    if not source:
        await update.message.reply_text(
            f"<b>{BRANDING}</b>\n\n❌ No file found. Please restart with 🔐 Expiry Inject.",
            parse_mode="HTML",
            reply_markup=BACK_KB,
        )
        return

    status_msg = await update.message.reply_text(
        f"<b>{BRANDING}</b>\n\n⚡ Injecting Expiry Protection...", parse_mode="HTML"
    )

    try:
        final_step = await animate_progress(status_msg, "expiry")
        result = run_expiry_injector(source, date_str)

        await status_msg.edit_text(f"<b>{BRANDING}</b>\n\n{final_step}", parse_mode="HTML")

        out_name = f"ExpiryProtected_{filename}"
        out_bytes = io.BytesIO(result.encode("utf-8"))
        out_bytes.name = out_name

        increment_user_files(user.id)
        context.user_data.pop("expiry_source", None)
        context.user_data.pop("expiry_filename", None)
        context.user_data.pop("awaiting_date", None)
        context.user_data.pop("module", None)

        await update.message.reply_document(
            document=out_bytes,
            filename=out_name,
            caption=(
                f"<b>{BRANDING}</b>\n\n"
                "✅ <b>Expiry Inject complete!</b>\n"
                f"📁 File: <code>{out_name}</code>\n"
                f"📅 Expires: <code>{date_str}</code>\n\n"
                f"<code>{BRANDING_LINE}</code>"
            ),
            parse_mode="HTML",
            reply_markup=BACK_KB,
        )
        await status_msg.delete()

    except Exception as e:
        logger.error(f"Expiry inject error for {user.id}: {e}")
        await status_msg.edit_text(
            f"<b>{BRANDING}</b>\n\n❌ Error: <code>{e}</code>",
            parse_mode="HTML",
            reply_markup=BACK_KB,
        )
