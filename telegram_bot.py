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

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- Config ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))
POOL_SIZE = int(os.getenv("POOL_SIZE", "20"))
COUPON_EXPIRY_HOURS = int(os.getenv("COUPON_EXPIRY_HOURS", "24"))

BANK_NAME = "Opay"
ACCOUNT_NUMBER = "9039475752"
ACCOUNT_NAME = "Abdulsalam Sulaiman Attah"
SUPPORT_USERNAME = "@bybimportsupp"
BOT_USERNAME = os.getenv("BOT_USERNAME", "Bybimport_bot")  # must set manually

# ---------------- Database Setup ----------------
DB_FILE = "bot.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

# Users
c.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    coupon_code TEXT,
    coupon_expiry TIMESTAMP,
    payment_status TEXT DEFAULT 'pending',
    wallet REAL DEFAULT 0,
    referred_by INTEGER
)""")

# Coupons
c.execute("""CREATE TABLE IF NOT EXISTS coupons (
    code TEXT PRIMARY KEY,
    assigned_to INTEGER,
    expiry TIMESTAMP,
    used INTEGER DEFAULT 0
)""")

# Withdrawals
c.execute("""CREATE TABLE IF NOT EXISTS withdrawals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    bank_name TEXT,
    account_number TEXT,
    account_name TEXT,
    status TEXT DEFAULT 'pending',
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)""")
conn.commit()

# ---------------- Menus ----------------
def user_menu():
    keyboard = [
        [KeyboardButton("💳 Pay with Bank Transfer")],
        [KeyboardButton("🎟️ My Coupon"), KeyboardButton("📋 My Payment Status")],
        [KeyboardButton("💰 My Wallet"), KeyboardButton("👥 My Referral Link")],
        [KeyboardButton("📞 Contact Support")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def admin_menu():
    keyboard = [
        [KeyboardButton("📝 Pending Payments")],
        [KeyboardButton("🎟️ Coupon Stats")],
        [KeyboardButton("🔄 Reissue Coupon")],
        [KeyboardButton("💸 Pending Withdrawals")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ---------------- Helpers ----------------
def generate_coupon(user_id: int):
    c.execute("SELECT COUNT(*) FROM coupons")
    total = c.fetchone()[0]
    if total >= POOL_SIZE:
        return None, None

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

def get_wallet(user_id: int):
    c.execute("SELECT wallet FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    return row[0] if row else 0

def add_to_wallet(user_id: int, amount: float):
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    c.execute("UPDATE users SET wallet = wallet + ? WHERE user_id=?", (amount, user_id))
    conn.commit()

# ---------------- User Handlers ----------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    # Track referral
    ref_id = None
    if args and args[0].isdigit():
        ref_id = int(args[0])
        if ref_id != user_id:
            c.execute("INSERT OR IGNORE INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, ref_id))
            conn.commit()

    if user_id == ADMIN_ID:
        await update.message.reply_text("🔐 Welcome Admin!", reply_markup=admin_menu())
    else:
        c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        await update.message.reply_text(
            "👋 Welcome to *Byb Importation Class* 🚀\n\n"
            "✅ Learn how to source from China\n"
            "✅ Ship cheaply\n"
            "✅ Avoid scams\n"
            "✅ Step-by-step mentorship\n\n"
            "💡 Complete payment below to join!",
            parse_mode="Markdown",
            reply_markup=user_menu()
        )

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    # --- User actions ---
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
                msg = ("⚠️ All coupons are used.\n💰 Pay: *₦60,000*")
        else:
            code, expiry = coupon
            msg = (f"🎟️ You already have a coupon!\n\n"
                   f"Coupon Code: `{code}`\n"
                   f"Valid until: {expiry}\n\n"
                   f"💰 Pay: *₦45,000*")

        await update.message.reply_text(
            f"{msg}\n\n"
            f"🏦 Bank Transfer:\n"
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
            await update.message.reply_text(f"🎟️ Coupon: `{code}`\nExpires: {expiry}", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ You don’t have a coupon.")

    elif text == "📋 My Payment Status":
        status = get_payment_status(user_id)
        await update.message.reply_text(f"📋 Payment Status: *{status}*", parse_mode="Markdown")

    elif text == "💰 My Wallet":
        balance = get_wallet(user_id)
        await update.message.reply_text(
            f"💰 Wallet Balance: ₦{balance}\n\nUse /withdraw <amount> <bank> <acct_no> <name> to request withdrawal."
        )

    elif text == "👥 My Referral Link":
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        await update.message.reply_text(f"👥 Share your referral link:\n{ref_link}")

    elif text == "📞 Contact Support":
        await update.message.reply_text(f"📞 Support: {SUPPORT_USERNAME}")

    # --- Admin actions ---
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
                    await update.message.reply_text(f"User {uid} awaiting approval.", reply_markup=InlineKeyboardMarkup(buttons))

        elif text == "🎟️ Coupon Stats":
            c.execute("SELECT COUNT(*) FROM coupons WHERE used=1")
            used = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM coupons WHERE used=0")
            unused = c.fetchone()[0]
            await update.message.reply_text(f"🎟️ Coupons:\nUsed: {used}\nUnused: {unused}")

        elif text == "🔄 Reissue Coupon":
            c.execute("SELECT code, assigned_to FROM coupons WHERE expiry < ? AND used=0", (datetime.utcnow(),))
            expired = c.fetchall()
            if not expired:
                await update.message.reply_text("✅ No expired coupons.")
            else:
                for code, uid in expired:
                    buttons = [[InlineKeyboardButton("♻️ Reissue", callback_data=f"reissue_{uid}")]]
                    await update.message.reply_text(f"Coupon {code} (User {uid}) expired.", reply_markup=InlineKeyboardMarkup(buttons))

        elif text == "💸 Pending Withdrawals":
            c.execute("SELECT id, user_id, amount, bank_name, account_number, account_name FROM withdrawals WHERE status='pending'")
            rows = c.fetchall()
            if not rows:
                await update.message.reply_text("✅ No pending withdrawals.")
            else:
                for w in rows:
                    wid, uid, amt, bname, accno, accname = w
                    buttons = [
                        [InlineKeyboardButton("✅ Approve", callback_data=f"wd_approve_{wid}")],
                        [InlineKeyboardButton("❌ Reject", callback_data=f"wd_reject_{wid}")]
                    ]
                    await update.message.reply_text(
                        f"💸 Withdrawal #{wid}\nUser: {uid}\nAmount: ₦{amt}\nBank: {bname}\nAcct: {accno}\nName: {accname}",
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )

# ---------------- Upload Receipt ----------------
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
        await update.message.reply_text("⚠️ Upload a valid receipt (image or document).")

# ---------------- Withdraw ----------------
async def withdraw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if len(args) < 4:
        await update.message.reply_text("⚠️ Usage: /withdraw <amount> <bank_name> <account_number> <account_name>")
        return
    try:
        amount = float(args[0])
    except:
        await update.message.reply_text("⚠️ Invalid amount.")
        return
    balance = get_wallet(user_id)
    if amount > balance:
        await update.message.reply_text("❌ Insufficient balance.")
        return
    bank_name, account_number, account_name = args[1], args[2], " ".join(args[3:])
    c.execute("INSERT INTO withdrawals (user_id, amount, bank_name, account_number, account_name) VALUES (?, ?, ?, ?, ?)",
              (user_id, amount, bank_name, account_number, account_name))
    c.execute("UPDATE users SET wallet = wallet - ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    await update.message.reply_text("✅ Withdrawal request submitted. Please wait for admin approval.")
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"💸 Withdrawal Request:\nUser: {user_id}\nAmount: ₦{amount}\nBank: {bank_name}\nAcct: {account_number}\nName: {account_name}"
    )

# ---------------- Callback Handler ----------------
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("approve_"):
        uid = int(data.split("_")[1])
        set_payment_status(uid, "approved")

        # ✅ Referral bonus
        c.execute("SELECT referred_by FROM users WHERE user_id=?", (uid,))
        row = c.fetchone()
        if row and row[0]:
            ref_id = row[0]
            # Decide bonus based on coupon or not
            c.execute("SELECT coupon_code FROM users WHERE user_id=?", (uid,))
            if c.fetchone()[0]:
                bonus = 900   # 2% of 45k
            else:
                bonus = 1200  # 2% of 60k
            add_to_wallet(ref_id, bonus)
            await context.bot.send_message(chat_id=ref_id, text=f"🎉 You earned ₦{bonus} referral bonus! It’s added to your wallet.")

        invite = await context.bot.create_chat_invite_link(chat_id=GROUP_ID, member_limit=1)
        await context.bot.send_message(chat_id=uid, text=f"✅ Approved! Join here:\n{invite.invite_link}")
        await query.edit_message_text(f"✅ Approved user {uid}")

    elif data.startswith("reject_"):
        uid = int(data.split("_")[1])
        set_payment_status(uid, "rejected")
        await context.bot.send_message(chat_id=uid, text="❌ Payment rejected. Contact support.")
        await query.edit_message_text(f"❌ Rejected user {uid}")

    elif data.startswith("reissue_"):
        uid = int(data.split("_")[1])
        code, expiry = generate_coupon(uid)
        if code:
            await context.bot.send_message(chat_id=uid, text=f"♻️ Coupon reissued: {code}, valid until {expiry}")
            await query.edit_message_text(f"♻️ Reissued coupon for user {uid}")
        else:
            await query.edit_message_text("⚠️ No coupons left to reissue.")

    elif data.startswith("wd_approve_"):
        wid = int(data.split("_")[2])
        c.execute("UPDATE withdrawals SET status='approved' WHERE id=?", (wid,))
        conn.commit()
        c.execute("SELECT user_id, amount FROM withdrawals WHERE id=?", (wid,))
        row = c.fetchone()
        if row:
            uid, amt = row
            await context.bot.send_message(chat_id=uid, text=f"✅ Withdrawal of ₦{amt} approved. Expect payment soon.")
        await query.edit_message_text(f"✅ Withdrawal {wid} approved.")

    elif data.startswith("wd_reject_"):
        wid = int(data.split("_")[2])
        c.execute("UPDATE withdrawals SET status='rejected' WHERE id=?", (wid,))
        conn.commit()
        c.execute("SELECT user_id, amount FROM withdrawals WHERE id=?", (wid,))
        row = c.fetchone()
        if row:
            uid, amt = row
            add_to_wallet(uid, amt)
            await context.bot.send_message(chat_id=uid, text=f"❌ Withdrawal of ₦{amt} rejected. Refunded to wallet.")
        await query.edit_message_text(f"❌ Withdrawal {wid} rejected and refunded.")

# ---------------- Main ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("withdraw", withdraw_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, upload_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
