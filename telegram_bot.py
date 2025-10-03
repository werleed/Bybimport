import os
import asyncio
import logging
from fastapi import FastAPI, Request
import uvicorn
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "8080"))

if not BOT_TOKEN:
    raise SystemExit("❌ Missing BOT_TOKEN environment variable")

# FastAPI app
api = FastAPI()

@api.get("/healthz")
async def health():
    return {"status": "ok"}

@api.post("/flutterwave-webhook")
async def flutterwave_webhook(request: Request):
    body = await request.body()
    logger.info(f"📩 Webhook received: {body.decode()}")
    return {"status": "ok"}

# Telegram Bot app
telegram_app = Application.builder().token(BOT_TOKEN).build()

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is alive and webhook server is running!")

telegram_app.add_handler(CommandHandler("start", start_cmd))

# Run both Telegram and FastAPI
async def main():
    # Start Telegram bot in background
    asyncio.create_task(telegram_app.run_polling())
    # Start FastAPI server
    config = uvicorn.Config(api, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
