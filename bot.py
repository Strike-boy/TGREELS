from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from config import TOKEN
from handlers import start
import logging

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

# Регистрируем хендлеры
start.register_handlers(dp)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
