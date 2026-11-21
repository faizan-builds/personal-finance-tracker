
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Automatically create data folder
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_FILE = DATA_DIR / "finance.db"


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    return conn


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS savings_goal (
            id INTEGER PRIMARY KEY,
            goal_amount REAL NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
