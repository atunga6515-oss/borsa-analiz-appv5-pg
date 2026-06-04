import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_telegram_report(text: str) -> dict:
    """
    .env içindeki token ve chat_id bilgilerini kullanarak 
    Telegram üzerinden Markdown formatında rapor gönderir.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        return {"success": False, "message": "Telegram API bilgileri (TOKEN/CHAT_ID) .env içinde eksik!"}
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return {"success": True, "message": "Gönderim başarılı"}
        else:
            return {"success": False, "message": f"Telegram Hatası: {response.text}"}
    except Exception as e:
        return {"success": False, "message": f"Telegram Bağlantı Hatası: {str(e)}"}
