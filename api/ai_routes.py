import os
import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from sqlalchemy import text
from database import engine
from api.auth_routes import get_current_user
from auth import log_action

router = APIRouter(prefix="/api/ai", tags=["ai"])

# Load Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class AIAnalysisRequest(BaseModel):
    ticker: str
    price: float
    rsi: float = None
    macd_signal: str = None
    trend: str = None
    note: str = ""

@router.post("/analyze")
def analyze_stock(req: AIAnalysisRequest, current_user: str = Depends(get_current_user)):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Anahtarı sunucuda tanımlı değil.")

    today = datetime.date.today().isoformat()

    with engine.begin() as conn:
        # 1. Quota Check
        user_row = conn.execute(
            text("SELECT ai_quota FROM users WHERE username=:u"), 
            {"u": current_user}
        ).fetchone()
        
        if not user_row:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
        
        current_quota = user_row[0] or 0

        # 2. Check History (Cache)
        history_row = conn.execute(
            text("SELECT result_text FROM ai_analyses_history WHERE username=:u AND ticker=:t AND run_date=:d"),
            {"u": current_user, "t": req.ticker, "d": today}
        ).fetchone()

        if history_row:
            # Already analyzed today, return cached result without consuming quota
            return {
                "status": "success",
                "cached": True,
                "analysis": history_row[0],
                "remaining_quota": current_quota
            }

        if current_quota <= 0:
            raise HTTPException(status_code=403, detail="Yapay Zeka analiz kotanız bitmiştir. Lütfen yöneticinizle iletişime geçin.")

        # 3. Generate AI Analysis
        system_prompt = (
            "Sen kıdemli bir BIST (Borsa İstanbul) Portföy Yöneticisi ve teknik analistsin. "
            "Kullanıcıya teknik veriler sunulacak. Lütfen kurumsal bir dille, Markdown formatında, "
            "kısa ama doyurucu bir şekilde şu 3 başlık altında yorum yap:\n"
            "1. **Teknik Görünüm** (Verilen RSI, MACD ve teknik parametrelerin özeti)\n"
            "2. **Risk/Ödül Analizi** (Mevcut seviyeye göre potansiyel destek ve direnç risk değerlendirmesi)\n"
            "3. **Broker Strateji Notu** (Kısa veya orta vadeli net bir aksiyon önerisi)\n\n"
            "Son olarak, en alta çok küçük puntolarla (*italik* ve küçük boyutta) şu yasal uyarıyı kesinlikle ekle: "
            "'Burada yer alan yatırım bilgi, yorum ve tavsiyeleri yatırım danışmanlığı kapsamında değildir (YTD).'"
        )

        user_prompt = f"""
        Hisse: {req.ticker}
        Mevcut Fiyat: {req.price}
        RSI: {req.rsi if req.rsi is not None else 'Bilinmiyor'}
        MACD Sinyali: {req.macd_signal if req.macd_signal else 'Bilinmiyor'}
        Trend Durumu: {req.trend if req.trend else 'Bilinmiyor'}
        Ek Notlar: {req.note}
        """

        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(
                system_prompt + "\n\n" + user_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                )
            )
            result_text = response.text
        except Exception as e:
            log_action(current_user, "AI_ERROR", str(e), level="ERROR")
            raise HTTPException(status_code=500, detail="Yapay Zeka sunucularına bağlanılamadı.")

        # 4. Save History and Deduct Quota
        conn.execute(
            text("""
                INSERT INTO ai_analyses_history (username, ticker, run_date, result_text)
                VALUES (:u, :t, :d, :r)
            """),
            {"u": current_user, "t": req.ticker, "d": today, "r": result_text}
        )

        new_quota = current_quota - 1
        conn.execute(
            text("UPDATE users SET ai_quota=:q WHERE username=:u"),
            {"q": new_quota, "u": current_user}
        )

    log_action(current_user, "AI_ANALYSIS", f"{req.ticker} hissesi için yapay zeka analizi yapıldı. Kalan: {new_quota}")

    return {
        "status": "success",
        "cached": False,
        "analysis": result_text,
        "remaining_quota": new_quota
    }
