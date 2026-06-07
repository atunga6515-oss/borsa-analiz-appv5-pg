import os
import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
import google.generativeai as genai
from sqlalchemy import text
from database import engine
from api.auth_routes import get_current_user
from auth import log_action
from limiter import limiter

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
@limiter.limit("10/minute")
def analyze_stock(request: Request, req: AIAnalysisRequest, current_user: str = Depends(get_current_user)):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Anahtarı sunucuda tanımlı değil.")

    today = datetime.date.today().isoformat()

    # 1. Cache kontrolü (kota tüketmeden)
    with engine.connect() as conn:
        history_row = conn.execute(
            text("SELECT result_text, (SELECT ai_quota FROM users WHERE username=:u) as quota FROM ai_analyses_history WHERE username=:u AND ticker=:t AND run_date=:d"),
            {"u": current_user, "t": req.ticker, "d": today}
        ).fetchone()

        if history_row:
            return {
                "status": "success",
                "cached": True,
                "analysis": history_row[0],
                "remaining_quota": history_row[1] or 0
            }

    # 2. Kota rezervasyonu — ATOMIK (Race Condition koruması)
    # UPDATE ... WHERE ai_quota > 0 sadece başarılı olursa 1 satır döner
    with engine.begin() as conn:
        result = conn.execute(
            text("UPDATE users SET ai_quota = ai_quota - 1 WHERE username=:u AND ai_quota > 0 RETURNING ai_quota"),
            {"u": current_user}
        ).fetchone()

        if result is None:
            # ya kullanıcı yok ya da kota 0
            user_exists = conn.execute(
                text("SELECT 1 FROM users WHERE username=:u"), {"u": current_user}
            ).fetchone()
            if not user_exists:
                raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
            raise HTTPException(status_code=403, detail="Yapay Zeka analiz kotanız bitmiştir. Lütfen yöneticinizle iletişime geçin.")

        new_quota = result[0]

    # 3. Generate AI Analysis (DB transaction dışında)
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
        try:
            model = genai.GenerativeModel('gemini-flash-latest')
            response = model.generate_content(
                system_prompt + "\n\n" + user_prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.7)
            )
        except Exception:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(
                system_prompt + "\n\n" + user_prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.7)
            )
        result_text = response.text
    except Exception as e:
        # AI başarısız — kotayı geri ver
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE users SET ai_quota = ai_quota + 1 WHERE username=:u"),
                {"u": current_user}
            )
        log_action(current_user, "AI_ERROR", str(e), level="ERROR")
        raise HTTPException(status_code=500, detail="Yapay Zeka sunucularına bağlanılamadı. Lütfen daha sonra tekrar deneyin.")

    # 4. Geçmişe kaydet
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO ai_analyses_history (username, ticker, run_date, result_text)
                VALUES (:u, :t, :d, :r)
                ON CONFLICT DO NOTHING
            """),
            {"u": current_user, "t": req.ticker, "d": today, "r": result_text}
        )

    log_action(current_user, "AI_ANALYSIS", f"{req.ticker} hissesi için yapay zeka analizi yapıldı. Kalan: {new_quota}")

    return {
        "status": "success",
        "cached": False,
        "analysis": result_text,
        "remaining_quota": new_quota
    }
