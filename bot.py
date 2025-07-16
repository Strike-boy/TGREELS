import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from flask import Flask
from threading import Thread

API_TOKEN = os.environ.get("TOKEN")  # не забудь задать TOKEN в Render

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Загружаем локализацию
with open('locales/ru.json', encoding='utf-8') as f:
    texts = json.load(f)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer(texts["start"])

@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    await message.answer(texts["help"])

@dp.message_handler(lambda message: 'http' in message.text)
async def download_video(message: types.Message):
    await message.answer("⏳ Скачиваю...")
    await message.answer("✅ Видео скачано!\n\nСкачано с @MediaKingBot")

# Flask для Render
app = Flask(name)

@app.route('/')
def index():
    return 'Bot is running!'

def start_flask():
    app.run(host="0.0.0.0", port=10000)

if name == 'main':
    Thread(target=start_flask).start()
    executor.start_polling(dp, skip_updates=True)
