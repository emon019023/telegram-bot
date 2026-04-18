import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import random
import string

# ================= CONFIG =================
import os
TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = "@vipincomex_bot"
CHANNEL_LINK = "https://t.me/incomezone1000"
CHANNEL_USERNAME = "@incomezone1000"
ADMIN_ID = 7036481355

bot = telebot.TeleBot(TOKEN)

# ================= DATABASE =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0,
    total_income REAL DEFAULT 0,
    completed INTEGER DEFAULT 0,
    pending INTEGER DEFAULT 0,
    refer INTEGER DEFAULT 0,
    refer_income REAL DEFAULT 0,
    ref_by INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    email TEXT,
    password TEXT,
    status TEXT DEFAULT 'pending'
)
""")

# ✅✅ WITHDRAW TABLE START
cursor.execute("""
CREATE TABLE IF NOT EXISTS withdraws (
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
amount REAL,
number TEXT,
status TEXT DEFAULT 'pending'
)
""")
# 💥💥 WITHDRAW TABLE END



# ================= JOIN CHECK =================
def is_joined(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def join_msg():
    text = """🎁 Welcome to Income Bot

⚠️ সম্পূর্ণ ফিচার ব্যবহার করতে হলে আগে চ্যানেলে জয়েন করতে হবে

📢 কেন জয়েন করবেন?
✔️ নতুন আপডেট
✔️ ইনকাম প্রুফ
✔️ নতুন কাজ

👇 এখনই জয়েন করুন

✅ জয়েন শেষে "Join Done" চাপুন"""
    
    m = InlineKeyboardMarkup()
    m.row(InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
    m.row(InlineKeyboardButton("✅ Join Done", callback_data="join_done"))
    return text, m

# ================= RANDOM DATA =================
bd_names = ["Priya","Nila","Sumaiya","Ayesha","Riya","Tania","Mim","Jannat","Sadia","Nusrat","Farzana","Lamia"]

def generate_gmail_data():
    name = random.choice(bd_names)
    num = random.randint(1000,9999)
    email = f"{name.lower()}{num}pro@gmail.com"
    rand = ''.join(random.choices(string.ascii_lowercase, k=5))
    password = f"{name.lower()}gmpro{rand}"
    return name, email, password

# ================= USER =================
def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return get_user(user_id)

    return user

# ================= TEMP =================
user_task_data = {}
user_last_task_msg = {}

# ✅✅ WITHDRAW TEMP START
withdraw_data = {}
# 💥💥 WITHDRAW TEMP END

# ================= MENU =================
def main_menu(user_id=None):
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("📄 কাজ", "💰 ব্যালেন্স")
    m.row("🏦 টাকা উত্তোলন", "🎁 Invite & Earn")
    m.row("📞 সাপোর্ট", "🎯 মিশন")

    # ✅ ONLY ADMIN দেখবে
    if user_id == ADMIN_ID:
        m.row("⚙️ ADMIN PANEL ⚙️")

    return m


# ================= WITHDRAW =================

# ✅✅ WITHDRAW SYSTEM START

@bot.message_handler(func=lambda m: m.text == "🏦 টাকা উত্তোলন")
def withdraw(msg):
    user = get_user(msg.from_user.id)

    if user[1] < 100:
        bot.send_message(msg.chat.id, "❌ দুঃখিত আপনার মিনিমাম ব্যালেন্স নেই❌ মিনিমাম 100 টাকা হলে উত্তোলন করতে পারবেন✅ উত্তোলন করতে বেশি বেশি করে কাজ করুন ধন্যবাদ 😊 ")
        return

    withdraw_data[msg.from_user.id] = {}

    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("❌ বাতিল")

    bot.send_message(msg.chat.id, "💰 কত টাকা তুলতে চান লিখুন:", reply_markup=m)


@bot.message_handler(func=lambda m: m.from_user.id in withdraw_data)
def process_withdraw(msg):
    uid = msg.from_user.id

    # ❌ cancel
    if msg.text == "❌ বাতিল":
        del withdraw_data[uid]
        bot.send_message(msg.chat.id, "❌ উত্তোলন বাতিল করা হয়েছে", reply_markup=main_menu(msg.from_user.id))
        return

    # STEP 1: amount
    if "amount" not in withdraw_data[uid]:
        try:
            amount = float(msg.text)
        except:
            bot.send_message(msg.chat.id, "❌ সঠিক এমাউন্ট দিন")
            return

        user = get_user(uid)

        # 🔥 MINIMUM FIX
        if amount < 100:
            bot.send_message(msg.chat.id, "❌ মিনিমাম 100 টাকা দিতে হবে")
            return

        if amount > user[1]:
            bot.send_message(msg.chat.id, "❌ আপনার ব্যালেন্সে এত টাকা নেই")
            return

        withdraw_data[uid]["amount"] = amount

        # 👉 METHOD BUTTON
        m = ReplyKeyboardMarkup(resize_keyboard=True)
        m.row("📱 bKash", "📱 Nagad")
        m.row("❌ বাতিল")

        bot.send_message(msg.chat.id, "💳 কোন মাধ্যমে টাকা নিতে চান?", reply_markup=m)

    # STEP 2: method select
    elif "method" not in withdraw_data[uid]:
        if msg.text not in ["📱 bKash", "📱 Nagad"]:
            bot.send_message(msg.chat.id, "❌ শুধু bKash বা Nagad বেছে নিন")
            return

        method = "bKash" if "bKash" in msg.text else "Nagad"
        withdraw_data[uid]["method"] = method

        bot.send_message(msg.chat.id, f"📱 আপনার {method} নাম্বার দিন (১১ ডিজিট):")

    # STEP 3: number validation
    else:
        number = msg.text

        if not (number.isdigit() and len(number) == 11 and number.startswith("01")):
            bot.send_message(msg.chat.id, "❌ সঠিক ১১ ডিজিট নাম্বার দিন (01XXXXXXXXX)")
            return

        amount = withdraw_data[uid]["amount"]
        method = withdraw_data[uid]["method"]

        cursor.execute("""
        INSERT INTO withdraws (user_id, amount, number)
        VALUES (?,?,?)
        """, (uid, amount, f"{method} - {number}"))

        cursor.execute(
            "UPDATE users SET balance = balance - ? WHERE user_id=?",
            (amount, uid)
        )
        conn.commit()

        bot.send_message(
            msg.chat.id,
            "✅ আপনার উত্তোলন রিকোয়েস্ট পাঠানো হয়েছে",
            reply_markup=main_menu(msg.from_user.id)
        )

        text = f"""💸 Withdraw Request

👤 User: {uid}
💰 Amount: {amount}
💳 Method: {method}
📱 Number: {number}"""

        wid = cursor.lastrowid

        m = InlineKeyboardMarkup()
        m.row(
            InlineKeyboardButton("✅ Approve", callback_data=f"wapprove_{wid}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"wreject_{wid}")
        )
        m.row(
            InlineKeyboardButton("💰 Balance Back", callback_data=f"wback_{wid}")
        )

        bot.send_message(ADMIN_ID, text, reply_markup=m)

        del withdraw_data[uid]

# 💥💥 WITHDRAW SYSTEM END
# ================= START =================
@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.from_user.id
    args = msg.text.split()

    ref_by = None
    if len(args) > 1:
        try:
            ref_by = int(args[1])
        except:
            pass

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (user_id, ref_by) VALUES (?,?)",(user_id, ref_by))
        conn.commit()

        if ref_by and ref_by != user_id:
            cursor.execute("UPDATE users SET refer = refer + 1 WHERE user_id=?",(ref_by,))
            conn.commit()

    # 🔴 JOIN CHECK
    if not is_joined(user_id):
        text, m = join_msg()
        bot.send_message(msg.chat.id, text, reply_markup=m)
        return

    bot.send_message(msg.chat.id, "মেনু থেকে অপশন নির্বাচন করুন 👇", reply_markup=main_menu(msg.from_user.id))

# ================= JOIN DONE =================
@bot.callback_query_handler(func=lambda call: call.data == "join_done")
def join_done(call):
    user_id = call.from_user.id

    if is_joined(user_id):
        bot.edit_message_text(
            "🎉 এখন আপনি বট ব্যবহার করতে পারবেন",
            call.message.chat.id,
            call.message.message_id
        )
        bot.send_message(call.message.chat.id, "মেনু 👇", reply_markup=main_menu(msg.from_user.id))
    else:
        bot.answer_callback_query(call.id, "❌ আগে চ্যানেল জয়েন করুন!", show_alert=True)

# ================= INVITE =================
@bot.message_handler(func=lambda m: m.text == "🎁 Invite & Earn")
def invite(msg):
    if not is_joined(msg.from_user.id):
        text, m = join_msg()
        bot.send_message(msg.chat.id, text, reply_markup=m)
        return

    user = get_user(msg.from_user.id)

    link = f"https://t.me/{BOT_USERNAME}?start={msg.from_user.id}"

    text = f"""🎁 Invite & Earn

👤 Total Refer: {user[5]}
💰 Total Refer Income: {user[6]} BDT

━━━━━━━━━━━━━━

ℹ️ আপনি আপনার প্রতিটি রেফারেলের সম্পূর্ণ করা কাজ থেকে আয়ের 20% কমিশন পাবেন।
🎉 এছাড়াও, প্রতিটি রেফারে ১০০ টাকা পর্যন্ত বোনাস পাওয়ার সুযোগ রয়েছে!

━━━━━━━━━━━━━━

🔗 আপনার রেফার লিংক:
{link}
"""

    bot.send_message(msg.chat.id, text)

# ================= SUPPORT =================
@bot.message_handler(func=lambda m: m.text == "📞 সাপোর্ট")
def support(msg):
    text = """📞 গ্রাহক সেবা কেন্দ্র
━━━━━━━━━━━━━━━━━━

সম্মানিত মেম্বার,
আপনার যেকোনো সমস্যা বা জিজ্ঞাসার জন্য আমাদের সাপোর্ট টিমের সাথে যোগাযোগ করুন। আমরা দ্রুত সমাধানের চেষ্টা করব।

⚠️ নোট: অযথা মেসেজ দেওয়া থেকে বিরত থাকুন। ধন্যবাদ!
"""

    m = InlineKeyboardMarkup()
    m.row(
        InlineKeyboardButton("📢 অফিসিয়াল চ্যানেল", url="https://t.me/incomezone1000")
    )
    m.row(
        InlineKeyboardButton("📞 অ্যাডমিন সাপোর্ট", url="https://t.me/emon0190237")
    )

    bot.send_message(msg.chat.id, text, reply_markup=m)

# ================= MISSION =================
@bot.message_handler(func=lambda m: m.text == "🎯 মিশন")
def mission(msg):
    bot.send_message(msg.chat.id, "ℹ️ বর্তমানে কোনো মিশন চালু নেই")

# ================= TASK MENU =================
@bot.message_handler(func=lambda m: m.text and m.text.startswith("📄"))
def task_menu(msg):
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("📧 Gmail কাজ 🚀")
    m.row("❌ কাজ বাতিল")
    bot.send_message(msg.chat.id, "🧾 কাজ নির্বাচন করুন:", reply_markup=m)

# ================= GMAIL TASK =================
@bot.message_handler(func=lambda m: m.text and "Gmail কাজ" in m.text)
def gmail_task(msg):
    user_id = msg.from_user.id

    if user_id in user_last_task_msg:
        try:
            bot.delete_message(msg.chat.id, user_last_task_msg[user_id])
        except:
            pass

    name, email, password = generate_gmail_data()
    user_task_data[user_id] = (name, email, password)

    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("✅ জমা দিন")
    m.row("❌ কাজ বাতিল", "❓ কাজের ভিডিও (Gmail)")

    text = f"""
📧 নির্ধারিত তথ্যগুলো ব্যবহার করে অ্যাকাউন্টটি রেজিস্টার করুন এবং 15.00 টাকা আয় করুন 😃

👤 প্রথম নাম : <code>{name}</code>
👤 শেষ নাম : ✖️
📧 ইমেইল : <code>{email}</code>
🔓 পাসওয়ার্ড : <code>{password}</code>

💎 অবশ্যই উপরের তথ্যগুলো ব্যবহার করবেন 🔥
"""

    # parse_mode="HTML" ব্যবহার করা হয়েছে
    sent = bot.send_message(msg.chat.id, text, reply_markup=m, parse_mode="HTML")
    user_last_task_msg[user_id] = sent.message_id
    
    
    # ================= VIDEO HANDLER =================
@bot.message_handler(func=lambda m: m.text == "❓ কাজের ভিডিও (Gmail)")
def send_task_video(msg):
    # আপনার অ্যাডমিন প্যানেল থেকে ভিডিওর File ID অথবা ভিডিও লিঙ্ক এখানে দিন
    # নিচের "FILE_ID_HERE" পরিবর্তন করে আপনার ভিডিওর আইডি বসান
    VIDEO_FILE_ID = "BAACAgUAAxkBAAIUx2niM7gG6H-urKQVHK2CE-ITQAxfAAIPJAACNB8RV5m4UYGXNTOaOwQ" 
    
    try:
        # যদি ভিডিওটি টেলিগ্রামে আপলোড করা থাকে তবে নিচের লাইনটি ব্যবহার করুন
        bot.send_video(msg.chat.id, VIDEO_FILE_ID, caption="📹 কাজ বোঝার জন্য ভিডিওটি দেখুন")
    except Exception as e:
        bot.send_message(msg.chat.id, "❌ ভিডিওটি এই মুহূর্তে পাওয়া যাচ্ছে না। দয়া করে এডমিনের সাথে যোগাযোগ করুন।")

# ================= CANCEL =================
@bot.message_handler(func=lambda m: m.text == "❌ কাজ বাতিল")
def cancel(msg):
    uid = msg.from_user.id

    if uid in user_last_task_msg:
        try:
            bot.delete_message(msg.chat.id, user_last_task_msg[uid])
        except:
            pass

    if uid in user_task_data:
        del user_task_data[uid]

    bot.send_message(msg.chat.id, "❌ কাজ বাতিল করা হয়েছে", reply_markup=main_menu(msg.from_user.id))

# ================= SUBMIT =================
@bot.message_handler(func=lambda m: m.text == "✅ জমা দিন")
def submit(msg):
    user_id = msg.from_user.id

    try:
        bot.delete_message(msg.chat.id, msg.message_id)
    except:
        pass

    if user_id not in user_task_data:
        bot.send_message(msg.chat.id, "❌ আগে কাজ নিন")
        return

    name, email, password = user_task_data[user_id]

    cursor.execute("""
    INSERT INTO submissions (user_id,name,email,password)
    VALUES (?,?,?,?)
    """,(user_id,name,email,password))
    conn.commit()

    sub_id = cursor.lastrowid

    cursor.execute("UPDATE users SET pending = pending + 1 WHERE user_id=?",(user_id,))
    conn.commit()

    if user_id in user_last_task_msg:
        try:
            bot.delete_message(msg.chat.id, user_last_task_msg[user_id])
        except:
            pass

    bot.send_message(msg.chat.id,"✅ আপনার কাজ রিভিউতে গেছে\n⏳ অপেক্ষা করুন...",reply_markup=main_menu(msg.from_user.id))

    text = f"""
🆕 New Submission #{sub_id}

👤 User: {user_id}
👤 Name: {name}
📧 Email: {email}
🔓 Password: {password}
"""

    m = InlineKeyboardMarkup()
    m.row(
        InlineKeyboardButton("✅ Approve",callback_data=f"approve_{sub_id}"),
        InlineKeyboardButton("❌ Reject",callback_data=f"reject_{sub_id}")
    )

    bot.send_message(ADMIN_ID,text,reply_markup=m)

    del user_task_data[user_id]


# ✅✅ WITHDRAW CALLBACK START
@bot.callback_query_handler(func=lambda call: call.data.startswith("w"))
def withdraw_callback(call):
    data = call.data
    wid = int(data.split("_")[1])

    cursor.execute("SELECT user_id, amount FROM withdraws WHERE id=?", (wid,))
    row = cursor.fetchone()

    if not row:
        return

    user_id, amount = row

    # ✅ APPROVE
    if data.startswith("wapprove"):
        cursor.execute("UPDATE withdraws SET status='approved' WHERE id=?", (wid,))
        conn.commit()

        bot.send_message(user_id, "💸 আপনার টাকা পাঠানো হয়েছে ✅")

    # ❌ REJECT
    elif data.startswith("wreject"):
        cursor.execute("UPDATE withdraws SET status='rejected' WHERE id=?", (wid,))
        conn.commit()

        bot.send_message(user_id, "❌ আপনার উত্তোলন রিজেক্ট করা হয়েছে")

    # 💰 BALANCE BACK
    elif data.startswith("wback"):
        cursor.execute("UPDATE withdraws SET status='returned' WHERE id=?", (wid,))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
        conn.commit()

        bot.send_message(user_id, "💰 আপনার টাকা ব্যালেন্সে ফেরত দেওয়া হয়েছে")

    bot.edit_message_text("✅ Done", call.message.chat.id, call.message.message_id)
# 💥💥 WITHDRAW CALLBACK END

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    data = call.data

    if data.startswith("approve_"):
        sub_id = int(data.split("_")[1])

        cursor.execute("SELECT user_id,status FROM submissions WHERE id=?",(sub_id,))
        row = cursor.fetchone()

        if not row:
            return

        user_id,status = row

        if status != "pending":
            return

        cursor.execute("UPDATE submissions SET status='approved' WHERE id=?",(sub_id,))
        cursor.execute("""
        UPDATE users SET 
        balance=balance+15,
        total_income=total_income+15,
        completed=completed+1,
        pending=pending-1
        WHERE user_id=?
        """,(user_id,))
        conn.commit()

        bot.send_message(user_id,"✅ আপনার কাজ অনুমোদন করা হয়েছে\n💰 15 BDT যোগ হয়েছে")

        # ===== 7% REF BONUS =====
        cursor.execute("SELECT ref_by FROM users WHERE user_id=?", (user_id,))
        ref = cursor.fetchone()[0]

        if ref:
            bonus = round(15 * 0.07, 2)

            cursor.execute("""
            UPDATE users SET 
            refer_income = refer_income + ?,
            balance = balance + ?
            WHERE user_id=?
            """,(bonus, bonus, ref))
            conn.commit()

            try:
                bot.send_message(ref, f"🎉 আপনার রেফার থেকে {bonus} BDT (20%) বোনাস যোগ হয়েছে!")
            except:
                pass

        try:
            bot.edit_message_text(
                f"✅ Approved\nSubmission ID: {sub_id}",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )
        except:
            pass

    elif data.startswith("reject_"):
        sub_id = int(data.split("_")[1])

        cursor.execute("SELECT user_id,status FROM submissions WHERE id=?",(sub_id,))
        row = cursor.fetchone()

        if not row:
            return

        user_id,status = row

        if status != "pending":
            return

        cursor.execute("UPDATE submissions SET status='rejected' WHERE id=?",(sub_id,))
        cursor.execute("UPDATE users SET pending=pending-1 WHERE user_id=?",(user_id,))
        conn.commit()

        bot.send_message(user_id,"❌ আপনার কাজ বাতিল করা হয়েছে")

        try:
            bot.edit_message_text(
                f"❌ Rejected\nSubmission ID: {sub_id}",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )
        except:
            pass
            
            
            
            
            
@bot.message_handler(func=lambda m: m.text == "⚙️ ADMIN PANEL ⚙️" and m.from_user.id == ADMIN_ID)
def admin_panel(msg):
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("📢 Send Notification", "📊 User Stats")
    m.row("💸 Withdraw List", "📋 All Users")
    m.row("🚫 Ban User")
    m.row("⬅️ Back")

    bot.send_message(
        msg.chat.id,
        "🔥 ADMIN CONTROL PANEL 🔥\n👑 Welcome Boss!\n⚙️ Control your bot easily",
        reply_markup=m
    )


@bot.message_handler(func=lambda m: m.text == "📋 All Users" and m.from_user.id == ADMIN_ID)
def all_users(msg):
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    total = len(users)

    # 🔥 Active users (recent) — এখানে simple ভাবে last 24h ধরলাম না, শুধু demo count
    active = total  # চাইলে পরে real active logic বসাবো

    text = f"""📋 All Users List:
👥 Total Users: {total}
🟢 Active Users: {active}

"""

    for u in users:
        text += f"{u[0]}\n"

    bot.send_message(msg.chat.id, text)


# ✅ এখানে কোনো space থাকবে না
@bot.message_handler(func=lambda m: m.text == "📊 User Stats" and m.from_user.id == ADMIN_ID)
def user_stats(msg):
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    if not users:
        bot.send_message(msg.chat.id, "❌ No users found")
        return

    text = "📊 USER STATS\n━━━━━━━━━━━━━━\n\n"

    for u in users:
        uid = u[0]
        balance = u[1]
        total_income = u[2]
        completed = u[3]
        pending = u[4]
        refer = u[5]
        refer_income = u[6]

        text += f"""👤 ID: {uid}
💰 Balance: {balance} BDT
💸 Total Income: {total_income} BDT
🎯 Completed: {completed}
⏳ Pending: {pending}
👥 Refer: {refer}
🎁 Refer Income: {refer_income} BDT
━━━━━━━━━━━━━━
"""

    bot.send_message(msg.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "💸 Withdraw List" and m.from_user.id == ADMIN_ID)
def withdraw_list(msg):
    cursor.execute("SELECT user_id, amount, number, status FROM withdraws")
    data = cursor.fetchall()

    if not data:
        bot.send_message(msg.chat.id, "❌ কোনো withdraw নেই")
        return

    text = "💸 Withdraw Requests:\n\n"

    for d in data:
        text += f"👤 {d[0]} | 💰 {d[1]} | 📱 {d[2]} | 📊 {d[3]}\n"

    bot.send_message(msg.chat.id, text)

# Line 645 (NO SPACE আগে)
@bot.message_handler(func=lambda m: m.text == "🚫 Ban User" and m.from_user.id == ADMIN_ID)
def ban_user(msg):
    bot.send_message(msg.chat.id, "👤 User ID দিন:")
    bot.register_next_step_handler(msg, process_ban)

def process_ban(msg):
    try:
        uid = int(msg.text)

        cursor.execute("DELETE FROM users WHERE user_id=?", (uid,))
        conn.commit()

        bot.send_message(msg.chat.id, f"🚫 User {uid} banned")

    except:
        bot.send_message(msg.chat.id, "❌ ভুল ID")


@bot.message_handler(func=lambda m: m.text == "📢 Send Notification" and m.from_user.id == ADMIN_ID)
def notify(msg):
    bot.send_message(msg.chat.id, "📩 মেসেজ লিখুন:")
    bot.register_next_step_handler(msg, send_all)
    bot.send_message(msg.chat.id, "✉️ মেসেজ লিখুন:")
    bot.register_next_step_handler(msg, send_all)


def send_all(msg):
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    sent = 0

    for u in users:
        try:
            bot.send_message(u[0], msg.text)
            sent += 1
        except:
            pass
    
  
# ================= BALANCE =================
@bot.message_handler(func=lambda m: m.text == "💰 ব্যালেন্স")
def balance(msg):
    user = get_user(msg.from_user.id)

    text = f"""
💵 আপনার ব্যালেন্স

🔥 ব্যালেন্স: {user[1]} BDT
💰 Total Income: {user[2]} BDT

━━━━━━━━━━━━━━

🎯 সম্পন্ন কাজ: {user[3]} টি
⏳ রিভিউতে আছে: {user[4]} টি
"""
    bot.send_message(msg.chat.id,text)
    
    
    
@bot.message_handler(func=lambda m: m.text == "⬅️ Back")
def back(msg):
    bot.send_message(msg.chat.id, "🔙 Main Menu", reply_markup=main_menu(msg.from_user.id))
    import os
from flask import Flask
import threading

# Flask অ্যাপ তৈরি (Render-কে খুশি করার জন্য)
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is alive!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Flask-কে আলাদা থ্রেডে চালানো যাতে বট আর ওয়েবসাইট একসাথে চলে
    threading.Thread(target=run_flask).start()
@bot.message_handler(content_types=['video'])
def get_file_id(msg):
    bot.reply_to(msg, f"আপনার ভিডিওর File ID হলো: \n<code>{msg.video.file_id}</code>", parse_mode="HTML")
# ================= RUN =================
print("Bot Running...")
bot.infinity_polling()
