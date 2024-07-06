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

wait_time = 40
light_resting_sent = False
database = '/root/bots/fun/esp32pinger/db.db'

ons = {
    'mon 1am': 'mon 12am',
    'mon 10am': 'mon 7am',
    'mon 6pm': 'mon 3pm',
    'tue 4am': 'tue 1am',
    'tue 1pm': 'tue 10am',
    'tue 10pm': 'tue 7pm',

    'wed 7am': 'wed 4am',
    'wed 4pm': 'wed 1pm',
    'thu 1am': 'wed 10pm',
    'thu 10am': 'thu 7am',
    'thu 7pm': 'thu 4pm',
    'fri 4am': 'fri 1am',
    'fri 1pm': 'fri 10am',
    'fri 10pm': 'fri 7pm',

    'sat 7am': 'sat 4am',
    'sat 4pm': 'sat 1pm',
    'sun 1am': 'sat 10pm',
    'sun 10am': 'sun 7am',
    'sun 7pm': 'sun 4pm'
}

offs = [
    'mon 3am',
    'mon 12pm',
    'mon 9pm',
    'tue 6am',
    'tue 3pm',
    'wed 12am',
    'wed 9am',
    'wed 6pm',
    'thu 3am',
    'thu 12pm',
    'thu 9pm',
    'fri 6am',
    'fri 3pm',
    'sat 12am',
    'sat 9am',
    'sat 6pm',
    'sun 3am',
    'sun 12pm',
    'sun 9pm'
]

def get_next_weekday(day_name):
    days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    today = datetime.datetime.now()
    today_day = today.weekday()  # Monday is 0 and Sunday is 6
    target_day = days.index(day_name[:3])
    days_ahead = target_day - today_day if target_day >= today_day else 7 - (today_day - target_day)
    next_day = today + timedelta(days=days_ahead)
    return next_day.replace(hour=0, minute=0, second=0, microsecond=0)

def parse_time(time_str):
    day_time = time_str.split(' ')
    day = day_time[0]
    time = day_time[1]
    next_day = get_next_weekday(day)
    parsed_time = datetime.datetime.strptime(time, '%I%p')
    return next_day + timedelta(hours=parsed_time.hour, minutes=parsed_time.minute)

def generate(date_time, lightEnable):
    if lightEnable:
        closest_off = min(offs, key=lambda x: abs(parse_time(x) - date_time) if parse_time(x) > date_time else timedelta.max)
        time_difference = (parse_time(closest_off) - date_time).total_seconds() // 60
        return f"Наступне вимкнення через {time_difference//60}г. {time_difference%60}хв."
    else:
        soonest_on = min(ons, key=lambda x: abs(parse_time(x) - date_time) if parse_time(x) > date_time else timedelta.max)
        time_difference1 = (parse_time(ons[soonest_on]) - date_time).total_seconds() // 60
        time_difference2 = (parse_time(soonest_on) - date_time).total_seconds() // 60
        return f"Наступне увімкнення через {time_difference1//60}г. {time_difference1%60}хв.\nабо\n{time_difference2//60}г. {time_difference2%60}хв."



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
                        current_date_time = datetime.datetime.now() + timedelta(hours=3)
                        result = generate(current_date_time, False)
                        await notify_all(f"🐈‍⬛Світло зникло\n{result}")
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
                        current_date_time = datetime.datetime.now() + timedelta(hours=3)
                        result = generate(current_date_time, True)
                        await notify_all(f"🐈Світло повернулося\n{result}")
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
                current_date_time = datetime.datetime.now() + timedelta(hours=3)
                result = generate(current_date_time, True)
                await bot.send_message(chat_id=message.chat.id, text=f"Світло є! ⏰{hours}г. {minutes}хв. як воно з нами\n{result}")
            else:
                hours = time_difference.seconds // 3600
                minutes = (time_difference.seconds % 3600) // 60
                current_date_time = datetime.datetime.now() + timedelta(hours=3)
                result = generate(current_date_time, False)
                await bot.send_message(chat_id=message.chat.id, text=f"Востаннє світло я бачив ⏰{hours}г. {minutes}хв. тому\n{result}")
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
    if query.message.chat.id != query.from_user.id:
        chat_member = await bot.get_chat_member(chat_id=query.message.chat.id, user_id=query.from_user.id)
        if chat_member.status == 'creator' or chat_member.status == 'owner' or chat_member.status == 'administrator':
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
                            firstname = query.from_user.first_name
                            await query.message.answer(f"{firstname}, ви вже підписані і так, для чого це робити ще раз!?")
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
    else:
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
                        firstname = query.from_user.first_name
                        await query.message.answer(f"{firstname}, ви вже підписані і так, для чого це робити ще раз!?")
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
