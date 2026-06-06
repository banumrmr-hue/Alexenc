import asyncio
import logging
from datetime import date
from telegram import Update
from telegram.ext import ContextTypes
from database.database import (
    get_user, get_or_create_user, set_premium, set_banned, get_stats, get_all_user_ids
)
from utils.helpers import require_admin, plan_badge
from config import BRANDING, BRANDING_LINE, ADMIN_IDS

logger = logging.getLogger(__name__)


@require_admin
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = get_stats()
    text = (
        f"<b>{BRANDING}</b>\n"
        f"<code>{BRANDING_LINE}</code>\n\n"
        "🛠 <b>Admin Panel</b>\n\n"
        f"👥 Total Users: <b>{stats['total_users']:,}</b>\n"
        f"📁 Total Files: <b>{stats['total_files']:,}</b>\n"
        f"💎 Premium Users: <b>{stats['premium_users']:,}</b>\n"
        f"📅 Today: <b>{stats['today_activity']:,}</b>\n\n"
        "<b>Commands:</b>\n"
        "/adduser &lt;user_id&gt;\n"
        "/addpremium &lt;user_id&gt;\n"
        "/removepremium &lt;user_id&gt;\n"
        "/ban &lt;user_id&gt;\n"
        "/unban &lt;user_id&gt;\n"
        "/broadcast &lt;message&gt;\n"
        "/stats\n\n"
        f"<code>{BRANDING_LINE}</code>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


@require_admin
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            f"<b>{BRANDING}</b>\n\nUsage: /adduser &lt;user_id&gt;",
            parse_mode="HTML",
        )
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Must be a number.")
        return

    existing = get_user(uid)
    if existing:
        plan = plan_badge(bool(existing["is_premium"]))
        status = "🚫 Banned" if existing["is_banned"] else "✅ Active"
        await update.message.reply_text(
            f"<b>{BRANDING}</b>\n"
            f"<code>{BRANDING_LINE}</code>\n\n"
            "ℹ️ User already exists:\n\n"
            f"🆔 <b>User ID:</b> <code>{uid}</code>\n"
            f"👤 <b>Name:</b> {existing['first_name'] or 'N/A'}\n"
            f"📅 <b>Join Date:</b> {existing['join_date']}\n"
            f"📦 <b>Plan:</b> {plan}\n"
            f"📊 <b>Status:</b> {status}\n"
            f"📁 <b>Files Total:</b> {existing['files_total']}\n\n"
            f"<code>{BRANDING_LINE}</code>",
            parse_mode="HTML",
        )
        return

    db_user = get_or_create_user(uid, username=None, first_name="Added by Admin")

    name = db_user.get("first_name") or "N/A"
    join = db_user.get("join_date", date.today().isoformat())

    await update.message.reply_text(
        f"<b>{BRANDING}</b>\n"
        f"<code>{BRANDING_LINE}</code>\n\n"
        "✅ <b>User added successfully!</b>\n\n"
        f"🆔 <b>User ID:</b> <code>{uid}</code>\n"
        f"📅 <b>Join Date:</b> {join}\n"
        f"📦 <b>Plan:</b> 🆓 Free\n"
        f"📊 <b>Status:</b> ✅ Active\n\n"
        f"<code>{BRANDING_LINE}</code>",
        parse_mode="HTML",
    )

    try:
        await context.bot.send_message(
            uid,
            f"<b>{BRANDING}</b>\n\n"
            "👋 You have been added to the bot by an admin.\n"
            "Use /start to begin.",
            parse_mode="HTML",
        )
    except Exception:
        pass


@require_admin
async def add_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /addpremium <user_id>")
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
        return

    set_premium(uid, True)
    await update.message.reply_text(
        f"<b>{BRANDING}</b>\n\n✅ User <code>{uid}</code> granted 💎 Premium.",
        parse_mode="HTML",
    )
    try:
        await context.bot.send_message(
            uid,
            f"<b>{BRANDING}</b>\n\n🎉 You have been upgraded to <b>💎 Premium</b>!\n\nEnjoy unlimited usage and the full Premium Combo.",
            parse_mode="HTML",
        )
    except Exception:
        pass


@require_admin
async def remove_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /removepremium <user_id>")
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
        return

    set_premium(uid, False)
    await update.message.reply_text(
        f"<b>{BRANDING}</b>\n\n✅ Premium removed from <code>{uid}</code>.",
        parse_mode="HTML",
    )


@require_admin
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id>")
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
        return
    if uid in ADMIN_IDS:
        await update.message.reply_text("⛔ Cannot ban an admin.")
        return

    set_banned(uid, True)
    await update.message.reply_text(
        f"<b>{BRANDING}</b>\n\n🚫 User <code>{uid}</code> has been banned.",
        parse_mode="HTML",
    )


@require_admin
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /unban <user_id>")
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
        return

    set_banned(uid, False)
    await update.message.reply_text(
        f"<b>{BRANDING}</b>\n\n✅ User <code>{uid}</code> has been unbanned.",
        parse_mode="HTML",
    )


@require_admin
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    msg_text = " ".join(context.args)
    broadcast_text = (
        f"<b>{BRANDING}</b>\n"
        f"<code>{BRANDING_LINE}</code>\n\n"
        f"📢 <b>Broadcast</b>\n\n{msg_text}\n\n"
        f"<code>{BRANDING_LINE}</code>"
    )

    user_ids = get_all_user_ids()
    status = await update.message.reply_text(f"⚡ Broadcasting to {len(user_ids)} users...")
    sent = failed = 0

    for uid in user_ids:
        try:
            await context.bot.send_message(uid, broadcast_text, parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await status.edit_text(
        f"<b>{BRANDING}</b>\n\n"
        f"📢 Broadcast complete!\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}",
        parse_mode="HTML",
    )


@require_admin
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = get_stats()
    text = (
        f"<b>{BRANDING}</b>\n"
        f"<code>{BRANDING_LINE}</code>\n\n"
        "📊 <b>Statistics</b>\n\n"
        f"👥 Total Users: <b>{stats['total_users']:,}</b>\n"
        f"📁 Total Files: <b>{stats['total_files']:,}</b>\n"
        f"💎 Premium Users: <b>{stats['premium_users']:,}</b>\n"
        f"📅 Today's Activity: <b>{stats['today_activity']:,}</b>\n\n"
        f"<code>{BRANDING_LINE}</code>"
    )
    await update.message.reply_text(text, parse_mode="HTML")
