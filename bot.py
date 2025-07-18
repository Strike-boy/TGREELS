import asyncio
import logging
import sqlite3
import os
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiohttp import ClientSession
from subprocess import run
import hashlib
import hmac
import base64

# === НАСТРОЙКИ ===
API_TOKEN = "7661435901:AAFx8X7mY9wwW5FEeKofbLc9GddmX_tLlYk"
ADMIN_ID = 1001788720
ACR_HOST = "identify-ap-southeast-1.acrcloud.com"
ACR_ACCESS_KEY = "e48f0d7b2af6ccad4015b26d57d75903"
ACR_SECRET_KEY = "WTWOUirBwcIPMJY6vOHEXVKilaMviC8doHQKGgaV"

# === ИНИЦИАЛИЗАЦИЯ ===
dp = Dispatcher(storage=MemoryStorage())
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)

# === СОЗДАНИЕ БД ===
conn = sqlite3.connect("users.db")
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, lang TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS history (user_id INTEGER, url TEXT, timestamp TEXT)")
conn.commit()

# === ЯЗЫКИ ===
LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "en": "🇺🇸 English",
    "uz": "🇺🇿 O‘zbek",
    "uk": "🇺🇦 Українська",
    "de": "🇩🇪 Deutsch",
    "kz": "🇰🇿 Қазақша",
    "ko": "🇰🇷 한국어",
    "tr": "🇹🇷 Türkçe"
}

# === ГЛАВНАЯ КЛАВИАТУРА ===
def main_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📥 Скачать видео")
    kb.button(text="🎵 Распознать музыку")
    kb.button(text="🌐 Изменить язык")
    kb.button(text="📂 История загрузок")
    kb.button(text="📤 Поделиться ботом")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

# === ОБРАБОТКА /start ===
@dp.message(Command("start"))
async def start_handler(msg: Message):
    user_id = msg.from_user.id
    username = msg.from_user.username or "unknown"
    cur.execute("INSERT OR IGNORE INTO users (id, username, lang) VALUES (?, ?, ?)", (user_id, username, 'ru'))
    conn.commit()
    await msg.answer(f"👋 Привет, {msg.from_user.first_name}!

Я бот для скачивания видео, распознавания музыки и многого другого.

Нажми кнопку ниже чтобы начать 👇", reply_markup=main_keyboard())

# === ОБРАБОТКА /help ===
@dp.message(Command("help"))
async def help_handler(msg: Message):
    await msg.answer("❓ <b>Как использовать бота:</b>

📥 Отправь ссылку на видео — я помогу скачать
🎵 Отправь голосовое/аудио — распознаю музыку
📂 История — покажу, что ты скачивал
🌐 Измени язык — если нужно")

# === ЗАГРУЗКА ВИДЕО ===
@dp.message(F.text.regexp(r'^https?://'))
async def download_video(msg: Message):
    url = msg.text.strip()
    user_id = msg.from_user.id
    filename = f"video_{user_id}_{int(time.time())}.mp4"
    try:
        await msg.answer("⏬ Загружаю видео, подожди немного...")
        run(["yt-dlp", "-o", filename, url], check=True)
        await bot.send_video(msg.chat.id, video=open(filename, "rb"), caption="🎬 Готово!")
        cur.execute("INSERT INTO history (user_id, url, timestamp) VALUES (?, ?, ?)", (user_id, url, time.ctime()))
        conn.commit()
    except Exception as e:
        await msg.answer("❌ Ошибка при загрузке видео.")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# === РАСПОЗНАВАНИЕ МУЗЫКИ ===
@dp.message(F.voice | F.audio)
async def recognize_music(msg: Message):
    file = await bot.get_file(msg.voice.file_id if msg.voice else msg.audio.file_id)
    file_path = file.file_path
    src = await bot.download_file(file_path)
    sample = src.read()

    # ACRCloud request
    http_method = "POST"
    http_uri = "/v1/identify"
    data_type = "audio"
    signature_version = "1"
    timestamp = str(int(time.time()))
    string_to_sign = f"{http_method}\n{http_uri}\n{ACR_ACCESS_KEY}\n{data_type}\n{signature_version}\n{timestamp}"
    sign = base64.b64encode(hmac.new(ACR_SECRET_KEY.encode(), string_to_sign.encode(), digestmod=hashlib.sha1).digest()).decode()

    files = {
        'sample': sample,
        'access_key': ACR_ACCESS_KEY,
        'data_type': data_type,
        'signature_version': signature_version,
        'signature': sign,
        'timestamp': timestamp,
    }

    async with ClientSession() as session:
        async with session.post(f"http://{ACR_HOST}/v1/identify", data=files) as resp:
            result = await resp.json()
            try:
                title = result['metadata']['music'][0]['title']
                artist = result['metadata']['music'][0]['artists'][0]['name']
                await msg.answer(f"🎵 Трек: <b>{title}</b>\n👤 Исполнитель: <b>{artist}</b>")
            except:
                await msg.answer("❌ Не удалось распознать музыку.")

# === ИСТОРИЯ ЗАГРУЗОК ===
@dp.message(F.text == "📂 История загрузок")
async def user_history(msg: Message):
    cur.execute("SELECT url, timestamp FROM history WHERE user_id=? ORDER BY timestamp DESC LIMIT 5", (msg.from_user.id,))
    rows = cur.fetchall()
    if not rows:
        await msg.answer("⛔ История пуста.")
    else:
        text = "🗂 <b>Последние загрузки:</b>\n" + "\n".join([f"{row[1]} — {row[0]}" for row in rows])
        await msg.answer(text)

# === ЗАПУСК ===
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
