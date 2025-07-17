import os
import json
import time
import hashlib
import sqlite3
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from aiogram.utils import executor
from threading import Thread
from flask import Flask
from yt_dlp import YoutubeDL
from acrcloud.recognizer import ACRCloudRecognizer
from datetime import datetime

TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# SQLite3
conn = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS downloads (
    user_id INTEGER,
    username TEXT,
    video_url TEXT,
    timestamp TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    download_count INTEGER DEFAULT 0
)
""")
conn.commit()

# ACRCloud конфигурация
acr_config = {
    'host': 'identify-ap-southeast-1.acrcloud.com',
    'access_key': 'e48f0d7b2af6ccad4015b26d57d75903',
    'access_secret': 'WTWOUirBwcIPMJY6vOHEXVKilaMviC8doHQKGgaV',
    'timeout': 10
}
acr_recognizer = ACRCloudRecognizer(acr_config)

# Flask
app = Flask(__name__)
@app.route("/")
def home():
    return "MediaKing работает!"

# Языки
LANGS = {
    'ru': "Русский",
    'en': "English",
    'uk': "Українська",
    'de': "Deutsch",
    'uz': "O'zbek",
    'kk': "Қазақ",
    'ko': "한국어",
    'tr': "Türkçe"
}

user_langs = {}

# Кнопки
def get_keyboard(lang='ru'):
    share_btn = InlineKeyboardButton("📤 Поделиться ботом", switch_inline_query="")
    return InlineKeyboardMarkup(row_width=1).add(share_btn)

# Переводы
def t(text, lang):
    tr = {
        'start': {
            'ru': "👋 Привет! Отправь мне ссылку на видео или аудио, или отправь музыку — я найду оригинал!",
            'en': "👋 Hi! Send me a video or audio link, or a music clip — I'll find the original!",
            'uk': "👋 Привіт! Надішли мені посилання на відео або аудіо, або музику — я знайду оригінал!",
            'de': "👋 Hallo! Sende mir einen Video-/Audiolink oder Musik – ich finde das Original!",
            'uz': "👋 Salom! Menga video yoki audio havolasini yuboring, yoki musiqa – men asl nusxasini topaman!",
            'kk': "👋 Сәлем! Маған бейне немесе аудио сілтеме жібер, не музыка – мен түпнұсқасын табамын!",
            'ko': "👋 안녕하세요! 영상이나 오디오 링크, 음악을 보내주세요 – 원곡을 찾아드릴게요!",
            'tr': "👋 Merhaba! Bana bir video/ses bağlantısı veya müzik gönder – orijinalini bulayım!"
        },
        'downloading': {
            'ru': "⏳ Скачиваю видео...",
            'en': "⏳ Downloading video...",
            'uk': "⏳ Завантажую відео...",
            'de': "⏳ Video wird heruntergeladen...",
            'uz': "⏳ Video yuklanmoqda...",
            'kk': "⏳ Видео жүктелуде...",
            'ko': "⏳ 비디오 다운로드 중...",
            'tr': "⏳ Video indiriliyor..."
        },
        'error': {
            'ru': "⚠️ Ошибка: ",
            'en': "⚠️ Error: ",
            'uk': "⚠️ Помилка: ",
            'de': "⚠️ Fehler: ",
            'uz': "⚠️ Xato: ",
            'kk': "⚠️ Қате: ",
            'ko': "⚠️ 오류: ",
            'tr': "⚠️ Hata: "
        },
        'recognized': {
            'ru': "🎵 Найдена песня: ",
            'en': "🎵 Recognized song: ",
            'uk': "🎵 Знайдено пісню: ",
            'de': "🎵 Erkannte Musik: ",
            'uz': "🎵 Topilgan qoʻshiq: ",
            'kk': "🎵 Табылған ән: ",
            'ko': "🎵 인식된 노래: ",
            'tr': "🎵 Tanınan şarkı: "
        }
    }
    return tr[text][lang]

# Команды
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_langs[message.from_user.id] = 'ru'
    await message.answer(t('start', 'ru'), reply_markup=get_keyboard('ru'))

@dp.message_handler(commands=['stats'])
async def stats(message: types.Message):
    cursor.execute("SELECT COUNT(*) FROM downloads")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT username, download_count FROM users ORDER BY download_count DESC LIMIT 3")
    top = cursor.fetchall()
    text = f"📊 Всего загрузок: {total}\n\n🥇 Топ 3 пользователя:\n"
    for i, row in enumerate(top):
        text += f"{i+1}. @{row[0]} — {row[1]} видео\n"
    await message.answer(text)

@dp.message_handler(commands=['settings'])
async def settings(message: types.Message):
    langs_buttons = [InlineKeyboardButton(LANGS[key], callback_data=f"lang:{key}") for key in LANGS]
    kb = InlineKeyboardMarkup(row_width=2).add(*langs_buttons)
    await message.answer("🌐 Выберите язык:", reply_markup=kb)

@dp.message_handler(commands=['help'])
async def help_cmd(message: types.Message):
    await message.answer("ℹ️ Просто отправь ссылку на видео или аудио, либо загрузи файл — и я помогу тебе! 🎬🎵")

@dp.message_handler(commands=['feedback'])
async def feedback(message: types.Message):
    await message.answer("📣 Напиши отзыв или предложение прямо здесь — мы читаем всё!")

@dp.callback_query_handler(lambda c: c.data.startswith("lang:"))
async def change_lang(callback: types.CallbackQuery):
    lang = callback.data.split(":")[1]
    user_langs[callback.from_user.id] = lang
    await callback.message.edit_text(t('start', lang), reply_markup=get_keyboard(lang))

@dp.message_handler(content_types=['text'])
async def handle_text(message: types.Message):
    lang = user_langs.get(message.from_user.id, 'ru')
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("⚠️ Введите ссылку на видео или отправьте аудиофайл.")
        return

    await message.answer(t('downloading', lang))
    try:
        ydl_opts = {
            'outtmpl': 'video.%(ext)s',
            'format': 'mp4/bestaudio',
            'noplaylist': True,
            'quiet': True,
            'cookiefile': 'cookies.txt'
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        file = next(f for f in os.listdir('.') if f.startswith("video"))
        await bot.send_video(message.chat.id, InputFile(file), caption="Скачано с @MediaKingBot")
        os.remove(file)

        cursor.execute("INSERT INTO downloads VALUES (?, ?, ?, ?)", (message.from_user.id, message.from_user.username, url, str(datetime.now())))
        cursor.execute("INSERT OR IGNORE INTO users(user_id, username) VALUES (?, ?) ", (message.from_user.id, message.from_user.username))
        cursor.execute("UPDATE users SET download_count = download_count + 1 WHERE user_id = ?", (message.from_user.id,))
        conn.commit()

    except Exception as e:
        await message.answer(t('error', lang) + str(e))

@dp.message_handler(content_types=['audio', 'voice'])
async def recognize_music(message: types.Message):
    lang = user_langs.get(message.from_user.id, 'ru')
    file = await message.audio.download(destination_file="music.mp3") if message.audio else await message.voice.download(destination_file="music.mp3")
    result = acr_recognizer.recognize_by_file("music.mp3", 0)
    os.remove("music.mp3")
    data = json.loads(result)
    if data['status']['msg'] == 'Success':
        song = data['metadata']['music'][0]
        reply = f"{t('recognized', lang)} {song['title']} - {song['artists'][0]['name']}"
    else:
        reply = "❌ Песня не найдена."
    await message.answer(reply)

# Запуск Flask и Telegram
def start_bot():
    import asyncio
    asyncio.set_event_loop(asyncio.new_event_loop())
    executor.start_polling(dp, skip_updates=True)

t = Thread(target=start_bot)
t.start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
