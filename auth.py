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

def update_password(username, new_password) -> bool:
    """Şifre güncelleme."""
    try:
        p_hash = hash_password(new_password)
        with engine.begin() as conn:
            conn.execute(text("UPDATE users SET password_hash=:p WHERE username=:u"), {"p": p_hash, "u": username})
        return True
    except Exception:
        return False
