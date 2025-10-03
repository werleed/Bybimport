import os
import asyncio
import logging
from datetime import datetime, timedelta
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
)

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # set in Railway
ADMIN_ID = int(os.getenv("ADMIN_ID", "7003416998"))  # replace with your real admin ID
GROUP_ID = int(os.getenv("GROUP_ID", "-1002358120135"))  # Telegram group/channel

BANK_NAME = "Opay"
ACCOUNT_NUMBER = "9039475752"
ACCOUNT_NAME = "Abdulsalam Sulaiman Attah"

SUPPORT_USERNAME = "@bybimportsupp"

MAX_COUPONS = 20
COUPON_EXPIRY_HOURS = 24

# ============================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# In-memory stores
coupons = {}  # user_id -> {"code": str, "expires": datetime, "used": bool}
pending_payments = {}  # user_id -> {"receipt": file_id, "status": str}

telegram_app = Application.builder().token(BOT_TOKEN).build()

# ================== MENUS ==================
def user_menu():
    keyboard = [
        [KeyboardButton("💳 Pay with Bank Transfer")],
        [KeyboardButton("🎟️ My Coupon"), KeyboardButton("📋 My Payment Status")],
        [KeyboardButton("📞 Contact Support")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def admin_menu():
    keyboard = [
        [KeyboardButton("📝 Pending Payments")],
        [KeyboardButton("🎟️ Coupon Stats")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================== HELPERS ==================
def generate_coupon(user_id: int):
    if len(coupons) >= MAX_COUPONS:
        return None
    code = f"BYB-{user_id}"
    coupons[user_id] = {
        "code": code,
        "expires": datetime.now() + timedelta(hours=COUPON_EXPIRY_HOURS),
        "used": False
    }
    return coupons[user_id]

def get_coupon(user_id: int):
    c = coupons.get(user_id)
    if not c:
        return None
    if datetime.now() > c["expires"] and not c["used"]:
        del coupons[user_id]  # expire and remove
        return None
    return c

# ================== COMMANDS ==================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text("👮 Welcome Admin!", reply_markup=admin_menu())
    else:
        # give coupon if available
        if user_id not in coupons and len(coupons) < MAX_COUPONS:
            generate_coupon(user_id)
        await update.message.reply_text(
            "👋 Welcome to *Byb Importation Class* 🚀\n\n"
            "Learn everything about China Importation step by step!\n\n"
            "💡 Please complete your payment to join the private group.",
            parse_mode="Markdown",
            reply_markup=user_menu()
        )

# ================== USER FLOW ==================
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if text == "💳 Pay with Bank Transfer":
        coupon = get_coupon(user_id)
        if coupon and not coupon["used"]:
            amount = 45000
            expiry = coupon["expires"].strftime("%Y-%m-%d %H:%M")
            msg = (f"🎟️ You have a valid coupon: {coupon['code']}\n"
                   f"💰 Discounted Amount: ₦{amount}\n"
                   f"⏳ Expires: {expiry}\n\n")
        else:
            amount = 60000
            msg = "💰 Amount: ₦60,000\n\n"

        msg += (
import os
import asyncio
import logging
from datetime import datetime, timedelta
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
)

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # set in Railway
ADMIN_ID = int(os.getenv("ADMIN_ID", "7003416998"))  # replace with your real admin ID
GROUP_ID = int(os.getenv("GROUP_ID", "-1002358120135"))  # Telegram group/channel

BANK_NAME = "Opay"
ACCOUNT_NUMBER = "9039475752"
ACCOUNT_NAME = "Abdulsalam Sulaiman Attah"

SUPPORT_USERNAME = "@bybimportsupp"

MAX_COUPONS = 20
COUPON_EXPIRY_HOURS = 24

# ============================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# In-memory stores
coupons = {}  # user_id -> {"code": str, "expires": datetime, "used": bool}
pending_payments = {}  # user_id -> {"receipt": file_id, "status": str}

telegram_app = Application.builder().token(BOT_TOKEN).build()

# ================== MENUS ==================
def user_menu():
    keyboard = [
        [KeyboardButton("💳 Pay with Bank Transfer")],
        [KeyboardButton("🎟️ My Coupon"), KeyboardButton("📋 My Payment Status")],
        [KeyboardButton("📞 Contact Support")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def admin_menu():
    keyboard = [
        [KeyboardButton("📝 Pending Payments")],
        [KeyboardButton("🎟️ Coupon Stats")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================== HELPERS ==================
def generate_coupon(user_id: int):
    if len(coupons) >= MAX_COUPONS:
        return None
    code = f"BYB-{user_id}"
    coupons[user_id] = {
        "code": code,
        "expires": datetime.now() + timedelta(hours=COUPON_EXPIRY_HOURS),
        "used": False
    }
    return coupons[user_id]

def get_coupon(user_id: int):
    c = coupons.get(user_id)
    if not c:
        return None
    if datetime.now() > c["expires"] and not c["used"]:
        del coupons[user_id]  # expire and remove
        return None
    return c

# ================== COMMANDS ==================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text("👮 Welcome Admin!", reply_markup=admin_menu())
    else:
        # give coupon if available
        if user_id not in coupons and len(coupons) < MAX_COUPONS:
            generate_coupon(user_id)
        await update.message.reply_text(
            "👋 Welcome to *Byb Importation Class* 🚀\n\n"
            "Learn everything about China Importation step by step!\n\n"
            "💡 Please complete your payment to join the private group.",
            parse_mode="Markdown",
            reply_markup=user_menu()
        )

# ================== USER FLOW ==================
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if text == "💳 Pay with Bank Transfer":
        coupon = get_coupon(user_id)
        if coupon and not coupon["used"]:
            amount = 45000
            expiry = coupon["expires"].strftime("%Y-%m-%d %H:%M")
            msg = (f"🎟️ You have a valid coupon: {coupon['code']}\n"
                   f"💰 Discounted Amount: ₦{amount}\n"
                   f"⏳ Expires: {expiry}\n\n")
        else:
            amount = 60000
            msg = "💰 Amount: ₦60,000\n\n"

        msg += (
            f"🏦 Transfer to:\n"
            f"• Bank: {BANK_NAME}\n"
            f"• Account: {ACCOUNT_NUMBER}\n"
            f"• Name: {ACCOUNT_NAME}\n\n"
            "📤 After transfer, upload your receipt here."
        )
        await update.message.reply_text(msg)

    elif text == "🎟️ My Coupon":
        coupon = get_coupon(user_id)
        if coupon and not coupon["used"]:
            hours_left = int((coupon["expires"] - datetime.now()).total_seconds() // 3600)
            await update.message.reply_text(
                f"🎟️ Your coupon: {coupon['code']}\n"
                f"💰 Discounted Amount: ₦45,000\n"
                f"⏳ Expires in {hours_left} hours."
            )
        else:
            await update.message.reply_text("❌ You don’t have an active coupon.")

    elif text == "📋 My Payment Status":
        data = pending_payments.get(user_id)
        if not data:
            await update.message.reply_text("❌ No payment submitted yet.")
        elif data["status"] == "pending":
            await update.message.reply_text("⏳ Your receipt is *waiting for admin approval*.", parse_mode="Markdown")
        elif data["status"] == "approved":
            await update.message.reply_text("✅ Your payment was *approved*!", parse_mode="Markdown")
        elif data["status"] == "rejected":
            await update.message.reply_text("❌ Your payment was *rejected*. Please contact support.", parse_mode="Markdown")

    elif text == "📞 Contact Support":
        await update.message.reply_text(f"📞 Contact us here: {SUPPORT_USERNAME}")

# ================== RECEIPT UPLOAD ==================
async def upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
    elif update.message.document:
        file_id = update.message.document.file_id
    else:
        await update.message.reply_text("⚠️ Please upload a valid receipt image or PDF.")
        return

    pending_payments[user_id] = {"receipt": file_id, "status": "pending"}
    caption = f"📥 Receipt from user {user_id}"
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve:{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject:{user_id}")
        ]
    ]
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))
    await update.message.reply_text("📩 Receipt uploaded. Please wait for admin approval.")

# ================== ADMIN FLOW ==================
async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📝 Pending Payments":
        if not pending_payments:
            await update.message.reply_text("✅ No pending payments.")
            return
        for uid, data in pending_payments.items():
            await update.message.reply_text(f"User {uid} → Status: {data['status']}")

    elif text == "🎟️ Coupon Stats":
        active = sum(1 for c in coupons.values() if not c["used"])
        used = sum(1 for c in coupons.values() if c["used"])
        await update.message.reply_text(
            f"🎟️ Coupon Stats\n"
            f"Total Created: {len(coupons)}\n"
            f"Active: {active}\n"
            f"Used: {used}\n"
            f"Remaining: {MAX_COUPONS - len(coupons)}"
        )

# ================== APPROVE/REJECT CALLBACKS ==================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, uid = query.data.split(":")
    uid = int(uid)

    if action == "approve":
        pending_payments[uid]["status"] = "approved"
        invite = await context.bot.create_chat_invite_link(chat_id=GROUP_ID, name="BYB Invite", member_limit=1)
        await context.bot.send_message(chat_id=uid, text=f"✅ Payment approved! Join the group:\n{invite.invite_link}")
        await query.edit_message_caption(caption=f"✅ Approved payment for user {uid}")

    elif action == "reject":
        pending_payments[uid]["status"] = "rejected"
        await context.bot.send_message(chat_id=uid, text="❌ Your payment was rejected. Please contact support.")
        await query.edit_message_caption(caption=f"❌ Rejected payment for user {uid}")

# ================== MAIN ==================
def main():
    telegram_app.add_handler(CommandHandler("start", start_cmd))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    telegram_app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, upload_handler))
    telegram_app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), admin_menu_handler))
    telegram_app.add_handler(CallbackQueryHandler(callback_handler))

    telegram_app.run_polling()

if __name__ == "__main__":
    main()
