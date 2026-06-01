
import telebot
from telebot import types
import random
import json
import os

TOKEN = "8741894676:AAFzHqxYLG5jxYYn_9jKtSTDKdNfR1eWZG4"
ADMIN_ID = 994054990

bot = telebot.TeleBot(TOKEN)

DB_FILE = "database.json"

CHANNEL = None
SPONSORS = []          # ← bitta SPONSOR o'rniga ro'yxat
ADMINS = [ADMIN_ID]

giveaways = {}
creating = {}

# ================= SAVE / LOAD =================

def save_data():
    data = {
        "channel": CHANNEL,
        "sponsors": SPONSORS,
        "admins": ADMINS,
        "giveaways": giveaways
    }
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_data():
    global CHANNEL, SPONSORS, ADMINS, giveaways

    if not os.path.exists(DB_FILE):
        return

    with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    CHANNEL = data.get("channel")
    # Eski "sponsor" (string) dan ham o'qiydi — migratsiya uchun
    old_sponsor = data.get("sponsor")
    SPONSORS = data.get("sponsors", [])
    if old_sponsor and old_sponsor not in SPONSORS:
        SPONSORS.append(old_sponsor)
    ADMINS = data.get("admins", [ADMIN_ID])
    giveaways = data.get("giveaways", {})


load_data()

# ================= MAIN MENU =================

def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🎁 Giveaway", "📊 Status")
    kb.row("🏁 Yakunlash")
    kb.row("⚙️ Sozlamalar")
    return kb


# ================= SETTINGS MENU =================

def settings_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📢 Kanal sozlamalari")
    kb.row("🎯 Homiy sozlamalari")
    kb.row("👮 Admin sozlamalari")
    kb.row("🔙 Orqaga")
    return kb


# ================= CHANNEL MENU =================

def channel_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Kanal qo'shish")
    kb.row("➖ Kanalni o'chirish")
    kb.row("🔙 Orqaga")
    return kb


# ================= SPONSOR MENU =================

def sponsor_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Homiy qo'shish")
    kb.row("➖ Homiyni o'chirish")
    kb.row("📋 Homiylar ro'yxati")
    kb.row("🔙 Orqaga")
    return kb


# ================= ADMIN MENU =================

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Admin qo'shish")
    kb.row("➖ Admin o'chirish")
    kb.row("🔙 Orqaga")
    return kb


# ================= START =================

@bot.message_handler(commands=['start', 'panel'])
def start(m):
    if m.from_user.id not in ADMINS:
        return
    bot.send_message(m.chat.id, "⚙️ ADMIN PANEL", reply_markup=menu())


# ================= SETTINGS =================

@bot.message_handler(func=lambda m: m.text == "⚙️ Sozlamalar")
def settings_panel(m):
    if m.from_user.id not in ADMINS:
        return
    bot.send_message(m.chat.id, "⚙️ SOZLAMALAR", reply_markup=settings_menu())


# ================= CHANNEL PANEL =================

@bot.message_handler(func=lambda m: m.text == "📢 Kanal sozlamalari")
def channel_panel(m):
    if m.from_user.id not in ADMINS:
        return
    bot.send_message(m.chat.id, "📢 KANAL PANELI", reply_markup=channel_menu())


# ================= SPONSOR PANEL =================

@bot.message_handler(func=lambda m: m.text == "🎯 Homiy sozlamalari")
def sponsor_panel(m):
    if m.from_user.id not in ADMINS:
        return
    count = len(SPONSORS)
    bot.send_message(
        m.chat.id,
        f"🎯 HOMIY PANELI\n\nJami homiylar: {count}/10",
        reply_markup=sponsor_menu()
    )


# ================= ADMIN PANEL =================

@bot.message_handler(func=lambda m: m.text == "👮 Admin sozlamalari")
def admin_panel(m):
    if m.from_user.id not in ADMINS:
        return
    bot.send_message(m.chat.id, "👮 ADMIN PANELI", reply_markup=admin_menu())


# ================= BACK =================

@bot.message_handler(func=lambda m: m.text == "🔙 Orqaga")
def back(m):
    if m.from_user.id not in ADMINS:
        return
    bot.send_message(m.chat.id, "🔙 Bosh menyu", reply_markup=menu())


# ================= CHANNEL =================

@bot.message_handler(func=lambda m: m.text == "➕ Kanal qo'shish")
def add_channel(m):
    msg = bot.send_message(
        m.chat.id,
        "📢 Kanal username yubor:\n\nMasalan:\n@kanalim"
    )
    bot.register_next_step_handler(msg, save_channel)


def save_channel(m):
    global CHANNEL
    CHANNEL = m.text.strip()
    save_data()
    bot.send_message(m.chat.id, "✅ Kanal saqlandi", reply_markup=channel_menu())


@bot.message_handler(func=lambda m: m.text == "➖ Kanalni o'chirish")
def delete_channel(m):
    global CHANNEL
    CHANNEL = None
    save_data()
    bot.send_message(m.chat.id, "✅ Kanal o'chirildi", reply_markup=channel_menu())


# ================= SPONSOR =================

@bot.message_handler(func=lambda m: m.text == "➕ Homiy qo'shish")
def add_sponsor(m):
    if len(SPONSORS) >= 10:
        bot.send_message(
            m.chat.id,
            "❌ Maksimal 10 ta homiy qo'shish mumkin!\n\nBirinchi birini o'chiring.",
            reply_markup=sponsor_menu()
        )
        return

    msg = bot.send_message(
        m.chat.id,
        f"🎯 Homiy kanal username yubor:\n\nMasalan: @kanalim\n\n"
        f"({len(SPONSORS)}/10 homiy mavjud)"
    )
    bot.register_next_step_handler(msg, save_sponsor)


def save_sponsor(m):
    username = m.text.strip()

    # @ belgisi yo'q bo'lsa qo'shib qo'yish
    if not username.startswith("@"):
        username = "@" + username

    if username in SPONSORS:
        bot.send_message(
            m.chat.id,
            "⚠️ Bu homiy allaqachon mavjud",
            reply_markup=sponsor_menu()
        )
        return

    SPONSORS.append(username)
    save_data()
    bot.send_message(
        m.chat.id,
        f"✅ Homiy qo'shildi: {username}\n\nJami: {len(SPONSORS)}/10",
        reply_markup=sponsor_menu()
    )


@bot.message_handler(func=lambda m: m.text == "➖ Homiyni o'chirish")
def delete_sponsor_menu(m):
    if not SPONSORS:
        bot.send_message(m.chat.id, "❌ Homiy yo'q", reply_markup=sponsor_menu())
        return

    txt = "🎯 Qaysi homiyni o'chirmoqchisiz?\n\n"
    for i, s in enumerate(SPONSORS, start=1):
        txt += f"{i}. {s}\n"
    txt += "\n❌ O'chirish uchun raqam yubor (masalan: 1)"

    msg = bot.send_message(m.chat.id, txt)
    bot.register_next_step_handler(msg, delete_sponsor)


def delete_sponsor(m):
    try:
        idx = int(m.text.strip()) - 1
        if 0 <= idx < len(SPONSORS):
            removed = SPONSORS.pop(idx)
            save_data()
            bot.send_message(
                m.chat.id,
                f"✅ Homiy o'chirildi: {removed}\n\nQolgan: {len(SPONSORS)}/10",
                reply_markup=sponsor_menu()
            )
        else:
            bot.send_message(m.chat.id, "❌ Noto'g'ri raqam", reply_markup=sponsor_menu())
    except ValueError:
        bot.send_message(m.chat.id, "❌ Raqam yubor", reply_markup=sponsor_menu())


@bot.message_handler(func=lambda m: m.text == "📋 Homiylar ro'yxati")
def list_sponsors(m):
    if m.from_user.id not in ADMINS:
        return

    if not SPONSORS:
        bot.send_message(m.chat.id, "❌ Hozircha homiy yo'q", reply_markup=sponsor_menu())
        return

    txt = f"🎯 HOMIYLAR ({len(SPONSORS)}/10):\n\n"
    for i, s in enumerate(SPONSORS, start=1):
        txt += f"{i}. {s}\n"

    bot.send_message(m.chat.id, txt, reply_markup=sponsor_menu())


# ================= ADMIN =================

@bot.message_handler(func=lambda m: m.text == "➕ Admin qo'shish")
def add_admin(m):
    msg = bot.send_message(m.chat.id, "🆔 Admin ID yubor:")
    bot.register_next_step_handler(msg, save_admin)


def save_admin(m):
    try:
        uid = int(m.text)
        if uid not in ADMINS:
            ADMINS.append(uid)
            save_data()
            bot.send_message(
                m.chat.id,
                f"✅ Admin qo'shildi:\n{uid}",
                reply_markup=admin_menu()
            )
        else:
            bot.send_message(m.chat.id, "⚠️ Bu admin mavjud", reply_markup=admin_menu())
    except:
        bot.send_message(m.chat.id, "❌ ID yubor", reply_markup=admin_menu())


@bot.message_handler(func=lambda m: m.text == "➖ Admin o'chirish")
def remove_admin_menu(m):
    txt = "👮 Adminlar:\n\n"
    for a in ADMINS:
        txt += f"{a}\n"
    txt += "\n❌ O'chirish uchun ID yubor"

    msg = bot.send_message(m.chat.id, txt)
    bot.register_next_step_handler(msg, remove_admin)


def remove_admin(m):
    try:
        uid = int(m.text)
        if uid == ADMIN_ID:
            bot.send_message(m.chat.id, "❌ Creator adminni o'chirib bo'lmaydi")
            return
        if uid in ADMINS:
            ADMINS.remove(uid)
            save_data()
            bot.send_message(
                m.chat.id,
                f"✅ Admin o'chirildi:\n{uid}",
                reply_markup=admin_menu()
            )
        else:
            bot.send_message(m.chat.id, "❌ Topilmadi", reply_markup=admin_menu())
    except:
        bot.send_message(m.chat.id, "❌ ID yubor", reply_markup=admin_menu())


# ================= GIVEAWAY =================

@bot.message_handler(func=lambda m: m.text == "🎁 Giveaway")
def new_giveaway(m):
    msg = bot.send_message(m.chat.id, "🆔 Giveaway ID yubor:")
    bot.register_next_step_handler(msg, get_gid)


def get_gid(m):
    gid = m.text.strip()
    creating[m.from_user.id] = {"gid": gid}
    msg = bot.send_message(m.chat.id, "🏆 Nechta g'olib?")
    bot.register_next_step_handler(msg, get_winners)


def get_winners(m):
    try:
        winners = int(m.text)
    except:
        bot.send_message(m.chat.id, "❌ Faqat son")
        return

    creating[m.from_user.id]["winners"] = winners
    msg = bot.send_message(m.chat.id, "📝 Asosiy text yubor:")
    bot.register_next_step_handler(msg, get_title)


def get_title(m):
    creating[m.from_user.id]["title"] = m.text
    msg = bot.send_message(m.chat.id, "🥇 Top1 text yubor:")
    bot.register_next_step_handler(msg, get_top1)


def get_top1(m):
    creating[m.from_user.id]["top1"] = m.text
    msg = bot.send_message(m.chat.id, "✍️ Qo'shimcha text yubor:")
    bot.register_next_step_handler(msg, get_extra)


def get_extra(m):
    creating[m.from_user.id]["extra"] = m.text
    msg = bot.send_message(m.chat.id, "🖼 Rasm yubor:")
    bot.register_next_step_handler(msg, get_photo)


def build_giveaway_keyboard(gid, count):
    """Giveaway uchun inline keyboard — barcha homiylar + qatnashish tugmasi."""
    kb = types.InlineKeyboardMarkup()

    # Har bir homiy uchun alohida tugma
    for sponsor in SPONSORS:
        kb.add(
            types.InlineKeyboardButton(
                f"🎯 {sponsor}",
                url=f"https://t.me/{sponsor.replace('@', '')}"
            )
        )

    kb.add(
        types.InlineKeyboardButton(
            f"🎉 Qatnashish ({count})",
            callback_data=f"join|{gid}"
        )
    )
    return kb


def get_photo(m):
    if not m.photo:
        bot.send_message(m.chat.id, "❌ Rasm yubor")
        return

    data = creating[m.from_user.id]
    gid = data["gid"]
    photo = m.photo[-1].file_id

    kb = build_giveaway_keyboard(gid, 0)

    text = (
        f"🎁 {data['title']}\n\n"
        f"🏆 Yutuqlar ✅\n\n"
        f"1. {data['top1']}\n\n"
        f"{data['extra']}\n\n"
        f"👥 Ishtirokchilar: 0\n"
        f"🏆 G'oliblar: {data['winners']}"
    )

    # Homiy borligini ham saqlash (qayta qo'shish uchun)
    giveaways[gid] = {
        "title": data["title"],
        "users": [],
        "active": True,
        "winners": data["winners"],
        "msg_id": None,
        "photo": photo,
        "caption": text
    }

    if CHANNEL:
        msg = bot.send_photo(
            CHANNEL,
            photo,
            caption=text,
            reply_markup=kb
        )
        giveaways[gid]["msg_id"] = msg.message_id

    bot.send_message(m.chat.id, "✅ Giveaway yaratildi", reply_markup=menu())
    save_data()


# ================= USER =================

def get_user(uid):
    try:
        u = bot.get_chat(uid)
        if u.username:
            return f"@{u.username}"
        return u.first_name
    except:
        return str(uid)


# ================= CALLBACK =================

@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    data = c.data

    # ================= JOIN =================
    if data.startswith("join|"):
        gid = data.split("|")[1]

        if gid not in giveaways:
            return

        g = giveaways[gid]

        if not g["active"]:
            bot.answer_callback_query(c.id, "❌ Giveaway tugagan")
            return

        uid = c.from_user.id

        # ================= HOMIYLAR TEKSHIRUVI =================
        if SPONSORS:
            not_subscribed = []
            for sponsor in SPONSORS:
                try:
                    member = bot.get_chat_member(sponsor, uid)
                    if member.status == "left":
                        not_subscribed.append(sponsor)
                except:
                    pass

            if not_subscribed:
                sponsors_list = "\n".join(not_subscribed)
                bot.answer_callback_query(
                    c.id,
                    f"❌ Avval quyidagi homiy kanallarga obuna bo'ling:\n{sponsors_list}",
                    show_alert=True
                )
                return

        # ================= DUPLICATE =================
        if uid in g["users"]:
            bot.answer_callback_query(c.id, "❌ Siz qatnashgansiz")
            return

        g["users"].append(uid)
        count = len(g["users"])

        kb = build_giveaway_keyboard(gid, count)

        # ================= UPDATE CAPTION =================
        lines = g["caption"].split("\n")
        final_text = ""
        for line in lines:
            if "👥 Ishtirokchilar:" in line:
                final_text += f"👥 Ishtirokchilar: {count}\n"
            else:
                final_text += line + "\n"

        g["caption"] = final_text.rstrip("\n")

        try:
            bot.edit_message_caption(
                caption=g["caption"],
                chat_id=CHANNEL,
                message_id=g["msg_id"],
                reply_markup=kb
            )
        except Exception as e:
            print(e)

        save_data()
        bot.answer_callback_query(c.id, "✅ Giveawayga qo'shildingiz")

    # ================= END =================
    elif data.startswith("end|"):
        gid = data.split("|")[1]

        if gid not in giveaways:
            return

        g = giveaways[gid]
        g["active"] = False

        if not g["users"]:
            bot.send_message(c.message.chat.id, "❌ Ishtirokchi yo'q")
            return

        winners = random.sample(
            g["users"],
            min(g["winners"], len(g["users"]))
        )

        txt = "🏆 G'OLIBLAR:\n\n"
        for i, w in enumerate(winners, start=1):
            txt += f"{i}. {get_user(w)}\n"

        bot.send_message(c.message.chat.id, txt)
        save_data()


# ================= STATUS =================

@bot.message_handler(func=lambda m: m.text == "📊 Status")
def status(m):
    txt = "📊 GIVEAWAYS\n\n"
    for gid, g in giveaways.items():
        txt += (
            f"🎁 {g['title']}\n"
            f"👥 {len(g['users'])}\n"
            f"🏆 {g['winners']}\n"
            f"🟢 {g['active']}\n\n"
        )
    bot.send_message(m.chat.id, txt)


# ================= END MENU =================

@bot.message_handler(func=lambda m: m.text == "🏁 Yakunlash")
def end_menu(m):
    kb = types.InlineKeyboardMarkup()
    found = False

    for gid, g in giveaways.items():
        if g["active"]:
            found = True
            kb.add(
                types.InlineKeyboardButton(
                    f"{g['title']} ({len(g['users'])})",
                    callback_data=f"end|{gid}"
                )
            )

    if not found:
        bot.send_message(m.chat.id, "❌ Aktiv giveaway yo'q")
        return

    bot.send_message(m.chat.id, "🏁 Giveaway tanlang", reply_markup=kb)


print("🔥 GIVEAWAY BOT RUNNING")
bot.infinity_polling()
