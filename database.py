import sqlite3
import streamlit as st

def get_connection():
    """
    Returns a thread-safe connection to the SQLite database.
    Using check_same_thread=False is necessary for Streamlit's architecture.
    """
    return sqlite3.connect('trading_vault.db', check_same_thread=False)

def init_db():
    """
    Initializes the database schema and performs structural maintenance.
    This runs every time the app starts to ensure the 'Vault' is secure.
    """
    conn = get_connection()
    c = conn.cursor()

    # 1. ARCHITECT TABLE: Stores the logic for your trading models
    # Added screenshot column for model schematics
    c.execute('''
        CREATE TABLE IF NOT EXISTS models (
            name TEXT PRIMARY KEY, 
            logic TEXT, 
            sessions TEXT,
            screenshot BLOB
        )
    ''')

    # 2. TRADES TABLE: Stores your scalping and backtesting execution data
    c.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            model_name TEXT, 
            model_var TEXT, 
            type TEXT, 
            market TEXT, 
            entry_time TEXT, 
            entry_tf TEXT, 
            session TEXT, 
            result TEXT, 
            risk_pc REAL, 
            rr REAL, 
            sl_handles REAL, 
            tp_handles REAL, 
            notes TEXT, 
            date TEXT, 
            duration_mins INTEGER, 
            news_impact TEXT, 
            screenshot BLOB
        )
    ''')

    # 3. PORTFOLIO TABLE: Stores your long-term DCA / Wealth Builder positions
    c.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            asset_name TEXT, 
            total_shares REAL, 
            avg_price REAL, 
            last_updated TEXT
        )
    ''')

    # --- STRUCTURAL MAINTENANCE (Auto-Repair) ---
    # This block prevents crashes if you add features but the DB file is old.
    trade_columns = [
        ('model_var', 'TEXT'), 
        ('duration_mins', 'INTEGER'), 
        ('news_impact', 'TEXT'),
        ('sl_handles', 'REAL'),
        ('tp_handles', 'REAL')
    ]
    
    for col_name, col_type in trade_columns:
        try:
            c.execute(f'ALTER TABLE trades ADD COLUMN {col_name} {col_type}')
        except sqlite3.OperationalError:
            # Column already exists, skip it
            pass

    # Maintenance for the models table (Adding screenshot column if it doesn't exist)
    try:
        c.execute('ALTER TABLE models ADD COLUMN screenshot BLOB')
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

def execute_query(query, params=(), commit=False):
    """
    A helper function to handle quick SQL operations safely.
    This is used by other modules to interact with the database without 
    writing full connection boilerplate every time.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if commit:
            conn.commit()
        return cursor.fetchall()
    finally:
        conn.close()

def get_all_models():
    """Utility to fetch all saved models for selectors."""
    conn = get_connection()
    try:
        return sqlite3.connect('trading_vault.db').cursor().execute("SELECT * FROM models").fetchall()
    finally:
        conn.close()