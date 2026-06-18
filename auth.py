import hashlib
import os
import logging
from sqlalchemy import text
from database import engine
import bcrypt

def hash_password(password: str) -> str:
    """Şifreyi bcrypt ile hashler."""
    pwd_bytes = password.encode('utf-8')
    if len(pwd_bytes) > 72:
        pwd_bytes = pwd_bytes[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Şifre doğrulaması yapar."""
    pwd_bytes = plain_password.encode('utf-8')
    if len(pwd_bytes) > 72:
        pwd_bytes = pwd_bytes[:72]
    try:
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode('utf-8'))
    except Exception:
        return False

def hash_password_legacy(password: str) -> str:
    """Eski sistem için SHA-256 hashler."""
    return hashlib.sha256(password.encode()).hexdigest()


def init_auth_db():
    """Kullanıcı tablosunu oluşturur ve admin kullanıcılarını tanımlar."""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                username VARCHAR(255) PRIMARY KEY,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                phone VARCHAR(50),
                role VARCHAR(20) DEFAULT 'user',
                is_active BOOLEAN DEFAULT TRUE,
                last_active TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                subscription_expires_at TIMESTAMP,
                ai_quota INT DEFAULT 0
            )
        """))

        # Sistem ayarları tablosu
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS system_settings (
                key VARCHAR(255) PRIMARY KEY,
                value TEXT
            )
        """))

        # Mevcut veritabanında phone ve subscription kolonu yoksa ekle (Migration)
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(255)"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(50)"))
        except Exception:
            pass  # Zaten varsa hata verecek ve geçecek
            
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN subscription_expires_at TIMESTAMP"))
        except Exception:
            pass
            
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))
        except Exception:
            pass
            
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN last_active TIMESTAMP"))
        except Exception:
            pass

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'"))
        except Exception:
            pass

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN ai_quota INT DEFAULT 0"))
        except Exception:
            pass        # Varsayılan admin kullanıcıları üretimi üretim ortamında kapatıldı
        # İlk admin kullanıcısının doğrudan veritabanı komutu veya güvenli bir CLI scripti ile oluşturulması önerilir.


def get_user_role(username: str) -> str:
    """Kullanıcının rolünü döndürür. Bulunamazsa 'user' döner."""
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT role FROM users WHERE username=:u"), {"u": username}
            ).fetchone()
        return row[0] if row and row[0] else "user"
    except Exception:
        return "user"


def get_user_quota(username: str) -> int:
    """Kullanıcının AI kotasını döndürür. Bulunamazsa 0 döner."""
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT ai_quota FROM users WHERE username=:u"), {"u": username}
            ).fetchone()
        return row[0] if row and row[0] is not None else 0
    except Exception:
        return 0


def touch_last_active(username: str):
    """Kullanıcının son aktif zamanını günceller."""
    from datetime import datetime
    import pytz
    TR_TZ = pytz.timezone("Europe/Istanbul")
    now_str = datetime.now(TR_TZ).strftime('%Y-%m-%d %H:%M:%S')
    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE users SET last_active=:n WHERE username=:u"),
                {"u": username, "n": now_str},
            )
    except Exception:
        pass


def verify_login(username: str, password: str) -> bool:
    """Kullanıcı girişi kontrolü ve bcrypt geçiş mekanizması."""
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT username, password_hash, is_active FROM users WHERE username=:u"
            ),
            {"u": username},
        ).fetchone()

    if not result:
        return False
        
    _, db_hash, is_active = result
    
    if not is_active:
        return False
        
    # Check if hash is bcrypt (typically starts with $2b$, $2a$ or $2y$)
    if db_hash.startswith("$2b$") or db_hash.startswith("$2a$") or db_hash.startswith("$2y$"):
        return verify_password(password, db_hash)
    else:
        # Check legacy SHA-256
        legacy_hash = hash_password_legacy(password)
        if legacy_hash == db_hash:
            # Upgrade to bcrypt immediately
            new_hash = hash_password(password)
            try:
                with engine.begin() as conn_update:
                    conn_update.execute(
                        text("UPDATE users SET password_hash=:p WHERE username=:u"),
                        {"p": new_hash, "u": username}
                    )
            except Exception as e:
                logging.error(f"Failed to upgrade password hash for {username}: {e}")
            return True
            
    return False


from datetime import datetime, timedelta

def register_user(username: str, password: str, email: str = "") -> dict:
    """Yeni kullanıcı kaydı."""
    if len(username) < 3:
        return {"ok": False, "error": "Kullanıcı adı en az 3 karakter olmalıdır."}
    if len(password) < 6:
        return {"ok": False, "error": "Şifre en az 6 karakter olmalıdır."}
    try:
        p_hash = hash_password(password)
        expires_at = datetime.utcnow() + timedelta(days=30)
        with engine.begin() as conn:
            existing = conn.execute(
                text("SELECT username FROM users WHERE username=:u"), {"u": username}
            ).fetchone()
            if existing:
                return {"ok": False, "error": "Bu kullanıcı adı zaten alınmış."}
            
            # SQLite ve Postgres uyumluluğu için datetime objesini string'e çevirmiyoruz, DB api halleder
            conn.execute(
                text(
                    "INSERT INTO users (username, password_hash, email, role, subscription_expires_at) VALUES (:u, :p, :e, 'user', :exp)"
                ),
                {"u": username, "p": p_hash, "e": email, "exp": expires_at},
            )
        log_action(username, "REGISTER", "Yeni kullanıcı kaydı (30 Gün Abonelik)")
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": "Kayıt sırasında beklenmeyen bir hata oluştu."}


def update_password(username: str, new_password: str) -> bool:
    """Şifre güncelleme."""
    try:
        p_hash = hash_password(new_password)
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE users SET password_hash=:p WHERE username=:u"),
                {"p": p_hash, "u": username},
            )
        return True
    except Exception:
        return False


def log_action(username: str, action: str, details: str = "", level: str = "INFO"):
    """system_logs tablosuna kayıt ekler."""
    from datetime import datetime
    import pytz
    TR_TZ = pytz.timezone("Europe/Istanbul")
    now_str = datetime.now(TR_TZ).strftime('%Y-%m-%d %H:%M:%S')
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO system_logs (username, action, details, level, created_at) "
                    "VALUES (:u, :a, :d, :l, :c)"
                ),
                {"u": username, "a": action, "d": details, "l": level, "c": now_str},
            )
    except Exception as e:
        logging.error(f"log_action hatası: {e}")
