import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
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
