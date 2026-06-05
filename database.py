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

if not DATABASE_URL:
    raise ValueError("Veritabanı bağlantı dizesi (DATABASE_URL veya DB_USER vb.) bulunamadı. Lütfen .env dosyasını kontrol edin.")

# Render veya Heroku gibi servislerde bazen postgres:// kalabiliyor, sqlalchemy postgresql:// istiyor
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
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
        
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS top_picks_history (
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
