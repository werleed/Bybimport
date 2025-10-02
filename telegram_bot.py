import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
GROUP_ID = os.getenv("GROUP_ID")

if not BOT_TOKEN or not FLW_SECRET_KEY or not GROUP_ID:
    raise ValueError("❌ Missing environment variables! Please set BOT_TOKEN, FLW_SECRET_KEY, and GROUP_ID.")

GROUP_ID = int(GROUP_ID)

# ----- START COMMAND -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *Byb Importation Class* 🚀\n\n"
        "To join the private class, you need to complete payment first.\n\n"
        "💳 Use this test link to pay: \n"
        "[Pay Here](https://flutterwave.com/pay/dummy-test-link)\n\n"
        "After payment, send /confirm <tx_ref> to verify.",
        parse_mode="Markdown"
    )

# ----- CONFIRM COMMAND -----
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text(
            "⚠️ Please provide your transaction reference. Example:\n"
            "/confirm tx_ref_12345"
        )
        return

    tx_ref = context.args[0]
    url = f"https://api.flutterwave.com/v3/transactions/verify_by_reference?tx_ref={tx_ref}"
    headers = {"Authorization": f"Bearer {FLW_SECRET_KEY}"}

    try:
        response = requests.get(url, headers=headers).json()
    except Exception as e:
        logger.error(f"Error contacting Flutterwave: {e}")
        await update.message.reply_text("❌ Error checking payment. Please try again later.")
        return

    if response.get("status") == "success" and response["data"]["status"] == "successful":
        try:
            invite = await context.bot.create_chat_invite_link(
                chat_id=GROUP_ID,
                name="Byb Importation Invite",
                member_limit=1
            )
            await update.message.reply_text(
                f"✅ Payment verified!\n\nHere’s your invite link to join the class:\n{invite.invite_link}"
            )
        except Exception as e:
            logger.error(f"Error creating invite link: {e}")
            await update.message.reply_text("❌ Could not generate invite link. Please contact admin.")
    else:
        await update.message.reply_text("❌ Payment not found or not successful. Please try again.")

# ----- MAIN -----
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))

    logger.info("🚀 Bot started polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
