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
app = Flask(__name__)

# Инициализация базы
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        language TEXT DEFAULT 'ru',
        downloads INTEGER DEFAULT 0,
        banned INTEGER DEFAULT 0
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

def get_total_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_total_downloads():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(downloads) FROM users")
    total = cursor.fetchone()[0] or 0
    conn.close()
    return total

def ban_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET banned = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET banned = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def is_banned(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT banned FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row and row[0] == 1

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

ADMIN_ID = 1001788720  # Замени на свой ID

admin_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
admin_keyboard.row("📊 Статистика", "🔍 Найти", "🚫 Бан")
admin_keyboard.row("✅ Разбан", "🗂 История", "📢 Рассылка")

@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🔧 Админ-панель", reply_markup=admin_keyboard)

@dp.message_handler(lambda m: m.from_user.id == ADMIN_ID and m.text == "📊 Статистика")
async def admin_stats(message: types.Message):
    users = get_total_users()
    downloads = get_total_downloads()
    await message.answer(f"👥 Пользователей: {users}\n📥 Скачиваний: {downloads}")

@dp.message_handler(lambda m: m.from_user.id == ADMIN_ID and m.text == "🔍 Найти")
async def ask_user_id_find(message: types.Message):
    await message.answer("Введите ID пользователя:\nПример: /find 123456789", parse_mode="Markdown")

@dp.message_handler(commands=['find'])
async def find_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("❌ Формат: /find <user_id>")
        return
    uid = int(parts[1])
    lang = get_user_language(uid)
    count = get_downloads(uid)
    banned = is_banned(uid)
    await message.answer(f"🆔 ID: {uid}\n🌐 Язык: {lang}\n📥 Скачиваний: {count}\n🚫 Бан: {'Да' if banned else 'Нет'}")

@dp.message_handler(commands=['ban'])
async def ban_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("❌ Формат: /ban <user_id>")
        return
    ban_user(int(parts[1]))
    await message.answer("👤 Пользователь заблокирован.")

@dp.message_handler(commands=['unban'])
async def unban_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("❌ Формат: /unban <user_id>")
        return
    unban_user(int(parts[1]))
    await message.answer("✅ Пользователь разбанен.")

@dp.message_handler(commands=['history'])
async def history_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("❌ Формат: /history <user_id>")
        return
    uid = int(parts[1])
    count = get_downloads(uid)
    await message.answer(f"📥 Скачиваний у {uid}: {count}")

@dp.message_handler(commands=['users'])
async def users_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(f"👥 Всего пользователей: {get_total_users()}")

@dp.message_handler(commands=['downloads'])
async def downloads_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(f"📥 Всего скачиваний: {get_total_downloads()}")

@dp.message_handler(commands=['broadcast'])
async def broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Введите текст рассылки:")

    @dp.message_handler()
    async def collect_broadcast(msg: types.Message):
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        conn.close()

        sent = 0
        for user in users:
            try:
                await bot.send_message(user[0], msg.text)
                sent += 1
            except:
                continue
        await msg.answer(f"📢 Разослано {sent} сообщений.")

@dp.message_handler(lambda m: m.text in ["🇷🇺 Русский", "🇺🇸 English", "🇺🇦 Українська", "🇩🇪 Deutsch"])
async def change_lang(message: types.Message):
    lang_code = {'🇷🇺 Русский': 'ru', '🇺🇸 English': 'en', '🇺🇦 Українська': 'ua', '🇩🇪 Deutsch': 'de'}[message.text]
    set_user_language(message.from_user.id, lang_code)
    await message.answer("✅ Язык обновлен!", reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler()
async def download_video(message: types.Message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    text = message.text.strip()

    # ❗️ Игнорируем нажатия на админ-кнопки
    if text in ["📊 Статистика", "🔍 Найти", "🚫 Бан", "✅ Разбан", "🗂 История", "📢 Рассылка"]:
        return

    if is_banned(user_id):
        await message.answer("🚫 Вы были заблокированы.")
        return

    await message.answer(texts['downloading'][lang])
    try:
        # Выбор cookie файла по ссылке
        if "youtube.com" in message.text or "youtu.be" in message.text:
            cookie_file = "cookiesyt.txt"
        else:
            cookie_file = "cookies.txt"

        ydl_opts = {
            'outtmpl': 'video.%(ext)s',
            'cookiefile': cookie_file,
            'format': 'bestvideo+bestaudio/best'
        }

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

if __name__ == "__main__":
    t = Thread(target=start_bot)
    t.start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
