import os
import sqlite3
import asyncio
import json from flask import Flask, request, abort
from aiogram import Bot, Dispatcher, types
from aiogram.types import (Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.dispatcher.filters import Command
from aiogram.utils.executor import start_webhook
from threading import Thread
from datetime import datetime
from collections import defaultdict
import yt_dlp

# === Настройки ===

TOKEN = "7661435901:AAFx8X7mY9wwW5FEeKofbLc9GddmX_tLlYk"
ADMIN_ID = 1001788720
DATABASE = "users.db"
WEBHOOK_PATH = f"/webhook/{TOKEN}"
RENDER_DOMAIN = os.environ.get("RENDER_EXTERNAL_URL", "https://tgreels.onrender.com").rstrip("/")
WEBHOOK_URL = f"{RENDER_DOMAIN}{WEBHOOK_PATH}"

# === Инициализация ===

bot = Bot(token=TOKEN)
Bot.set_current(bot)
dp = Dispatcher(bot)
app = Flask(__name__)

# === Антиспам ===

user_last_request = defaultdict(lambda: 0)
SPAM_TIMEOUT = 10


# === Клавиатура языков ===

def get_language_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🇬🇧 English"), KeyboardButton("🇷🇺 Русский"))
    keyboard.add(KeyboardButton("🇺🇦 Українська"), KeyboardButton("🇩🇪 Deutsch"))
    keyboard.add(KeyboardButton("🇺🇿 O‘zbekcha"), KeyboardButton("🇰🇿 Қазақша"))
    keyboard.add(KeyboardButton("🇰🇷 한국어"), KeyboardButton("🇹🇷 Türkçe"))
    return keyboard

# === Инициализация базы данных ===

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users( user_id INTEGER PRIMARY KEY, language TEXT DEFAULT 'en', downloads INTEGER DEFAULT 0, banned INTEGER DEFAULT 0 ) ''')
    conn.commit()
    conn.close()
init_db()

# === Работа с БД ===

def get_user_language(user_id):
    conn = sqlite3.connect(DATABASE) cursor = conn.cursor()
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 'en'

def set_user_language(user_id, lang):
    conn = sqlite3.connect(DATABASE) cursor = conn.cursor()
    cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect(DATABASE) cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def increment_downloads(user_id):
    conn = sqlite3.connect(DATABASE) cursor = conn.cursor()
    cursor.execute("UPDATE users SET downloads = downloads + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_user_downloads(user_id):
    conn = sqlite3.connect(DATABASE) cursor = conn.cursor()
    cursor.execute("SELECT downloads FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

# === Команды ===

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    add_user(user_id)
    lang = get_user_language(user_id)
    await message.answer("👋 Hi! Send me a video link to download.", reply_markup=get_language_keyboard())

@dp.message_handler(commands=['settings'])
async def cmd_settings(message: types.Message):
    await message.answer("🌐 Choose language:", reply_markup=get_language_keyboard())

@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    lang = get_user_language(message.from_user.id)
    await message.answer("/start - welcome\n/settings - language\n/help - info")

@dp.message_handler(commands=['stats'])
async def cmd_stats(message: types.Message):
    count = get_user_downloads(message.from_user.id)
    await message.answer(f"📊 You have downloaded {count} videos.")

@dp.message_handler(lambda m: m.text in [ "🇷🇺 Русский", "🇺🇸 English", "🇺🇦 Українська", "🇩🇪 Deutsch", "🇺🇿 O‘zbekcha", "🇰🇿 Қазақша", "🇰🇷 한국어", "🇹🇷 Türkçe" ])
async def lang_select(message: types.Message):
    mapping = { "🇷🇺 Русский": "ru", "🇺🇸 English": "en", "🇺🇦 Українська": "ua", "🇩🇪 Deutsch": "de", "🇺🇿 O‘zbekcha": "uz", "🇰🇿 Қазақша": "kz", "🇰🇷 한국어": "kr", "🇹🇷Türkçe": "tr" }
    lang_code = mapping.get(message.text, "en")
    set_user_language(message.from_user.id, lang_code)
    await message.answer("✅ Language updated!", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True))

# === Загрузка видео ===

@dp.message_handler(lambda m: m.text and m.text.startswith("http"))
async def download_video(message: types.Message):
    user_id = message.from_user.id
    if user_last_request[user_id] + SPAM_TIMEOUT > time.time():
        return await message.answer("⏳ Please wait before trying again.")
        user_last_request[user_id] = time.time()
        lang = get_user_language(user_id)
        await message.answer("⏬ Downloading, please wait...")
        try:
            ydl_opts = { 'outtmpl': 'video.%(ext)s', 'format': 'best', 'cookiefile': 'cookies.txt' }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([message.text])
            video_file = next((f for f in os.listdir('.') if f.startswith('video.')), None)
            if video_file:
                with open(video_file, 'rb') as video:
                    await message.answer_video(video)
                    os.remove(video_file)
                    increment_downloads(user_id)
            else:
                await message.answer("❌ Error: file not found")
        except Exception as e:
            await message.answer(f"❌ Error: {e}")

# === Webhook ===

@app.route('/')
def index():
    return 'MediaKing bot is running!', 200

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = Update.to_object(request.get_json())
        asyncio.run(dp.process_update(update))
        return 'ok'
    else:
        abort(403)

async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    print("✅ Webhook установлен")

async def on_shutdown():
    await bot.delete_webhook()
    print("🛑 Webhook удалён")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup())
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
