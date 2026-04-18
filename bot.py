import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import pymongo
import random
import string
import os
import threading
from flask import Flask
from bson import ObjectId # এটি পরে ডেটাবেস আইডি খুঁজে পেতে লাগবে

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = "@vipincomex_bot"
CHANNEL_LINK = "https://t.me/incomezone1000"
CHANNEL_USERNAME = "@incomezone1000"
ADMIN_ID = 7036481355

bot = telebot.TeleBot(TOKEN)

# ================= MONGODB DATABASE =================
MONGO_URL = os.getenv("MONGO_URL")
client = pymongo.MongoClient(MONGO_URL)
db = client['vip_income_db']

users_col = db['users']
submissions_col = db['submissions']
withdraws_col = db['withdraws']
# ================= DATABASE =================

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
    user = users_col.find_one({"user_id": user_id})
    if not user:
        user = {
            "user_id": user_id,
            "balance": 0.0,
            "total_income": 0.0,
            "completed": 0,
            "pending": 0,
            "refer": 0,
            "refer_income": 0.0,
            "ref_by": None
        }
        users_col.insert_one(user)
    return user

# ================= TEMP DATA (In-Memory) =================
user_task_data = {}
user_last_task_msg = {}
withdraw_data = {}

# ================= MENU =================
def main_menu(user_id=None):
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("📄 কাজ", "💰 ব্যালেন্স")
    m.row("🏦 টাকা উত্তোলন", "🎁 Invite & Earn")
    m.row("📞 সাপোর্ট", "🎯 মিশন")

    # ✅ শুধুমাত্র অ্যাডমিন এই বাটনটি দেখবে
    if user_id == ADMIN_ID:
        m.row("⚙️ ADMIN PANEL ⚙️")

    return m


# ================= WITHDRAW SYSTEM =================

@bot.message_handler(func=lambda m: m.text == "🏦 টাকা উত্তোলন")
def withdraw(msg):
    user = get_user(msg.from_user.id)

    # মঙ্গোডিবিতে ইনডেক্স [1] এর বদলে সরাসরি 'balance' কী ব্যবহার করতে হয়
    if user['balance'] < 100:
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
        bot.send_message(msg.chat.id, "❌ উত্তোলন বাতিল করা হয়েছে", reply_markup=main_menu(uid))
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

        if amount > user['balance']:
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

        method = "bKash" if "📱 bKash" in msg.text else "Nagad"
        withdraw_data[uid]["method"] = method

        bot.send_message(msg.chat.id, f"📱 আপনার {method} নাম্বার দিন (১১ ডিজিট):")

    # STEP 3: number validation (MongoDB Version)
    else:
        number = msg.text

        if not (number.isdigit() and len(number) == 11 and number.startswith("01")):
            bot.send_message(msg.chat.id, "❌ সঠিক ১১ ডিজিট নাম্বার দিন (01XXXXXXXXX)")
            return

        amount = withdraw_data[uid]["amount"]
        method = withdraw_data[uid]["method"]

        # MongoDB তে ডেটা ইনসার্ট করা
        withdraw_doc = {
            "user_id": uid,
            "amount": amount,
            "number": f"{method} - {number}",
            "status": "pending"
        }
        result = withdraws_col.insert_one(withdraw_doc)
        
        # MongoDB তে ব্যালেন্স আপডেট করা
        users_col.update_one({"user_id": uid}, {"$inc": {"balance": -amount}})

        bot.send_message(
            msg.chat.id,
            "✅ আপনার উত্তোলন রিকোয়েস্ট পাঠানো হয়েছে",
            reply_markup=main_menu(uid)
        )

        text = f"""💸 Withdraw Request

👤 User: {uid}
💰 Amount: {amount}
💳 Method: {method}
📱 Number: {number}"""

        # wid টাকে স্ট্রিং কনভার্ট করে নিচ্ছি (ObjectId টা স্ট্রিংয়ে রুপান্তর করতে হবে)
        wid = str(result.inserted_id)

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

    # মঙ্গোডিবিতে ইউজার চেক করা
    user = users_col.find_one({"user_id": user_id})

    if not user:
        # নতুন ইউজার ইনসার্ট করা
        users_col.insert_one({
            "user_id": user_id,
            "balance": 0.0,
            "total_income": 0.0,
            "completed": 0,
            "pending": 0,
            "refer": 0,
            "refer_income": 0.0,
            "ref_by": ref_by
        })

        # রেফারেল আপডেট করা
        if ref_by and ref_by != user_id:
            users_col.update_one({"user_id": ref_by}, {"$inc": {"refer": 1}})

    # 🔴 JOIN CHECK
    if not is_joined(user_id):
        text, m = join_msg()
        bot.send_message(msg.chat.id, text, reply_markup=m)
        return

    bot.send_message(msg.chat.id, "মেনু থেকে অপশন নির্বাচন করুন 👇", reply_markup=main_menu(user_id))

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
        # এখানে call.from_user.id ব্যবহার করা হয়েছে কারণ msg ভেরিয়েবলটি এখানে নেই
        bot.send_message(call.message.chat.id, "মেনু 👇", reply_markup=main_menu(user_id))
    else:
        bot.answer_callback_query(call.id, "❌ আগে চ্যানেল জয়েন করুন!", show_alert=True)


# ================= INVITE & EARN =================
@bot.message_handler(func=lambda m: m.text == "🎁 Invite & Earn")
def invite(msg):
    if not is_joined(msg.from_user.id):
        text, m = join_msg()
        bot.send_message(msg.chat.id, text, reply_markup=m)
        return

    user = get_user(msg.from_user.id)
    # বট ইউজারনেম থেকে '@' বাদ দিয়ে লিংকের জন্য তৈরি করছি
    bot_username_clean = BOT_USERNAME.replace("@", "")
    link = f"https://t.me/{bot_username_clean}?start={msg.from_user.id}"

    text = f"""🎁 Invite & Earn

👤 Total Refer: {user['refer']}
💰 Total Refer Income: {user['refer_income']} BDT

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

    sent = bot.send_message(msg.chat.id, text, reply_markup=m, parse_mode="HTML")
    user_last_task_msg[user_id] = sent.message_id
    
# ================= VIDEO HANDLER =================
@bot.message_handler(func=lambda m: m.text == "❓ কাজের ভিডিও (Gmail)")
def send_task_video(msg):
    VIDEO_FILE_ID = "BAACAgUAAxkBAAIUx2niM7gG6H-urKQVHK2CE-ITQAxfAAIPJAACNB8RV5m4UYGXNTOaOwQ" 
    
    try:
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

    # মঙ্গোডিবিতে সাবমিশন ইনসার্ট
    result = submissions_col.insert_one({
        "user_id": user_id,
        "name": name,
        "email": email,
        "password": password,
        "status": "pending"
    })
    
    # সাবমিশন আইডি (ObjectId-কে স্ট্রিং এ কনভার্ট করে নিচ্ছি)
    sub_id = str(result.inserted_id)

    # ইউজার পেন্ডিং কাউন্ট আপডেট
    users_col.update_one({"user_id": user_id}, {"$inc": {"pending": 1}})

    if user_id in user_last_task_msg:
        try:
            bot.delete_message(msg.chat.id, user_last_task_msg[user_id])
        except:
            pass

    bot.send_message(msg.chat.id, "✅ আপনার কাজ রিভিউতে গেছে\n⏳ অপেক্ষা করুন...", reply_markup=main_menu(user_id))

    text = f"""
🆕 New Submission #{sub_id[:8]}...

👤 User: {user_id}
👤 Name: {name}
📧 Email: {email}
🔓 Password: {password}
"""

    m = InlineKeyboardMarkup()
    m.row(
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{sub_id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{sub_id}")
    )

    bot.send_message(ADMIN_ID, text, reply_markup=m)

    del user_task_data[user_id]


# ================= WITHDRAW CALLBACK =================
@bot.callback_query_handler(func=lambda call: call.data.startswith("w"))
def withdraw_callback(call):
    data = call.data
    # এখানে wid স্ট্রিং হিসেবে আসছে (ObjectId)
    wid = data.split("_")[1]

    # ডাটাবেস থেকে উইথড্র রিকোয়েস্ট খুঁজে বের করা
    withdraw = withdraws_col.find_one({"_id": ObjectId(wid)})

    if not withdraw:
        return

    user_id = withdraw['user_id']
    amount = withdraw['amount']

    # ✅ APPROVE
    if data.startswith("wapprove"):
        withdraws_col.update_one({"_id": ObjectId(wid)}, {"$set": {"status": "approved"}})
        bot.send_message(user_id, "💸 আপনার টাকা পাঠানো হয়েছে ✅")

    # ❌ REJECT
    elif data.startswith("wreject"):
        withdraws_col.update_one({"_id": ObjectId(wid)}, {"$set": {"status": "rejected"}})
        bot.send_message(user_id, "❌ আপনার উত্তোলন রিজেক্ট করা হয়েছে")

    # 💰 BALANCE BACK
    elif data.startswith("wback"):
        withdraws_col.update_one({"_id": ObjectId(wid)}, {"$set": {"status": "returned"}})
        # টাকা ব্যালেন্সে ফেরত দেওয়া
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": amount}})
        bot.send_message(user_id, "💰 আপনার টাকা ব্যালেন্সে ফেরত দেওয়া হয়েছে")

    bot.edit_message_text("✅ Done", call.message.chat.id, call.message.message_id)

# ================= CALLBACK (SUBMISSION APPROVE) =================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    data = call.data

    if data.startswith("approve_"):
        sub_id = data.split("_")[1]

        # সাবমিশন খুঁজে বের করা
        sub = submissions_col.find_one({"_id": ObjectId(sub_id)})

        if not sub or sub.get('status') != "pending":
            return

        # স্ট্যাটাস আপডেট
        submissions_col.update_one({"_id": ObjectId(sub_id)}, {"$set": {"status": "approved"}})
        
        # ইউজার ব্যালেন্স ও স্ট্যাটাস আপডেট
        users_col.update_one({"user_id": sub['user_id']}, {
            "$inc": {
                "balance": 15,
                "total_income": 15,
                "completed": 1,
                "pending": -1
            }
        })

        bot.send_message(sub['user_id'], "✅ আপনার কাজ অনুমোদন করা হয়েছে\n💰 15 BDT যোগ হয়েছে")
        bot.edit_message_text("✅ কাজ অনুমোদন করা হয়েছে!", call.message.chat.id, call.message.message_id)

       
       # ===== 7% REF BONUS =====
        # আগের সাবমিশন থেকে ইউজার আইডি পেয়েছি, এখন তার রেফারার খুঁজে বের করছি
        worker = users_col.find_one({"user_id": sub['user_id']})
        ref = worker.get('ref_by')

        if ref:
            bonus = round(15 * 0.07, 2)
            users_col.update_one({"user_id": ref}, {"$inc": {"refer_income": bonus, "balance": bonus}})
            
            try:
                bot.send_message(ref, f"🎉 আপনার রেফার থেকে {bonus} BDT বোনাস যোগ হয়েছে!")
            except:
                pass

        try:
            bot.edit_message_text(
                f"✅ Approved\nSubmission ID: {sub_id[:8]}...",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )
        except:
            pass

    elif data.startswith("reject_"):
        sub_id = data.split("_")[1]
        
        # সাবমিশন খুঁজে বের করা
        sub = submissions_col.find_one({"_id": ObjectId(sub_id)})

        if not sub or sub.get('status') != "pending":
            return

        # স্ট্যাটাস আপডেট এবং ইউজার পেন্ডিং কমানো
        submissions_col.update_one({"_id": ObjectId(sub_id)}, {"$set": {"status": "rejected"}})
        users_col.update_one({"user_id": sub['user_id']}, {"$inc": {"pending": -1}})

        bot.send_message(sub['user_id'], "❌ আপনার কাজ বাতিল করা হয়েছে")

        try:
            bot.edit_message_text(
                f"❌ Rejected\nSubmission ID: {sub_id[:8]}...",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )
        except:
            pass     
            
            
            
            
# ================= ADMIN PANEL =================
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

# ================= ALL USERS =================
@bot.message_handler(func=lambda m: m.text == "📋 All Users" and m.from_user.id == ADMIN_ID)
def all_users(msg):
    # মঙ্গোডিবি থেকে শুধুমাত্র user_id গুলো নিয়ে আসছি
    users = list(users_col.find({}, {"user_id": 1}))
    total = len(users)

    text = f"📋 All Users List:\n👥 Total Users: {total}\n\n"

    for u in users:
        text += f"{u['user_id']}\n"

    # মেসেজ বড় হয়ে গেলে এরর হতে পারে, তাই ছোট ছোট ভাগে পাঠানো ভালো
    bot.send_message(msg.chat.id, text)

# ================= USER STATS =================
@bot.message_handler(func=lambda m: m.text == "📊 User Stats" and m.from_user.id == ADMIN_ID)
def user_stats(msg):
    users = list(users_col.find())

    if not users:
        bot.send_message(msg.chat.id, "❌ No users found")
        return

    text = "📊 USER STATS\n━━━━━━━━━━━━━━\n\n"

    # সব ইউজারের তথ্য দেখাচ্ছে
    for u in users:
        text += f"""👤 ID: {u['user_id']}
💰 Balance: {u['balance']} BDT
💸 Total Income: {u['total_income']} BDT
🎯 Completed: {u['completed']}
⏳ Pending: {u['pending']}
👥 Refer: {u['refer']}
🎁 Refer Income: {u['refer_income']} BDT
━━━━━━━━━━━━━━
"""
    bot.send_message(msg.chat.id, text)


# ================= WITHDRAW LIST =================
@bot.message_handler(func=lambda m: m.text == "💸 Withdraw List" and m.from_user.id == ADMIN_ID)
def withdraw_list(msg):
    data = list(withdraws_col.find()) # মঙ্গোডিবি থেকে সব উইথড্র ডেটা আনা

    if not data:
        bot.send_message(msg.chat.id, "❌ কোনো withdraw নেই")
        return

    text = "💸 Withdraw Requests:\n\n"

    for d in data:
        text += f"👤 {d['user_id']} | 💰 {d['amount']} | 📱 {d['number']} | 📊 {d['status']}\n"

    bot.send_message(msg.chat.id, text)

# ================= BAN USER =================
@bot.message_handler(func=lambda m: m.text == "🚫 Ban User" and m.from_user.id == ADMIN_ID)
def ban_user(msg):
    bot.send_message(msg.chat.id, "👤 User ID দিন:")
    bot.register_next_step_handler(msg, process_ban)

def process_ban(msg):
    try:
        uid = int(msg.text)
        # ইউজার ডিলিট করা
        result = users_col.delete_one({"user_id": uid})
        
        if result.deleted_count > 0:
            bot.send_message(msg.chat.id, f"🚫 User {uid} banned")
        else:
            bot.send_message(msg.chat.id, "❌ ইউজার খুঁজে পাওয়া যায়নি")
    except:
        bot.send_message(msg.chat.id, "❌ ভুল ID (সংখ্যা লিখুন)")

# ================= NOTIFICATION =================
@bot.message_handler(func=lambda m: m.text == "📢 Send Notification" and m.from_user.id == ADMIN_ID)
def notify(msg):
    bot.send_message(msg.chat.id, "📩 মেসেজ লিখুন (যা সবার কাছে যাবে):")
    bot.register_next_step_handler(msg, send_all)

def send_all(msg):
    # শুধু user_id ফিল্ডগুলো নিয়ে আসা
    users = list(users_col.find({}, {"user_id": 1}))
    sent = 0

    for u in users:
        try:
            bot.send_message(u['user_id'], msg.text)
            sent += 1
        except:
            pass
    
    bot.send_message(msg.chat.id, f"✅ মেসেজ পাঠানো সম্পন্ন। মোট {sent} জনকে পাঠানো হয়েছে।")    
  
# ================= BALANCE =================
@bot.message_handler(func=lambda m: m.text == "💰 ব্যালেন্স")
def balance(msg):
    # এখানে SQLite ইনডেক্স [1], [2] এর বদলে আমরা সরাসরি ডিকশনারি কী ব্যবহার করছি
    user = get_user(msg.from_user.id)

    text = f"""
💵 আপনার ব্যালেন্স

🔥 ব্যালেন্স: {user['balance']} BDT
💰 Total Income: {user['total_income']} BDT

━━━━━━━━━━━━━━

🎯 সম্পন্ন কাজ: {user['completed']} টি
⏳ রিভিউতে আছে: {user['pending']} টি
"""
    bot.send_message(msg.chat.id, text)

# ================= BACK =================
@bot.message_handler(func=lambda m: m.text == "⬅️ Back")
def back(msg):
    bot.send_message(msg.chat.id, "🔙 Main Menu", reply_markup=main_menu(msg.from_user.id))

# ================= FLASK SERVER (For Keep-Alive) =================
# এটি রেন্ডার (Render) বা হেরোকু (Heroku)-তে বটকে সচল রাখার জন্য জরুরি
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

    print("Bot Running...")
    bot.infinity_polling()
