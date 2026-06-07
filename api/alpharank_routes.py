from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from api.auth_routes import get_current_user
from alpharank_engine import AlphaRank15D
import requests
import os
import json
from datetime import datetime
from database import engine
from sqlalchemy import text

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
def run_analysis_endpoint(current_user: str = Depends(get_current_user)):
    """Havuzdaki tüm hisseleri analiz edip skor sıralaması döner ve veritabanına kaydeder."""
    results = engine_obj.run_analysis(current_user)
    
    if results:
        # Geçmişe kaydet
        run_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO alpharank_history (username, run_date, results_json)
                    VALUES (:u, :d, :r)
                """), {
                    "u": current_user,
                    "d": run_date,
                    "r": json.dumps(results, ensure_ascii=False)
                })
        except Exception as e:
            print(f"History save error: {e}")
            
    return {"status": "success", "data": results}

@router.get("/history-dates")
def get_history_dates(current_user: str = Depends(get_current_user)):
    """Geçmiş son 15 AlphaRank taramasının tarihlerini getirir."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT id, run_date 
            FROM alpharank_history 
            WHERE username = :u 
            ORDER BY id DESC LIMIT 15
        """), {"u": current_user}).fetchall()
        
    dates = [{"id": r[0], "run_date": r[1]} for r in rows]
    return {"status": "success", "dates": dates}

@router.get("/history/{history_id}")
def get_history_detail(history_id: int, current_user: str = Depends(get_current_user)):
    """Belirli bir geçmiş taramanın detaylarını getirir."""
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT results_json 
            FROM alpharank_history 
            WHERE id = :h_id AND username = :u
        """), {"h_id": history_id, "u": current_user}).fetchone()
        
    if not row:
        raise HTTPException(status_code=404, detail="Geçmiş analiz bulunamadı veya size ait değil.")
        
    try:
        data = json.loads(row[0])
        return {"status": "success", "data": data}
    except:
        return {"status": "error", "message": "JSON parse error"}

@router.post("/telegram")
def send_to_telegram(current_user: str = Depends(get_current_user)):
    """Son analizi kullanıcının telegramına atar."""
    # Veritabanından kullanıcının telegram chat_id'sini al
    with engine.connect() as conn:
        row = conn.execute(text("SELECT telegram_chat_id FROM users WHERE username=:u"), {"u": current_user}).fetchone()
        
    chat_id = row[0] if row else None
    if not chat_id:
        raise HTTPException(status_code=400, detail="Telegram entegrasyonunuz bulunamadı. Ayarlar menüsünden Chat ID ekleyin.")
        
    # Son analizi veritabanından al (yeniden çalıştırıp vakit kaybetmemek için)
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT results_json 
            FROM alpharank_history 
            WHERE username = :u 
            ORDER BY id DESC LIMIT 1
        """), {"u": current_user}).fetchone()
        
    if not row:
        raise HTTPException(status_code=400, detail="Önce bir analiz yapmanız gerekmektedir.")
        
    try:
        results = json.loads(row[0])
    except:
        raise HTTPException(status_code=400, detail="Analiz sonuçları okunamadı.")
        
    if not results:
        raise HTTPException(status_code=400, detail="Havuzunuz boş. Lütfen hisse ekleyin.")
        
    # Telegram mesajını formatla (HTML kullanarak Markdown parsing hatalarını önleyelim)
    msg = "🚀 <b>AlphaRank 15D - Analiz Raporu</b>\n\n"
    for r in results:
        msg += f"🏅 <b>Sıra:</b> {r['rank']}\n"
        msg += f"📈 <b>Hisse:</b> {r['ticker']}\n"
        msg += f"💵 <b>Fiyat:</b> {r['price']} TL\n"
        msg += f"🔥 <b>Yükseliş Olasılığı:</b> %{r['score']}\n"
        msg += "📝 <b>Gerekçeler:</b>\n"
        for ev in r['evidences']:
            # Replace angle brackets to avoid breaking HTML
            ev_clean = str(ev).replace("<", "&lt;").replace(">", "&gt;")
            msg += f"  - {ev_clean}\n"
        msg += "\n"
        
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        # Eğer henüz TELEGRAM_BOT_TOKEN yoksa sahte başarı dönelim (UI testi için)
        return {"status": "success", "message": "Bot token eksik, ancak mesaj formatlandı.", "preview": msg}
        
    # Eğer metin 4000 karakterden uzunsa Telegram sınırına (4096) takılmamak için kırpalım.
    if len(msg) > 4000:
        msg = msg[:4000] + "\n\n<i>...Mesaj çok uzun olduğu için kesildi.</i>"

    # Gerçek gönderim
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}
    resp = requests.post(url, json=payload)
    
    if resp.status_code == 200:
        return {"status": "success", "message": "Rapor Telegram'a gönderildi!"}
    else:
        raise HTTPException(status_code=400, detail=f"Telegram gönderimi başarısız: {resp.text}")
