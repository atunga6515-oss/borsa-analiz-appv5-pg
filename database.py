import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/borsa_v5")

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
    # Bu fonksiyon tablo modelleri import edildikten sonra çağrılacak
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
