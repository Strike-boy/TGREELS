import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from uuid import uuid4
import yt_dlp
import requests

API_TOKEN = "7661435901:AAFx8X7mY9wwW5FEeKofbLc9GddmX_tLlYk"
ADMIN_ID = 1001788720

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

logging.basicConfig(level=logging.INFO)

# ========= МУЛЬТИЯЗЫЧНОСТЬ =============
LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "en": "🇺🇸 English",
    "uz": "🇺🇿 Uzbek",
    "uk": "🇺🇦 Українська",
    "de": "🇩🇪 Deutsch",
    "kz": "🇰🇿 Қазақша",
    "ko": "🇰🇷 한국어",
    "tr": "🇹🇷 Türkçe"
}

user_languages = {}

# ========== КНОПКИ =============
def main_keyboard(lang="en"):
    return types.ReplyKeyboardMarkup(resize_keyboard=True).add(
        types.KeyboardButton("📥 Download video"),
        types.KeyboardButton("🎵 Recognize music"),
        types.KeyboardButton("🌐 Language"),
        types.KeyboardButton("📤 Share bot"),
        types.KeyboardButton("🗂 History")
    )

# ========== КОМАНДЫ ==============
@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    user_languages[message.from_user.id] = "en"
    await message.answer("👋 Welcome to MediaKing Bot!
Send a video link or audio.", reply_markup=main_keyboard())

@dp.message_handler(commands=["help"])
async def help_cmd(message: types.Message):
    await message.answer("Just send a video link or audio file to begin.")

@dp.message_handler(commands=["settings"])
async def settings_cmd(message: types.Message):
    langs = [types.KeyboardButton(f"{v}") for v in LANGUAGES.values()]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(*langs)
    await message.answer("🌐 Choose language:", reply_markup=markup)

@dp.message_handler(commands=["feedback"])
async def feedback_cmd(message: types.Message):
    await message.answer("✉️ Send your suggestions here: @YourUsername")

@dp.message_handler(commands=["stats"])
async def stats_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("👤 Total users: 123
📥 Total downloads: 456")
    else:
        await message.answer("🚫 You are not admin.")

@dp.message_handler(commands=["history"])
async def history_cmd(message: types.Message):
    await message.answer("🕘 Here's your download history (mocked).")

# ========== РАСПОЗНАВАНИЕ МУЗЫКИ ==========
@dp.message_handler(content_types=types.ContentType.VOICE)
@dp.message_handler(content_types=types.ContentType.AUDIO)
async def recognize_music(message: types.Message):
    file = await bot.get_file(message.voice.file_id if message.voice else message.audio.file_id)
    file_path = file.file_path
    file_url = f"https://api.telegram.org/file/bot{API_TOKEN}/{file_path}"
    data = requests.get(file_url).content

    acr_host = "identify-ap-southeast-1.acrcloud.com"
    acr_access_key = "e48f0d7b2af6ccad4015b26d57d75903"
    acr_secret_key = "WTWOUirBwcIPMJY6vOHEXVKilaMviC8doHQKGgaV"

    import hmac
    import hashlib
    import base64
    import time

    http_method = "POST"
    http_uri = "/v1/identify"
    data_type = "audio"
    signature_version = "1"
    timestamp = str(int(time.time()))
    string_to_sign = f"{http_method}\n{http_uri}\n{acr_access_key}\n{data_type}\n{signature_version}\n{timestamp}"
    sign = base64.b64encode(hmac.new(acr_secret_key.encode(), string_to_sign.encode(), digestmod=hashlib.sha1).digest()).decode()

    files = {"sample": data}
    payload = {
        "access_key": acr_access_key,
        "data_type": data_type,
        "signature_version": signature_version,
        "signature": sign,
        "timestamp": timestamp
    }

    r = requests.post(f"http://{acr_host}/v1/identify", files=files, data=payload)
    result = r.json()

    if result.get("status", {}).get("msg") == "Success":
        metadata = result["metadata"]["music"][0]
        title = metadata.get("title", "Unknown")
        artist = metadata.get("artists", [{}])[0].get("name", "Unknown")
        await message.reply(f"🎵 {title} by {artist}")
    else:
        await message.reply("❌ Failed to recognize music.")

# ========== ВИДЕО ЗАГРУЗКА ==========
@dp.message_handler(lambda message: message.text and "http" in message.text)
async def download_video(message: types.Message):
    url = message.text.strip()
    await message.reply("🔍 Processing...")
    try:
        ydl_opts = {
            "format": "best",
            "outtmpl": "downloads/%(title)s.%(ext)s"
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get("url")
            title = info.get("title")
            await message.answer(f"🎬 {title}
🔗 {video_url}")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# ========== INLINE MODE ==========
@dp.inline_handler()
async def inline_query_handler(inline_query: types.InlineQuery):
    query = inline_query.query
    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Example video result",
            input_message_content=InputTextMessageContent("🔗 https://youtube.com/example"),
            description="Click to download"
        )
    ]
    await bot.answer_inline_query(inline_query.id, results=results, cache_time=1)

# ========== ОСНОВНОЙ ЦИКЛ ==========
if __name__ == "__main__":
    print("🚀 MediaKing Bot is running...")
    executor.start_polling(dp, skip_updates=True)
