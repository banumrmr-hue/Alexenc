import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import BRANDING, BRANDING_LINE

logger = logging.getLogger(__name__)

BACK_KB = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="nav:menu")]])

HELP_TEXT = (
    f"<b>{BRANDING}</b>\n"
    f"<code>{BRANDING_LINE}</code>\n\n"
    "ℹ️ <b>Help — Module Guide</b>\n\n"

    "⚡ <b>ObfuXtreme</b>\n"
    "Applies powerful multi-layer code obfuscation:\n"
    "• Variable renaming\n"
    "• AES-256 string encryption\n"
    "• Marshal protection\n"
    "• Zlib compression\n"
    "• Loader generation\n"
    "• Anti-debug detection\n"
    "• Code integrity check\n\n"

    "🧠 <b>Logic Changer</b>\n"
    "Transforms your code's control flow:\n"
    "• State machine generation\n"
    "• Logic mutation\n"
    "• Control flow flattening\n"
    "• Function restructuring\n\n"

    "🔐 <b>Expiry Inject</b>\n"
    "Injects time-based expiry protection:\n"
    "• Set a custom expiry date (YYYY-MM-DD)\n"
    "• Blocks execution after expiry\n"
    "• Detects debuggers\n"
    "• Checks code integrity\n"
    "• Prevents time rollback attacks\n\n"

    "✂️ <b>Short Py</b>\n"
    "Minifies and shrinks your Python code:\n"
    "• Removes comments & docstrings\n"
    "• Renames variables & globals\n"
    "• Removes assertions\n"
    "• Combines imports\n"
    "• Compresses overall code size\n\n"

    "💎 <b>Premium Combo</b>\n"
    "Full protection pipeline (Premium only):\n"
    "<code>Short Py → Logic Changer → Expiry Inject → ObfuXtreme</code>\n\n"

    f"<code>{BRANDING_LINE}</code>\n\n"
    "📌 <b>How to use:</b>\n"
    "1. Choose a module from the menu\n"
    "2. Upload your <code>.py</code> file\n"
    "3. Receive the protected file instantly\n\n"
    "💡 <b>Tip:</b> Upgrade to Premium for unlimited usage and the full combo module."
)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            HELP_TEXT, parse_mode="HTML", reply_markup=BACK_KB
        )
    else:
        await update.message.reply_text(HELP_TEXT, parse_mode="HTML", reply_markup=BACK_KB)
