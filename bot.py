import os
import sqlite3
import asyncio
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from aiogram.utils.markdown import escape_md
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.deep_linking import get_start_link
from aiogram.utils.executor import start_polling
from aiogram.dispatcher.filters import Command
import yt_dlp
import acrcloud
# Вверху bot.py (глобально)
from collections import defaultdict
import time

user_last_request = defaultdict(lambda: 0)
SPAM_TIMEOUT = 10  # секунд

TOKEN = "7661435901:AAFx8X7mY9wwW5FEeKofbLc9GddmX_tLlYk"
ADMIN_ID = 1001788720

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
app = Flask(__name__)
# Инициализация SQLite
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        language TEXT DEFAULT 'en',
        banned INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS downloads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        url TEXT,
        type TEXT,
        quality TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Таблица отзывов
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        feedback TEXT
    )''')
    conn.commit()
    conn.close()
    # Поддерживаемые языки
LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "en": "🇺🇸 English",
    "uk": "🇺🇦 Українська",
    "de": "🇩🇪 Deutsch",
    "uz": "🇺🇿 Oʻzbekcha",
    "kz": "🇰🇿 Қазақша",
    "ko": "🇰🇷 한국어",
    "tr": "🇹🇷 Türkçe"
}

# Переводы
MESSAGES = {
    "en": {
        "start": "👋 Welcome to MediaKing!\nSend a video link or audio to begin.",
        "help": "📌 *How to use MediaKing:*\n\n1. Send a video link (YouTube, TikTok...)\n2. Choose quality or audio\n3. Bot will send you the file!\n\nSend voice/audio to recognize music.",
        "banned": "🚫 You are banned from using this bot.",
        "choose_lang": "🌐 Choose your language:",
        "lang_updated": "✅ Language updated.",
        "history_empty": "🗂 No download history found.",
        "your_history": "🗂 Your last downloads:",
        "send_link": "📥 Please send a valid video link.",
        "recognizing": "🎧 Recognizing music...",
        "not_recognized": "❌ Could not recognize the music.",
        "feedback": "✉️ Please send your feedback or suggestions.",
        "thanks_feedback": "✅ Thank you for your feedback!",
        "download_started": "⏳ Download started...",
        "invalid_link": "⚠️ Invalid or unsupported link.",
        "too_fast": "⏱ Please wait a bit before sending again.",
    },
    "ru": {
        "start": "👋 Добро пожаловать в MediaKing!\nОтправь ссылку на видео или аудио.",
        "help": "📌 *Как использовать MediaKing:*\n\n1. Отправь ссылку (YouTube, TikTok...)\n2. Выбери качество или только аудио\n3. Бот отправит тебе файл!\n\nОтправь голос или аудио — бот определит музыку.",
        "banned": "🚫 Вы заблокированы в этом боте.",
        "choose_lang": "🌐 Выберите язык:",
        "lang_updated": "✅ Язык обновлён.",
        "history_empty": "🗂 История загрузок пуста.",
        "your_history": "🗂 Последние загрузки:",
        "send_link": "📥 Пожалуйста, отправьте корректную ссылку на видео.",
        "recognizing": "🎧 Распознаём музыку...",
        "not_recognized": "❌ Не удалось распознать трек.",
        "feedback": "✉️ Отправьте отзыв или предложение.",
        "thanks_feedback": "✅ Спасибо за ваш отзыв!",
        "download_started": "⏳ Начинаем загрузку...",
        "invalid_link": "⚠️ Неверная или неподдерживаемая ссылка.",
        "too_fast": "⏱ Пожалуйста, подождите немного перед следующей попыткой.",
    },
    "uk": {
        "start": "👋 Ласкаво просимо до MediaKing!\nНадішли посилання на відео або аудіо.",
        "help": "📌 *Як користуватись MediaKing:*\n\n1. Надішли посилання (YouTube, TikTok...)\n2. Обери якість або лише аудіо\n3. Бот надішле тобі файл!\n\nНадішли голос або аудіо — бот розпізнає музику.",
        "banned": "🚫 Вас заблоковано в цьому боті.",
        "choose_lang": "🌐 Оберіть мову:",
        "lang_updated": "✅ Мову оновлено.",
        "history_empty": "🗂 Історія завантажень порожня.",
        "your_history": "🗂 Ваші останні завантаження:",
        "send_link": "📥 Будь ласка, надішліть правильне посилання на відео.",
        "recognizing": "🎧 Розпізнавання музики...",
        "not_recognized": "❌ Не вдалося розпізнати трек.",
        "feedback": "✉️ Надішліть відгук або пропозицію.",
        "thanks_feedback": "✅ Дякуємо за ваш відгук!",
        "download_started": "⏳ Завантаження розпочато...",
        "invalid_link": "⚠️ Неправильне або непідтримуване посилання.",
        "too_fast": "⏱ Будь ласка, зачекайте трохи перед наступною спробою.",
    },
    "de": {
        "start": "👋 Willkommen bei MediaKing!\nSende einen Video- oder Audio-Link.",
        "help": "📌 *So benutzt du MediaKing:*\n\n1. Sende einen Link (YouTube, TikTok...)\n2. Wähle Qualität oder nur Audio\n3. Der Bot sendet dir die Datei!\n\nSende eine Sprachnachricht, um Musik zu erkennen.",
        "banned": "🚫 Du bist in diesem Bot gesperrt.","choose_lang": "🌐 Sprache auswählen:",
        "lang_updated": "✅ Sprache aktualisiert.",
        "history_empty": "🗂 Kein Download-Verlauf gefunden.",
        "your_history": "🗂 Deine letzten Downloads:",
        "send_link": "📥 Bitte sende einen gültigen Video-Link.",
        "recognizing": "🎧 Musik wird erkannt...",
        "not_recognized": "❌ Musik konnte nicht erkannt werden.",
        "feedback": "✉️ Sende dein Feedback oder Vorschläge.",
        "thanks_feedback": "✅ Danke für dein Feedback!",
        "download_started": "⏳ Download wird gestartet...",
        "invalid_link": "⚠️ Ungültiger oder nicht unterstützter Link.",
        "too_fast": "⏱ Bitte warte ein wenig vor dem nächsten Versuch.",
    },
    "uz": {
        "start": "👋 MediaKing ga xush kelibsiz!\nVideo yoki audio havolasini yuboring.",
        "help": "📌 *MediaKing dan qanday foydalaniladi:*\n\n1. YouTube, TikTok... havolasini yuboring\n2. Sifat yoki audio tanlang\n3. Bot sizga faylni yuboradi!\n\nOvoz yuboring — bot musiqa aniqlaydi.",
        "banned": "🚫 Siz ushbu botdan bloklangansiz.",
        "choose_lang": "🌐 Tilni tanlang:",
        "lang_updated": "✅ Til yangilandi.",
        "history_empty": "🗂 Yuklab olish tarixi topilmadi.",
        "your_history": "🗂 Oxirgi yuklamalaringiz:",
        "send_link": "📥 Iltimos, to‘g‘ri video havolasini yuboring.",
        "recognizing": "🎧 Musiqa aniqlanmoqda...",
        "not_recognized": "❌ Musiqa aniqlanmadi.",
        "feedback": "✉️ Fikr yoki takliflaringizni yuboring.",
        "thanks_feedback": "✅ Fikringiz uchun rahmat!",
        "download_started": "⏳ Yuklab olish boshlandi...",
        "invalid_link": "⚠️ Noto‘g‘ri yoki qo‘llab-quvvatlanmaydigan havola.",
        "too_fast": "⏱ Keyingi yuborishdan oldin biroz kuting.",
    },
    "kz": {
        "start": "👋 MediaKing ботына қош келдіңіз!\nБейне немесе аудио сілтемесін жіберіңіз.",
        "help": "📌 *MediaKing қолдану нұсқаулығы:*\n\n1. Сілтеме жіберіңіз (YouTube, TikTok...)\n2. Сапа немесе тек аудио таңдаңыз\n3. Бот сізге файл жібереді!\n\nМузыка тану үшін дыбыс жіберіңіз.",
        "banned": "🚫 Сіз бұл ботта бұғатталғансыз.",
        "choose_lang": "🌐 Тілді таңдаңыз:",
        "lang_updated": "✅ Тіл жаңартылды.",
        "history_empty": "🗂 Жүктеу тарихы жоқ.",
        "your_history": "🗂 Соңғы жүктеулеріңіз:",
        "send_link": "📥 Дұрыс бейне сілтемесін жіберіңіз.",
        "recognizing": "🎧 Музыка танылуда...",
        "not_recognized": "❌ Музыка танылмады.",
        "feedback": "✉️ Пікір немесе ұсыныс жіберіңіз.",
        "thanks_feedback": "✅ Пікіріңіз үшін рахмет!",
        "download_started": "⏳ Жүктеу басталды...",
        "invalid_link": "⚠️ Қате немесе қолдау көрсетілмейтін сілтеме.",
        "too_fast": "⏱ Қайта жібермес бұрын біраз күтіңіз.",
    },
    "ko": {
        "start": "👋 MediaKing에 오신 것을 환영합니다!\n비디오 또는 오디오 링크를 보내주세요.",
        "help": "📌 *MediaKing 사용법:*\n\n1. 링크를 보내세요 (YouTube, TikTok...)\n2. 화질 또는 오디오 선택\n3. 봇이 파일을 전송합니다!\n\n음성을 보내면 음악을 인식합니다.",
        "banned": "🚫 이 봇에서 차단되었습니다.",
        "choose_lang": "🌐 언어를 선택하세요:",
        "lang_updated": "✅ 언어가 업데이트되었습니다.",
        "history_empty": "🗂 다운로드 기록이 없습니다.",
        "your_history": "🗂 최근 다운로드:",
        "send_link": "📥 올바른 링크를 보내주세요.",
        "recognizing": "🎧 음악 인식 중...",
        "not_recognized": "❌ 음악을 인식할 수 없습니다.",
        "feedback": "✉️ 피드백 또는 제안을 보내주세요.",
        "thanks_feedback": "✅ 피드백 감사합니다!",
        "download_started": "⏳ 다운로드 시작...",
        "invalid_link": "⚠️ 잘못되었거나 지원되지 않는 링크입니다.",
        "too_fast": "⏱ 다시 보내기 전에 잠시 기다려주세요.",
    },
    "tr": {
        "start": "👋 MediaKing'e hoş geldiniz!\nBir video veya ses bağlantısı gönderin.",
        "help": "📌 *MediaKing nasıl kullanılır:*\n\n1. Bağlantı gönderin (YouTube, TikTok...)\n2. Kalite veya sadece ses seçin\n3. Bot dosyayı size gönderir!\n\nMüziği tanımak için ses gönderin.","banned": "🚫 Bu botta engellendiniz.",
        "choose_lang": "🌐 Dil seçin:",
        "lang_updated": "✅ Dil güncellendi.",
        "history_empty": "🗂 İndirme geçmişi yok.",
        "your_history": "🗂 Son indirmeleriniz:",
        "send_link": "📥 Lütfen geçerli bir video bağlantısı gönderin.",
        "recognizing": "🎧 Müzik tanınıyor...",
        "not_recognized": "❌ Müzik tanınamadı.",
        "feedback": "✉️ Geri bildirim veya önerilerinizi gönderin.",
        "thanks_feedback": "✅ Geri bildiriminiz için teşekkürler!",
        "download_started": "⏳ İndirme başladı...",
        "invalid_link": "⚠️ Geçersiz veya desteklenmeyen bağlantı.",
        "too_fast": "⏱ Lütfen tekrar denemeden önce biraz bekleyin.",
    }
}

# Главная клавиатура
def main_keyboard(lang="en"):
    return ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton("📥 Download Video"),
        KeyboardButton("🎵 Recognize Music")
    ).add(
        KeyboardButton("🌐 Change Language"),
        KeyboardButton("🗂 Download History")
    ).add(
        KeyboardButton("📤 Share Bot")
    )
    === БЛОК 4: Команды /start /help /settings /feedback /history + админ-команды ===

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton 
from aiogram.dispatcher.filters import Command 
from aiogram import types

=== Локализация текста ===

translations = {
    'start': { 
        'en': "Welcome! Send me a video link to download.",
        'ru': "Добро пожаловать! Пришлите мне ссылку на видео для загрузки.",
        'uz': "Xush kelibsiz! Yuklab olish uchun menga video havolasini yuboring.",
        'tr': "Hoş geldiniz! Lütfen bana indirmek için bir video bağlantısı gönderin.",
        'de': "Willkommen! Senden Sie mir einen Videolink zum Herunterladen.",
        'uk': "Ласкаво просимо! Надішліть мені посилання на відео для завантаження.",
        'kk': "Қош келдіңіз! Маған жүктеу үшін бейне сілтемесін жіберіңіз.",
        'ko': "환영합니다! 다운로드할 비디오 링크를 보내주세요."
    },
    'help': {
        'en': "Just send a video link. I will give you download options.",
        'ru': "Просто пришлите ссылку на видео, и я предложу варианты загрузки.",
        'uz': "Faqat video havolasini yuboring. Yuklab olish variantlarini olasiz.",
        'tr': "Sadece bir video bağlantısı gönderin. Size indirme seçenekleri sunacağım.",
        'de': "Senden Sie einfach einen Videolink. Ich werde Download-Optionen anbieten.",
        'uk': "Просто надішліть посилання на відео — я запропоную варіанти завантаження.",
        'kk': "Тек бейне сілтемесін жіберіңіз. Мен жүктеу нұсқаларын ұсынамын.",
        'ko': "비디오 링크를 보내주세요. 다운로드 옵션을 제공합니다."
    },
    'settings': {
        'en': "Select your language:",
        'ru': "Выберите язык:",
        'uz': "Tilni tanlang:",
        'tr': "Dil seçin:",
        'de': "Sprache wählen:",
        'uk': "Оберіть мову:",
        'kk': "Тілді таңдаңыз:",
        'ko': "언어를 선택하세요:" },
    'feedback': {
        'en': "Please write your feedback. We'll review it soon!",
        'ru': "Пожалуйста, напишите ваш отзыв. Мы скоро его рассмотрим!",
        'uz': "Iltimos, fikr-mulohazalaringizni yozing. Tez orada ko'rib chiqamiz!",
        'tr': "Lütfen geri bildiriminizi yazın. Yakında inceleyeceğiz!",
        'de': "Bitte schreiben Sie Ihr Feedback. Wir werden es bald prüfen!",
        'uk': "Напишіть ваш відгук. Ми скоро його переглянемо!",
        'kk': "Пікіріңізді жазыңыз. Жақында қараймыз!",
        'ko': "피드백을 작성해주세요. 곧 검토하겠습니다!" },
    'history': {
        'en': "Your download history:",
        'ru': "Ваша история загрузок:",
        'uz': "Yuklab olish tarixi:",
        'tr': "İndirme geçmişiniz:",
        'de': "Ihr Download-Verlauf:",
        'uk': "Ваша історія завантажень:",
        'kk': "Жүктеу тарихыңыз:",
        'ko': "다운로드 기록:" 
    }
}

=== Команды пользователя ===

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    lang = get_user_language(message.from_user.id)
    text = translations['start'].get(lang, translations['start']['en'])
    keyboard = get_main_keyboard(lang)
    await message.answer(text, reply_markup=keyboard)

@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    lang = get_user_language(message.from_user.id)
    text = translations['help'].get(lang, translations['help']['en'])
    await message.answer(text)

@dp.message_handler(commands=['settings'])
async def cmd_settings(message: types.Message):
    lang = get_user_language(message.from_user.id)
    text = translations['settings'].get(lang, translations['settings']['en'])
    keyboard = get_language_keyboard()
    await message.answer(text, reply_markup=keyboard)

@dp.message_handler(commands=['feedback'])
async def cmd_feedback(message: types.Message):
    lang = get_user_language(message.from_user.id)
    text = translations['feedback'].get(lang, translations['feedback']['en'])
    await message.answer(text)
    await FeedbackStates.waiting_for_text.set()

@dp.message_handler(commands=['history'])
async def cmd_history(message: types.Message):
    # ========== БЛОК 6.2.2: Команда /history для пользователя ==========

@dp.message_handler(commands=['history'])
async def user_history(message: types.Message):
    lang = get_user_language(message.from_user.id)
    args = message.get_args()
    
@dp.message_handler(commands=["history"])
async def show_history(message: types.Message):
    lang = get_user_language(message.from_user.id)
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT video_title, video_url, download_time FROM downloads WHERE user_id=? ORDER BY download_time DESC LIMIT 10", (message.from_user.id,))
    results = c.fetchall()
    conn.close()

    if not results:
        await message.reply(LANGUAGES[lang]["no_history"])
        return

    history_text = LANGUAGES[lang]["your_history"] + "\n\n"
    for title, url, timestamp in results:
        history_text += f"• <b>{title}</b>\n{url}\n🕒 {timestamp}\n\n"

    await message.reply(history_text, parse_mode="HTML")
    # Если админ вводит ID
    if message.from_user.id == 1001788720 and args.isdigit():
        target_id = int(args)
    else:
        target_id = message.from_user.id

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT video_title, video_url, download_time FROM downloads WHERE user_id=? ORDER BY download_time DESC LIMIT 10", (target_id,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        await message.reply(LANGUAGES[lang]['no_history'])
        return

    text = f"🕘 <b>{'Ваша история загрузок' if target_id == message.from_user.id else f'История пользователя {target_id}'}</b>\n\n"
    for title, url, time in rows:
        text += f"🎬 <b>{title}</b>\n🔗 <code>{url}</code>\n🕒 {time}\n\n"

    await message.reply(text, parse_mode='HTML')
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    text = translations['history'].get(lang, translations['history']['en'])
    history = get_user_history(user_id)
    if not history:
        await message.answer(text + "\n(Empty)")
    else: msg = f"{text}\n\n" + "\n".join([f"{i+1}. {item['type']} - {item['url']}" for i, item in enumerate(history)])
        await message.answer(msg)

=== Админ-команды ===

@dp.message_handler(commands=['stats'])
async def cmd_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(get_stats_text())

@dp.message_handler(commands=['ban'])
async def cmd_ban(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Использование: /ban <user_id>")
        return
    user_id = int(parts[1])
    ban_user(user_id)
    await message.answer(f"Пользователь {user_id} забанен")

@dp.message_handler(commands=['unban'])
async def cmd_unban(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Использование: /unban <user_id>")
        return
    user_id = int(parts[1])
    unban_user(user_id)
    await message.answer(f"Пользователь {user_id} разбанен")

@dp.message_handler(commands=['find'])
async def cmd_find(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Использование: /find <user_id>")
        return
    user_id = int(parts[1])
    profile = get_user_profile(user_id)
    await message.answer(profile)

@dp.message_handler(commands=['history'])
async def cmd_admin_history(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2:
        return
    user_id = int(parts[1])
    history = get_user_history(user_id)
    if not history:
        await message.answer("История пуста")
    else:
        msg = "История загрузок:\n" + "\n".join([f"{i+1}. {item['type']} - {item['url']}" for i, item in enumerate(history)])
        await message.answer(msg)

@dp.message_handler(commands=['users'])
async def cmd_users(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"Всего пользователей: {count_users()}")

@dp.message_handler(commands=['downloads'])
async def cmd_downloads(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"Всего загрузок: {count_downloads()}")

=== Кнопочная админ-панель ===

admin_panel = ReplyKeyboardMarkup(resize_keyboard=True)
admin_panel.row("📊 Статистика", "🔍 Найти")
admin_panel.row("🚫 Бан", "✅ Разбан")
admin_panel.row("🗂 История", "📢 Рассылка")

@dp.message_handler(lambda msg: msg.from_user.id == ADMIN_ID and msg.text == "📊 Статистика")
async def btn_stats(message: types.Message):
    await message.answer(get_stats_text())

@dp.message_handler(lambda msg: msg.from_user.id == ADMIN_ID and msg.text == "🔍 Найти")
async def btn_find(message: types.Message):
    await message.answer("Введите /find <user_id>")

@dp.message_handler(lambda msg: msg.from_user.id == ADMIN_ID and msg.text == "🚫 Бан")
async def btn_ban(message: types.Message):
    await message.answer("Введите /ban <user_id>")

@dp.message_handler(lambda msg: msg.from_user.id == ADMIN_ID and msg.text == "✅ Разбан")
async def btn_unban(message: types.Message):
    await message.answer("Введите /unban <user_id>")

@dp.message_handler(lambda msg: msg.from_user.id == ADMIN_ID and msg.text == "🗂 История")
async def btn_history(message: types.Message):
    await message.answer("Введите /history <user_id>")

@dp.message_handler(lambda msg: msg.from_user.id == ADMIN_ID and msg.text == "📢 Рассылка")
async def btn_broadcast(message: types.Message):
    await message.answer("Введите /broadcast и текст рассылки")
    
# ========== БЛОК 5: Feedback обработка и просмотр (для админа) ==========

def save_feedback(user_id, feedback_text):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO feedback (user_id, feedback) VALUES (?, ?)", (user_id, feedback_text))
    conn.commit()
    conn.close()

def get_latest_feedbacks(limit=10):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT user_id, feedback FROM feedback ORDER BY id DESC LIMIT ?", (limit,))
    feedbacks = c.fetchall()
    conn.close()
    return feedbacks

@dp.message_handler(commands=['feedback'])
async def send_feedback(message: types.Message):
    lang = get_user_language(message.from_user.id)
    await message.reply(LANGUAGES[lang]['send_feedback'])

    @dp.message_handler(lambda m: m.reply_to_message and m.reply_to_message.text == LANGUAGES[lang]['send_feedback'])
    async def receive_feedback(msg: types.Message):
        save_feedback(msg.from_user.id, msg.text)
        await msg.reply(LANGUAGES[lang]['thank_feedback'])

        # Отправка админу
        admin_id = 1001788720
        if msg.from_user.id != admin_id:
            text = f"💬 <b>Новый отзыв</b>\n\n<b>ID:</b> {msg.from_user.id}\n<b>Отзыв:</b>\n{msg.text}"
            await bot.send_message(admin_id, text, parse_mode='HTML')

# Обработка кнопки "📬 Отзывы" в админ-панели
@dp.message_handler(lambda msg: msg.text == "📬 Отзывы" and msg.from_user.id == 1001788720)
async def show_feedbacks(message: types.Message):
    feedbacks = get_latest_feedbacks()
    if not feedbacks:
        await message.reply("Пока нет отзывов.")
        return

    msg = "📬 <b>Последние отзывы:</b>\n\n"
    for uid, fb in feedbacks:
        msg += f"<b>ID:</b> <code>{uid}</code>\n<b>Сообщение:</b> {fb}\n\n"

    await message.reply(msg, parse_mode="HTML")
@dp.inline_handler()
async def inline_query_handler(inline_query: types.InlineQuery):
    query = inline_query.query.strip()
    user_id = inline_query.from_user.id

    if not (query.startswith("http://") or query.startswith("https://")):
        return  # Пропускаем пустые или не-ссылки

    try:
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(query, download=False)
            title = info.get("title", "Видео")
            thumbnail = info.get("thumbnail")
            url = query

        result = types.InlineQueryResultArticle(
            id=hash(url),
            title="🎬 Скачать видео",
            description=title,
            thumb_url=thumbnail,
            input_message_content=types.InputTextMessageContent(
                message_text=url
            )
        )
        await inline_query.answer([result], cache_time=1)

    except Exception as e:
        print(f"[INLINE ERROR]: {e}")
        return
# === Flask сервер для Render / других хостингов ===
from flask import Flask, request, abort

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://{os.environ.get('RENDER_EXTERNAL_URL', 'your-domain.com')}{WEBHOOK_PATH}"

app = Flask(name)

@app.route('/')
def index():
    return 'MediaKing bot is running!', 200

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = types.Update.de_json(json_string)
        asyncio.run(dp.process_update(update))
        return "ok"
    else:
        abort(403)

async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    print("✅ Webhook установлен")

async def on_shutdown():
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    print("🛑 Webhook удалён")

if name == "main":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
