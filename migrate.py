import os
from auth import init_auth_db
from database import init_db, engine
from sqlalchemy import text

def migrate():
    # 1. Auth DB Başlat
    init_auth_db()
    
    print(f"Connecting to database engine: {engine.name}")
    
    # 2. Base.metadata tablolari olustur
    print("Creating all tables from models...")
    init_db()
    
    # 3. Alter tables eger sqlite ve eski versiyonsa (manuel guncellemeler)
    if engine.name == "sqlite":
        import sqlite3
        DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bist_cache.db")
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            
            for table in ["portfolio", "scan_history", "watchlist"]:
                try:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN username TEXT")
                    conn.execute(f"UPDATE {table} SET username='admin1' WHERE username IS NULL")
                    print(f"{table} table updated with username.")
                except sqlite3.OperationalError:
                    print(f"{table} table already updated or error.")
                    
            conn.commit()
            conn.close()
    else:
        # PostgreSQL vs icin
        print("Running on PostgreSQL. Assuming models.py schema handles columns correctly.")
        
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
