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
BOT_USERNAME = os.getenv("BOT_USERNAME", "Bybimport_bot")

# ---------------- Database ----------------
DB_FILE = "bot.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    coupon_code TEXT,
    coupon_expiry TIMESTAMP,
    payment_status TEXT DEFAULT 'pending',
    wallet REAL DEFAULT 0,
    referred_by INTEGER
)""")

c.execute("""CREATE TABLE IF NOT EXISTS coupons (
    code TEXT PRIMARY KEY,
    assigned_to INTEGER,
    expiry TIMESTAMP,
    used INTEGER DEFAULT 0
)""")

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
    return ReplyKeyboardMarkup([
        [KeyboardButton("💳 Pay with Bank Transfer")],
        [KeyboardButton("🎟️ My Coupon"), KeyboardButton("📋 My Payment Status")],
        [KeyboardButton("💰 My Wallet"), KeyboardButton("👥 My Referral Link")],
        [KeyboardButton("📞 Contact Support")]
    ], resize_keyboard=True)

def admin_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📝 Pending Payments")],
        [KeyboardButton("🎟️ Coupon Stats")],
        [KeyboardButton("🔄 Reissue Coupon")],
        [KeyboardButton("💸 Pending Withdrawals")]
    ], resize_keyboard=True)

# ---------------- Helpers ----------------
def generate_coupon(user_id: int):
    c.execute("SELECT payment_status FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row and row[0] == "approved":  # don't issue coupon to approved users
        return None, None

    c.execute("SELECT COUNT(*) FROM coupons WHERE used=0")
    total = c.fetchone()[0]
    if total >= POOL_SIZE:
        return None, None

    code = f"BYB-{user_id}"
    expiry = datetime.utcnow() + timedelta(hours=COUPON_EXPIRY_HOURS)

    c.execute("INSERT OR REPLACE INTO coupons (code, assigned_to, expiry, used) VALUES (?, ?, ?, 0)",
              (code, user_id, expiry.isoformat()))
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    c.execute("UPDATE users SET coupon_code=?, coupon_expiry=? WHERE user_id=?",
              (code, expiry.isoformat(), user_id))
    conn.commit()
    return code, expiry

def get_coupon(user_id: int):
    c.execute("SELECT coupon_code, coupon_expiry FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row and row[0] and row[1]:
        expiry = datetime.fromisoformat(str(row[1]))
        if datetime.utcnow() > expiry:
            # Expire coupon
            c.execute("UPDATE users SET coupon_code=NULL, coupon_expiry=NULL WHERE user_id=?", (user_id,))
            c.execute("UPDATE coupons SET used=1 WHERE code=?", (row[0],))
            conn.commit()
            return None
    return row

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

# ---------------- Handlers ----------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    # ✅ Lock referral: only first time
    if args and args[0].isdigit():
        ref_id = int(args[0])
        if ref_id != user_id:
            c.execute("SELECT referred_by FROM users WHERE user_id=?", (user_id,))
            row = c.fetchone()
            if row is None:  # new user
                c.execute("INSERT INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, ref_id))
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

    if text == "💳 Pay with Bank Transfer":
        coupon = get_coupon(user_id)
        status = get_payment_status(user_id)

        if status == "approved":
            msg = "✅ You are already approved!"
        elif not coupon:
            code, expiry = generate_coupon(user_id)
            if code:
                hours_left = int((expiry - datetime.utcnow()).total_seconds() // 3600)
                msg = f"🎟️ Discount Coupon: `{code}`\nExpires in: {hours_left} hours\n💰 Pay: *₦45,000*"
            else:
                msg = "⚠️ No coupons available.\n💰 Pay: *₦60,000*"
        else:
            code, expiry = coupon
            hours_left = int((datetime.fromisoformat(str(expiry)) - datetime.utcnow()).total_seconds() // 3600)
            msg = f"🎟️ Coupon: `{code}`\nExpires in: {hours_left} hours\n💰 Pay: *₦45,000*"

        await update.message.reply_text(
            f"{msg}\n\n🏦 Bank: {BANK_NAME}\nAcct: {ACCOUNT_NAME}\nNo: {ACCOUNT_NUMBER}\n\n📌 Upload receipt after payment.",
            parse_mode="Markdown"
        )

    elif text == "🎟️ My Coupon":
        coupon = get_coupon(user_id)
        if coupon:
            code, expiry = coupon
            hours_left = int((datetime.fromisoformat(str(expiry)) - datetime.utcnow()).total_seconds() // 3600)
            await update.message.reply_text(f"🎟️ Coupon: `{code}`\nExpires in: {hours_left} hours", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ No coupon assigned.")

    elif text == "📋 My Payment Status":
        status = get_payment_status(user_id)
        await update.message.reply_text(f"📋 Status: *{status}*", parse_mode="Markdown")

    elif text == "💰 My Wallet":
        bal = get_wallet(user_id)
        await update.message.reply_text(f"💰 Wallet Balance: ₦{bal}\nUse /withdraw to request withdrawal.")

    elif text == "👥 My Referral Link":
        link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        await update.message.reply_text(f"👥 Share your referral link:\n{link}")

    elif text == "📞 Contact Support":
        await update.message.reply_text(f"📞 Support: {SUPPORT_USERNAME}")

    elif user_id == ADMIN_ID:
        if text == "📝 Pending Payments":
            c.execute("SELECT user_id FROM users WHERE payment_status='pending'")
            rows = c.fetchall()
            if not rows:
                await update.message.reply_text("✅ No pending payments.")
            for u in rows:
                uid = u[0]
                buttons = [[InlineKeyboardButton("✅ Approve", callback_data=f"approve_{uid}")],
                           [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{uid}")]]
                await update.message.reply_text(f"User {uid} awaiting approval.", reply_markup=InlineKeyboardMarkup(buttons))

        elif text == "🎟️ Coupon Stats":
            c.execute("SELECT COUNT(*) FROM coupons WHERE used=1")
            used = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM coupons WHERE used=0")
            unused = c.fetchone()[0]
            await update.message.reply_text(f"🎟️ Used: {used}\nUnused: {unused}")

        elif text == "🔄 Reissue Coupon":
            c.execute("SELECT code, assigned_to FROM coupons WHERE expiry < ? AND used=0", (datetime.utcnow().isoformat(),))
            expired = c.fetchall()
            if not expired:
                await update.message.reply_text("✅ No expired coupons.")
            for code, uid in expired:
                btn = [[InlineKeyboardButton("♻️ Reissue", callback_data=f"reissue_{uid}")]]
                await update.message.reply_text(f"Expired {code} (User {uid})", reply_markup=InlineKeyboardMarkup(btn))

        elif text == "💸 Pending Withdrawals":
            c.execute("SELECT id, user_id, amount, bank_name, account_number, account_name FROM withdrawals WHERE status='pending'")
            rows = c.fetchall()
            if not rows:
                await update.message.reply_text("✅ No pending withdrawals.")
            for w in rows:
                wid, uid, amt, bname, accno, accname = w
                btns = [[InlineKeyboardButton("✅ Approve", callback_data=f"wd_ok_{wid}")],
                        [InlineKeyboardButton("❌ Reject", callback_data=f"wd_no_{wid}")]]
                await update.message.reply_text(f"💸 Withdraw {wid}\nUser {uid}\n₦{amt}\n{bname} {accno}\n{accname}", reply_markup=InlineKeyboardMarkup(btns))

# ---------------- Upload Receipt ----------------
async def upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message.photo or update.message.document:
        cap = f"📥 Receipt from {user_id}"
        if update.message.photo:
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=cap)
        else:
            await context.bot.send_document(chat_id=ADMIN_ID, document=update.message.document.file_id, caption=cap)
        await update.message.reply_text("📩 Receipt uploaded. Waiting for admin approval.")
    else:
        await update.message.reply_text("⚠️ Upload a valid receipt.")

# ---------------- Withdraw ----------------
async def withdraw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if len(args) < 4:
        await update.message.reply_text("⚠️ /withdraw <amount> <bank> <account_no> <name>")
        return
    try:
        amt = float(args[0])
    except:
        return await update.message.reply_text("⚠️ Invalid amount.")
    if amt > get_wallet(user_id):
        return await update.message.reply_text("❌ Insufficient balance.")
    bank, acc, name = args[1], args[2], " ".join(args[3:])
    c.execute("INSERT INTO withdrawals (user_id, amount, bank_name, account_number, account_name) VALUES (?,?,?,?,?)",
              (user_id, amt, bank, acc, name))
    c.execute("UPDATE users SET wallet = wallet - ? WHERE user_id=?", (amt, user_id))
    conn.commit()
    await update.message.reply_text("✅ Withdrawal submitted. Await admin approval.")
    await context.bot.send_message(ADMIN_ID, f"💸 Withdrawal from {user_id}\n₦{amt}\n{bank} {acc}\n{name}")

# ---------------- Callback ----------------
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data.startswith("approve_"):
        uid = int(data.split("_")[1])
        set_payment_status(uid, "approved")

        # Referral bonus
        c.execute("SELECT referred_by FROM users WHERE user_id=?", (uid,))
        ref = c.fetchone()
        if ref and ref[0]:
            c.execute("SELECT coupon_code FROM users WHERE user_id=?", (uid,))
            coupon = c.fetchone()[0]
            bonus = 900 if coupon else 1200
            add_to_wallet(ref[0], bonus)
            await context.bot.send_message(ref[0], f"🎉 You earned ₦{bonus} referral bonus!")

        inv = await context.bot.create_chat_invite_link(GROUP_ID, member_limit=1)
        await context.bot.send_message(uid, f"✅ Payment approved! Join here:\n{inv.invite_link}")
        await q.edit_message_text(f"✅ Approved {uid}")

    elif data.startswith("reject_"):
        uid = int(data.split("_")[1])
        set_payment_status(uid, "rejected")
        await context.bot.send_message(uid, "❌ Payment rejected. Contact support.")
        await q.edit_message_text(f"❌ Rejected {uid}")

    elif data.startswith("reissue_"):
        uid = int(data.split("_")[1])
        code, expiry = generate_coupon(uid)
        if code:
            hours_left = int((expiry - datetime.utcnow()).total_seconds() // 3600)
            await context.bot.send_message(uid, f"♻️ New Coupon: {code}\nExpires in {hours_left} hours")
            await q.edit_message_text(f"♻️ Reissued coupon to {uid}")
        else:
            await q.edit_message_text("⚠️ No coupons available")

    elif data.startswith("wd_ok_"):
        wid = int(data.split("_")[2])
        c.execute("UPDATE withdrawals SET status='approved' WHERE id=?", (wid,))
        conn.commit()
        c.execute("SELECT user_id, amount FROM withdrawals WHERE id=?", (wid,))
        u = c.fetchone()
        if u: await context.bot.send_message(u[0], f"✅ Withdrawal ₦{u[1]} approved.")
        await q.edit_message_text(f"✅ Approved withdrawal {wid}")

    elif data.startswith("wd_no_"):
        wid = int(data.split("_")[2])
        c.execute("UPDATE withdrawals SET status='rejected' WHERE id=?", (wid,))
        conn.commit()
        c.execute("SELECT user_id, amount FROM withdrawals WHERE id=?", (wid,))
        u = c.fetchone()
        if u:
            add_to_wallet(u[0], u[1])
            await context.bot.send_message(u[0], f"❌ Withdrawal ₦{u[1]} rejected. Refunded.")
        await q.edit_message_text(f"❌ Rejected withdrawal {wid}")

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
