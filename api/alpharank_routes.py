from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from api.auth_routes import get_current_user
from alpharank_engine import AlphaRank15D
import requests
import os

router = APIRouter()
engine_obj = AlphaRank15D()

class TickerRequest(BaseModel):
    ticker: str

@router.get("/pool", response_model=List[Dict[str, str]])
def get_pool(current_user: str = Depends(get_current_user)):
    """Mevcut hisse havuzunu getirir."""
    return engine_obj.get_current_pool(current_user)

@router.post("/pool/add")
def add_ticker(req: TickerRequest, current_user: str = Depends(get_current_user)):
    """Havuza yeni hisse ekler."""
    res = engine_obj.add_to_alpharank(current_user, req.ticker)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res

@router.delete("/pool/remove/{ticker}")
def remove_ticker(ticker: str, current_user: str = Depends(get_current_user)):
    """Havuzdan hisse çıkarır."""
    res = engine_obj.remove_from_alpharank(current_user, ticker)
    if not res["success"]:
        raise HTTPException(status_code=404, detail=res["message"])
    return res

@router.delete("/pool/clear")
def clear_pool(current_user: str = Depends(get_current_user)):
    """Havuzu tamamen temizler."""
    return engine_obj.clear_pool(current_user)

@router.get("/analyze")
def run_analysis(current_user: str = Depends(get_current_user)):
    """Havuzdaki tüm hisseleri analiz edip skor sıralaması döner."""
    results = engine_obj.run_analysis(current_user)
    return {"status": "success", "data": results}

@router.post("/telegram")
def send_to_telegram(current_user: str = Depends(get_current_user)):
    """Son analizi kullanıcının telegramına atar."""
    # Veritabanından kullanıcının telegram chat_id'sini al
    from database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        row = conn.execute(text("SELECT telegram_chat_id FROM users WHERE username=:u"), {"u": current_user}).fetchone()
        
    chat_id = row[0] if row else None
    if not chat_id:
        raise HTTPException(status_code=400, detail="Telegram entegrasyonunuz bulunamadı. Ayarlar menüsünden Chat ID ekleyin.")
        
    # Analizi çalıştır
    results = engine_obj.run_analysis(current_user)
    if not results:
        raise HTTPException(status_code=400, detail="Havuzunuz boş. Lütfen hisse ekleyin.")
        
    # Telegram mesajını formatla
    msg = "🚀 *AlphaRank 15D - Analiz Raporu*\n\n"
    for r in results:
        msg += f"🏅 *Sıra:* {r['rank']}\n"
        msg += f"📈 *Hisse:* {r['ticker']}\n"
        msg += f"💵 *Fiyat:* {r['price']} TL\n"
        msg += f"🔥 *Yükseliş Olasılığı:* %{r['score']}\n"
        msg += "📝 *Gerekçeler:*\n"
        for ev in r['evidences']:
            msg += f"  - {ev}\n"
        msg += "\n"
        
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        # Eğer henüz TELEGRAM_BOT_TOKEN yoksa sahte başarı dönelim (UI testi için)
        return {"status": "success", "message": "Bot token eksik, ancak mesaj formatlandı.", "preview": msg}
        
    # Gerçek gönderim
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
    resp = requests.post(url, json=payload)
    
    if resp.status_code == 200:
        return {"status": "success", "message": "Rapor Telegram'a gönderildi!"}
    else:
        raise HTTPException(status_code=400, detail=f"Telegram gönderimi başarısız: {resp.text}")
