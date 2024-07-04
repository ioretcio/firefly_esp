import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import sqlite3
from sqlite3 import Error
import datetime

API_TOKEN = 'TOKEN'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

wait_time = 15
light_resting_sent = False
database = '/root/bots/fun/esp32pinger/db.db'




def initialize_db():
    
    sql_create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        tg_id INTEGER NOT NULL UNIQUE,
        status BOOLEAN NOT NULL
    );
    """
    conn = create_connection(database)
    if conn is not None:
        create_table(conn, sql_create_users_table)
    else:
        print("Error! cannot create the database connection.")
    conn.close()

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def create_connection():
    try:
        conn = sqlite3.connect(database)
        return conn
    except Error as e:
        print(f"The error '{e}' occurred")
        return None

def get_config_value(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT date FROM config WHERE id = 0")
        value = cursor.fetchone()
        if value:
            return value[0]
        else:
            return "No value found"
    except Error as e:
        print(f"The error '{e}' occurred")
        return "Error retrieving value"

async def check_config_value_periodically():
    """Періодична перевірка значення в базі даних і вивід його в консоль."""
    while True:
        conn = create_connection()
        if conn:
            value = get_config_value(conn)
            if datetime.datetime.now() - datetime.datetime.fromisoformat(value) > datetime.timedelta(seconds=wait_time):
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM config WHERE id = 1 OR id = 2")
                count = cursor.fetchone()[0]
                if count != 2:
                    current_time = datetime.datetime.now().isoformat()
                    cursor.execute("INSERT OR REPLACE INTO config (id, date) VALUES (1, ?);", (current_time,))
                    cursor.execute("INSERT OR REPLACE INTO config (id, date) VALUES (2, ?);", (current_time,))
                    conn.commit()
                else:
                    cursor = conn.cursor()
                    cursor.execute("SELECT date FROM config WHERE id = 1")
                    value1 = cursor.fetchone()[0]
                    cursor.execute("SELECT date FROM config WHERE id = 2")
                    value2 = cursor.fetchone()[0]
                    if datetime.datetime.fromisoformat(value2) >= datetime.datetime.fromisoformat(value1):
                        current_time = datetime.datetime.now().isoformat()
                        insert_query = """
                        INSERT OR REPLACE INTO config (id, date) VALUES (1, ?);
                        """
                        cursor.execute(insert_query, (current_time,))
                        conn.commit()
                        await notify_all("🐈‍⬛Світло зникло")
            else:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM config WHERE id = 1 OR id = 2")
                count = cursor.fetchone()[0]
                if count != 2:
                    current_time = datetime.datetime.now().isoformat()
                    cursor.execute("INSERT OR REPLACE INTO config (id, date) VALUES (1, ?);", (current_time,))
                    cursor.execute("INSERT OR REPLACE INTO config (id, date) VALUES (2, ?);", (current_time,))
                    conn.commit()
                else:
                    cursor = conn.cursor()
                    cursor.execute("SELECT date FROM config WHERE id = 1")
                    value1 = cursor.fetchone()[0]
                    cursor.execute("SELECT date FROM config WHERE id = 2")
                    value2 = cursor.fetchone()[0]
                    if datetime.datetime.fromisoformat(value1) >= datetime.datetime.fromisoformat(value2):
                        current_time = datetime.datetime.now().isoformat()
                        insert_query = """
                        INSERT OR REPLACE INTO config (id, date) VALUES (2, ?);
                        """
                        cursor.execute(insert_query, (current_time,))
                        conn.commit()
                        await notify_all("🐈Світло повернулося")
        conn.close()
        await asyncio.sleep(5)

def display_users():
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        for user in users:
            print(user)
    conn.close()

async def notify_all(message):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT tg_id FROM users WHERE status = 1")
        active_users = cursor.fetchall()
        for user in active_users:
            tg_id = user[0] 
            try:
                await bot.send_message(chat_id=tg_id, text=message)
            except Exception as e:
                print(f"Error sending message to user {tg_id}: {e}")
    else:
        print("Connection to database failed.")

@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    button_subscribe = InlineKeyboardButton(text="Підписатися", callback_data="subscribe")
    button_unsubscribe = InlineKeyboardButton(text="Відписатися", callback_data="unsubscribe")
    keyboard.add(button_subscribe, button_unsubscribe)
    await message.reply("Привіт добра людино!!", reply_markup=keyboard)

@dp.message_handler(commands=['ask'])
async def handle_start(message: types.Message):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT date FROM config WHERE id = 0")
        value = cursor.fetchone()[0]
        cursor.execute("SELECT date FROM config WHERE id = 2")
        value2 = cursor.fetchone()[0]
        if value:
            current_time = datetime.datetime.fromisoformat(value)
            on_time = datetime.datetime.fromisoformat(value2)
            time_difference = datetime.datetime.now() - current_time
            lifetime = datetime.datetime.now() - on_time
            if time_difference.seconds < 60:
                hours = lifetime.seconds // 3600
                minutes = (lifetime.seconds % 3600) // 60
                await bot.send_message(chat_id=message.chat.id, text=f"Світло є! ⏰{hours}г. {minutes}хв. як воно з нами")
            else:
                hours = time_difference.seconds // 3600
                minutes = (time_difference.seconds % 3600) // 60
                await bot.send_message(chat_id=message.chat.id, text=f"Востаннє світло я бачив ⏰{hours}г. {minutes}хв. тому")
    conn.close()


@dp.message_handler(commands=['stat'])
async def handle_start(message: types.Message):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        await bot.send_message(chat_id=message.chat.id, text=f"Кількість записів в таблиці users: {count}")
    conn.close()


@dp.callback_query_handler(lambda query: query.data in ['subscribe', 'unsubscribe'])
async def callback_query_handler(query: types.CallbackQuery):
    data = query.data
    print("Received callback with data:", data)
    if data == "subscribe":
        with sqlite3.connect(database) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT EXISTS(SELECT 1 FROM users WHERE tg_id = ?)", (query.message.chat.id,))
            exists = cursor.fetchone()[0]
            if not exists:
                conn.execute("INSERT INTO users (tg_id, status) VALUES (?, ?)", (query.message.chat.id, True))
                await query.message.answer("Ви успішно підписались!😇")
            else:
                cursor.execute("SELECT status FROM users WHERE tg_id = ?", (query.message.chat.id,))
                status = cursor.fetchone()[0]
                if status == 1:
                    await query.message.answer("Ви вже підписані і так, для чого це робити ще раз!?")
                else:
                    conn.execute("UPDATE users SET status = ? WHERE tg_id = ?", (True, query.message.chat.id))
                    await query.message.answer("Ви успішно підписались!😇")
            conn.commit()
            try:
                await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id-1)
                await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
            except:
                pass
    elif data == "unsubscribe":
        with sqlite3.connect(database) as conn:
            conn.execute("UPDATE users SET status = ? WHERE tg_id = ?", (False, query.message.chat.id))
            conn.commit()
            await query.message.answer("Чекаю повернення. Хоча сподіваюсь, що я не пригожусь)")
            try:
                await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id-1)
                await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
            except:
                pass
    await query.answer()

async def start_polling():
    await dp.skip_updates()
    await dp.start_polling()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(check_config_value_periodically())
    loop.run_until_complete(start_polling())
