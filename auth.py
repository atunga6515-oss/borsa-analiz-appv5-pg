import hashlib
import os
import logging
from sqlalchemy import text
from database import engine
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Şifreyi bcrypt ile hashler."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Şifre doğrulaması yapar."""
    return pwd_context.verify(plain_password, hashed_password)

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
                role VARCHAR(20) DEFAULT 'user',
                is_active BOOLEAN DEFAULT TRUE,
                last_active TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Varsayılan admin kullanıcıları üretimi üretim ortamında kapatıldı
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
    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE users SET last_active=NOW() WHERE username=:u"),
                {"u": username},
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


def register_user(username: str, password: str, email: str = "") -> dict:
    """Yeni kullanıcı kaydı."""
    if len(username) < 3:
        return {"ok": False, "error": "Kullanıcı adı en az 3 karakter olmalıdır."}
    if len(password) < 6:
        return {"ok": False, "error": "Şifre en az 6 karakter olmalıdır."}
    try:
        p_hash = hash_password(password)
        with engine.begin() as conn:
            existing = conn.execute(
                text("SELECT username FROM users WHERE username=:u"), {"u": username}
            ).fetchone()
            if existing:
                return {"ok": False, "error": "Bu kullanıcı adı zaten alınmış."}
            conn.execute(
                text(
                    "INSERT INTO users (username, password_hash, email, role) VALUES (:u, :p, :e, 'user')"
                ),
                {"u": username, "p": p_hash, "e": email},
            )
        log_action(username, "REGISTER", "Yeni kullanıcı kaydı")
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
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO system_logs (username, action, details, level) "
                    "VALUES (:u, :a, :d, :l)"
                ),
                {"u": username, "a": action, "d": details, "l": level},
            )
    except Exception as e:
        logging.error(f"log_action hatası: {e}")
