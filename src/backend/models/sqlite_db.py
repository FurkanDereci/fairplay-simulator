import sqlite3
import tempfile
import os

# Cross-platform SQLite path (works on Windows, macOS, and Linux/VM)
DB_FILE = os.path.join(tempfile.gettempdir(), "fairplay_app.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_sqlite_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_balances (
        user_id TEXT PRIMARY KEY,
        cash_balance REAL NOT NULL DEFAULT 1000.0,
        locked_stakes REAL NOT NULL DEFAULT 0.0,
        simulation_energy INTEGER NOT NULL DEFAULT 100,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cooldown_states (
        user_id TEXT PRIMARY KEY,
        current_tier INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        cooldown_expires_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)

    conn.commit()
    conn.close()

init_sqlite_db()
