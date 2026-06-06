import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME')
safe_password = urllib.parse.quote_plus(db_password)
DATABASE_URL = f'postgresql://{db_user}:{safe_password}@{db_host}:{db_port}/{db_name}'

engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    # 1. Eksik sütunları tabloya ekle
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR DEFAULT '';"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'user';"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_active TIMESTAMP;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))
        print("✅ Tablo sütunları güncellendi.")
    except Exception as e:
        print("Tablo güncellemesinde hata:", e)

    # 2. user_alarms tablosunu kontrol et
    try:
        conn.execute(text("ALTER TABLE user_alarms ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'active';"))
    except Exception:
        pass

    # 3. admin1 harici kullanıcıları sil
    try:
        # Önce onların alarmlarını sil (Foreign key hatası almamak için)
        conn.execute(text("DELETE FROM user_alarms WHERE username != 'admin1';"))
        # Sonra kullanıcıları sil
        res = conn.execute(text("DELETE FROM users WHERE username != 'admin1';"))
        print("✅ admin1 haricindeki diğer kullanıcılar silindi.")
    except Exception as e:
        print("Kullanıcıları silerken hata:", e)

print("İşlem tamam!")
