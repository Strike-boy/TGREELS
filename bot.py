import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from aiogram.dispatcher.filters.state import State, StatesGroup

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_ban_id = State()
    waiting_for_broadcast = State()
from uuid import uuid4
import aiohttp

# 🔐 Настройки
TOKEN = "7661435901:AAFx8X7mY9wwW5FEeKofbLc9GddmX_tLlYk"
ADMIN_ID = 1001788720  # Твой Telegram ID
LANGUAGES = ['ru', 'en', 'uk', 'de', 'uz', 'kz', 'ko', 'tr']

# 🎛 Запуск
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# 🔧 Логирование
logging.basicConfig(level=logging.INFO)

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# 🌐 Клавиатура (многоязычная)
def get_main_keyboard(lang='en'):
    buttons = {
        'en': ["📥 Download video", "🎵 Recognize music", "🌐 Change language", "📤 Share bot", "🗂 My downloads"],
        'ru': ["📥 Скачать видео", "🎵 Распознать музыку", "🌐 Изменить язык", "📤 Поделиться ботом", "🗂 История загрузок"],
        'uz': ["📥 Video yuklash", "🎵 Musiqani aniqlash", "🌐 Tilni o‘zgartirish", "📤 Botni ulashish", "🗂 Yuklash tarixi"],
        'tr': ["📥 Video indir", "🎵 Müziği tanı", "🌐 Dili değiştir", "📤 Botu paylaş", "🗂 İndirme geçmişi"],
        'de': ["📥 Video herunterladen", "🎵 Musik erkennen", "🌐 Sprache ändern", "📤 Bot teilen", "🗂 Download-Verlauf"],
        'uk': ["📥 Завантажити відео", "🎵 Розпізнати музику", "🌐 Змінити мову", "📤 Поділитися ботом", "🗂 Історія завантажень"],
        'kz': ["📥 Видео жүктеу", "🎵 Әнді тану", "🌐 Тілді өзгерту", "📤 Ботты бөлісу", "🗂 Жүктеу тарихы"],
        'ko': ["📥 동영상 다운로드", "🎵 음악 인식", "🌐 언어 변경", "📤 봇 공유하기", "🗂 다운로드 기록"]
    }
    return ReplyKeyboardMarkup(resize_keyboard=True).add(*[KeyboardButton(b) for b in buttons.get(lang, buttons['en'])])

# 🌐 Словари приветствий
WELCOME_MESSAGES = {
    'en': "👋 Welcome to MediaKing Bot!\nSend me a video link to download or audio to recognize music.",
    'ru': "👋 Добро пожаловать в MediaKing!\nОтправь ссылку на видео для загрузки или аудио для распознавания музыки.",
    'uz': "👋 MediaKing botiga xush kelibsiz!\nVideo havolasini yuboring yoki musiqa taniqligi uchun audio yuboring.",
    'tr': "👋 MediaKing Bot'a hoş geldin!\nVideo bağlantısı gönder veya müzik tanımak için ses gönder.",
    'de': "👋 Willkommen bei MediaKing!\nSende einen Videolink oder ein Audio zur Musikerkennung.",
    'uk': "👋 Ласкаво просимо до MediaKing!\nНадішліть посилання на відео або аудіо для розпізнавання музики.",
    'kz': "👋 MediaKing боты қош келдіңіз!\nБейне сілтемесін немесе музыканы тану үшін аудио жіберіңіз.",
    'ko': "👋 MediaKing 봇에 오신 것을 환영합니다!\n동영상 링크를 보내거나 음악을 인식하기 위해 오디오를 보내세요."
}

# 💾 Память языка пользователя
user_languages = {}

# 🔁 /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_languages[user_id] = 'en'  # По умолчанию
    await message.answer("Please choose your language / Пожалуйста, выберите язык:", reply_markup=get_language_keyboard())

def get_language_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🇷🇺 Русский", "🇺🇸 English")
    kb.row("🇺🇿 Uzbek", "🇺🇦 Українська")
    kb.row("🇩🇪 Deutsch", "🇹🇷 Türkçe")
    kb.row("🇰🇿 Қазақша", "🇰🇷 한국어")
    return kb

@dp.message_handler(lambda message: message.text in ["🇷🇺 Русский", "🇺🇸 English", "🇺🇿 Uzbek", "🇺🇦 Українська", "🇩🇪 Deutsch", "🇹🇷 Türkçe", "🇰🇿 Қазақша", "🇰🇷 한국어"])
async def language_selected(message: types.Message):
    lang_map = {
        "🇷🇺 Русский": "ru",
        "🇺🇸 English": "en",
        "🇺🇿 Uzbek": "uz",
        "🇺🇦 Українська": "uk",
        "🇩🇪 Deutsch": "de",
        "🇹🇷 Türkçe": "tr",
        "🇰🇿 Қазақша": "kz",
        "🇰🇷 한국어": "ko"
    }
    lang = lang_map[message.text]
    user_languages[message.from_user.id] = lang
    await message.answer(WELCOME_MESSAGES[lang], reply_markup=get_main_keyboard(lang))
  # ➕ Inline-режим (бот реагирует на @MediaKingBot запросы)
@dp.inline_handler()
async def inline_handler(query: types.InlineQuery):
    results = []
    input_text = query.query.strip()
    if not input_text:
        results.append(
            InlineQueryResultArticle(
                id="1",
                title="❔ Enter a video or music query",
                input_message_content=InputTextMessageContent("Please enter something to search."),
                description="Paste a video link or type a song name"
            )
        )
    else:
        results.append(
            InlineQueryResultArticle(
                id="2",
                title="📥 Download or recognize",
                input_message_content=InputTextMessageContent(f"{input_text}"),
                description="Tap to send this to the bot"
            )
        )
    await query.answer(results, cache_time=1)

# 🆘 Команда /help
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    await message.answer(
        "📖 *Help Guide*\n\n"
        "1. 📥 Send a video link to download.\n"
        "2. 🎵 Send an audio or voice to recognize the song.\n"
        "3. 🌐 Change your language anytime.\n"
        "4. 📊 Use /stats to view usage.\n"
        "5. 🗂 Use /history to see your downloads.\n"
        "6. ❓ Still need help? Use /feedback to contact us.",
        parse_mode="Markdown"
    )

# ⚙️ Команда /settings
@dp.message_handler(commands=['settings'])
async def settings_command(message: types.Message):
    lang = user_languages.get(message.from_user.id, 'en')
    await message.answer(WELCOME_MESSAGES[lang], reply_markup=get_main_keyboard(lang))

# 💬 Команда /feedback
@dp.message_handler(commands=['feedback'])
async def feedback_command(message: types.Message):
    await message.answer("✉️ Please send your feedback or question. We will read it soon!")

# 📊 Статистика
@dp.message_handler(commands=['stats'])
async def stats_command(message: types.Message):
    total_users = len(user_languages)
    await message.answer(f"📊 Total users: {total_users}")

# 📂 История (заглушка пока)
user_history = {}

@dp.message_handler(commands=['history'])
async def history_command(message: types.Message):
    history = user_history.get(message.from_user.id, [])
    if not history:
        await message.answer("📂 You haven't downloaded anything yet.")
    else:
        text = "\n".join(history[-10:])
        await message.answer(f"📥 Your last downloads:\n{text}")
      # =============== АНТИСПАМ ===============
from datetime import datetime, timedelta

user_timestamps = {}

@dp.message_handler(lambda msg: msg.text and not msg.text.startswith('/'))
async def handle_video_link(message: types.Message):
    user_id = message.from_user.id
    now = datetime.utcnow()

    # Проверка на спам
    if user_id in user_timestamps:
        diff = now - user_timestamps[user_id]
        if diff.total_seconds() < 10:
            await message.answer("⚠️ Пожалуйста, подождите несколько секунд перед следующей ссылкой.")
            return

    user_timestamps[user_id] = now

    url = message.text.strip()

    # Заглушка на скачивание (реализация будет позже)
    await message.answer(f"🔗 Обрабатываю ссылку: {url}\n\n⏳ Подождите...")

    # Добавим в историю
    user_history.setdefault(user_id, []).append(url)

# =============== РАСПОЗНАВАНИЕ МУЗЫКИ ===============
import hmac
import hashlib
import base64
import json
import time
import aiohttp

ACR_HOST = "identify-ap-southeast-1.acrcloud.com"
ACR_KEY = "e48f0d7b2af6ccad4015b26d57d75903"
ACR_SECRET = "WTWOUirBwcIPMJY6vOHEXVKilaMviC8doHQKGgaV"

async def recognize_music(data):
    http_method = "POST"
    http_uri = "/v1/identify"
    data_type = "audio"
    signature_version = "1"
    timestamp = str(int(time.time()))

    string_to_sign = "\n".join([http_method, http_uri, ACR_KEY, data_type, signature_version, timestamp])
    sign = base64.b64encode(hmac.new(
        ACR_SECRET.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        digestmod=hashlib.sha1
    ).digest()).decode('utf-8')

    form = aiohttp.FormData()
    form.add_field('sample', data, filename='sample.wav', content_type='audio/wav')
    form.add_field('access_key', ACR_KEY)
    form.add_field('data_type', data_type)
    form.add_field('signature_version', signature_version)
    form.add_field('signature', sign)
    form.add_field('timestamp', timestamp)

    async with aiohttp.ClientSession() as session:
        async with session.post(f'https://{ACR_HOST}/v1/identify', data=form) as resp:
            result = await resp.text()
            return json.loads(result)

@dp.message_handler(content_types=types.ContentType.VOICE)
@dp.message_handler(content_types=types.ContentType.AUDIO)
async def handle_voice(message: types.Message):
    file = await message.bot.get_file(message.voice.file_id if message.voice else message.audio.file_id)
    file_path = file.file_path
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            data = await resp.read()

    result = await recognize_music(data)
    try:
        metadata = result['metadata']['music'][0]
        title = metadata.get("title", "Unknown")
        artist = metadata.get("artists", [{}])[0].get("name", "Unknown")
        album = metadata.get("album", {}).get("name", "Unknown")
        msg = f"🎵 *Title:* {title}\n🎤 *Artist:* {artist}\n💿 *Album:* {album}"
        await message.answer(msg, parse_mode="Markdown")
    except:
        await message.answer("😔 Не удалось распознать трек.")
      # =============== АДМИН ПАНЕЛЬ ===============
ADMIN_ID = 1001788720
banned_users = set()
error_logs = []
user_stats = {}

@dp.message_handler(commands="admin")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
        InlineKeyboardButton("🔍 Find user", callback_data="admin_find"),
        InlineKeyboardButton("🚫 Ban", callback_data="admin_ban"),
        InlineKeyboardButton("📢 Newsletter", callback_data="admin_broadcast"),
        InlineKeyboardButton("🔧 Update mode", callback_data="admin_update"),
        InlineKeyboardButton("📄 Error logs", callback_data="admin_logs")
    )
    await message.answer("⚙️ Админ-панель:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("admin_"))
async def handle_admin_callback(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    action = callback.data.replace("admin_", "")
    if action == "stats":
        total = len(user_stats)
        await callback.message.answer(f"📊 Пользователей: {total}")
    elif action == "find":
        await callback.message.answer("🔍 Введите ID пользователя:")
        await AdminStates.waiting_for_user_id.set()
    elif action == "ban":
        await callback.message.answer("🚫 Введите ID пользователя для блокировки:")
        await AdminStates.waiting_for_ban_id.set()
    elif action == "broadcast":
        await callback.message.answer("📢 Введите текст рассылки:")
        await AdminStates.waiting_for_broadcast.set()
    elif action == "update":
        await callback.message.answer("✅ Режим обновления включён.")
    elif action == "logs":
        if error_logs:
            text = "\n\n".join(error_logs[-5:])
        else:
            text = "ℹ️ Логи ошибок пусты."
        await callback.message.answer(text)

@dp.message_handler(state=AdminStates.waiting_for_user_id)
async def find_user(message: types.Message, state: FSMContext):
    user_id = int(message.text)
    history = user_history.get(user_id, [])
    if not history:
        await message.answer("❌ История пуста.")
    else:
        await message.answer("🕓 История:\n" + "\n".join(history[-5:]))
    await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_ban_id)
async def ban_user(message: types.Message, state: FSMContext):
    banned_users.add(int(message.text))
    await message.answer("✅ Пользователь забанен.")
    await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_broadcast)
async def broadcast_message(message: types.Message, state: FSMContext):
    text = message.text
    success = 0
    fail = 0
    for uid in user_stats:
        try:
            await bot.send_message(uid, f"📢 Сообщение от админа:\n\n{text}")
            success += 1
        except:
            fail += 1
    await message.answer(f"✅ Разослано: {success}, ❌ Ошибок: {fail}")
    await state.finish()
  # =============== INLINE MODE ===============
@dp.inline_handler()
async def inline_query_handler(query: InlineQuery):
    results = []
    if query.query:
        results.append(
            InlineQueryResultArticle(
                id='1',
                title='🔗 Вставить ссылку',
                input_message_content=InputTextMessageContent(f"/get {query.query}"),
                description="Нажмите, чтобы отправить ссылку боту"
            )
        )
    await query.answer(results, cache_time=1)

# =============== КОМАНДЫ ===============
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    await message.answer("ℹ️ Просто отправь ссылку на видео или аудио, и я помогу скачать его!")

@dp.message_handler(commands=['settings'])
async def settings_command(message: types.Message):
    langs = ", ".join(SUPPORTED_LANGUAGES.values())
    await message.answer(f"🌐 Поддерживаемые языки: {langs}\n\n(Автоопределение языка включено)")

@dp.message_handler(commands=['stats'])
async def stats_command(message: types.Message):
    total_users = len(user_stats)
    await message.answer(f"📊 Всего пользователей: {total_users}")

@dp.message_handler(commands=['feedback'])
async def feedback_command(message: types.Message):
    await message.answer("💬 Напиши свои пожелания или отзывы сюда: @YourFeedbackBot")

@dp.message_handler(commands=['history'])
async def history_command(message: types.Message):
    history = user_history.get(message.from_user.id, [])
    if not history:
        await message.answer("❌ История пуста.")
    else:
        await message.answer("🕓 Твоя история:\n" + "\n".join(history[-5:]))

# =============== ЗАПУСК БОТА ===============
if __name__ == "__main__":
    import threading
    from flask import Flask

    app = Flask(__name__)

    @app.route("/")
    def index():
        return "Бот работает!"

    def run_bot():
        import asyncio
        asyncio.run(delete_webhook())  # <-- удалить webhook перед polling
        executor.start_polling(dp, skip_updates=True)

    thread = threading.Thread(target=run_bot)
    thread.start()
    app.run(host="0.0.0.0", port=8080)
