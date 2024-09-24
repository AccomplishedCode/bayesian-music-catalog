import sqlite3
from fastapi import Depends

DATABASE = 'music_catalog.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
