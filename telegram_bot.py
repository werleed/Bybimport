import os
import hmac
import hashlib
import json
import logging
from typing import Dict, Any

from fastapi import FastAPI, Request, Header, HTTPException
import uvicorn

from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes,
    filters, CallbackQueryHandler
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

if not BOT_TOKEN or not FLW_SECRET_KEY:
    logger.error("Missing BOT_TOKEN or FLW_SECRET_KEY")
    raise SystemExit("❌ Missing required environment variables")

# In-memory verified users
verified_users: Dict[int, Dict[str, Any]] = {}

# Sandbox Flutterwave payment link
BASE_FLW_LINK = "https://sandbox.flutterwave.com/pay/oryrdela2fvy"

# FastAPI app for webhook
api = FastAPI()

# Telegram application
telegram_app = Application.builder().token(BOT_TOKEN).build()


# ===== MENU BUILDER =====
def build_menu():
    keyboard = [
        [KeyboardButton("💳 Pay with Flutterwave")],
        [KeyboardButton("🏦 Bank Transfer")],
        [KeyboardButton("📋 Check Payment Status")],
        [KeyboardButton("🔙 Back to Main Menu")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ===== START COMMAND =====
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *Byb Importation Class* 🚀\n\n"
        "Here, you’ll learn everything about *China Importation*:\n"
        "✅ How to source products\n"
        "✅ How to ship to Nigeria cheaply\n"
        "✅ Avoid scams & bad suppliers\n"
        "✅ Step-by-step guidance until your goods arrive safely\n\n"
        "💡 Choose a payment option below to get started:",
        parse_mode="Markdown",
        reply_markup=build_menu()
    )


# ===== MENU HANDLER =====
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    user_id = update.message.from_user.id

    if text == "💳 Pay with Flutterwave":
        tx_ref = f"tg_{user_id}"
        pay_link = f"{BASE_FLW_LINK}?tx_ref={tx_ref}"
        keyboard = [[InlineKeyboardButton("💳 Pay Now", url=pay_link)]]
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
            "💰 Bank: Opay\n"
            "👤 Account Name: Abdulsalam Sulaiman Attah\n"
            "🔢 Account Number: 9039475752\n\n"
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
        await start_cmd(update, context)


# ===== CALLBACK HANDLER =====
async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "upload_receipt":
        await query.message.reply_text("📤 Please send your payment receipt (photo, pdf, or document).")


# ===== UPLOAD HANDLER =====
async def upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    caption = f"📥 New receipt from user {user.id} (@{user.username})"

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=caption)
    elif update.message.document:
        file_id = update.message.document.file_id
        await context.bot.send_document(chat_id=ADMIN_ID, document=file_id, caption=caption)
    else:
        await update.message.reply_text("⚠️ Please upload a valid receipt image or document.")
        return

    await update.message.reply_text("📩 Receipt uploaded! Please wait for admin approval.")


# ===== APPROVE COMMAND =====
async def approve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /approve <user_id>")
        return

    user_id = int(context.args[0])
    verified_users[user_id] = {"status": "verified", "tx": "manual", "method": "Bank Transfer"}
    invite = await context.bot.create_chat_invite_link(
        chat_id=GROUP_ID, name="Byb Importation Invite", member_limit=1
    )
    await context.bot.send_message(chat_id=user_id, text=f"✅ Approved! Join here:\n{invite.invite_link}")
    await update.message.reply_text(f"User {user_id} approved.")


# ===== FLUTTERWAVE WEBHOOK =====
@api.post("/flutterwave-webhook")
async def flutterwave_webhook(request: Request, verif_hash: str = Header(None)):
    body = await request.body()

    if not verif_hash:
        raise HTTPException(status_code=400, detail="Missing signature header")

    expected = hmac.new(FLW_SECRET_KEY.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, verif_hash):
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = json.loads(body.decode("utf-8"))
    data = payload.get("data", {})
    status = data.get("status")

    if status and status.lower() in ("successful", "success", "completed"):
        tx_ref = data.get("tx_ref")
        if tx_ref and tx_ref.startswith("tg_"):
            telegram_id = int(tx_ref.split("tg_")[1])
            verified_users[telegram_id] = {
                "status": "verified",
                "tx": data.get("id"),
                "method": "Flutterwave"
            }
            invite = await telegram_app.bot.create_chat_invite_link(
                chat_id=GROUP_ID, name="Byb Importation Invite", member_limit=1
            )
            await telegram_app.bot.send_message(
                chat_id=telegram_id,
                text=f"✅ Payment verified!\nHere’s your invite link:\n{invite.invite_link}"
            )

    return {"status": "ok"}


@api.get("/healthz")
async def health():
    return {"status": "ok"}


# ===== MAIN =====
def main():
    telegram_app.add_handler(CommandHandler("start", start_cmd))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    telegram_app.add_handler(CommandHandler("approve", approve_cmd))
    telegram_app.add_handler(CallbackQueryHandler(callback_query_handler))
    telegram_app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, upload_handler))

    # Start polling Telegram
    telegram_app.run_polling()


if __name__ == "__main__":
    main()
