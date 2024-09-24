import sqlite3

DATABASE = 'music_catalog.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    with open('schema.sql', 'r') as f:
        conn.executescript(f.read())
    conn.close()
    print('Database initialized.')

if __name__ == '__main__':
    init_db()
