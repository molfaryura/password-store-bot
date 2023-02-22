from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import os

from dotenv import load_dotenv

load_dotenv()

storage = MemoryStorage()

bot = Bot(os.environ.get('TOKEN'))
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    account = State()
    password = State()
    secret_word = State()
    hint = State()

@dp.message_handler(commands=['start'])
async def start(message:types.Message):
    info = (f'Hello <b>{message.from_user.first_name}</b>,\n'
        'Welcome to the Password Store Bot!\n'
        'Here you can securely store your passwords.\n\n'

        '/add - adding a new password to the database.')
    
    await bot.send_message(message.chat.id, info, parse_mode='html')


@dp.message_handler(commands=['add'], state=None)
async def add(message:types.Message):
    await Form.account.set()
    await bot.send_message(message.chat.id, 'Hi, what is this account?')

@dp.message_handler(state=Form.account)
async def account(message:types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['account'] = message.text
    await Form.next()
    await  message.answer("Type your password: ")

@dp.message_handler(state=Form.password)
async def pwd(message:types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['password'] = message.text
    await Form.next()
    await  message.answer("Type your secret word: ")


@dp.message_handler(state=Form.secret_word)
async def secret_word(message:types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['secret_word'] = message.text
    await Form.next()
    await  message.answer("""Enter a hint for your secret word. Keep in mind that 
if you forget your secret word, you won't be able to see your passwords! """)

@dp.message_handler(state=Form.hint)
async def hint(message:types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['hint'] = message.text
    await  message.answer("Your password is successfully stored in the database")
    await state.finish()  


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
