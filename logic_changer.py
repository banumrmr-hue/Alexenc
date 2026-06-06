import logging
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.database import get_or_create_user, increment_user_files
from utils.helpers import require_not_banned, require_membership, can_process
from utils.progress import animate_progress
from modules.logic_changer import run_logic_changer
from config import BRANDING, BRANDING_LINE

logger = logging.getLogger(__name__)

BACK_KB = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="nav:menu")]])

SELECT_TEXT = (
    f"<b>{BRANDING}</b>\n"
    f"<code>{BRANDING_LINE}</code>\n\n"
    "🧠 <b>Logic Changer</b>\n\n"
    "Restructures your code's control flow:\n"
    "• State machine generation\n"
    "• Logic mutation\n"
    "• Control flow flattening\n"
    "• Function restructuring\n\n"
    "📁 <b>Please upload your <code>.py</code> file now.</b>\n\n"
    f"<code>{BRANDING_LINE}</code>"
)


@require_not_banned
@require_membership
async def logic_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["module"] = "logic_changer"
    context.user_data["awaiting_file"] = True
    await query.message.edit_text(SELECT_TEXT, parse_mode="HTML", reply_markup=BACK_KB)


@require_not_banned
async def logic_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    doc = update.message.document
    get_or_create_user(user.id, user.username, user.first_name)

    ok, reason = can_process(user.id)
    if not ok:
        await update.message.reply_text(f"<b>{BRANDING}</b>\n\n{reason}", parse_mode="HTML")
        return

    status_msg = await update.message.reply_text(
        f"<b>{BRANDING}</b>\n\n⚡ Reading File...", parse_mode="HTML"
    )

    try:
        tg_file = await context.bot.get_file(doc.file_id)
        raw = await tg_file.download_as_bytearray()
        source = raw.decode("utf-8")

        final_step = await animate_progress(status_msg, "logic_changer")
        result = run_logic_changer(source)

        await status_msg.edit_text(f"<b>{BRANDING}</b>\n\n{final_step}", parse_mode="HTML")

        out_name = f"LogicChanged_{doc.file_name}"
        out_bytes = io.BytesIO(result.encode("utf-8"))
        out_bytes.name = out_name

        increment_user_files(user.id)
        context.user_data.pop("awaiting_file", None)
        context.user_data.pop("module", None)

        await update.message.reply_document(
            document=out_bytes,
            filename=out_name,
            caption=(
                f"<b>{BRANDING}</b>\n\n"
                "✅ <b>Logic Changer complete!</b>\n"
                f"📁 File: <code>{out_name}</code>\n\n"
                f"<code>{BRANDING_LINE}</code>"
            ),
            parse_mode="HTML",
            reply_markup=BACK_KB,
        )
        await status_msg.delete()

    except Exception as e:
        logger.error(f"Logic Changer error for {user.id}: {e}")
        await status_msg.edit_text(
            f"<b>{BRANDING}</b>\n\n❌ Error: <code>{e}</code>",
            parse_mode="HTML",
            reply_markup=BACK_KB,
        )
