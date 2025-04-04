import sqlite3
import os

DB_PATH = "data/emails.db"

def create_connection():
    if not os.path.exists("data"):
        os.makedirs("data")
    return sqlite3.connect(DB_PATH)

def create_tables():
    conn = create_connection()
    cursor = conn.cursor()

    # Create Emails Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gmail_id TEXT UNIQUE,
            sender TEXT,
            recipient TEXT,
            subject TEXT,
            timestamp TEXT,
            body TEXT,
            attachments TEXT,
            summary TEXT,
            priority TEXT
        )
    """)

    # Check if 'Category' column exists before altering the table
    cursor.execute("PRAGMA table_info(emails)")
    columns = [col[1] for col in cursor.fetchall()]
    if "Category" not in columns:
        cursor.execute("""
            ALTER TABLE emails ADD COLUMN Category TEXT DEFAULT 'Uncategorized'
        """)

    

    conn.commit()
    conn.close()
    print("✅ Database and Tables Created Successfully!")

if __name__ == "__main__":
    create_tables()