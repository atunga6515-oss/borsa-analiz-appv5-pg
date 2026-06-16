import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# .env dosyasındaki değişkenleri sisteme yükle
load_dotenv()

# .env üzerinden parçalı okuma
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME")

if db_user and db_password and db_host and db_name:
    # Kritik Güvenlik: Şifredeki ^, @, & gibi özel karakterleri güvenli url formatına dönüştürür
    safe_password = urllib.parse.quote_plus(db_password)
    DATABASE_URL = f"postgresql://{db_user}:{safe_password}@{db_host}:{db_port}/{db_name}"
else:
    # Fallback olarak doğrudan DATABASE_URL değişkenini kullan
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # KULLANICI HATASINI TESPİT ET (Şifrede @ varsa SQLAlchemy patlar)
    if DATABASE_URL and DATABASE_URL.startswith("postgres"):
        if DATABASE_URL.count("@") > 1:
            raise ValueError(
                "\n\n[KRITIK HATA]: .env dosyasında DATABASE_URL kullanmışsınız ancak şifrenizin içinde "
                "'@' işareti (veya benzeri özel karakterler) bulunuyor. Bu durum veritabanı sürücüsünün "
                "sunucu adresini (localhost) yanlış anlamasına neden oluyor.\n"
                "LÜTFEN .env dosyanızı şu şekilde DÜZELTİN (DATABASE_URL satırını SİLİN):\n"
                "DB_USER=kullaniciadi\n"
                "DB_PASSWORD=sifreniz\n"
                "DB_HOST=localhost\n"
                "DB_PORT=5432\n"
                "DB_NAME=alfabist_db\n\n"
            )

if not DATABASE_URL:
    raise ValueError("Veritabanı bağlantı dizesi (DATABASE_URL veya DB_USER vb.) bulunamadı. Lütfen .env dosyasını kontrol edin.")

# Render veya Heroku gibi servislerde bazen postgres:// kalabiliyor, sqlalchemy postgresql:// istiyor
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL, 
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=1800  # 30 dakikada bir bağlantıyı yenile (uzun idle bağlantı hatası önleme)
    )
else:
    raise ValueError("Lütfen geçerli bir PostgreSQL bağlantı dizesi kullanın.")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from sqlalchemy import text
    import models  # Modellerin metadata'ya register olması için import ediyoruz
    
    # Tüm tabloları oluşturur (Ohlcv, Portfolio, vs.)
    Base.metadata.create_all(bind=engine)
    
    # Raw SQL tablolari icin CREATE IF NOT EXISTS (SQLite / Postgres uyumlu)
    is_pg = engine.name == "postgresql"
    serial_type = "SERIAL" if is_pg else "INTEGER"
    
    with engine.begin() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS watchlist (
                id {serial_type} PRIMARY KEY,
                username VARCHAR(255),
                ticker VARCHAR(20),
                added_date VARCHAR(50),
                note TEXT
            )
        """))
        
        # Kesin çözüm: ohlcv tablosunu RAW SQL ile yaratmak
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
        
        # İndeks (PostgreSQL ve SQLite uyumlu IF NOT EXISTS formati)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ticker_interval_date 
            ON ohlcv (ticker, interval, date)
        """))
        
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS top_picks_history (
                id {serial_type} PRIMARY KEY,
                username VARCHAR(255),
                run_date VARCHAR(50),
                results_json TEXT
            )
        """))
        
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS top_picks_15d_history (
                id {serial_type} PRIMARY KEY,
                username VARCHAR(255),
                run_date VARCHAR(50),
                results_json TEXT
            )
        """))
        
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS screener_history (
                id {serial_type} PRIMARY KEY,
                username VARCHAR(255),
                run_date VARCHAR(50),
                results_json TEXT
            )
        """))
        
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id {serial_type} PRIMARY KEY,
                username VARCHAR(255),
                ticker VARCHAR(20),
                run_date VARCHAR(50),
                results_json TEXT
            )
        """))
        
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS alpharank_pool (
                id {serial_type} PRIMARY KEY,
                username VARCHAR(255),
                ticker VARCHAR(20),
                added_at VARCHAR(50),
                UNIQUE (username, ticker)
            )
        """))
        
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS alpharank_history (
                id {serial_type} PRIMARY KEY,
                username VARCHAR(255),
                run_date VARCHAR(50),
                results_json TEXT
            )
        """))
        
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS portfolio (
                id {serial_type} PRIMARY KEY,
                username VARCHAR(255),
                ticker VARCHAR(20),
                adet FLOAT,
                alis_fiyati FLOAT,
                alis_tarihi VARCHAR(50),
                satis_fiyati FLOAT,
                satis_tarihi VARCHAR(50),
                durum VARCHAR(20),
                not_text TEXT,
                sl FLOAT,
                tp FLOAT,
                var FLOAT
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                username VARCHAR(255) PRIMARY KEY,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS user_alarms (
                id {serial_type} PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                ticker VARCHAR(20) NOT NULL,
                condition VARCHAR(50) NOT NULL,
                target_value FLOAT NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                triggered_at TIMESTAMP
            )
        """))

        # users tablosuna role, is_active, last_active, ai_quota, abonelik, telefon ve email alanları ekle (migration)
        for col_def in [
            ("email",       "VARCHAR(255)"),
            ("created_at",  "TIMESTAMP    DEFAULT CURRENT_TIMESTAMP"),
            ("role",        "VARCHAR(20)  DEFAULT 'user'"),
            ("is_active",   "BOOLEAN      DEFAULT TRUE"),
            ("last_active", "TIMESTAMP"),
            ("ai_quota",    "INTEGER      DEFAULT 5"),
            ("subscription_expires_at", "TIMESTAMP"),
            ("phone_number", "VARCHAR(20)"),
            ("telegram_chat_id", "VARCHAR(100)"),
        ]:
            col_name, col_type = col_def
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
            except Exception:
                pass  # Sütun zaten varsa atla (SQLite IF NOT EXISTS desteklemez)

        # scan_history tablosuna smc_bos ve intermediate_target alanlarını ekle (migration)
        for col_def in [
            ("smc_bos", "VARCHAR(50)"),
            ("intermediate_target", "FLOAT"),
        ]:
            col_name, col_type = col_def
            try:
                conn.execute(text(f"ALTER TABLE scan_history ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
            except Exception:
                pass

        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS system_logs (
                id {serial_type} PRIMARY KEY,
                username   VARCHAR(255),
                action     VARCHAR(255)  NOT NULL,
                details    TEXT,
                level      VARCHAR(20)   DEFAULT 'INFO',
                created_at TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
            )
        """))

        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS ai_analyses_history (
                id {serial_type} PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                ticker VARCHAR(20) NOT NULL,
                run_date VARCHAR(50) NOT NULL,
                result_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (username, ticker, run_date)
            )
        """))

        # --- ROBOT (PAPER TRADING) MODÜLÜ TABLOLARI ---
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS robot_sessions (
                id {serial_type} PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP NOT NULL,
                initial_balance FLOAT NOT NULL,
                current_balance FLOAT NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                mode VARCHAR(20) DEFAULT 'Normal',
                max_positions INTEGER DEFAULT 5
            )
        """))

        # Mevcut robot_sessions tablosuna mode ve max_positions eklenecek (migration)
        for col_def in [
            ("mode", "VARCHAR(20) DEFAULT 'Normal'"),
            ("max_positions", "INTEGER DEFAULT 5")
        ]:
            col_name, col_type = col_def
            try:
                conn.execute(text(f"ALTER TABLE robot_sessions ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
            except Exception:
                pass

        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS robot_watchlist (
                id {serial_type} PRIMARY KEY,
                ticker VARCHAR(20) NOT NULL,
                vote_strength FLOAT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (ticker)
            )
        """))

        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS robot_portfolio (
                id {serial_type} PRIMARY KEY,
                session_id INTEGER NOT NULL,
                ticker VARCHAR(20) NOT NULL,
                adet FLOAT NOT NULL,
                alis_fiyati FLOAT NOT NULL,
                alis_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (session_id, ticker)
            )
        """))

        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS robot_trades (
                id {serial_type} PRIMARY KEY,
                session_id INTEGER NOT NULL,
                ticker VARCHAR(20) NOT NULL,
                type VARCHAR(10) NOT NULL,
                price FLOAT NOT NULL,
                adet FLOAT NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reason TEXT
            )
        """))
        # ----------------------------------------------

        # system_logs için index (sorgular hızlı olsun)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_system_logs_created
            ON system_logs (created_at DESC)
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS system_settings (
                key VARCHAR(100) PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bist_symbols (
                symbol VARCHAR(20) PRIMARY KEY,
                name VARCHAR(255),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # ai_analyses_history UNIQUE constraint (sadece PostgreSQL için)
        if engine.name == "postgresql":
            conn.execute(text("""
                DO $$ BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint 
                        WHERE conname = 'ai_analyses_history_username_ticker_run_date_key'
                        AND conrelid = 'ai_analyses_history'::regclass
                    ) THEN
                        ALTER TABLE ai_analyses_history 
                        ADD CONSTRAINT ai_analyses_history_username_ticker_run_date_key 
                        UNIQUE (username, ticker, run_date);
                    END IF;
                EXCEPTION WHEN undefined_table THEN NULL;
                END $$;
            """))

