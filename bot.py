from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from handlers import register_handlers
import logging

# 🔐 Конфигурация прямо здесь:
BOT_TOKEN = "7661435901:AAFx8X7mY9wwW5FEeKofbLc9GddmX_tLlYk"
ADMIN_ID = 1001788720

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# Подключение всех хендлеров
register_handlers(dp)

# Запуск бота
if name == 'main':
    executor.start_polling(dp, skip_updates=True)
