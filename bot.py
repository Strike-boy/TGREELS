from aiogram import Bot, Dispatcher, types
from threading import Thread
from flask import Flask
import os
import yt_dlp

TOKEN = os.environ.get("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

app = Flask(__name__)

@app.route("/")
def home():
    return "Бот работает!"

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("👋 Привет!\nОтправь мне ссылку на Instagram Reels или TikTok, и я скачаю видео для тебя!")

@dp.message_handler()
async def download_video(message: types.Message):
    url = message.text
    await message.answer("⏳ Скачиваю видео, подожди немного...")
    try:
        ydl_opts = {
    'outtmpl': 'video_%(id)s.%(ext)s',
    'cookiefile': 'cookies.txt'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        with open('video.mp4', 'rb') as video:
            await message.answer_video(video)
        os.remove('video.mp4')
    except Exception as e:
        await message.answer(f"⚠ Упс! Ошибка: {e}")

def start_bot():
    import asyncio
    asyncio.set_event_loop(asyncio.new_event_loop())
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)

if __name__ == "__main__":
    t = Thread(target=start_bot)
    t.start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
