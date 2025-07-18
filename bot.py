from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config.ру import BOT_TOKEN, ADMIN_ID
from handlers import register_handlers
import logging

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# Регистрируем все хендлеры
register_handlers(dp)

# Запуск бота
if name == 'main':
    executor.start_polling(dp, skip_updates=True)
