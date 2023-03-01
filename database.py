import psycopg2
from psycopg2 import sql

import os

from dotenv import load_dotenv

load_dotenv()

hostname = os.environ.get('hostname')
database = os.environ.get('database')
username = os.environ.get('username')
pwd = os.environ.get('pwd')
port_id = os.environ.get('port_id')

conn = None
cur = None

def connect_to_db_and_create_table(table_name):
    global conn, cur
    
    conn = psycopg2.connect(host=hostname,
                            dbname=database,
                            user=username,
                            password=pwd,
                            port=port_id)
    
    cur = conn.cursor()
    cur.execute(sql.SQL('''CREATE TABLE IF NOT EXISTS {} 
                        (id serial PRIMARY KEY, account varchar(255), 
                        password varchar(255),
                        secret_word varchar(255),
                        hint varchar(255))''').format(sql.Identifier(table_name)))
    conn.commit()

def close_db_connection():
    global conn, cur
    if cur is not None:
        cur.close()
    if conn is not None:
        conn.close()



async def add_to_db(state, table_name):
    async with state.proxy() as data:
        cur.execute(sql.SQL('''INSERT INTO {}
                    (account, password, secret_word, hint) 
                    VALUES (%s, %s, %s, %s)''').format(sql.Identifier(table_name)),
                    tuple(data.values()))
        conn.commit()
