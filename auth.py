import hashlib
import os
from sqlalchemy import text
from database import engine

def hash_password(password: str) -> str:
    """Şifreyi SHA-256 ile hashler."""
    return hashlib.sha256(password.encode()).hexdigest()

def init_auth_db():
    """Kullanıcı tablosunu oluşturur ve admin kullanıcılarını tanımlar."""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                username VARCHAR(255) PRIMARY KEY,
                password_hash VARCHAR(255) NOT NULL
            )
        """))
        
        users = ["admin1", "admin2", "admin3"]
        default_pass = hash_password("admin123")
        
        for u in users:
            result = conn.execute(text("SELECT username FROM users WHERE username=:u"), {"u": u}).fetchone()
            if not result:
                conn.execute(text("INSERT INTO users (username, password_hash) VALUES (:u, :p)"), {"u": u, "p": default_pass})

def verify_login(username, password) -> bool:
    """Kullanıcı girişi kontrolü."""
    p_hash = hash_password(password)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT username FROM users WHERE username=:u AND password_hash=:p"), {"u": username, "p": p_hash}).fetchone()
    return result is not None

def register_user(username: str, password: str, email: str = "") -> dict:
    """Yeni kullanıcı kaydı. Başarılıysa True döner."""
    if len(username) < 3:
        return {"ok": False, "error": "Kullanıcı adı en az 3 karakter olmalıdır."}
    if len(password) < 6:
        return {"ok": False, "error": "Şifre en az 6 karakter olmalıdır."}
    try:
        p_hash = hash_password(password)
        with engine.begin() as conn:
            existing = conn.execute(text("SELECT username FROM users WHERE username=:u"), {"u": username}).fetchone()
            if existing:
                return {"ok": False, "error": "Bu kullanıcı adı zaten alınmış."}
            conn.execute(
                text("INSERT INTO users (username, password_hash, email) VALUES (:u, :p, :e)"),
                {"u": username, "p": p_hash, "e": email}
            )
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def update_password(username, new_password) -> bool:
    """Şifre güncelleme."""
    try:
        p_hash = hash_password(new_password)
        with engine.begin() as conn:
            conn.execute(text("UPDATE users SET password_hash=:p WHERE username=:u"), {"p": p_hash, "u": username})
        return True
    except Exception:
        return False
