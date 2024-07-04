from quart import Quart
import sqlite3
from sqlite3 import Error
import datetime
import os

app = Quart(__name__)
database = '/root/bots/fun/esp32pinger/db.db'

def create_connection():
    """Створити та повернути з'єднання з базою даних та вивести в консоль абсолютний шлях до бази даних."""
    try:
        conn = sqlite3.connect(os.path.abspath(database))
        return conn
    except Error as e:
        print(f"The error '{e}' occurred")

def ensure_table_exists(conn):
    """Перевірка наявності таблиці 'config' і її створення, якщо вона відсутня."""
    create_table_query = """
    CREATE TABLE IF NOT EXISTS config (
        id INTEGER PRIMARY KEY,
        date TEXT NOT NULL
    );
    """
    try:
        cursor = conn.cursor()
        cursor.execute(create_table_query)
    except Error as e:
        print(f"The error '{e}' occurred")

def update_config(conn):
    current_time = datetime.datetime.now().isoformat()
    update_query = """
    INSERT OR REPLACE INTO config (id, date) VALUES (0, ?);
    """
    try:
        cursor = conn.cursor()
        cursor.execute(update_query, (current_time,))
        conn.commit()
    except Error as e:
        print(f"The error '{e}' occurred")

@app.route('/imalive', methods=['GET'])
async def im_alive():
    conn = create_connection()
    if conn:
        
        ensure_table_exists(conn)
        update_config(conn)
        conn.close()
    return '', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2705)