from aiogram import Bot, Dispatcher, types
from threading import Thread
from flask import Flask
import os
import yt_dlp
import sqlite3
import asyncio

TOKEN = os.environ.get("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
app = Flask(name)

# Инициализация базы
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            language TEXT DEFAULT 'ru',
            downloads INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Словари переводов
texts = {
    'start': {
        'ru': "👋 Привет! Отправь мне ссылку на видео, и я скачаю его для тебя!",
        'en': "👋 Hi! Send me a video link, and I'll download it for you!",
        'ua': "👋 Привіт! Надішли мені посилання на відео, і я його скачаю для тебе!",
        'de': "👋 Hallo! Schick mir einen Videolink, und ich lade es für dich herunter!"
    },
    'help': {
        'ru': "/start - начать\n/languages - сменить язык\n/stats - статистика\n/about - о боте",
        'en': "/start - start\n/languages - change language\n/stats - statistics\n/about - about bot",
        'ua': "/start - почати\n/languages - змінити мову\n/stats - статистика\n/about - про бота",
        'de': "/start - starten\n/languages - Sprache ändern\n/stats - Statistik\n/about - über Bot"
    },
    'about': {
        'ru': "🤖 Я бот MediaKing! Скачиваю Reels, TikTok, Shorts и многое другое.",
        'en': "🤖 I'm MediaKing bot! I download Reels, TikTok, Shorts and more.",
        'ua': "🤖 Я бот MediaKing! Завантажую Reels, TikTok, Shorts та інше.",
        'de': "🤖 Ich bin der MediaKing Bot! Ich lade Reels, TikTok, Shorts und mehr herunter."
    },
    'choose_lang': {
        'ru': "Выбери язык:",
        'en': "Choose your language:",
        'ua': "Оберіть мову:",
        'de': "Wähle deine Sprache:"
    },
    'stats': {
        'ru': "📊 Ты скачал видео: ",
        'en': "📊 You've downloaded videos: ",
        'ua': "📊 Ви завантажили відео: ",
        'de': "📊 Du hast Videos heruntergeladen: "
    },
    'downloading': {
        'ru': "⏳ Скачиваю видео, подожди немного...",
        'en': "⏳ Downloading video, please wait...",
        'ua': "⏳ Завантажую відео, зачекай...",
        'de': "⏳ Lade Video herunter, bitte warten..."
    },
    'error': {
        'ru': "⚠️ Упс! Ошибка: ",
        'en': "⚠️ Oops! Error: ",
        'ua': "⚠️ Ой! Помилка: ",
        'de': "⚠️ Ups! Fehler: "
    }
}

def get_user_language(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 'ru'

def set_user_language(user_id, lang):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    conn.close()

def add_or_update_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def increment_downloads(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET downloads = downloads + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_downloads(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT downloads FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

@app.route("/")
def home():
    return "Бот работает!"

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    add_or_update_user(message.from_user.id)
    lang = get_user_language(message.from_user.id)
    await message.answer(texts['start'][lang])

@dp.message_handler(commands=['help'])
async def help_cmd(message: types.Message):
    lang = get_user_language(message.from_user.id)
    await message.answer(texts['help'][lang])

@dp.message_handler(commands=['about'])
async def about_cmd(message: types.Message):
    lang = get_user_language(message.from_user.id)
    await message.answer(texts['about'][lang])

@dp.message_handler(commands=['languages'])
async def languages_cmd(message: types.Message):
    lang = get_user_language(message.from_user.id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("🇷🇺 Русский", "🇺🇸 English", "🇺🇦 Українська", "🇩🇪 Deutsch")
    await message.answer(texts['choose_lang'][lang], reply_markup=keyboard)

@dp.message_handler(commands=['stats'])
async def stats_cmd(message: types.Message):
    lang = get_user_language(message.from_user.id)
    count = get_downloads(message.from_user.id)
    await message.answer(f"{texts['stats'][lang]} {count}")

@dp.message_handler(lambda m: m.text in ["🇷🇺 Русский", "🇺🇸 English", "🇺🇦 Українська", "🇩🇪 Deutsch"])
async def change_lang(message: types.Message):
    lang_code = {'🇷🇺 Русский': 'ru', '🇺🇸 English': 'en', '🇺🇦 Українська': 'ua', '🇩🇪 Deutsch': 'de'}[message.text]
    set_user_language(message.from_user.id, lang_code)
    await message.answer("✅ Язык обновлен!", reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler()
async def download_video(message: types.Message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    await message.answer(texts['downloading'][lang])
    try:
        ydl_opts = {'outtmpl': 'video.%(ext)s', 'cookiefile': 'cookies.txt'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([message.text])
        with open('video.mp4', 'rb') as video:
            await message.answer_video(video)
        os.remove('video.mp4')
        increment_downloads(user_id)
    except Exception as e:
        await message.answer(f"{texts['error'][lang]} {e}")

def start_bot():
    asyncio.set_event_loop(asyncio.new_event_loop())
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)

if name == "main":
    t = Thread(target=start_bot)
    t.start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
