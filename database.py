import sqlite3
import json
import hashlib
import os          # <-- Add this import
from datetime import datetime
from typing import List, Dict, Optional

# ===== ADD THIS LINE =====
DB_PATH = "data/chat_history.db"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
# ===== END =====

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            messages TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, password: str, display_name: str) -> bool:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, display_name) VALUES (?, ?, ?)",
            (username, hash_password(password), display_name)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password_hash = ?",
        (username, hash_password(password))
    )
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_id(user_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def save_chat(user_id: int, title: str, messages: List[Dict]) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    messages_json = json.dumps(messages)
    cursor.execute(
        "INSERT INTO chats (user_id, title, messages) VALUES (?, ?, ?)",
        (user_id, title, messages_json)
    )
    chat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return chat_id

def update_chat(chat_id: int, messages: List[Dict]):
    conn = get_db_connection()
    cursor = conn.cursor()
    messages_json = json.dumps(messages)
    cursor.execute(
        "UPDATE chats SET messages = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (messages_json, chat_id)
    )
    conn.commit()
    conn.close()

def get_user_chats(user_id: int) -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, created_at, updated_at FROM chats WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,)
    )
    chats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return chats

def get_chat(chat_id: int, user_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM chats WHERE id = ? AND user_id = ?",
        (chat_id, user_id)
    )
    chat = cursor.fetchone()
    conn.close()
    if chat:
        chat_dict = dict(chat)
        chat_dict['messages'] = json.loads(chat_dict['messages'])
        return chat_dict
    return None

def delete_chat(chat_id: int, user_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chats WHERE id = ? AND user_id = ?", (chat_id, user_id))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_or_create_user_id(username: str, password: str, display_name: str) -> Optional[int]:
    user = authenticate_user(username, password)
    if user:
        return user['id']
    if create_user(username, password, display_name):
        user = authenticate_user(username, password)
        return user['id'] if user else None
    return None

# Initialize the database on import
init_db()
