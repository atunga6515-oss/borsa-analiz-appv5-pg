import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import engine
from sqlalchemy import text
import logging

def get_setting(key: str, default=""):
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT value FROM system_settings WHERE key=:k"), {"k": key}).fetchone()
            return row[0] if row else default
    except Exception:
        return default

def send_subscription_warning_email(to_email: str, username: str, days_left: int):
    """Kullanıcıya abonelik süresi uyarısı gönderir."""
    if not to_email:
        return False
        
    smtp_server = get_setting("smtp_server", "smtp.gmail.com")
    smtp_port = int(get_setting("smtp_port", "587"))
    smtp_user = get_setting("smtp_user", "")
    smtp_pass = get_setting("smtp_password", "")
    
    if not smtp_user or not smtp_pass:
        logging.warning("SMTP ayarları eksik. Mail gönderilemedi.")
        return False
        
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = f"Borsa Terminali - Abonelik Süreniz {days_left} Gün Sonra Bitiyor"
    
    body = f"""Merhaba {username},

Borsa Terminali aboneliğinizin bitmesine sadece {days_left} gün kaldı. 
Kesintisiz hizmet almaya devam etmek için aboneliğinizi yenilemeyi unutmayın.

Teşekkürler,
Borsa Terminali Ekibi
"""
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        logging.info(f"Uyarı maili gönderildi: {to_email}")
        return True
    except Exception as e:
        logging.error(f"Mail gönderme hatası ({to_email}): {e}")
        return False
