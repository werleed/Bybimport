import os
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ---------------- Logging ----------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------- Config ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1003184123814"))  # Replace with your group id
ADMIN_ID = int(os.getenv("ADMIN_ID", "7003416998"))      # Replace with your Telegram ID

if not BOT_TOKEN:
    raise SystemExit("❌ Missing BOT_TOKEN environment variable")

# ---------------- Store ----------------
verified_users = {}  # {telegram_id: {"status": "pending|verified|denied", "method": "Bank Transfer", "tx": "receipt/manual"}}

# ---------------- Menu ----------------
def build_menu():
    keyboard = [
        [KeyboardButton("🏦 Bank Transfer")],
        [KeyboardButton("📋 My Status")],
        [KeyboardButton("🔙 Back to Main Menu")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ---------------- Handlers ----------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Welcome to Byb Importation Class!* 🚀\n\n"
        "Here you’ll learn everything about *China Importation*:\n"
        "✅ How to source products\n"
        "✅ How to ship to Nigeria cheaply\n"
        "✅ Avoid scams & bad suppliers\n"
        "✅ Step-by-step guidance until your goods arrive safely\n\n"
        "💡 To join the private class, pay via *Bank Transfer* and upload your receipt.",
        parse_mode="Markdown",
        reply_markup=build_menu()
    )

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "🏦 Bank Transfer":
        await update.message.reply_text(
            "🏦 *Manual Bank Transfer Instructions*\n\n"
            "💰 Send payment to:\n"
            "• Bank: Opay\n"
            "• Account Name: Abdulsalam Sulaiman Attah\n"
            "• Account Number: 9039475752\n\n"
            "📌 After transfer, upload your receipt here (as photo or document).",
            parse_mode="Markdown"
        )

    elif text == "📋 My Status":
        user_status = verified_users.get(user_id, {"status": "not_found"})
        if user_status["status"] == "pending":
            await update.message.reply_text("⏳ Your payment is *pending approval* from admin.", parse_mode="Markdown")
        elif user_status["status"] == "verified":
            await update.message.reply_text("✅ Your payment is *verified*! You should already have your invite link.", parse_mode="Markdown")
        elif user_status["status"] == "denied":
            await update.message.reply_text("❌ Your payment was *denied*. Please contact admin.", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ No payment record found. Please upload your receipt.", parse_mode="Markdown")

    elif text == "🔙 Back to Main Menu":
        await start_cmd(update, context)

# Upload receipt
async def upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    caption = f"📥 New receipt from user {user.id} (@{user.username})\n\nUse /approve {user.id} or /deny {user.id}"

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=caption)
    elif update.message.document:
        file_id = update.message.document.file_id
        await context.bot.send_document(chat_id=ADMIN_ID, document=file_id, caption=caption)
    else:
        await update.message.reply_text("⚠️ Please upload a valid receipt image or document.")
        return

    verified_users[user.id] = {"status": "pending", "method": "Bank Transfer", "tx": "receipt"}
    await update.message.reply_text("📩 Receipt uploaded! Please wait for admin approval.")

# Approve payment
async def approve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /approve <user_id>")
        return

    user_id = int(context.args[0])
    verified_users[user_id] = {"status": "verified", "method": "Bank Transfer", "tx": "manual"}

    invite = await context.bot.create_chat_invite_link(chat_id=GROUP_ID, member_limit=1)
    await context.bot.send_message(chat_id=user_id, text=f"✅ Approved! Here’s your invite link:\n{invite.invite_link}")
    await update.message.reply_text(f"User {user_id} approved ✅")

# Deny payment
async def deny_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /deny <user_id>")
        return

    user_id = int(context.args[0])
    verified_users[user_id] = {"status": "denied", "method": "Bank Transfer", "tx": "manual"}

    await context.bot.send_message(chat_id=user_id, text="❌ Your payment has been denied. Please contact support.")
    await update.message.reply_text(f"User {user_id} denied ❌")

# ---------------- Main ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, upload_handler))
    app.add_handler(CommandHandler("approve", approve_cmd))
    app.add_handler(CommandHandler("deny", deny_cmd))

    app.run_polling()

if __name__ == "__main__":
    main()
