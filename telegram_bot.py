import os
import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
GROUP_ID = int(os.getenv("GROUP_ID"))  # e.g., -100xxxxxxxx

# ----- START COMMAND -----
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Welcome to *Byb Importation Class* 🚀\n\n"
        "To join the private class, you need to complete payment first.\n\n"
        "💳 Use this test link to pay: \n"
        "[Pay Here](https://flutterwave.com/pay/dummy-test-link)\n\n"
        "After payment, send /confirm <email> to verify.",
        parse_mode="Markdown"
    )

# ----- CONFIRM COMMAND -----
def confirm(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        update.message.reply_text("⚠️ Please provide your email. Example:\n/confirm your@email.com")
        return

    email = context.args[0]
    
    # ---- DEMO PAYMENT VERIFICATION (Flutterwave) ----
    url = "https://api.flutterwave.com/v3/transactions"
    headers = {
        "Authorization": f"Bearer {FLW_SECRET_KEY}"
    }
    
    # NOTE: This is just a demo check.
    # In live, you must confirm using transaction_id or reference.
    try:
        response = requests.get(url, headers=headers).json()
    except Exception as e:
        logger.error(e)
        update.message.reply_text("❌ Error checking payment. Please try again later.")
        return

    if response.get("status") == "success":
        try:
            context.bot.invite_link = context.bot.create_chat_invite_link(
                chat_id=GROUP_ID,
                name="Byb Importation Invite",
                member_limit=1
            )
            invite = context.bot.invite_link.invite_link
            update.message.reply_text(
                f"✅ Payment verified!\n\nHere’s your invite link to join the class:\n{invite}"
            )
        except Exception as e:
            logger.error(e)
            update.message.reply_text("❌ Could not add you to the group. Please contact admin.")
    else:
        update.message.reply_text("❌ Payment not found or not successful. Please try again.")

# ----- ERROR HANDLER -----
def error(update: Update, context: CallbackContext):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

# ----- MAIN -----
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("confirm", confirm))

    dp.add_error_handler(error)

    updater.start_polling()
    logger.info("Bot started polling...")
    updater.idle()

if __name__ == '__main__':
    main()
