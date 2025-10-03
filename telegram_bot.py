import os
import logging
import requests
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup
)
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

# Storage for verified users (in memory)
verified_users = {}

# Flutterwave Sandbox Payment Link (replace with live later)
FLW_PAY_LINK = "https://sandbox.flutterwave.com/pay/osi7s2n4i39v"

# -------- MENU --------
def build_menu():
    keyboard = [
        [KeyboardButton("💳 Pay with Flutterwave")],
        [KeyboardButton("🏦 Bank Transfer")],
        [KeyboardButton("📋 Check Payment Status")],
        [KeyboardButton("🔙 Back to Main Menu")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Welcome to Byb Importation Class!* 🚀\n\n"
        "Here, you’ll learn everything about *China Importation*:\n"
        "✅ How to source products\n"
        "✅ How to ship to Nigeria cheaply\n"
        "✅ Avoiding scams & bad suppliers\n"
        "✅ Step-by-step guidance until your goods arrive safely\n\n"
        "💡 To join the private class, complete payment using one of the options below.",
        parse_mode="Markdown",
        reply_markup=build_menu()
    )

# -------- MENU HANDLER --------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    user_id = update.message.from_user.id

    if text == "💳 Pay with Flutterwave":
        keyboard = [[InlineKeyboardButton("💳 Pay Now", url=FLW_PAY_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "💳 Click the button below to pay via Flutterwave:",
            reply_markup=reply_markup
        )

    elif text == "🏦 Bank Transfer":
        keyboard = [[InlineKeyboardButton("📤 Upload Receipt", callback_data="upload_receipt")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🏦 *Manual Bank Transfer Instructions*\n\n"
            "💰 Send payment to:\n"
            "• Bank: Opay\n"
            "• Account Name: Abdulsalam Sulaiman Attah\n"
            "• Account Number: 9039475752\n\n"
            "📌 After transfer, click below to upload your receipt.",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    elif text == "📋 Check Payment Status":
        if user_id in verified_users:
            data = verified_users[user_id]
            await update.message.reply_text(
                f"📋 *Payment Status*\n\n"
                f"Status: ✅ Verified\n"
                f"Method: {data['method']}\n"
                f"Transaction ID: {data['tx']}",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "📋 *Payment Status*\n\n"
                "Status: ❌ Not Verified\n"
                "Please complete payment first.",
                parse_mode="Markdown"
            )

    elif text == "🔙 Back to Main Menu":
        await start(update, context)

# -------- CALLBACK HANDLER --------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "upload_receipt":
        await query.message.reply_text(
            "📤 Please send your payment receipt now (photo, pdf, or document)."
        )

# -------- CONFIRM PAYMENT (Flutterwave) --------
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("⚠️ Please provide your transaction ID. Example:\n/confirm 123456789")
        return

    tx_id = context.args[0]
    url = f"https://api.flutterwave.com/v3/transactions/{tx_id}/verify"
    headers = {"Authorization": f"Bearer {FLW_SECRET_KEY}"}

    try:
        response = requests.get(url, headers=headers).json()
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Error checking payment.")
        return

    if response.get("status") == "success" and response["data"]["status"] == "successful":
        user_id = update.message.from_user.id
        verified_users[user_id] = {
            "status": "verified",
            "tx": tx_id,
            "method": "Flutterwave"
        }
        try:
            invite = await context.bot.create_chat_invite_link(
                chat_id=GROUP_ID,
                name="Byb Importation Invite",
                member_limit=1
            )
            await update.message.reply_text(
                f"✅ Payment verified!\nHere’s your invite link:\n{invite.invite_link}"
            )
        except Exception as e:
            logger.error(e)
            await update.message.reply_text("❌ Could not generate invite link.")
    else:
        await update.message.reply_text("❌ Payment not found or not successful.")

# -------- UPLOAD RECEIPT (Bank Transfer) --------
async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    caption = f"📥 New receipt from user {user.id} (@{user.username})"

    if update.message.photo:
        file = update.message.photo[-1].file_id
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=file, caption=caption)
    elif update.message.document:
        file = update.message.document.file_id
        await context.bot.send_document(chat_id=ADMIN_ID, document=file, caption=caption)
    else:
        await update.message.reply_text("⚠️ Please upload a valid receipt image or document.")
        return

    await update.message.reply_text("📩 Receipt uploaded! Please wait for admin approval.")

# -------- APPROVE (Admin only) --------
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /approve <user_id>")
        return

    user_id = int(context.args[0])
    verified_users[user_id] = {"status": "verified", "tx": "manual", "method": "Bank Transfer"}

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
async def reset_webhook(app: Application):
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
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, upload))
    app.add_handler(MessageHandler(filters.Document.ALL, upload))
    app.add_handler(MessageHandler(filters.PHOTO, upload))

    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(button_handler))

    app.post_init = reset_webhook
    logger.info("🚀 Bot starting in polling mode")
    app.run_polling()

if __name__ == "__main__":
    main()
