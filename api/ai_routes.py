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

from typing import Optional

class AIAnalysisRequest(BaseModel):
    ticker: str
    price: float
    rsi: Optional[float] = None
    macd_signal: Optional[str] = None
    trend: Optional[str] = None
    note: Optional[str] = ""

@router.post("/analyze")
@limiter.limit("10/minute")
def analyze_stock(request: Request, req: AIAnalysisRequest, current_user: str = Depends(get_current_user)):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Anahtarı sunucuda tanımlı değil.")

    today = datetime.date.today().isoformat()

    # AI analizlerinde Cache (Önbellek) özelliği kaldırıldı. 
    # Kullanıcının kotası varsa her zaman canlı, güncel piyasa verisine göre yepyeni analiz istenir.

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

    # Kullanıcıdan gelen bazı veriler eksik olabileceği için (RSI vs.), arka planda o hisseye anlık derin analiz atıyoruz
    # Sentiment false yapıyoruz ki AI kendi içinde bir daha Gemini API'ye gidip haber özeti sormasın (hız ve kota için)
    try:
        from core.analysis_service import run_deep_analysis
        deep_data = run_deep_analysis(req.ticker, include_sentiment=False)
        
        if deep_data.get("status") == "success":
            d = deep_data.get("data", {})
            ssot = d.get("ssot_result", {})
            indicators = d.get("indicators", {})
            
            # Use dynamic live data
            dynamic_price = d.get("current_price", req.price)
            dynamic_rsi = indicators.get("RSI", req.rsi)
            dynamic_macd = indicators.get("MACD_Signal", req.macd_signal)
            dynamic_trend = ssot.get("decision", req.trend)
            
            # Ekstra zengin veriler:
            smc = d.get("market_structure", {})
            sr_data = d.get("support_resistance", {})
            takas_info = d.get("takas_info", {})

            bos_detected = smc.get("bos_detected", False)
            last_peak = smc.get("last_peak")
            last_trough = smc.get("last_trough")

            bos_text = "Tespit Edildi (Kırılım Var)" if bos_detected else "Yok"
            peak_text = f"Tepe: {last_peak:.2f}" if last_peak else "Bilinmiyor"
            trough_text = f"Dip: {last_trough:.2f}" if last_trough else "Bilinmiyor"

            # Destek/Direnç: calculate_best_zones -> best_buy_zones / best_sell_zones = [(ad, fiyat), ...]
            buy_zones = sr_data.get("best_buy_zones") or []
            sell_zones = sr_data.get("best_sell_zones") or []
            destek_text = f"{buy_zones[0][1]:.2f}" if buy_zones else "Bilinmiyor"
            direnc_text = f"{sell_zones[0][1]:.2f}" if sell_zones else "Bilinmiyor"

            fr_ratio = takas_info.get("foreign_ratio", "Bilinmiyor")
            fr_change = takas_info.get("daily_change", "Bilinmiyor")

            user_prompt = f"""
            Hisse: {req.ticker}
            Mevcut Fiyat: {dynamic_price}
            RSI (14): {dynamic_rsi if dynamic_rsi is not None else 'Bilinmiyor'}
            MACD Sinyali: {dynamic_macd if dynamic_macd is not None else 'Bilinmiyor'}
            Trend Durumu ve Algoritma Kararı: {dynamic_trend if dynamic_trend else 'Bilinmiyor'}

            Önemli Seviyeler:
            - Destek: {destek_text}
            - Direnç: {direnc_text}

            SMC (Akıllı Para Konsepti):
            - Son Kırılım (BOS): {bos_text}
            - En Yakın Zirve (Likit): {peak_text}
            - En Yakın Dip (Likit): {trough_text}

            Yabancı Oranı ve Değişim:
            - Yabancı Oranı: %{fr_ratio}
            - Son Değişim: %{fr_change}

            Ek Notlar: {req.note}
            """
        else:
            # Fallback to frontend request data if error fetching
            raise Exception("Deep analysis failed")
    except Exception:
        # Fallback
        user_prompt = f"""
        Hisse: {req.ticker}
        Mevcut Fiyat: {req.price}
        RSI: {req.rsi if req.rsi is not None else 'Bilinmiyor'}
        MACD Sinyali: {req.macd_signal if req.macd_signal else 'Bilinmiyor'}
        Trend Durumu: {req.trend if req.trend else 'Bilinmiyor'}
        Ek Notlar: {req.note}
        """

    try:
        model_names = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
        response = None
        last_error = None
        
        for m_name in model_names:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(
                    system_prompt + "\n\n" + user_prompt,
                    generation_config=genai.types.GenerationConfig(temperature=0.7)
                )
                break  # If successful, exit the loop
            except Exception as e:
                last_error = e
                continue
                
        if response is None:
            raise last_error

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

    # 4. Geçmişe kaydet (Eğer o gün ilk defa yapılıyorsa insert eder, varsa en güncel analizle değiştirir)
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO ai_analyses_history (username, ticker, run_date, result_text)
                VALUES (:u, :t, :d, :r)
                ON CONFLICT (username, ticker, run_date) 
                DO UPDATE SET result_text = EXCLUDED.result_text
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

from api.analysis_routes import get_layered_data
import json

class AIAnalysisRequestLayered(BaseModel):
    ticker: str
    active_indicators: list[str] = []

@router.post("/analyze-indicators")
@limiter.limit("10/minute")
def analyze_indicators_endpoint(request: Request, req: AIAnalysisRequestLayered, current_user: str = Depends(get_current_user)):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Anahtarı sunucuda tanımlı değil. Lütfen .env dosyasına GEMINI_API_KEY ekleyin.")

    # 1. Kota rezervasyonu — ATOMIK (Race Condition koruması)
    with engine.begin() as conn:
        result = conn.execute(
            text("UPDATE users SET ai_quota = ai_quota - 1 WHERE username=:u AND ai_quota > 0 RETURNING ai_quota"),
            {"u": current_user}
        ).fetchone()

        if result is None:
            user_exists = conn.execute(
                text("SELECT 1 FROM users WHERE username=:u"), {"u": current_user}
            ).fetchone()
            if not user_exists:
                raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
            raise HTTPException(status_code=403, detail="Yapay Zeka analiz kotanız bitmiştir. Lütfen yöneticinizle iletişime geçin.")

        new_quota = result[0]

    try:
        raw_data = get_layered_data(req.ticker)
        
        candles = raw_data["candles"]
        layers = raw_data["layers"]
        latest_candle = candles[-1] if candles else {}
        
        indicator_texts = []
        if "supertrend" in req.active_indicators:
            latest_supertrend = layers["supertrend"][-1] if layers.get("supertrend") else {"color": "unknown"}
            indicator_texts.append(f"- SuperTrend Durumu: Line color is {latest_supertrend.get('color')} (yeşil ise boğa, kırmızı ise ayı)")
            
        if "squeeze" in req.active_indicators:
            latest_squeeze = layers["squeeze"][-1] if layers.get("squeeze") else {"value": 0, "dot_color": "unknown"}
            indicator_texts.append(f"- Squeeze Momentum: Value={latest_squeeze.get('value')}, Dot status={latest_squeeze.get('dot_color')} (red/orange ise sıkışma var, green ise patlama başladı)")
            
        if "wavetrend" in req.active_indicators:
            latest_wavetrend = layers["wavetrend"][-1] if layers.get("wavetrend") else {"wt1": 0, "wt2": 0}
            indicator_texts.append(f"- WaveTrend Osilatörü: WT1={latest_wavetrend.get('wt1')}, WT2={latest_wavetrend.get('wt2')} (-60 altı dip, +60 üstü tepe kesişimidir)")
            
        if "adxDmi" in req.active_indicators:
            latest_adx = layers["adx_dmi"][-1] if layers.get("adx_dmi") else {"adx": 20, "plus_di": 20, "minus_di": 20}
            indicator_texts.append(f"- ADX & DMI Trend Gücü: ADX={latest_adx.get('adx')}, +DI={latest_adx.get('plus_di')}, -DI={latest_adx.get('minus_di')} (ADX > 25 ise trend güçlüdür)")
            
        if "stochRSI" in req.active_indicators:
            latest_stoch = layers["stoch_rsi"][-1] if layers.get("stoch_rsi") else {"k": 50, "d": 50}
            indicator_texts.append(f"- Stochastic RSI Hızı: K={latest_stoch.get('k')}, D={latest_stoch.get('d')} (20 altı aşırı satım dip dönüşü, 80 üstü aşırı alım zirvesidir)")
            
        if "cmf" in req.active_indicators:
            latest_cmf = layers["cmf"][-1] if layers.get("cmf") else {"value": 0}
            indicator_texts.append(f"- Chaikin Para Girişi (CMF): Value={latest_cmf.get('value')} (0'ın üzeri kurumsal para girişini, altı para çıkışını belgeler)")
            
        if "volProfilePoc" in req.active_indicators:
            indicator_texts.append(f"- Vol. Profile POC (Yoğun Hacim Seviyesi): {raw_data.get('poc_price')} TL")

        indicators_joined = "\n        ".join(indicator_texts) if indicator_texts else "- Yalnızca fiyat analizi istenmiştir (İndikatör seçilmemiş)."

        ai_prompt = f"""
        Sen AlfaBIST Terminali'nin kıdemli kantitatif finans ve algoritmik trade uzmanı yapay zeka modülüsün.
        Aşağıda, {req.ticker} hissesinin günlük grafiğindeki en son muma ait kullanıcının seçtiği teknik indikatörlerin matematiksel ham değerleri yer almaktadır:
        
        - Son Kapanış Fiyatı: {latest_candle.get('close')} TL
        {indicators_joined}
        
        GÖREV: Bu verileri 0-15 günlük kısa vadeli 'Swing Trading / Momentum' stratejisi doğrultusunda analiz et. Sadece sağlanan indikatörlere göre bir karara var.
        
        ZORUNLU FORMAT: Yanıtını kesinlikle başka hiçbir açıklama metni eklemeden, doğrudan aşağıdaki JSON formatında döndür:
        {{
          "decision": "STRONG_BUY" veya "BUY" veya "HOLD" veya "SELL" veya "STRONG_SELL",
          "summary": "Maksimum 3-4 cümleden oluşan, sağlanan indikatör verilerini yorumlayan, hedef ve stop mantığını özetleyen net, Türkçe analist yorumu."
        }}
        """

        # Model yedeği (analyze ile tutarlı): 2.5 -> 2.0 -> 1.5 flash
        model_names = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
        response = None
        last_error = None
        for m_name in model_names:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(
                    ai_prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                break
            except Exception as e:
                last_error = e
                continue
        if response is None:
            raise last_error or Exception("AI yanıtı alınamadı")

        res_data = json.loads(response.text)

        log_action(current_user, "AI_ANALYSIS", f"Pro Terminal: {req.ticker} için AI analizi yapıldı. Kalan kota: {new_quota}")

        res_data["remaining_quota"] = new_quota
        return res_data

    except Exception as e:
        # AI başarısız — kotayı geri ver (analyze ile tutarlı)
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE users SET ai_quota = ai_quota + 1 WHERE username=:u"),
                {"u": current_user}
            )
        log_action(current_user, "AI_ERROR", f"Pro Terminal AI: {str(e)}", level="ERROR")
        raise HTTPException(status_code=500, detail="Yapay Zeka sunucularına bağlanılamadı. Lütfen daha sonra tekrar deneyin.")
