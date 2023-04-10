"""Database code for telegram bot"""

import os

import psycopg2
from psycopg2 import sql

from dotenv import load_dotenv

from encrypt import decrypt, KEY

load_dotenv()

hostname = os.environ.get('hostname')
database = os.environ.get('database')
username = os.environ.get('username')
pwd = os.environ.get('pwd')
port_id = os.environ.get('port_id')

CONN = None
CUR = None

async def connect_to_db():
    """Connects to the postgresql database

    returns: None
    """

    global CUR, CONN

    CONN = psycopg2.connect(host=hostname,
                            dbname=database,
                            user=username,
                            password=pwd,
                            port=port_id)

    CUR = CONN.cursor()


async def create_main_table(table_name):
    """Creates a table, where name of the table is telegram username

    param table_name: username
    returns: None
    """

    CUR.execute(sql.SQL('''CREATE TABLE IF NOT EXISTS {}
                        (id serial PRIMARY KEY, account varchar(255), 
                        password BYTEA)''').format(sql.Identifier(table_name)))
    CONN.commit()


async def create_table_secret_word(table_name):
    """Creates a table, where name of the table is telegram username + '_secret_word'

    param table_name: username
    returns: None
    """

    CUR.execute(sql.SQL('''CREATE TABLE IF NOT EXISTS {}
                        (id serial PRIMARY KEY,
                        secret_word varchar(255),
                        hint varchar(255))''').format(sql.Identifier(table_name+'_secret_word')))
    CONN.commit()

async def close_db_connection():
    """Closes connection to the database

    returns: None
    """

    global CONN, CUR

    if CUR is not None:
        CUR.close()
        CUR = None

    if CONN is not None:
        CONN.close()
        CONN = None

async def add_to_main_db(table_name, account, password):
    """Adds records to the table, where name of the table is telegram username

    param table_name: username
    param account: account name
    param password: password for the account

    returns: None
    """

    CUR.execute(sql.SQL('''INSERT INTO {}
                    (account, password) 
                    VALUES (%s, %s)''').format(sql.Identifier(table_name)),
                    tuple([account, password]))
    CONN.commit()

async def add_to_secret_word_db(table_name, secret_word, hint):
    """Adds records to the table,where name of the table is telegram username + '_secret_word'

    param table_name: username
    param secret_word: secret word
    param hint: hint for the secret word

    returns: None
    """

    CUR.execute(sql.SQL('''INSERT INTO {}
                    (secret_word, hint) 
                    VALUES (%s, %s)''').format(sql.Identifier(table_name+'_secret_word')),
                    tuple([secret_word, hint]))
    CONN.commit()

async def delete_table_from_db(table_name):
    """Deletes table from the database

    param table_name: username
    returns: None
    """

    CUR.execute(sql.SQL('''DROP table IF EXISTS {}''').format(sql.Identifier(table_name)))
    CUR.execute(sql.SQL('''DROP table
                        IF EXISTS {}''').format(sql.Identifier(table_name+'_secret_word')))
    CONN.commit()


async def delete_row_from_db(account, table_name):
    """Deletes row from the table

    param account: account name
    param table_name: username
    returns: None
    """

    CUR.execute(sql.SQL('''DELETE FROM {}
                        WHERE account=%s''').format(sql.Identifier(table_name)),(account,))
    CONN.commit()

async def check_connection():
    """Connect to the database if the user is not connected

    returns: None
    """

    if CONN is None or CUR is None:
        await connect_to_db()

def check_secret_word(table_name):
    """Selects secret_word from the table

    param table_name: username

    returns(str): secret word
    """

    CUR.execute(sql.SQL('''SELECT secret_word
                        FROM {}''').format(sql.Identifier(table_name+'_secret_word')))
    rows = CUR.fetchall()
    return rows[0][0]

def check_if_secret_table_exists(table_name):
    """Selects secret_word table from the database

    param table_name: username

    returns(bool): True if table exists
    """

    CUR.execute('''SELECT EXISTS (SELECT 1 FROM information_schema.tables
                WHERE table_name=%s)''', (table_name+"_secret_word",))
    rows = CUR.fetchall()
    return rows[0][0]

def select_hint(table_name):
    """Selects hint from the table

    param table_name: username

    returns(str): hint for the secret word
    """

    CUR.execute(sql.SQL('''SELECT hint
                        FROM {}''').format(sql.Identifier(table_name+'_secret_word')))
    rows = CUR.fetchall()
    return rows[0][0]


def select_from_db(table_name):
    """Selects account name and password from the table

    param table_name: username

    returns(str): account name: password
    """

    CUR.execute(sql.SQL('''SELECT account, password FROM {}''').format(sql.Identifier(table_name)))
    rows = CUR.fetchall()
    result = {row[0]:decrypt(KEY,row[1]).decode('utf8') for row in rows}
    return '\n'.join(f'{acc}: {pwd}' for acc, pwd in result.items())

async def change_secret_word(state, table_name):
    """Updates a record in the database

    param state: State() from StatesGroup()
    param table_name: username

    returns: None
    """

    query = '''UPDATE {} SET secret_word=%s, hint=%s'''

    async with state.proxy() as data:
        data_values = tuple(data.values())[1:3]
        CUR.execute(sql.SQL(query).format(sql.Identifier(table_name+"_secret_word")), data_values)
        CONN.commit()
