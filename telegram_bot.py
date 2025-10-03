import os
import asyncio
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
    Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
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
PORT = int(os.getenv("PORT", "8000"))

if not BOT_TOKEN or not FLW_SECRET_KEY:
    logger.error("❌ Missing BOT_TOKEN or FLW_SECRET_KEY")
    raise SystemExit("Missing required environment variables")

# In-memory store for verified users
verified_users: Dict[int, Dict[str, Any]] = {}

# Flutterwave sandbox payment link
BASE_FLW_LINK = "https://sandbox.flutterwave.com/pay/oryrdela2fvy"

# FastAPI app
api = FastAPI()

# Telegram bot app
telegram_app = Application.builder().token(BOT_TOKEN).build()


# ----- Build Menu -----
def build_menu():
    keyboard = [
        [KeyboardButton("💳 Pay with Flutterwave")],
        [KeyboardButton("🏦 Bank Transfer")],
        [KeyboardButton("📋 Check Payment Status")],
        [KeyboardButton("🔙 Back to Main Menu")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ----- START -----
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *Byb Importation Class* 🚀\n\n"
        "Choose one of the payment methods below to join:",
        reply_markup=build_menu()
    )


# ----- Menu Handler -----
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    user_id = update.message.from_user.id

    if text == "💳 Pay with Flutterwave":
        tx_ref = f"tg_{user_id}"
        pay_link = f"{BASE_FLW_LINK}?tx_ref={tx_ref}"
        keyboard = [[InlineKeyboardButton("💳 Pay Now", url=pay_link)]]
        await update.message.reply_text(
            "Click below to complete payment securely with Flutterwave:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif text == "🏦 Bank Transfer":
        keyboard = [[InlineKeyboardButton("📤 Upload Receipt", callback_data="upload_receipt")]]
        await update.message.reply_text(
            "🏦 *Bank Transfer Instructions*\n\n"
            "Bank: Opay\n"
            "Account Name: Abdulsalam Sulaiman Attah\n"
            "Account Number: 9039475752\n\n"
            "After transfer, upload your receipt below.",
            reply_markup=InlineKeyboardMarkup(keyboard)
import os
import asyncio
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
    Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
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
PORT = int(os.getenv("PORT", "8000"))

if not BOT_TOKEN or not FLW_SECRET_KEY:
    logger.error("❌ Missing BOT_TOKEN or FLW_SECRET_KEY")
    raise SystemExit("Missing required environment variables")

# In-memory store for verified users
verified_users: Dict[int, Dict[str, Any]] = {}

# Flutterwave sandbox payment link
BASE_FLW_LINK = "https://sandbox.flutterwave.com/pay/oryrdela2fvy"

# FastAPI app
api = FastAPI()

# Telegram bot app
telegram_app = Application.builder().token(BOT_TOKEN).build()


# ----- Build Menu -----
def build_menu():
    keyboard = [
        [KeyboardButton("💳 Pay with Flutterwave")],
        [KeyboardButton("🏦 Bank Transfer")],
        [KeyboardButton("📋 Check Payment Status")],
        [KeyboardButton("🔙 Back to Main Menu")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ----- START -----
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *Byb Importation Class* 🚀\n\n"
        "Choose one of the payment methods below to join:",
        reply_markup=build_menu()
    )


# ----- Menu Handler -----
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    user_id = update.message.from_user.id

    if text == "💳 Pay with Flutterwave":
        tx_ref = f"tg_{user_id}"
        pay_link = f"{BASE_FLW_LINK}?tx_ref={tx_ref}"
        keyboard = [[InlineKeyboardButton("💳 Pay Now", url=pay_link)]]
        await update.message.reply_text(
            "Click below to complete payment securely with Flutterwave:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif text == "🏦 Bank Transfer":
        keyboard = [[InlineKeyboardButton("📤 Upload Receipt", callback_data="upload_receipt")]]
        await update.message.reply_text(
            "🏦 *Bank Transfer Instructions*\n\n"
            "Bank: Opay\n"
            "Account Name: Abdulsalam Sulaiman Attah\n"
            "Account Number: 9039475752\n\n"
            "After transfer, upload your receipt below.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif text == "📋 Check Payment Status":
        if user_id in verified_users:
            data = verified_users[user_id]
            await update.message.reply_text(
                f"📋 Payment Status:\n✅ Verified\nMethod: {data['method']}\nTX: {data['tx']}"
            )
        else:
            await update.message.reply_text("📋 Payment Status:\n❌ Not Verified yet.")

    elif text == "🔙 Back to Main Menu":
        await start_cmd(update, context)


# ----- Callback for Receipt Upload -----
async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "upload_receipt":
        await query.message.reply_text("📤 Please send your receipt (photo or document).")


# ----- Upload Handler -----
async def upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    caption = f"📥 Receipt from {user.id} (@{user.username})"

    if update.message.photo:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=caption)
    elif update.message.document:
        await context.bot.send_document(chat_id=ADMIN_ID, document=update.message.document.file_id, caption=caption)
    else:
        await update.message.reply_text("⚠️ Please upload a valid receipt (photo or doc).")
        return

    await update.message.reply_text("📩 Receipt uploaded! Wait for admin approval.")


# ----- Approve by Admin -----
async def approve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /approve <user_id>")
        return

    user_id = int(context.args[0])
    verified_users[user_id] = {"status": "verified", "tx": "manual", "method": "Bank Transfer"}
    invite = await context.bot.create_chat_invite_link(chat_id=GROUP_ID, name="Byb Importation Invite", member_limit=1)
    await context.bot.send_message(chat_id=user_id, text=f"✅ Approved! Join here:\n{invite.invite_link}")
    await update.message.reply_text(f"User {user_id} approved.")


# ----- Flutterwave Webhook -----
@api.post("/flutterwave-webhook")
async def flutterwave_webhook(request: Request, verif_hash: str = Header(None)):
    body = await request.body()
    if not verif_hash:
        raise HTTPException(status_code=400, detail="Missing signature")

    expected = hmac.new(FLW_SECRET_KEY.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, verif_hash):
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = json.loads(body.decode("utf-8"))
    data = payload.get("data", {})
    if data.get("status", "").lower() in ("successful", "success", "completed"):
        tx_ref = data.get("tx_ref")
        if tx_ref and tx_ref.startswith("tg_"):
            telegram_id = int(tx_ref.split("tg_")[1])
            verified_users[telegram_id] = {"status": "verified", "tx": data.get("id"), "method": "Flutterwave"}
            invite = await telegram_app.bot.create_chat_invite_link(chat_id=GROUP_ID, name="Byb Importation Invite", member_limit=1)
            await telegram_app.bot.send_message(chat_id=telegram_id, text=f"✅ Payment verified!\nHere’s your invite link:\n{invite.invite_link}")

    return {"status": "ok"}


@api.get("/healthz")
async def health():
    return {"status": "ok"}


# ----- Start Services -----
async def start_services():
    telegram_app.add_handler(CommandHandler("start", start_cmd))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    telegram_app.add_handler(CommandHandler("approve", approve_cmd))
    telegram_app.add_handler(CommandHandler("upload", upload_handler))
    telegram_app.add_handler(CallbackQueryHandler(callback_query_handler))
    telegram_app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, upload_handler))

    await telegram_app.initialize()
    await telegram_app.start()
    logger.info("✅ Telegram bot started")

    config = uvicorn.Config(api, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
    await telegram_app.stop()


def main():
    asyncio.run(start_services())


if __name__ == "__main__":
    main()
