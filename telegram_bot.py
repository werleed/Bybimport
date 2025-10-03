import os
import sqlite3
import logging
from datetime import datetime, timedelta

from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes,
    filters, CallbackQueryHandler
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config from Railway Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))
POOL_SIZE = int(os.getenv("POOL_SIZE", "20"))
COUPON_EXPIRY_HOURS = int(os.getenv("COUPON_EXPIRY_HOURS", "24"))

BANK_NAME = "Opay"
ACCOUNT_NUMBER = "9039475752"
ACCOUNT_NAME = "Abdulsalam Sulaiman Attah"
SUPPORT_USERNAME = "@bybimportsupp"

# Database setup
DB_FILE = "bot.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    coupon_code TEXT,
    coupon_expiry TIMESTAMP,
    payment_status TEXT DEFAULT 'pending'
)""")

c.execute("""CREATE TABLE IF NOT EXISTS coupons (
    code TEXT PRIMARY KEY,
    assigned_to INTEGER,
    expiry TIMESTAMP,
    used INTEGER DEFAULT 0
)""")

conn.commit()

# ---------------- User Menus ----------------
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
        [KeyboardButton("🔄 Reissue Coupon")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ---------------- Helpers ----------------
def generate_coupon(user_id: int):
    # Count used coupons
    c.execute("SELECT COUNT(*) FROM coupons")
    total = c.fetchone()[0]
    if total >= POOL_SIZE:
        return None, None

    # Generate coupon
    code = f"BYB-{user_id}"
    expiry = datetime.utcnow() + timedelta(hours=COUPON_EXPIRY_HOURS)

    c.execute("INSERT OR REPLACE INTO coupons (code, assigned_to, expiry, used) VALUES (?, ?, ?, 0)",
              (code, user_id, expiry))
    c.execute("INSERT OR REPLACE INTO users (user_id, coupon_code, coupon_expiry, payment_status) VALUES (?, ?, ?, 'pending')",
              (user_id, code, expiry))
    conn.commit()
    return code, expiry

def get_coupon(user_id: int):
    c.execute("SELECT coupon_code, coupon_expiry FROM users WHERE user_id=?", (user_id,))
    return c.fetchone()

def get_payment_status(user_id: int):
    c.execute("SELECT payment_status FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    return row[0] if row else "not found"

def set_payment_status(user_id: int, status: str):
    c.execute("UPDATE users SET payment_status=? WHERE user_id=?", (status, user_id))
    conn.commit()

# ---------------- Handlers ----------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text("🔐 Welcome Admin!", reply_markup=admin_menu())
    else:
        await update.message.reply_text(
            "👋 Welcome to *Byb Importation Class* 🚀\n\n"
            "You’ll learn everything about *China Importation*:\n"
            "✅ How to source products\n"
            "✅ How to ship to Nigeria cheaply\n"
            "✅ Avoiding scams & bad suppliers\n"
            "✅ Step-by-step guidance until your goods arrive safely\n\n"
            "💡 Complete payment below to join!",
            parse_mode="Markdown",
            reply_markup=user_menu()
        )

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "💳 Pay with Bank Transfer":
        coupon = get_coupon(user_id)
        if not coupon:
            code, expiry = generate_coupon(user_id)
            if code:
                msg = (f"🎟️ You received a *Discount Coupon!*\n\n"
                       f"Coupon Code: `{code}`\n"
                       f"Valid until: {expiry}\n\n"
                       f"💰 Pay: *₦45,000*")
            else:
                msg = ("⚠️ All coupons are used.\n"
                       "💰 Pay: *₦60,000*")
        else:
            code, expiry = coupon
            msg = (f"🎟️ You already have a coupon!\n\n"
                   f"Coupon Code: `{code}`\n"
                   f"Valid until: {expiry}\n\n"
                   f"💰 Pay: *₦45,000*")

        await update.message.reply_text(
            f"{msg}\n\n"
            f"🏦 Bank Transfer Details:\n"
            f"• Bank: {BANK_NAME}\n"
            f"• Account Name: {ACCOUNT_NAME}\n"
            f"• Account Number: {ACCOUNT_NUMBER}\n\n"
            "📌 After transfer, upload your receipt here.",
            parse_mode="Markdown"
        )

    elif text == "🎟️ My Coupon":
        coupon = get_coupon(user_id)
        if coupon:
            code, expiry = coupon
            await update.message.reply_text(f"🎟️ Your Coupon:\nCode: `{code}`\nExpires: {expiry}", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ You don’t have a coupon.")

    elif text == "📋 My Payment Status":
        status = get_payment_status(user_id)
        await update.message.reply_text(f"📋 Payment Status: *{status}*", parse_mode="Markdown")

    elif text == "📞 Contact Support":
        await update.message.reply_text(f"📞 Contact support here: {SUPPORT_USERNAME}")

    # ---------------- Admin Menu ----------------
    elif user_id == ADMIN_ID:
        if text == "📝 Pending Payments":
            c.execute("SELECT user_id FROM users WHERE payment_status='pending'")
            pending = c.fetchall()
            if not pending:
                await update.message.reply_text("✅ No pending payments.")
            else:
                for u in pending:
                    uid = u[0]
                    buttons = [
                        [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{uid}")],
                        [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{uid}")]
                    ]
                    await update.message.reply_text(f"User {uid} is awaiting approval.", reply_markup=InlineKeyboardMarkup(buttons))

        elif text == "🎟️ Coupon Stats":
            c.execute("SELECT COUNT(*) FROM coupons WHERE used=1")
            used = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM coupons WHERE used=0")
            unused = c.fetchone()[0]
            await update.message.reply_text(f"🎟️ Coupon Stats:\nUsed: {used}\nUnused: {unused}")

        elif text == "🔄 Reissue Coupon":
            await update.message.reply_text("Send /reissue <user_id> to reissue a coupon.")

async def upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message.photo or update.message.document:
        caption = f"📥 New receipt from user {user_id}"
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=caption)
        else:
            file_id = update.message.document.file_id
            await context.bot.send_document(chat_id=ADMIN_ID, document=file_id, caption=caption)
        await update.message.reply_text("📩 Receipt uploaded! Waiting for admin approval.")
    else:
        await update.message.reply_text("⚠️ Please upload a valid receipt image or document.")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("approve_"):
        uid = int(data.split("_")[1])
        set_payment_status(uid, "approved")
        invite = await context.bot.create_chat_invite_link(chat_id=GROUP_ID, member_limit=1)
        await context.bot.send_message(chat_id=uid, text=f"✅ Approved! Join the class here:\n{invite.invite_link}")
        await query.edit_message_text(f"✅ Approved user {uid}")
    elif data.startswith("reject_"):
        uid = int(data.split("_")[1])
        set_payment_status(uid, "rejected")
        await context.bot.send_message(chat_id=uid, text="❌ Your payment was rejected. Contact support for help.")
        await query.edit_message_text(f"❌ Rejected user {uid}")

# ---------------- Main ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, upload_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
