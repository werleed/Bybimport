import os
import logging
from datetime import datetime, timedelta
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables (from Railway)
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7003416998"))
GROUP_ID = int(os.getenv("GROUP_ID", "-1002358120135"))

COUPON_AMOUNT = int(os.getenv("COUPON_AMOUNT", "45000"))
NORMAL_AMOUNT = int(os.getenv("NORMAL_AMOUNT", "60000"))
MAX_COUPONS = int(os.getenv("MAX_COUPONS", "20"))
SUPPORT_BOT = os.getenv("SUPPORT_BOT", "https://t.me/YourSupportBotUsername")

# State storage
verified_users = {}   # {user_id: {"status": "verified"|"pending", "method": "Bank Transfer"}}
receipts = {}         # {user_id: file_id}
coupons = {}          # {user_id: {"code": str, "expires": datetime}}

# --- MENUS ---
def build_user_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🏦 Bank Transfer")],
            [KeyboardButton("📋 Check Payment Status")],
            [KeyboardButton("☎️ Contact Support")]
        ],
        resize_keyboard=True
    )

def build_admin_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("✅ Approve Payments"), KeyboardButton("❌ Reject Payments")],
            [KeyboardButton("🎟️ Generate Coupons"), KeyboardButton("📊 Coupon Status")]
        ],
        resize_keyboard=True
    )

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text("👋 Welcome Admin! Choose an action:", reply_markup=build_admin_menu())
    else:
        await update.message.reply_text(
            "👋 Welcome to *Byb Importation Class!* 🚀\n\n"
            "Learn everything about *China Importation*:\n"
            "✅ Product sourcing\n✅ Cheap shipping\n✅ Scam avoidance\n✅ Full step-by-step guidance\n\n"
            "💡 To join the private class, complete payment using the menu below.",
            parse_mode="Markdown",
            reply_markup=build_user_menu()
        )

# --- USER MENU ---
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    # User flow
    if text == "🏦 Bank Transfer":
        if user_id in coupons:
            code = coupons[user_id]["code"]
            expires = coupons[user_id]["expires"]
            time_left = expires - datetime.now()
            hours_left = max(0, int(time_left.total_seconds() // 3600))
            amount = COUPON_AMOUNT
            msg = (f"🎟️ You have a coupon! Pay *₦{amount:,}* (instead of ₦{NORMAL_AMOUNT:,}).\n"
                   f"Coupon expires in {hours_left}h.\n\n"
                   "🏦 Transfer to:\n• Bank: Opay\n• Account: Abdulsalam Sulaiman Attah\n• Number: 9039475752")
        else:
            amount = NORMAL_AMOUNT
            msg = (f"🏦 Please transfer *₦{amount:,}* to:\n\n"
                   "• Bank: Opay\n• Account: Abdulsalam Sulaiman Attah\n• Number: 9039475752")
        await update.message.reply_text(msg, parse_mode="Markdown")
        await update.message.reply_text("📤 Upload your receipt as photo/document here after payment.")

    elif text == "📋 Check Payment Status":
        if user_id in verified_users:
            status = verified_users[user_id]["status"]
            if status == "verified":
                await update.message.reply_text("✅ Your payment has been approved! You should have received your invite link.")
            else:
                await update.message.reply_text("⏳ Your payment is still pending admin approval.")
        else:
            await update.message.reply_text("❌ No payment found. Please make a transfer first.")

    elif text == "☎️ Contact Support":
        await update.message.reply_text(f"☎️ Contact support here: {SUPPORT_BOT}")

    # Admin flow
    elif user_id == ADMIN_ID:
        if text == "✅ Approve Payments":
            for uid, file in receipts.items():
                btns = [
                    [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{uid}")],
                    [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{uid}")]
                ]
                await context.bot.send_document(chat_id=ADMIN_ID, document=file,
                                                caption=f"Receipt from user {uid}", reply_markup=InlineKeyboardMarkup(btns))
        elif text == "🎟️ Generate Coupons":
            if len(coupons) < MAX_COUPONS:
                code = f"COUPON{len(coupons)+1}"
                expires = datetime.now() + timedelta(hours=24)
                coupons[ADMIN_ID] = {"code": code, "expires": expires}
                await update.message.reply_text(f"🎟️ Coupon generated: {code} (expires in 24h)")
            else:
                await update.message.reply_text("⚠️ Max coupons reached!")

# --- UPLOAD RECEIPT ---
async def upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
    elif update.message.document:
        file_id = update.message.document.file_id
    else:
        await update.message.reply_text("⚠️ Please upload a valid receipt (photo or document).")
        return

    receipts[user_id] = file_id
    verified_users[user_id] = {"status": "pending", "method": "Bank Transfer"}
    await update.message.reply_text("📩 Receipt uploaded! Waiting for admin approval...")

    # Notify admin
    btns = [
        [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}")],
        [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")]
    ]
    await context.bot.send_document(chat_id=ADMIN_ID, document=file_id,
                                    caption=f"📥 New receipt from {user_id}", reply_markup=InlineKeyboardMarkup(btns))

# --- CALLBACKS (Approve/Reject) ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("approve_"):
        user_id = int(query.data.split("_")[1])
        verified_users[user_id] = {"status": "verified", "method": "Bank Transfer"}
        invite = await context.bot.create_chat_invite_link(chat_id=GROUP_ID, name="Byb Importation Invite", member_limit=1)
        await context.bot.send_message(chat_id=user_id, text=f"✅ Payment approved! Join here:\n{invite.invite_link}")
        await query.edit_message_caption(caption=f"✅ Approved user {user_id}")
    elif query.data.startswith("reject_"):
        user_id = int(query.data.split("_")[1])
        verified_users[user_id] = {"status": "rejected", "method": "Bank Transfer"}
        await context.bot.send_message(chat_id=user_id, text="❌ Your payment was rejected. Please contact support.")
        await query.edit_message_caption(caption=f"❌ Rejected user {user_id}")

# --- MAIN ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, upload_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
