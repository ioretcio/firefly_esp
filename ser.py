import sqlite3

def display_all_records():
    conn = sqlite3.connect('db.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY tg_id ASC")  # Sort records in ascending order by a specific column
    records = cursor.fetchall()
    for record in records:
        print(record)
    conn.close()

display_all_records()
