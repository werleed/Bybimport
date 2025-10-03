import os
import logging
import requests
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------- Logging ----------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------- Environment ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
GROUP_ID = int(os.getenv("GROUP_ID", "-1003184123814"))
ADMIN_ID = int(os.getenv("ADMIN_ID", "1234567890"))  # replace with your Telegram ID

if not BOT_TOKEN or not FLW_SECRET_KEY or not GROUP_ID:
    raise ValueError("❌ Missing environment variables! Please set BOT_TOKEN, FLW_SECRET_KEY, GROUP_ID, ADMIN_ID")

# ---------------- Menus ----------------
def build_menu(user_id):
    if user_id == ADMIN_ID:
        # Admin menu
        keyboard = [
            [KeyboardButton("📖 Info"), KeyboardButton("💳 Flutterwave Pay")],
            [KeyboardButton("🏦 Bank Transfer"), KeyboardButton("📩 Confirm Payment")],
            ["👥 Approve Manual", "❌ Revoke User"],
            ["🚫 Revoke All", "📊 Stats", "📥 Logs"],
            ["🔙 Back to Menu"],
        ]
    else:
        # User menu
        keyboard = [
            [KeyboardButton("📖 Info"), KeyboardButton("💳 Flutterwave Pay")],
            [KeyboardButton("🏦 Bank Transfer"), KeyboardButton("📩 Confirm Payment")],
            ["🔙 Back to Menu"],
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ---------------- Start Command ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    welcome_msg = (
        "👋 Welcome to *Byb Importation Class* 🚀\n\n"
        "💳 You can pay via Flutterwave OR make a manual bank transfer.\n"
        "📩 After payment, confirm inside the bot.\n\n"
        "👇 Use the menu below to continue."
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=build_menu(user_id))

# ---------------- Handle Menu Buttons ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "📖 Info":
        await update.message.reply_text(
            "📘 This is the Byb Importation Class.\n"
            "Pay to gain access to the private group.\n"
            "Use the menu options to proceed.",
            reply_markup=build_menu(user_id),
        )

    elif text == "💳 Flutterwave Pay":
        await update.message.reply_text(
            "💳 Pay here:\nhttps://flutterwave.com/pay/dummy-test-link\n\n"
            "After payment, click 📩 Confirm Payment.",
            reply_markup=build_menu(user_id),
        )

    elif text == "🏦 Bank Transfer":
        bank_details = (
            "🏦 *Manual Bank Transfer Instructions*\n\n"
            "💰 Send payment to:\n"
            "• Bank: Opay\n"
            "• Account Name: Abdulsalam Sulaiman Attah\n"
            "• Account Number: 9039475752\n\n"
            "📌 After transfer, upload your receipt using:\n"
            "`/upload`\n\n"
            "⚠️ Admin will review and approve before you join the class."
        )
        await update.message.reply_text(bank_details, parse_mode="Markdown", reply_markup=build_menu(user_id))

    elif text == "📩 Confirm Payment":
        await update.message.reply_text("ℹ️ Use /confirm <email> to verify your payment.", reply_markup=build_menu(user_id))

    elif text == "👥 Approve Manual" and user_id == ADMIN_ID:
        await update.message.reply_text("✅ Use /approve <user_id> to approve manual transfers.", reply_markup=build_menu(user_id))

    elif text == "❌ Revoke User" and user_id == ADMIN_ID:
        await update.message.reply_text("❌ Use /revoke <user_id> to revoke access.", reply_markup=build_menu(user_id))

    elif text == "🚫 Revoke All" and user_id == ADMIN_ID:
        await update.message.reply_text("🚫 Revoking all users (not yet implemented).", reply_markup=build_menu(user_id))

    elif text == "📊 Stats" and user_id == ADMIN_ID:
        await update.message.reply_text("📊 Stats: coming soon.", reply_markup=build_menu(user_id))

    elif text == "📥 Logs" and user_id == ADMIN_ID:
        await update.message.reply_text("📥 Logs: coming soon.", reply_markup=build_menu(user_id))

    elif text == "🔙 Back to Menu":
        await update.message.reply_text("🔙 Back to main menu.", reply_markup=build_menu(user_id))

# ---------------- Flutterwave Confirm (auto invite) ----------------
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("⚠️ Please provide your email. Example:\n/confirm your@email.com")
        return

    email = context.args[0]
    url = "https://api.flutterwave.com/v3/transactions"
    headers = {"Authorization": f"Bearer {FLW_SECRET_KEY}"}

    try:
        response = requests.get(url, headers=headers).json()
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Error checking payment. Please try again later.")
        return

    if response.get("status") == "success":
        try:
            # Direct approval for Flutterwave
            invite = await context.bot.create_chat_invite_link(
                chat_id=GROUP_ID,
                name=f"Invite for {email}",
                member_limit=1
            )
            await update.message.reply_text(
                f"✅ Payment verified successfully!\n\nHere’s your invite link:\n{invite.invite_link}"
            )
        except Exception as e:
            logger.error(e)
            await update.message.reply_text("❌ Could not create invite link. Contact admin.")
    else:
        await update.message.reply_text("❌ Payment not found or not successful. Please try again.")

# ---------------- Upload Receipt ----------------
async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if update.message.document or update.message.photo:
        if update.message.document:
            file = update.message.document
            await context.bot.send_document(
                chat_id=ADMIN_ID,
                document=file.file_id,
                caption=f"📥 Receipt from user {user_id}\nApprove with: /approve {user_id}",
            )
        elif update.message.photo:
            photo = update.message.photo[-1]
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=photo.file_id,
                caption=f"📥 Receipt from user {user_id}\nApprove with: /approve {user_id}",
            )
        await update.message.reply_text("✅ Receipt uploaded successfully!\n⏳ Please wait for admin approval.", reply_markup=build_menu(user_id))
    else:
        await update.message.reply_text("⚠️ Please upload a valid receipt (image or PDF).", reply_markup=build_menu(user_id))

# ---------------- Approve Manual ----------------
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if len(context.args) == 0:
        await update.message.reply_text("⚠️ Usage: /approve <user_id>")
        return
    user_id = int(context.args[0])
    try:
        invite = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID, name=f"Invite for {user_id}", member_limit=1
        )
        await context.bot.send_message(
            chat_id=user_id, text=f"✅ Your payment has been approved!\n\nHere’s your private invite link:\n{invite.invite_link}"
        )
        await update.message.reply_text(f"✅ Approved and invite sent to {user_id}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# ---------------- Main ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CommandHandler("upload", upload))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Set bot commands
    async def set_bot_commands(app):
        commands = [
            BotCommand("start", "Start and open menu"),
            BotCommand("confirm", "Confirm your payment (Flutterwave)"),
            BotCommand("upload", "Upload bank transfer receipt"),
            BotCommand("approve", "Approve manual transfer (admin only)"),
        ]
        await app.bot.set_my_commands(commands)

    app.post_init = lambda _: set_bot_commands(app)

    logger.info("🤖 Bot started polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
