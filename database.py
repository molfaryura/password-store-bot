import psycopg2
from psycopg2 import sql
import asyncio

from concurrent.futures import ThreadPoolExecutor

import os

from dotenv import load_dotenv

from encrypt import decrypt, key

load_dotenv()

hostname = os.environ.get('hostname')
database = os.environ.get('database')
username = os.environ.get('username')
pwd = os.environ.get('pwd')
port_id = os.environ.get('port_id')

conn = None
cur = None

thread_executor = ThreadPoolExecutor()

async def connect_to_db():
    global cur, conn

    conn = psycopg2.connect(host=hostname,
                            dbname=database,
                            user=username,
                            password=pwd,
                            port=port_id)
    
    cur = conn.cursor()


async def create_main_table(table_name):
    cur.execute(sql.SQL('''CREATE TABLE IF NOT EXISTS {} 
                        (id serial PRIMARY KEY, account varchar(255), 
                        password BYTEA)''').format(sql.Identifier(table_name)))
    conn.commit()


async def create_table_secret_word(table_name):
    cur.execute(sql.SQL('''CREATE TABLE IF NOT EXISTS {} 
                        (id serial PRIMARY KEY,
                        secret_word varchar(255),
                        hint varchar(255))''').format(sql.Identifier(table_name+'_secret_word')))
    conn.commit()

async def close_db_connection():
    global conn, cur
    if cur is not None:
        cur.close()
        cur = None

    if conn is not None:
        conn.close()
        conn = None

async def add_to_main_db(state, table_name, account, password):
    async with state.proxy() as data:
        cur.execute(sql.SQL('''INSERT INTO {}
                    (account, password) 
                    VALUES (%s, %s)''').format(sql.Identifier(table_name)),
                    tuple([account, password]))
        conn.commit()

async def add_to_secret_word_db(state, table_name, secret_word, hint):
    async with state.proxy() as data:
        cur.execute(sql.SQL('''INSERT INTO {}
                    (secret_word, hint) 
                    VALUES (%s, %s)''').format(sql.Identifier(table_name+'_secret_word')),
                    tuple([secret_word, hint]))
        conn.commit()

async def delete_table_from_db(state, table_name):
    async with state.proxy() as data:
        cur.execute(sql.SQL('''DROP table IF EXISTS {}''').format(sql.Identifier(table_name)))
        cur.execute(sql.SQL('''DROP table IF EXISTS {}''').format(sql.Identifier(table_name+'_secret_word')))
        conn.commit()


async def delete_row_from_db(state, account, table_name):
    async with state.proxy() as data:
        cur.execute(sql.SQL('''DELETE FROM {} WHERE account=%s''').format(sql.Identifier(table_name)),(account,))
        conn.commit()

async def check_connection():
    if conn is None or cur is None:
       await connect_to_db()

def check_secret_word(table_name):
        cur.execute(sql.SQL('''SELECT secret_word FROM {}''').format(sql.Identifier(table_name+'_secret_word')))     
        rows = cur.fetchall()
        return rows[0][0]


def select_from_db(table_name):
    cur.execute(sql.SQL('''SELECT account, password FROM {}''').format(sql.Identifier(table_name)))
    rows = cur.fetchall()
    result = {row[0]:decrypt(key,row[1]).decode('utf8') for row in rows}
    return '\n'.join(f'{acc}: {pwd}' for acc, pwd in result.items())
