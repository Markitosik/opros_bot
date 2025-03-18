from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import API_TOKEN_TG

bot = Bot(token=API_TOKEN_TG)
dp = Dispatcher(storage=MemoryStorage())
