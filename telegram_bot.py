import os
import logging
import requests
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Config
BOT_TOKEN = os.getenv("BOT_TOKEN")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
GROUP_ID = int(os.getenv("GROUP_ID", "-1003184123814"))
ADMIN_ID = int(os.getenv("ADMIN_ID", "7003416998"))

# -------- MENU --------
def build_menu():
    keyboard = [
        [KeyboardButton("💳 Pay with Flutterwave")],
        [KeyboardButton("🏦 Bank Transfer")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *Byb Importation Class* 🚀\n\n"
        "Choose a payment method:",
        parse_mode="Markdown",
        reply_markup=build_menu()
    )

# -------- MENU HANDLER --------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    if text == "💳 Pay with Flutterwave":
        await update.message.reply_text(
            "💳 Use this link to pay via Flutterwave:\n"
            "[Pay Here](https://flutterwave.com/pay/dummy-test-link)\n\n"
            "After payment, send /confirm <email> to verify.",
            parse_mode="Markdown"
        )
    elif text == "🏦 Bank Transfer":
        await update.message.reply_text(
            "🏦 *Manual Bank Transfer Instructions*\n\n"
            "💰 Send payment to:\n"
            "• Bank: Opay\n"
            "• Account Name: Abdulsalam Sulaiman Attah\n"
            "• Account Number: 9039475752\n\n"
            "📌 After transfer, upload your receipt using:\n"
            "`/upload`\n\n"
            "⚠️ Admin will review and approve before you join the class.",
            parse_mode="Markdown",
            reply_markup=build_menu()
        )

# -------- CONFIRM PAYMENT (Flutterwave) --------
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
        await update.message.reply_text("❌ Error checking payment.")
        return

    if response.get("status") == "success":
        try:
            invite = await context.bot.create_chat_invite_link(
                chat_id=GROUP_ID,
                name="Byb Importation Invite",
                member_limit=1
            )
            await update.message.reply_text(f"✅ Payment verified!\nHere’s your invite link:\n{invite.invite_link}")
        except Exception as e:
            logger.error(e)
            await update.message.reply_text("❌ Could not generate invite link.")
    else:
        await update.message.reply_text("❌ Payment not found or not successful.")

# -------- UPLOAD RECEIPT (Bank Transfer) --------
async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        file = update.message.photo[-1].file_id
        caption = f"📥 New receipt from user {update.message.from_user.id} (@{update.message.from_user.username})"
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=file, caption=caption)
        await update.message.reply_text("📩 Receipt uploaded! Please wait for admin approval.")
    else:
        await update.message.reply_text("⚠️ Please send a valid receipt image.")

# -------- APPROVE (Admin only) --------
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /approve <user_id>")
        return

    user_id = int(context.args[0])
    try:
        invite = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            name="Byb Importation Invite",
            member_limit=1
        )
        await context.bot.send_message(chat_id=user_id, text=f"✅ Approved! Join here:\n{invite.invite_link}")
        await update.message.reply_text(f"User {user_id} approved.")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Failed to approve.")

# -------- MAIN (Polling Mode + Webhook Reset) --------
async def reset_webhook(app):
    # Clear any existing webhook to avoid conflicts
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Old webhook cleared, bot will start in polling mode")
    except Exception as e:
        logger.warning(f"Could not delete webhook: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CommandHandler("upload", upload))
    app.add_handler(CommandHandler("approve", approve))

    # Reset webhook and run polling
    app.post_init = reset_webhook
    logger.info("🚀 Bot starting in polling mode")
    app.run_polling()

if __name__ == "__main__":
    main()
