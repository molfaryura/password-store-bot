from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

import os

from dotenv import load_dotenv

load_dotenv()

bot = Bot(os.environ.get('TOKEN'))
dp = Dispatcher(bot)

@dp.message_handler()
async def talk(message:types.Message):
    await message.answer(message.date)
    await message.reply(message.date)
    await bot.send_message(message.chat.id, "Hello")


executor.start_polling(dp, skip_updates=True)