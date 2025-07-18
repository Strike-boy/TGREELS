from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand
import logging

from handlers import (
    start,
    help_handler,
    settings,
    stats,
    feedback,
    history,
    admin,
    downloads,
    recognition
)

from middlewares.anti_flood import ThrottlingMiddleware

# 🔐 Конфигурация:
BOT_TOKEN = "7661435901:AAFx8X7mY9wwW5FEeKofbLc9GddmX_tLlYk"
ADMIN_ID = 1001788720

# 📋 Логирование
logging.basicConfig(level=logging.INFO)

# 🤖 Инициализация бота
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# 🛡 Антифлуд Middleware
dp.middleware.setup(ThrottlingMiddleware())

# 📦 Регистрация всех хендлеров
start.register_start(dp)
help_handler.register_help(dp)
settings.register_settings(dp)
stats.register_stats(dp)
feedback.register_feedback(dp)
history.register_history(dp)
downloads.register_downloads(dp)
recognition.register_recognition(dp)
admin.register_admin(dp, ADMIN_ID)

# ✅ Команды для меню бота
async def on_startup(dp):
    await bot.set_my_commands([
        BotCommand("start", "🔹 Запустить бота"),
        BotCommand("help", "ℹ Помощь"),
        BotCommand("settings", "⚙ Настройки"),
        BotCommand("stats", "📊 Статистика"),
        BotCommand("feedback", "✉️ Обратная связь"),
        BotCommand("history", "📁 История загрузок"),
    ])
    print("✅ Бот успешно запущен!")

# 🚀 Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
