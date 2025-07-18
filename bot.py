from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging

# 🔐 Конфигурация прямо тут
BOT_TOKEN = "ТВОЙ_ТОКЕН_СЮДА"
ADMIN_ID = 1001788720
ACR_HOST = "identify-ap-southeast-1.acrcloud.com"
ACR_ACCESS_KEY = "e48f0d7b2af6ccad4015b26d57d75903"
ACR_SECRET_KEY = "WTWOUirBwcIPMJY6vOHEXVKilaMviC8doHQKGgaV"

# 🧠 Инициализация
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# 📦 Импорт регистраций
from handlers import register_handlers
register_handlers(dp)

# ▶️ Старт
if name == 'main':
    executor.start_polling(dp, skip_updates=True)
