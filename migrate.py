import os
from sqlalchemy import text
from auth import init_auth_db
import database
import models

def migrate():
    print("=== STARTING DIAGNOSTIC MIGRATION PROCESS ===")
    
    # 1. Auth DB Başlat
    init_auth_db()
    
    print(f"[INFO] Engine Name: {database.engine.name}")
    print(f"[INFO] Connecting to database URL: {repr(str(database.engine.url).replace(database.engine.url.password or 'PASS', '***'))}")
    
    # Veritabanı test bağlantısı
    with database.engine.connect() as conn:
        try:
            version = conn.execute(text("SELECT version();")).scalar()
            print(f"[INFO] Database Version: {version}")
        except Exception as e:
            print(f"[WARN] Could not fetch DB version: {e}")
            
        print("[INFO] Executing Base.metadata.create_all()...")
        models.Base.metadata.create_all(bind=database.engine)
        print("[INFO] create_all() executed.")
        
        # ZORLA CREATE TABLE (autocommit mode via execution_options)
        print("[INFO] Executing RAW SQL for ohlcv table with isolated isolation_level...")
        with conn.execution_options(isolation_level="AUTOCOMMIT"):
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ohlcv (
                    ticker VARCHAR(50) NOT NULL,
                    interval VARCHAR(10) NOT NULL,
                    date VARCHAR(50) NOT NULL,
                    open FLOAT,
                    high FLOAT,
                    low FLOAT,
                    close FLOAT,
                    adj_close FLOAT,
                    volume BIGINT,
                    PRIMARY KEY (ticker, interval, date)
                )
            """))
            print("[INFO] RAW CREATE TABLE ohlcv executed.")
            
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_ticker_interval_date 
                    ON ohlcv (ticker, interval, date)
                """))
                print("[INFO] RAW CREATE INDEX executed.")
            except Exception as e:
                print(f"[WARN] Failed to create index (might be syntax error on old PG): {e}")
                
        # Tabloları listele
        print("[INFO] Fetching list of tables directly from database...")
        tables = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema='public'
        """)).fetchall()
        print(f"[RESULT] Tables in public schema: {[t[0] for t in tables]}")
    
    # database.py içindeki init_db() de çağrılsın
    database.init_db()

    print("=== MIGRATION COMPLETE ===")

if __name__ == "__main__":
    migrate()
