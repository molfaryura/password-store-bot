import psycopg2
from psycopg2 import sql

import os

from dotenv import load_dotenv

load_dotenv()

hostname = os.environ.get('hostname')
database = os.environ.get('example_db')
username = os.environ.get('username')
pwd = os.environ.get('pwd')
port_id = os.environ.get('port_id')

conn = None
cur = None

table_name = str(input('What is your name?: '))
pwd_name = input('For what dou you need to store a password?: ')
password = int(input('Type your password '))


create_table = sql.SQL('''CREATE TABLE IF NOT EXISTS {} 
                        (id serial PRIMARY KEY, password_name varchar(255), 
                        password int)''').format(sql.Identifier(table_name))
insert = sql.SQL('''INSERT INTO {}
                    (password_name, password) 
                    VALUES (%s, %s)''').format(sql.Identifier(table_name))

try:
    conn = psycopg2.connect(host=hostname,
                            dbname=database,
                            user=username,
                            password=pwd,
                            port=port_id)
    
    cur = conn.cursor()

    cur.execute(create_table)
    conn.commit()
    cur.execute(insert, (pwd_name, password))
    conn.commit()

except Exception as error:
    print(error)

finally:
    if cur:
        cur.close()
    if conn:
        conn.close()
