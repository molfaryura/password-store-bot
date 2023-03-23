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

from encrypt import encrypt, key, hash_secret_word

load_dotenv()

storage = MemoryStorage()

bot = Bot(os.environ.get('TOKEN'))
dp = Dispatcher(bot, storage=storage)

thread_executor = ThreadPoolExecutor()

class AddSecretWordForm(StatesGroup):
    secret_word = State()
    hint  = State()

class AddAccPwdForm(StatesGroup):
    account = State()
    password = State()

class SelectForm(StatesGroup):
    check_secret = State()

class DeleteTableForm(StatesGroup):
    check_secret = State()
    table_or_row = State()
    table = State()
    row = State()

class ChangeSecretWordForm(StatesGroup):
    check_secret = State()
    new_secret_word = State()
    new_hint = State()

@dp.message_handler(commands=['start'])
async def start(message:types.Message):
    info = (f'Hello <b>{message.from_user.first_name}</b>,\n'
        'Welcome to the Password Store Bot!\n'
        'Here you can securely store your passwords.\n\n'
        
        '/help - type to receive instructions for use')
    
    await bot.send_message(message.chat.id, info, parse_mode='html')

@dp.message_handler(commands=['help'])
async def help_(message:types.Message):
    help_info = ('To use this bot, at first you need to create a secret word '
                 'for your passwords: type /secret\n\n'
                 'Here are the commands you can use:\n'
                 '/add - add a new password to the database.\n'
                 '/cancel - cancel the current action.\n'
                 '/delete - delete your passwords in the database.'
                 )
    await bot.send_message(message.chat.id, help_info, parse_mode='html')

@dp.message_handler(commands=['cancel'], state="*")
async def cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.answer("Canceled!")


@dp.message_handler(commands=['secret'], state=None)
async def start_secret_word(message:types.Message):
    await database.check_connection()
    loop = asyncio.get_event_loop()
    if await loop.run_in_executor(thread_executor, database.check_if_secret_table_exists, message.from_user.username):
        await bot.send_message(message.chat.id, "You already have a secret word!")
    else:
        await AddSecretWordForm.secret_word.set()
        await bot.send_message(message.chat.id, "Type your secret word: ")

@dp.message_handler(state=AddSecretWordForm.secret_word)
async def add_secret_word(message: types.Message, state: FSMContext):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(thread_executor, hash_secret_word, message.text)
    async with state.proxy() as data:
        data['secret_word'] = result
    await AddSecretWordForm.next()
    await  message.answer("""Enter a hint for your secret word.Keep in mind that if you forget your secret word, you won't be able to see your passwords! """)

@dp.message_handler(state=AddSecretWordForm.hint)
async def hint_(message:types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['hint'] = message.text
    try:
        await database.connect_to_db()
        await database.create_table_secret_word(table_name=message.from_user.username)

        await database.add_to_secret_word_db(state, message.from_user.username, data['secret_word'], data['hint'])
    except Exception as error:
        await message.answer(f"{error}")
    finally:
        await database.close_db_connection()
    await message.answer("Your secret word and a hint are successfully created.")
    await state.finish()

@dp.message_handler(commands=['show_hint'])
async def show_hint(message:types.Message):
    await database.check_connection()
    loop = asyncio.get_event_loop()
    if await loop.run_in_executor(thread_executor, database.check_if_secret_table_exists, message.from_user.username):
        result = await loop.run_in_executor(thread_executor, database.select_hint, message.from_user.username)
        await message.answer(f"The hint for your secret words is: {result}.")
    else:
        await message.answer("You do not have a secret word. Type /secret to create one", parse_mode='html')


@dp.message_handler(commands=['add'], state=None)
async def add(message:types.Message):
    await database.check_connection()
    loop = asyncio.get_event_loop()

    if await loop.run_in_executor(thread_executor, database.check_if_secret_table_exists, message.from_user.username):
        await AddAccPwdForm.account.set()
        await bot.send_message(message.chat.id, 'Hi, what is this account?')
    else:
        await message.answer("You do not have a secret word. Type /secret to create one", parse_mode='html')

@dp.message_handler(state=AddAccPwdForm.account)
async def account(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['account'] = message.text
    await AddAccPwdForm.next()
    await message.answer("Type your password: ")


@dp.message_handler(state=AddAccPwdForm.password)
async def pwd(message:types.Message, state: FSMContext):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(thread_executor, encrypt, key, message.text.encode())
    async with state.proxy() as data:
        data['password'] = result

    task = asyncio.create_task(asyncio.sleep(10))

    try:
        await database.connect_to_db()
        await database.create_main_table(table_name=message.from_user.username)
        await database.add_to_main_db(state, message.from_user.username, data['account'], data['password'])

    except Exception as error:
        await message.answer(f"{error}")
    finally:
        await database.close_db_connection()

    await  message.answer(f"Your password is successfully stored in the database")
    await state.finish()

    await task
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


@dp.message_handler(commands=['show', 'delete', 'change_secret_word'], state=None)
async def check_secret(message:types.Message, state: FSMContext):
        if message.text == '/show':
            await SelectForm.check_secret.set()
        elif message.text == '/delete':
            await DeleteTableForm.check_secret.set()
        else:
            await ChangeSecretWordForm.check_secret.set()

        await bot.send_message(message.chat.id, 'Type your secret word.')


@dp.message_handler(state=SelectForm.check_secret)
async def show_passwords(message:types.Message, state: FSMContext):
    if message.text == '/add':
        await state.finish()
        await add(message)
    else:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(thread_executor, hash_secret_word, message.text)
        async with state.proxy() as data:
            data['check_secret'] = result

        await database.check_connection()
        
        if data['check_secret'] == await loop.run_in_executor(thread_executor, database.check_secret_word, message.from_user.username):
            result = await loop.run_in_executor(thread_executor, database.select_from_db, message.from_user.username)
            await state.finish()
            task = asyncio.create_task(asyncio.sleep(15))
            bot_message = await bot.send_message(message.chat.id, result)
            await task
            await bot.delete_message(chat_id=message.chat.id, message_id=bot_message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        else:
            await bot.send_message(message.chat.id, 'Type your secret word again.')
        await state.finish()
            

@dp.message_handler(state=DeleteTableForm.check_secret)
async def ask_what_to_delete(message:types.Message, state: FSMContext):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(thread_executor, hash_secret_word, message.text)

    async with state.proxy() as data:
        data['check_secret'] = result

    if data['check_secret'] == await loop.run_in_executor(thread_executor, database.check_secret_word, message.from_user.username):
        await bot.send_message(message.chat.id, "Type 'all' to delete all password or type a specific account which you want to delete.")
        await DeleteTableForm.next()

    else:
        await bot.send_message(message.chat.id, "Your secret word is incorrect!")
        await state.finish()
    
@dp.message_handler(state=DeleteTableForm.table_or_row)
async def choose_table_or_row(message:types.Message, state: FSMContext):
    await database.check_connection()
    if message.text == 'all':
        try:
            await database.delete_table_from_db(state, message.from_user.username)
            await bot.send_message(message.chat.id, 'All your passwords are successfully deleted.')
        except:
            await bot.send_message(message.chat.id, 'You do not have any passwords stored in the database!')
    else:
        await database.delete_row_from_db(state, message.text, message.from_user.username)
        await bot.send_message(message.chat.id, 'All your passwords are successfully deleted.')
    await state.finish()


@dp.message_handler(state=ChangeSecretWordForm.check_secret)
async def ask_for_new_secret_word(message:types.Message, state: FSMContext):
    await database.check_connection()

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(thread_executor, hash_secret_word, message.text)

    async with state.proxy() as data:
        data['check_secret'] = result

    if data['check_secret'] == await loop.run_in_executor(thread_executor, database.check_secret_word, message.from_user.username):
        await bot.send_message(message.chat.id, "Type a new secret word.")
        await ChangeSecretWordForm.next()
    else:
        await bot.send_message(message.chat.id, "Your secret word is incorrect!")
        await state.finish()
 
@dp.message_handler(state=ChangeSecretWordForm.new_secret_word)
async def ask_for_new_hint(message:types.Message, state: FSMContext):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(thread_executor, hash_secret_word, message.text)
    async with state.proxy() as data:
        data['new_secret_word'] = result
    
    await bot.send_message(message.chat.id, "Type a a new hint.")
    await ChangeSecretWordForm.next()

@dp.message_handler(state=ChangeSecretWordForm.new_hint)
async def update_secret_word(message:types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['new_hint'] = message.text
    try:
        await database.change_secret_word(state, message.from_user.username)
        await bot.send_message(message.chat.id, "Your secret word is succesfully updated")
    except Exception as error:
        await bot.send_message(message.chat.id, error)
    finally:
        await state.finish()
        await database.close_db_connection()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
