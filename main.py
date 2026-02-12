#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ziyo Star Production Bot - Advanced Marketing Bot (IMPROVED VERSION)
Python Telegram Bot 13.15 versiyasi uchun
YANGI FUNKSIYALAR: Bo'lim boshqaruvi, Reklama yuborish, Kontent qo'shish
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext, \
    ConversationHandler
import logging
import sqlite3
from datetime import datetime
import json
import time

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot tokeni
TOKEN = "8241680310:AAEGaFcOdx0vjDYEy1AypAjh8uFQLQMsg6g"

# Conversation states
(WAITING_SECTION_NAME, WAITING_SECTION_CONTENT,
 WAITING_CHANNEL_USERNAME, WAITING_ADMIN_ID,
 WAITING_BLOCK_USER_ID, WAITING_SUBSECTION_NAME,
 WAITING_SUBSECTION_CONTENT, WAITING_DELETE_SECTION_NAME,
 WAITING_ADD_CONTENT_SECTION, WAITING_ADD_CONTENT_SUBSECTION_NAME,
 WAITING_ADD_CONTENT_TEXT, WAITING_BROADCAST_MESSAGE,
 WAITING_MESSAGE_TO_USER, WAITING_USER_ID_FOR_MESSAGE) = range(14)


class Database:
    def __init__(self):
        self.conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Barcha jadvallarni yaratish"""
        # Foydalanuvchilar jadvali
        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS users
                            (
                                user_id
                                INTEGER
                                PRIMARY
                                KEY,
                                username
                                TEXT,
                                first_name
                                TEXT,
                                last_name
                                TEXT,
                                join_date
                                TEXT,
                                last_active
                                TEXT,
                                is_blocked
                                INTEGER
                                DEFAULT
                                0
                            )
                            ''')

        # Adminlar jadvali
        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS admins
                            (
                                user_id
                                INTEGER
                                PRIMARY
                                KEY,
                                added_date
                                TEXT,
                                added_by
                                INTEGER
                            )
                            ''')

        # Bo'limlar jadvali
        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS sections
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                name
                                TEXT
                                UNIQUE,
                                emoji
                                TEXT,
                                callback_data
                                TEXT
                                UNIQUE,
                                created_date
                                TEXT,
                                order_num
                                INTEGER
                            )
                            ''')

        # Bo'limlar tarkibi (subsections)
        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS subsections
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                section_id
                                INTEGER,
                                name
                                TEXT,
                                content
                                TEXT,
                                callback_data
                                TEXT
                                UNIQUE,
                                created_date
                                TEXT,
                                FOREIGN
                                KEY
                            (
                                section_id
                            ) REFERENCES sections
                            (
                                id
                            )
                                )
                            ''')

        # Majburiy kanallar jadvali
        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS channels
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                channel_username
                                TEXT
                                UNIQUE,
                                channel_id
                                TEXT,
                                added_date
                                TEXT,
                                is_active
                                INTEGER
                                DEFAULT
                                1
                            )
                            ''')

        # Statistika jadvali
        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS statistics
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                user_id
                                INTEGER,
                                section_id
                                INTEGER,
                                subsection_id
                                INTEGER,
                                action_date
                                TEXT
                            )
                            ''')

        # Bloklangan foydalanuvchilar
        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS blocked_users
                            (
                                user_id
                                INTEGER
                                PRIMARY
                                KEY,
                                blocked_date
                                TEXT,
                                blocked_by
                                INTEGER,
                                reason
                                TEXT
                            )
                            ''')

        # Reklama jadvali
        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS broadcasts
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                admin_id
                                INTEGER,
                                message_text
                                TEXT,
                                sent_count
                                INTEGER
                                DEFAULT
                                0,
                                failed_count
                                INTEGER
                                DEFAULT
                                0,
                                created_date
                                TEXT
                            )
                            ''')

        self.conn.commit()

        # Dastlabki adminni qo'shish
        self.add_admin(8381500320, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0)

        # Dastlabki bo'limlarni qo'shish
        self.init_default_sections()

    def init_default_sections(self):
        """Dastlabki bo'limlarni qo'shish"""
        default_sections = [
            ("📊 Instagram Marketing", "📊", "instagram"),
            ("📹 Video Marketing", "📹", "video"),
            ("🎯 SMM Strategiyalar", "🎯", "smm"),
            ("💡 Kontent Yaratish", "💡", "content"),
            ("📈 Analytics va Metrics", "📈", "analytics"),
        ]

        for i, (name, emoji, callback) in enumerate(default_sections):
            try:
                self.cursor.execute('''
                                    INSERT
                                    OR IGNORE INTO sections (name, emoji, callback_data, created_date, order_num)
                    VALUES (?, ?, ?, ?, ?)
                                    ''', (name, emoji, callback, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), i))
            except:
                pass

        self.conn.commit()
        self.init_default_subsections()

    def init_default_subsections(self):
        """Bo'limlarga dastlabki subsectionlarni qo'shish"""

        # Instagram subsections
        instagram_subs = [
            ("👁️ Ko'rishlar sonini oshirish", "instagram_views", self.get_instagram_views_content()),
            ("❤️ Engagement oshirish", "instagram_engagement", self.get_instagram_engagement_content()),
            ("📈 Reels strategiyasi", "instagram_reels", self.get_instagram_reels_content()),
        ]
        section_id = self.get_section_id_by_callback("instagram")
        if section_id:
            for name, callback, content in instagram_subs:
                try:
                    self.cursor.execute('''
                                        INSERT
                                        OR IGNORE INTO subsections (section_id, name, content, callback_data, created_date) 
                        VALUES (?, ?, ?, ?, ?)
                                        ''', (section_id, name, content, callback,
                                              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                except:
                    pass

        self.conn.commit()

    def get_instagram_views_content(self):
        return """👁️ <b>INSTAGRAM'DA KO'RISHLARNI OSHIRISH</b>

<b>1. REELS UCHUN:</b>
✅ Birinchi 3 soniya juda muhim
✅ Trending audio ishlatish
✅ Hook (qiziqarli boshlanish) yarating
✅ 15-30 soniya optimal davomiylik
✅ Vertikal format (9:16)

<b>2. KONTENT SIFATI:</b>
✅ HD sifatli video
✅ Yaxshi yoritilganlik
✅ Professional montaj
✅ Subtitles qo'shing
✅ Birinchi kadrda emotsiya

<b>3. POSTING VAQTI:</b>
✅ Auditoriya faol vaqti: 18:00-21:00
✅ Dushanba-Juma aktiv
✅ Insights'dan foydalaning

<b>💡 PRO MASLAHAT:</b>
Birinchi 30 daqiqa kritik! Ko'proq engagement = ko'proq reach!"""

    def get_instagram_engagement_content(self):
        return """❤️ <b>ENGAGEMENT OSHIRISH</b>

<b>1. KONTENT STRATEGIYA:</b>
✅ 80/20: 80% value, 20% promo
✅ Storytelling
✅ Shaxsiy tajriba

<b>2. CAPTION:</b>
✅ Hook bilan boshlash
✅ Savol bilan tugash
✅ Emoji ishlatish

<b>3. INTERAKTIV:</b>
✅ Poll (so'rovnoma)
✅ Quiz yaratish
✅ Q&A

<b>💡 MUHIM:</b>
Save va Share > Likes!"""

    def get_instagram_reels_content(self):
        return """📈 <b>REELS STRATEGIYA</b>

<b>1. VIRAL:</b>
✅ 7 soniya hook
✅ Trending audio
✅ Loop yaratish

<b>2. MONTAJ:</b>
✅ Quick cuts
✅ Transitions
✅ Text overlay

<b>3. COVER:</b>
✅ Yaxshi dizayn
✅ Matn
✅ Brand color

<b>💡 PRO TIP:</b>
1 soatda story'ga qo'ying!"""

    # ================== DATABASE HELPERS ==================
    def get_section_id_by_callback(self, callback_data):
        self.cursor.execute('SELECT id FROM sections WHERE callback_data = ?', (callback_data,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_section_id_by_name(self, section_name):
        """Bo'limni nomi bo'yicha ID ni topish"""
        self.cursor.execute('SELECT id FROM sections WHERE name LIKE ?', (f'%{section_name}%',))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_section_name_by_id(self, section_id):
        """Bo'lim nomini ID bo'yicha olish"""
        self.cursor.execute('SELECT name FROM sections WHERE id = ?', (section_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def add_user(self, user_id, username, first_name, last_name):
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, join_date, last_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name,
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            self.conn.commit()
        except Exception as e:
            logger.error(f"User add error: {e}")

    def update_last_active(self, user_id):
        try:
            self.cursor.execute('''
                                UPDATE users
                                SET last_active = ?
                                WHERE user_id = ?
                                ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
            self.conn.commit()
        except:
            pass

    def is_admin(self, user_id):
        self.cursor.execute('SELECT * FROM admins WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone() is not None

    def add_admin(self, user_id, added_date, added_by):
        try:
            self.cursor.execute('''
                                INSERT
                                OR IGNORE INTO admins (user_id, added_date, added_by)
                VALUES (?, ?, ?)
                                ''', (user_id, added_date, added_by))
            self.conn.commit()
            return True
        except:
            return False

    def remove_admin(self, user_id):
        try:
            self.cursor.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
            self.conn.commit()
            return True
        except:
            return False

    def get_admins(self):
        self.cursor.execute('SELECT user_id FROM admins')
        return [row[0] for row in self.cursor.fetchall()]

    def add_channel(self, channel_username, channel_id=None):
        try:
            self.cursor.execute('''
                                INSERT INTO channels (channel_username, channel_id, added_date, is_active)
                                VALUES (?, ?, ?, 1)
                                ''', (channel_username, channel_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            self.conn.commit()
            return True
        except:
            return False

    def remove_channel(self, channel_id):
        try:
            self.cursor.execute('DELETE FROM channels WHERE id = ?', (channel_id,))
            self.conn.commit()
            return True
        except:
            return False

    def get_active_channels(self):
        self.cursor.execute('SELECT id, channel_username FROM channels WHERE is_active = 1')
        return self.cursor.fetchall()

    def is_user_blocked(self, user_id):
        self.cursor.execute('SELECT * FROM blocked_users WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone() is not None

    def block_user(self, user_id, blocked_by, reason=""):
        try:
            self.cursor.execute('''
                                INSERT INTO blocked_users (user_id, blocked_date, blocked_by, reason)
                                VALUES (?, ?, ?, ?)
                                ''', (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), blocked_by, reason))
            self.conn.commit()
            return True
        except:
            return False

    def unblock_user(self, user_id):
        try:
            self.cursor.execute('DELETE FROM blocked_users WHERE user_id = ?', (user_id,))
            self.conn.commit()
            return True
        except:
            return False

    def get_blocked_users(self):
        self.cursor.execute('SELECT user_id, reason, blocked_date FROM blocked_users')
        return self.cursor.fetchall()

    def get_all_sections(self):
        self.cursor.execute('SELECT id, name, emoji, callback_data FROM sections ORDER BY order_num')
        return self.cursor.fetchall()

    def get_subsections(self, section_id):
        self.cursor.execute('SELECT id, name, callback_data FROM subsections WHERE section_id = ?', (section_id,))
        return self.cursor.fetchall()

    def get_subsection_content(self, callback_data):
        self.cursor.execute('SELECT content FROM subsections WHERE callback_data = ?', (callback_data,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def add_section(self, name, emoji, callback_data):
        try:
            self.cursor.execute('SELECT MAX(order_num) FROM sections')
            max_order = self.cursor.fetchone()[0] or 0

            self.cursor.execute('''
                                INSERT INTO sections (name, emoji, callback_data, created_date, order_num)
                                VALUES (?, ?, ?, ?, ?)
                                ''', (name, emoji, callback_data, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                      max_order + 1))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Section add error: {e}")
            return False

    def delete_section(self, section_id):
        try:
            self.cursor.execute('DELETE FROM subsections WHERE section_id = ?', (section_id,))
            self.cursor.execute('DELETE FROM sections WHERE id = ?', (section_id,))
            self.conn.commit()
            return True
        except:
            return False

    def delete_section_by_name(self, section_name):
        """Bo'limni nomi bo'yicha o'chirish"""
        section_id = self.get_section_id_by_name(section_name)
        if section_id:
            return self.delete_section(section_id)
        return False

    def add_subsection(self, section_id, name, content, callback_data):
        try:
            self.cursor.execute('''
                                INSERT INTO subsections (section_id, name, content, callback_data, created_date)
                                VALUES (?, ?, ?, ?, ?)
                                ''', (section_id, name, content, callback_data,
                                      datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Subsection add error: {e}")
            return False

    def delete_subsection(self, subsection_id):
        try:
            self.cursor.execute('DELETE FROM subsections WHERE id = ?', (subsection_id,))
            self.conn.commit()
            return True
        except:
            return False

    def get_all_users(self):
        """Barcha foydalanuvchilarni olish"""
        self.cursor.execute('SELECT user_id FROM users')
        return [row[0] for row in self.cursor.fetchall()]

    def get_statistics(self):
        stats = {}
        self.cursor.execute('SELECT COUNT(*) FROM users')
        stats['total_users'] = self.cursor.fetchone()[0]

        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute('SELECT COUNT(*) FROM users WHERE join_date LIKE ?', (f"{today}%",))
        stats['today_users'] = self.cursor.fetchone()[0]

        self.cursor.execute('''
                            SELECT COUNT(*)
                            FROM users
                            WHERE datetime(last_active) > datetime('now', '-1 day')
                            ''')
        stats['active_24h'] = self.cursor.fetchone()[0]

        self.cursor.execute('SELECT COUNT(*) FROM sections')
        stats['total_sections'] = self.cursor.fetchone()[0]

        self.cursor.execute('SELECT COUNT(*) FROM channels WHERE is_active = 1')
        stats['total_channels'] = self.cursor.fetchone()[0]

        self.cursor.execute('SELECT COUNT(*) FROM blocked_users')
        stats['blocked_users'] = self.cursor.fetchone()[0]

        self.cursor.execute('SELECT COUNT(*) FROM admins')
        stats['total_admins'] = self.cursor.fetchone()[0]

        return stats

    def save_broadcast(self, admin_id, message_text, sent_count, failed_count):
        """Reklama yuborish statistikasini saqlash"""
        try:
            self.cursor.execute('''
                                INSERT INTO broadcasts (admin_id, message_text, sent_count, failed_count, created_date)
                                VALUES (?, ?, ?, ?, ?)
                                ''', (admin_id, message_text, sent_count, failed_count,
                                      datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            self.conn.commit()
            return True
        except:
            return False


# Global database instance
db = Database()


# ================== BOT FUNCTIONS ==================
def check_subscription(update: Update, context: CallbackContext) -> bool:
    user_id = update.effective_user.id
    channels = db.get_active_channels()

    if not channels:
        return True

    not_subscribed = []

    for channel_id, channel_username in channels:
        try:
            member = context.bot.get_chat_member(f"@{channel_username}", user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_subscribed.append(channel_username)
        except:
            continue

    if not_subscribed:
        keyboard = []
        for username in not_subscribed:
            keyboard.append([InlineKeyboardButton(f"📢 {username}", url=f"https://t.me/{username}")])
        keyboard.append([InlineKeyboardButton("✅ Tekshirish", callback_data='check_subscription')])

        reply_markup = InlineKeyboardMarkup(keyboard)

        text = """
🔒 <b>BOTDAN FOYDALANISH</b>

Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:

Obuna bo'lgandan keyin "✅ Tekshirish" tugmasini bosing.
"""

        if update.message:
            update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        else:
            update.callback_query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

        return False

    return True


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user

    if db.is_user_blocked(user.id):
        update.message.reply_text("❌ Siz botdan foydalanish huquqidan mahrum qilindingiz.")
        return

    db.add_user(user.id, user.username, user.first_name, user.last_name)
    db.update_last_active(user.id)

    if not check_subscription(update, context):
        return

    show_main_menu(update, context, is_start=True)


def show_main_menu(update, context, is_start=False):
    user = update.effective_user
    sections = db.get_all_sections()

    keyboard = []
    row = []
    for section_id, name, emoji, callback_data in sections:
        button = InlineKeyboardButton(f"{emoji} {name.replace(emoji, '').strip()}",
                                      callback_data=f'section_{callback_data}')
        row.append(button)
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("ℹ️ Bot haqida", callback_data='about')])

    if db.is_admin(user.id):
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin_panel')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = f"""
🌟 <b>Assalomu alaykum, {user.first_name}!</b>

Ziyo Star Production botiga xush kelibsiz! 🎬

Men sizga marketing bo'yicha professional maslahatlar berishga tayyorman.

Kerakli bo'limni tanlang! 👇
"""

    if is_start:
        update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    else:
        if update.callback_query:
            update.callback_query.message.edit_text(welcome_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        else:
            update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        query.message.edit_text("❌ Siz botdan foydalanish huquqidan mahrum qilindingiz.")
        return

    db.update_last_active(user_id)

    if query.data == 'check_subscription':
        if check_subscription(update, context):
            show_main_menu(update, context)
        return

    if query.data not in ['about', 'admin_panel', 'admin_back'] and not query.data.startswith('admin_'):
        if not check_subscription(update, context):
            return

    if query.data.startswith('section_'):
        callback_data = query.data.replace('section_', '')
        show_section_details(query, callback_data)

    elif query.data.startswith('sub_'):
        callback_data = query.data.replace('sub_', '')
        show_subsection_content(query, callback_data, user_id)

    elif query.data == 'about':
        show_about(query)

    elif query.data == 'back':
        show_main_menu(update, context)

    elif query.data == 'admin_panel':
        if db.is_admin(user_id):
            show_admin_panel(query)

    elif query.data.startswith('admin_'):
        if db.is_admin(user_id):
            handle_admin_actions(update, context)


def show_section_details(query, callback_data):
    section_id = db.get_section_id_by_callback(callback_data)

    if not section_id:
        query.message.edit_text("❌ Bo'lim topilmadi!")
        return

    subsections = db.get_subsections(section_id)

    if not subsections:
        query.message.edit_text("❌ Bu bo'limda hali ma'lumot yo'q!")
        return

    sections = db.get_all_sections()
    section_name = next((name for sid, name, emoji, cbd in sections if cbd == callback_data), "")

    keyboard = []
    for sub_id, sub_name, sub_callback in subsections:
        keyboard.append([InlineKeyboardButton(sub_name, callback_data=f'sub_{sub_callback}')])

    keyboard.append([InlineKeyboardButton("◀️ Orqaga", callback_data='back')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = f"""
<b>{section_name}</b>

Quyidagi mavzulardan birini tanlang: 👇
"""

    query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


def show_subsection_content(query, callback_data, user_id):
    content = db.get_subsection_content(callback_data)

    if not content:
        query.message.edit_text("❌ Ma'lumot topilmadi!")
        return

    keyboard = [[InlineKeyboardButton("◀️ Orqaga", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.edit_text(content, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


def show_about(query):
    text = """
ℹ️ <b>BOT HAQIDA</b>

🌟 <b>Ziyo Star Production Bot</b>

Professional marketing maslahatlar boti.

<b>📚 Imkoniyatlar:</b>
✅ Marketing bo'limlari
✅ Professional maslahatlar
✅ Doimiy yangilanishlar
✅ Admin panel

<b>🎯 Maqsad:</b>
Biznesingizni social media'da o'stirish!

<b>👨‍💻 Yaratuvchi:</b>
Ziyo Star Production

<b>📊 Versiya:</b>
3.0 Advanced (Improved)

<i>Marketing - bu san'at va fan!</i> 🎨📊
"""

    keyboard = [[InlineKeyboardButton("◀️ Orqaga", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


def show_admin_panel(query):
    keyboard = [
        [InlineKeyboardButton("📊 Statistika", callback_data='admin_stats')],
        [InlineKeyboardButton("📢 Reklama Yuborish", callback_data='admin_broadcast')],
        [InlineKeyboardButton("📁 Bo'limlar Boshqaruvi", callback_data='admin_sections')],
        [InlineKeyboardButton("➕ Kontent Qo'shish", callback_data='admin_add_content')],
        [InlineKeyboardButton("✉️ Xabar Yuborish", callback_data='admin_message_user')],
        [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data='admin_users')],
        [InlineKeyboardButton("📢 Kanallar", callback_data='admin_channels')],
        [InlineKeyboardButton("👨‍💼 Adminlar", callback_data='admin_admins')],
        [InlineKeyboardButton("🚫 Bloklash", callback_data='admin_block')],
        [InlineKeyboardButton("◀️ Orqaga", callback_data='back')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = """
⚙️ <b>ADMIN PANEL</b>

Yangi funksiyalar:
✅ Reklama yuborish tizimi
✅ Bo'limlarga kontent qo'shish
✅ Foydalanuvchiga xabar yuborish

Bo'limni tanlang:
"""

    query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


def handle_admin_actions(update: Update, context: CallbackContext):
    query = update.callback_query

    if query.data == 'admin_stats':
        show_statistics(query)
    elif query.data == 'admin_broadcast':
        start_broadcast(update, context)
    elif query.data == 'admin_sections':
        show_sections_management(query)
    elif query.data == 'admin_add_content':
        start_add_content(update, context)
    elif query.data == 'admin_message_user':
        start_message_to_user(update, context)
    elif query.data == 'admin_users':
        show_users_list(query)
    elif query.data == 'admin_channels':
        show_channels_management(query)
    elif query.data == 'admin_admins':
        show_admins_management(query)
    elif query.data == 'admin_block':
        show_block_management(query)
    elif query.data == 'admin_back':
        show_admin_panel(query)


def show_statistics(query):
    stats = db.get_statistics()

    text = f"""
📊 <b>BOT STATISTIKASI</b>

👥 <b>Foydalanuvchilar:</b>
• Jami: {stats['total_users']}
• Bugungi yangi: {stats['today_users']}
• Aktiv (24h): {stats['active_24h']}

📁 <b>Bo'limlar:</b>
• Jami: {stats['total_sections']}

📢 <b>Kanallar:</b>
• Aktiv: {stats['total_channels']}

👨‍💼 <b>Adminlar:</b>
• Jami: {stats['total_admins']}

🚫 <b>Bloklangan:</b>
• Foydalanuvchilar: {stats['blocked_users']}

<i>Oxirgi yangilanish: {datetime.now().strftime("%Y-%m-%d %H:%M")}</i>
"""

    keyboard = [
        [InlineKeyboardButton("🔄 Yangilash", callback_data='admin_stats')],
        [InlineKeyboardButton("◀️ Orqaga", callback_data='admin_back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


def show_sections_management(query):
    sections = db.get_all_sections()

    text = f"""
📁 <b>BO'LIMLAR BOSHQARUVI</b>

<b>Mavjud bo'limlar ({len(sections)}):</b>
"""

    for section_id, name, emoji, callback in sections[:15]:
        text += f"\n• {section_id}. {name}"

    if len(sections) > 15:
        text += f"\n\n... va yana {len(sections) - 15} ta bo'lim"

    text += "\n\n<b>Buyruqlar:</b>"
    text += "\n/add_section Nomi;Emoji;callback - Bo'lim qo'shish"
    text += "\n/delete_section_by_name Bo'lim nomi - Bo'limni o'chirish"
    text += "\n\n<b>Misol:</b>"
    text += "\n/delete_section_by_name Instagram Marketing"

    keyboard = [[InlineKeyboardButton("◀️ Orqaga", callback_data='admin_back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


def show_users_list(query):
    stats = db.get_statistics()

    text = f"""
👥 <b>FOYDALANUVCHILAR</b>

<b>Umumiy ma'lumot:</b>
• Jami: {stats['total_users']}
• Bugungi yangi: {stats['today_users']}
• Aktiv (24h): {stats['active_24h']}

Batafsil ma'lumot uchun database'ni tekshiring.
"""

    keyboard = [[InlineKeyboardButton("◀️ Orqaga", callback_data='admin_back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


def show_channels_management(query):
    channels = db.get_active_channels()

    text = """
📢 <b>KANALLAR BOSHQARUVI</b>

<b>Aktiv kanallar:</b>
"""

    if channels:
        for i, (channel_id, username) in enumerate(channels, 1):
            text += f"\n{i}. @{username} (ID: {channel_id})"
    else:
        text += "\n<i>Hozircha kanallar yo'q</i>"

    text += "\n\n/add_channel @username - Kanal qo'shish"
    text += "\n/remove_channel ID - Kanal o'chirish"

    keyboard = [[InlineKeyboardButton("◀️ Orqaga", callback_data='admin_back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


def show_admins_management(query):
    admins = db.get_admins()

    text = f"""
👨‍💼 <b>ADMINLAR BOSHQARUVI</b>

<b>Adminlar soni:</b> {len(admins)}

<b>Admin ID'lar:</b>
"""

    for admin_id in admins:
        text += f"\n• {admin_id}"

    text += "\n\n/add_admin USER_ID - Admin qo'shish"
    text += "\n/remove_admin USER_ID - Admin o'chirish"

    keyboard = [[InlineKeyboardButton("◀️ Orqaga", callback_data='admin_back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


def show_block_management(query):
    blocked = db.get_blocked_users()

    text = """
🚫 <b>BLOKLASH BOSHQARUVI</b>

"""

    if blocked:
        text += f"<b>Bloklangan ({len(blocked)}):</b>\n"
        for user_id, reason, date in blocked[:10]:
            text += f"\n• ID: {user_id}"
            if reason:
                text += f" ({reason})"
    else:
        text += "<i>Bloklangan foydalanuvchilar yo'q</i>"

    text += "\n\n/block USER_ID sabab - Bloklash"
    text += "\n/unblock USER_ID - Blokdan chiqarish"

    keyboard = [[InlineKeyboardButton("◀️ Orqaga", callback_data='admin_back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


# ================== YANGI FUNKSIYALAR ==================

# 1. REKLAMA YUBORISH
def start_broadcast(update: Update, context: CallbackContext):
    query = update.callback_query

    text = """
📢 <b>REKLAMA YUBORISH</b>

Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring.

Xabar har qanday formatda bo'lishi mumkin:
• Matn
• Rasm + matn
• Video + matn
• Audio + matn
• Dokument + matn

Bekor qilish uchun /cancel ni yuboring.
"""

    query.message.edit_text(text, parse_mode=ParseMode.HTML)
    return WAITING_BROADCAST_MESSAGE


def receive_broadcast_message(update: Update, context: CallbackContext):
    if update.message.text and update.message.text == '/cancel':
        update.message.reply_text("❌ Bekor qilindi!")
        return ConversationHandler.END

    # Xabarni saqlash
    context.user_data['broadcast_message'] = update.message

    confirm_text = """
✅ <b>Xabar qabul qilindi!</b>

Ushbu xabarni barcha foydalanuvchilarga yuborishni tasdiqlaysizmi?

/yes - Yuborish
/no - Bekor qilish
"""

    update.message.reply_text(confirm_text, parse_mode=ParseMode.HTML)
    return WAITING_BROADCAST_MESSAGE


def confirm_broadcast(update: Update, context: CallbackContext):
    if update.message.text == '/no':
        update.message.reply_text("❌ Bekor qilindi!")
        return ConversationHandler.END

    if update.message.text != '/yes':
        update.message.reply_text("Iltimos /yes yoki /no yuboring!")
        return WAITING_BROADCAST_MESSAGE

    # Yuborish jarayoni
    broadcast_msg = context.user_data.get('broadcast_message')
    users = db.get_all_users()

    sent_count = 0
    failed_count = 0

    progress_msg = update.message.reply_text("📤 Yuborilmoqda... 0%")

    total_users = len(users)
    for i, user_id in enumerate(users):
        try:
            # Xabar turini aniqlash va yuborish
            if broadcast_msg.text:
                context.bot.send_message(chat_id=user_id, text=broadcast_msg.text, parse_mode=ParseMode.HTML)
            elif broadcast_msg.photo:
                context.bot.send_photo(
                    chat_id=user_id,
                    photo=broadcast_msg.photo[-1].file_id,
                    caption=broadcast_msg.caption or "",
                    parse_mode=ParseMode.HTML
                )
            elif broadcast_msg.video:
                context.bot.send_video(
                    chat_id=user_id,
                    video=broadcast_msg.video.file_id,
                    caption=broadcast_msg.caption or "",
                    parse_mode=ParseMode.HTML
                )
            elif broadcast_msg.document:
                context.bot.send_document(
                    chat_id=user_id,
                    document=broadcast_msg.document.file_id,
                    caption=broadcast_msg.caption or "",
                    parse_mode=ParseMode.HTML
                )
            elif broadcast_msg.audio:
                context.bot.send_audio(
                    chat_id=user_id,
                    audio=broadcast_msg.audio.file_id,
                    caption=broadcast_msg.caption or "",
                    parse_mode=ParseMode.HTML
                )

            sent_count += 1
            time.sleep(0.05)  # Telegram limitlaridan qochish uchun
        except Exception as e:
            failed_count += 1
            logger.error(f"Broadcast error for user {user_id}: {e}")

        # Progress yangilash
        if (i + 1) % 10 == 0:
            percent = int(((i + 1) / total_users) * 100)
            try:
                progress_msg.edit_text(
                    f"📤 Yuborilmoqda... {percent}%\n\n✅ Yuborildi: {sent_count}\n❌ Xatolik: {failed_count}")
            except:
                pass

    # Natijani saqlash
    message_text = broadcast_msg.text or broadcast_msg.caption or "Media fayl"
    db.save_broadcast(update.effective_user.id, message_text, sent_count, failed_count)

    final_text = f"""
✅ <b>REKLAMA YUBORILDI!</b>

📊 <b>Statistika:</b>
• Jami: {total_users}
• Yuborildi: {sent_count}
• Xatolik: {failed_count}

<i>Vaqt: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</i>
"""

    progress_msg.edit_text(final_text, parse_mode=ParseMode.HTML)
    return ConversationHandler.END


# 2. BO'LIMGA KONTENT QO'SHISH
def start_add_content(update: Update, context: CallbackContext):
    query = update.callback_query
    sections = db.get_all_sections()

    text = """
➕ <b>KONTENT QO'SHISH</b>

Qaysi bo'limga kontent qo'shmoqchisiz?

<b>Mavjud bo'limlar:</b>
"""

    for section_id, name, emoji, callback in sections:
        text += f"\n{section_id}. {name}"

    text += "\n\nBo'lim nomini yuboring (masalan: Instagram Marketing)"
    text += "\nBekor qilish: /cancel"

    query.message.edit_text(text, parse_mode=ParseMode.HTML)
    return WAITING_ADD_CONTENT_SECTION


def receive_content_section(update: Update, context: CallbackContext):
    if update.message.text == '/cancel':
        update.message.reply_text("❌ Bekor qilindi!")
        return ConversationHandler.END

    section_name = update.message.text
    section_id = db.get_section_id_by_name(section_name)

    if not section_id:
        update.message.reply_text("❌ Bunday bo'lim topilmadi! Qaytadan urinib ko'ring yoki /cancel ni yuboring.")
        return WAITING_ADD_CONTENT_SECTION

    context.user_data['content_section_id'] = section_id
    context.user_data['content_section_name'] = db.get_section_name_by_id(section_id)

    update.message.reply_text(
        f"✅ Bo'lim tanlandi: {context.user_data['content_section_name']}\n\n"
        "Endi subsection nomini yuboring (masalan: Yangi mavzu)\n"
        "Bekor qilish: /cancel",
        parse_mode=ParseMode.HTML
    )
    return WAITING_ADD_CONTENT_SUBSECTION_NAME


def receive_content_subsection_name(update: Update, context: CallbackContext):
    if update.message.text == '/cancel':
        update.message.reply_text("❌ Bekor qilindi!")
        return ConversationHandler.END

    context.user_data['content_subsection_name'] = update.message.text

    update.message.reply_text(
        "📝 Endi kontent matnini yuboring (HTML formatda):\n\n"
        "Bekor qilish: /cancel",
        parse_mode=ParseMode.HTML
    )
    return WAITING_ADD_CONTENT_TEXT


def receive_content_text(update: Update, context: CallbackContext):
    if update.message.text == '/cancel':
        update.message.reply_text("❌ Bekor qilindi!")
        return ConversationHandler.END

    section_id = context.user_data['content_section_id']
    subsection_name = context.user_data['content_subsection_name']
    content_text = update.message.text

    # Callback data yaratish
    import re
    callback_data = re.sub(r'[^a-z0-9_]', '', subsection_name.lower().replace(' ', '_'))
    callback_data = f"content_{callback_data}_{int(time.time())}"

    if db.add_subsection(section_id, subsection_name, content_text, callback_data):
        update.message.reply_text(
            f"✅ <b>Kontent muvaffaqiyatli qo'shildi!</b>\n\n"
            f"Bo'lim: {context.user_data['content_section_name']}\n"
            f"Subsection: {subsection_name}",
            parse_mode=ParseMode.HTML
        )
    else:
        update.message.reply_text("❌ Xatolik yuz berdi! Qaytadan urinib ko'ring.")

    return ConversationHandler.END


# 3. FOYDALANUVCHIGA XABAR YUBORISH
def start_message_to_user(update: Update, context: CallbackContext):
    query = update.callback_query

    text = """
✉️ <b>FOYDALANUVCHIGA XABAR</b>

Foydalanuvchi ID sini yuboring:

Bekor qilish: /cancel
"""

    query.message.edit_text(text, parse_mode=ParseMode.HTML)
    return WAITING_USER_ID_FOR_MESSAGE


def receive_user_id_for_message(update: Update, context: CallbackContext):
    if update.message.text == '/cancel':
        update.message.reply_text("❌ Bekor qilindi!")
        return ConversationHandler.END

    try:
        user_id = int(update.message.text)
        context.user_data['message_target_user_id'] = user_id

        update.message.reply_text(
            f"✅ Foydalanuvchi ID: {user_id}\n\n"
            "Endi yubormoqchi bo'lgan xabaringizni yuboring:\n\n"
            "Bekor qilish: /cancel"
        )
        return WAITING_MESSAGE_TO_USER
    except:
        update.message.reply_text("❌ Noto'g'ri ID! Raqam kiriting yoki /cancel yuboring.")
        return WAITING_USER_ID_FOR_MESSAGE


def receive_message_to_user(update: Update, context: CallbackContext):
    if update.message.text == '/cancel':
        update.message.reply_text("❌ Bekor qilindi!")
        return ConversationHandler.END

    target_user_id = context.user_data['message_target_user_id']

    try:
        # Xabarni yuborish
        if update.message.text:
            context.bot.send_message(chat_id=target_user_id, text=update.message.text, parse_mode=ParseMode.HTML)
        elif update.message.photo:
            context.bot.send_photo(
                chat_id=target_user_id,
                photo=update.message.photo[-1].file_id,
                caption=update.message.caption or ""
            )

        update.message.reply_text(f"✅ Xabar yuborildi! (User ID: {target_user_id})")
    except Exception as e:
        update.message.reply_text(f"❌ Xatolik: {str(e)}")

    return ConversationHandler.END


# Admin commands
def add_channel_command(update: Update, context: CallbackContext):
    if not db.is_admin(update.effective_user.id):
        return

    if len(context.args) < 1:
        update.message.reply_text("Format: /add_channel @username")
        return

    username = context.args[0].replace('@', '')

    if db.add_channel(username):
        update.message.reply_text(f"✅ Kanal @{username} qo'shildi!")
    else:
        update.message.reply_text("❌ Xatolik yuz berdi!")


def remove_channel_command(update: Update, context: CallbackContext):
    if not db.is_admin(update.effective_user.id):
        return

    if len(context.args) < 1:
        update.message.reply_text("Format: /remove_channel ID")
        return

    try:
        channel_id = int(context.args[0])
        if db.remove_channel(channel_id):
            update.message.reply_text("✅ Kanal o'chirildi!")
        else:
            update.message.reply_text("❌ Xatolik!")
    except:
        update.message.reply_text("ID raqam bo'lishi kerak!")


def add_admin_command(update: Update, context: CallbackContext):
    if not db.is_admin(update.effective_user.id):
        return

    if len(context.args) < 1:
        update.message.reply_text("Format: /add_admin USER_ID")
        return

    try:
        user_id = int(context.args[0])
        if db.add_admin(user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), update.effective_user.id):
            update.message.reply_text(f"✅ Admin qo'shildi: {user_id}")
        else:
            update.message.reply_text("❌ Xatolik!")
    except:
        update.message.reply_text("ID raqam bo'lishi kerak!")


def remove_admin_command(update: Update, context: CallbackContext):
    if not db.is_admin(update.effective_user.id):
        return

    if len(context.args) < 1:
        update.message.reply_text("Format: /remove_admin USER_ID")
        return

    try:
        user_id = int(context.args[0])
        if db.remove_admin(user_id):
            update.message.reply_text(f"✅ Admin o'chirildi: {user_id}")
        else:
            update.message.reply_text("❌ Xatolik!")
    except:
        update.message.reply_text("ID raqam bo'lishi kerak!")


def block_user_command(update: Update, context: CallbackContext):
    if not db.is_admin(update.effective_user.id):
        return

    if len(context.args) < 1:
        update.message.reply_text("Format: /block USER_ID sabab")
        return

    try:
        user_id = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else ""

        if db.block_user(user_id, update.effective_user.id, reason):
            update.message.reply_text(f"✅ Foydalanuvchi bloklandi: {user_id}")
        else:
            update.message.reply_text("❌ Xatolik!")
    except:
        update.message.reply_text("ID raqam bo'lishi kerak!")


def unblock_user_command(update: Update, context: CallbackContext):
    if not db.is_admin(update.effective_user.id):
        return

    if len(context.args) < 1:
        update.message.reply_text("Format: /unblock USER_ID")
        return

    try:
        user_id = int(context.args[0])
        if db.unblock_user(user_id):
            update.message.reply_text(f"✅ Blokdan chiqarildi: {user_id}")
        else:
            update.message.reply_text("❌ Xatolik!")
    except:
        update.message.reply_text("ID raqam bo'lishi kerak!")


def add_section_command(update: Update, context: CallbackContext):
    if not db.is_admin(update.effective_user.id):
        return

    args_text = " ".join(context.args)
    parts = args_text.split(";")

    if len(parts) < 3:
        update.message.reply_text(
            "Format: /add_section Bo'lim Nomi;Emoji;callback_data\n"
            "Misol: /add_section Yangi Bo'lim;🆕;new_section"
        )
        return

    name = parts[0].strip()
    emoji = parts[1].strip()
    callback = parts[2].strip()

    if db.add_section(name, emoji, callback):
        update.message.reply_text(f"✅ Bo'lim qo'shildi: {emoji} {name}")
    else:
        update.message.reply_text("❌ Xatolik! Callback data takrorlangan bo'lishi mumkin.")


def delete_section_by_name_command(update: Update, context: CallbackContext):
    """Bo'limni nomi bo'yicha o'chirish"""
    if not db.is_admin(update.effective_user.id):
        return

    if len(context.args) < 1:
        update.message.reply_text(
            "Format: /delete_section_by_name Bo'lim nomi\n"
            "Misol: /delete_section_by_name Instagram Marketing"
        )
        return

    section_name = " ".join(context.args)

    if db.delete_section_by_name(section_name):
        update.message.reply_text(f"✅ Bo'lim o'chirildi: {section_name}")
    else:
        update.message.reply_text(f"❌ Bo'lim topilmadi: {section_name}")


def help_command(update: Update, context: CallbackContext):
    text = """
📖 <b>YORDAM</b>

<b>Foydalanuvchi buyruqlari:</b>
/start - Botni boshlash
/help - Yordam

<b>Admin buyruqlari:</b>
/add_channel @username - Kanal qo'shish
/remove_channel ID - Kanal o'chirish
/add_admin USER_ID - Admin qo'shish
/remove_admin USER_ID - Admin o'chirish
/block USER_ID sabab - Bloklash
/unblock USER_ID - Blokdan chiqarish
/add_section Nomi;Emoji;callback - Bo'lim qo'shish
/delete_section_by_name Bo'lim nomi - Bo'limni o'chirish

<b>Yangi funksiyalar:</b>
• Reklama yuborish (Admin Panel)
• Bo'limga kontent qo'shish (Admin Panel)
• Foydalanuvchiga xabar yuborish (Admin Panel)
"""

    update.message.reply_text(text, parse_mode=ParseMode.HTML)


def cancel_command(update: Update, context: CallbackContext):
    update.message.reply_text("❌ Jarayon bekor qilindi!")
    return ConversationHandler.END


def text_handler(update: Update, context: CallbackContext):
    update.message.reply_text("Menyu ko'rish uchun /start bosing! 😊")


def error_handler(update: Update, context: CallbackContext):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Conversation Handlers
    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_broadcast, pattern='^admin_broadcast$')],
        states={
            WAITING_BROADCAST_MESSAGE: [
                MessageHandler(Filters.all & ~Filters.command, receive_broadcast_message),
                CommandHandler('yes', confirm_broadcast),
                CommandHandler('no', confirm_broadcast),
                CommandHandler('cancel', cancel_command)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel_command)]
    )

    add_content_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_content, pattern='^admin_add_content$')],
        states={
            WAITING_ADD_CONTENT_SECTION: [MessageHandler(Filters.text & ~Filters.command, receive_content_section)],
            WAITING_ADD_CONTENT_SUBSECTION_NAME: [
                MessageHandler(Filters.text & ~Filters.command, receive_content_subsection_name)],
            WAITING_ADD_CONTENT_TEXT: [MessageHandler(Filters.text & ~Filters.command, receive_content_text)]
        },
        fallbacks=[CommandHandler('cancel', cancel_command)]
    )

    message_user_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_message_to_user, pattern='^admin_message_user$')],
        states={
            WAITING_USER_ID_FOR_MESSAGE: [MessageHandler(Filters.text & ~Filters.command, receive_user_id_for_message)],
            WAITING_MESSAGE_TO_USER: [MessageHandler(Filters.all & ~Filters.command, receive_message_to_user)]
        },
        fallbacks=[CommandHandler('cancel', cancel_command)]
    )

    # Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("cancel", cancel_command))
    dp.add_handler(CommandHandler("add_channel", add_channel_command))
    dp.add_handler(CommandHandler("remove_channel", remove_channel_command))
    dp.add_handler(CommandHandler("add_admin", add_admin_command))
    dp.add_handler(CommandHandler("remove_admin", remove_admin_command))
    dp.add_handler(CommandHandler("block", block_user_command))
    dp.add_handler(CommandHandler("unblock", unblock_user_command))
    dp.add_handler(CommandHandler("add_section", add_section_command))
    dp.add_handler(CommandHandler("delete_section_by_name", delete_section_by_name_command))

    # Conversation handlers
    dp.add_handler(broadcast_conv)
    dp.add_handler(add_content_conv)
    dp.add_handler(message_user_conv)

    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, text_handler))

    dp.add_error_handler(error_handler)

    updater.start_polling()
    logger.info("Bot ishga tushdi!")
    print("🤖 Improved Bot ishlayapti...")
    print("📊 Database: bot_database.db")
    print("✅ YANGI FUNKSIYALAR:")
    print("   1. Bo'limni nom bilan o'chirish")
    print("   2. Bo'limga kontent qo'shish")
    print("   3. Reklama yuborish tizimi")
    print("   4. Foydalanuvchiga xabar yuborish")
    print("   5. Takomillashtirilgan admin panel")
    print("\n✅ Tayyor!")

    updater.idle()


if __name__ == '__main__':
    main()
