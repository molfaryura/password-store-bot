import asyncio
from concurrent.futures import ThreadPoolExecutor

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import database

import os

from dotenv import load_dotenv

from encrypt import encrypt, key

load_dotenv()

storage = MemoryStorage()

bot = Bot(os.environ.get('TOKEN'))
dp = Dispatcher(bot, storage=storage)

thread_executor = ThreadPoolExecutor()

class Form(StatesGroup):
    account = State()
    password = State()
    secret_word = State()
    hint = State()

class SecondForm(StatesGroup):
    check_secret = State()

@dp.message_handler(commands=['start'])
async def start(message:types.Message):
    info = (f'Hello <b>{message.from_user.first_name}</b>,\n'
        'Welcome to the Password Store Bot!\n'
        'Here you can securely store your passwords.\n\n'

        '/add - adding a new password to the database.')
    
    await bot.send_message(message.chat.id, info, parse_mode='html')

@dp.message_handler(commands=['cancel'], state="*")
async def cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.answer("Canceled!")


@dp.message_handler(commands=['add'], state=None)
async def add(message:types.Message):
    await Form.account.set()
    await bot.send_message(message.chat.id, 'Hi, what is this account?')

@dp.message_handler(state=Form.account)
async def account(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['account'] = message.text
    await Form.next()
    await message.answer("Type your password: ")


@dp.message_handler(state=Form.password)
async def pwd(message:types.Message, state: FSMContext):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(thread_executor, encrypt, key, message.text.encode())
    async with state.proxy() as data:
        data['password'] = result
    await Form.next()
    task = asyncio.create_task(asyncio.sleep(350))
    await  message.answer("Type your secret word: ")
    await task
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


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
    try:
        await database.connect_to_db()
        await database.create_table_secret_word(table_name=message.from_user.username)
        await database.create_main_table(table_name=message.from_user.username)
        await database.add_to_secret_word_db(state, message.from_user.username, data['secret_word'], data['hint'])
        await database.add_to_main_db(state, message.from_user.username, data['account'], data['password'])

    except Exception as error:
        await message.answer(f"{error}")
    finally:
        await database.close_db_connection()
    await  message.answer(f"Your password is successfully stored in the database")
    await state.finish()  


@dp.message_handler(commands=['show'], state=None)
async def check_secret(message:types.Message, state: FSMContext):
        await SecondForm.check_secret.set()
        await bot.send_message(message.chat.id, 'Type your secret word.')


@dp.message_handler(state=SecondForm.check_secret)
async def show_passwords(message:types.Message, state: FSMContext):
    if message.text == '/add':
        await state.finish()
        await add(message)
    else:
        async with state.proxy() as data:
            data['check_secret'] = message.text
        await database.check_connection()
        loop = asyncio.get_event_loop()
        
        if data['check_secret'] == await loop.run_in_executor(thread_executor, database.check_secret_word, message.from_user.username):
            result = await loop.run_in_executor(thread_executor, database.select_from_db, message.from_user.username)
            await state.finish()
            task = asyncio.create_task(asyncio.sleep(60))
            bot_message = await bot.send_message(message.chat.id, result)
            await task
            await bot.delete_message(chat_id=message.chat.id, message_id=bot_message.message_id)
        else:
            await bot.send_message(message.chat.id, 'Type your secret word again.')
            await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
