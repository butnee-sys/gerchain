import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = "database/gerchain.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs("database", exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Дансны хүснэгт (Wallets)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_address TEXT UNIQUE NOT NULL,
            owner_name TEXT NOT NULL,
            balance REAL DEFAULT 0.0,
            locked_balance REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Эскроу гэрээний хүснэгт (Escrows)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS escrows (
            id TEXT PRIMARY KEY,
            sender_address TEXT NOT NULL,
            receiver_address TEXT NOT NULL,
            amount REAL NOT NULL,
            state TEXT NOT NULL, -- CREATED, LOCKED, RELEASED
            condition_desc TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 3. Аудитын мөр ба төлөв шилжилтийн түүх (Audit & State Logs)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            escrow_id TEXT NOT NULL,
            previous_state TEXT,
            new_state TEXT NOT NULL,
            actor TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tx_hash TEXT NOT NULL,
            FOREIGN KEY (escrow_id) REFERENCES escrows (id)
        )
    ''')

    # 4. Бодит хөрөнгө болон ногоон төслийн хүснэгт (RWA & Projects)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rwa_assets (
            id TEXT PRIMARY KEY,
            asset_name TEXT NOT NULL,
            asset_type TEXT NOT NULL, 
            owner_wallet TEXT NOT NULL,
            valuation_amount REAL NOT NULL,
            status TEXT DEFAULT 'ACTIVE', 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 5. Төслийн үе шат болон шалгуурын хүснэгт (Milestones)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            escrow_id TEXT NOT NULL,
            milestone_title TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING', -- PENDING, COMPLETED
            target_date TEXT,
            FOREIGN KEY (escrow_id) REFERENCES escrows (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Өгөгдлийн сангийн архитектур Milestones хүснэгттэйгээр амжилттай өргөтгөгдлөө.")

def log_transition(escrow_id: str, prev_state: str, new_state: str, actor: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    timestamp = datetime.utcnow().isoformat()
    raw_data = f"{escrow_id}:{prev_state}:{new_state}:{actor}:{timestamp}"
    tx_hash = hashlib.sha256(raw_data.encode('utf-8')).hexdigest()
    
    cursor.execute('''
        INSERT INTO audit_logs (escrow_id, previous_state, new_state, actor, timestamp, tx_hash)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (escrow_id, prev_state, new_state, actor, timestamp, tx_hash))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
