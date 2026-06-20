"""
Top Picks ortak yardımcıları (DRY).
Geçmiş kayıt (history) fonksiyonları, top_picks.py ve top_picks_15d.py tarafından
ortak kullanılır; tek fark veritabanı tablo adıdır, o da parametre olarak geçilir.

NOT: `table` argümanı yalnızca kod içinden sabit string'lerle çağrılır
(kullanıcı girdisi DEĞİL), bu yüzden f-string ile tablo adı enterpolasyonu güvenlidir.
"""
import json
from datetime import datetime
import pytz
import pandas as pd
from sqlalchemy import text
from database import engine

TR_TZ = pytz.timezone("Europe/Istanbul")


def save_picks_history(table: str, username: str, results: list):
    """Tarama sonuçlarını ilgili history tablosuna JSON olarak kaydeder (son 30 kayıt tutulur)."""
    if not results:
        return
    now_str = datetime.now(TR_TZ).strftime("%Y-%m-%d %H:%M:%S")
    with engine.begin() as conn:
        conn.execute(
            text(f"INSERT INTO {table} (username, run_date, results_json) VALUES (:u, :d, :r)"),
            {"u": username, "d": now_str, "r": json.dumps(results)}
        )
        # Sadece son 30 kalsın
        conn.execute(text(f"""
            DELETE FROM {table}
            WHERE username = :u AND id NOT IN (
                SELECT id FROM {table}
                WHERE username = :u
                ORDER BY id DESC LIMIT 30
            )
        """), {"u": username})


def get_history_dates(table: str, username: str) -> list:
    """Kaydedilmiş analiz tarihlerini id ve run_date olarak döndürür."""
    with engine.connect() as conn:
        cursor = conn.execute(
            text(f"SELECT id, run_date FROM {table} WHERE username=:u ORDER BY id DESC"),
            {"u": username}
        )
        return [{"id": row[0], "run_date": row[1]} for row in cursor.fetchall()]


def get_picks_by_date(table: str, username: str, history_id: int) -> list:
    """Belirli bir ID'deki analiz sonuçlarını döndürür."""
    with engine.connect() as conn:
        cursor = conn.execute(
            text(f"SELECT results_json FROM {table} WHERE username=:u AND id=:id"),
            {"u": username, "id": history_id}
        )
        row = cursor.fetchone()
    return json.loads(row[0]) if row else []


# ============================================================
# ORTAK DERİN ANALİZ PARÇALARI (top_picks.py & top_picks_15d.py)
# Davranış birebir korunur; iki stratejinin SADECE farklı olan kısmı
# (kompozit formülü, confluence, V6 oranı, sonuç sözlüğü) çağıran tarafta kalır.
# ============================================================

def compute_base(sym: str, market_regime: dict = None, tf_substring_al: bool = False):
    """
    İki seçki motorunun da AYNI olan ön-hazırlık bölümü:
    veri çekme + indikatör + sinyal/skor + tüm bonus hesapları.

    tf_substring_al: Çoklu zaman dilimi (tf) bonusunda karar eşleştirme yöntemi.
        - False  -> sig['decision'] in ['Al','Güçlü Al']   (Orta-Uzun vade motoru)
        - True   -> 'AL' in sig['decision']                 (15 Gün motoru)

    Dönüş: ortak değerleri içeren ctx sözlüğü; veri yetersizse {"error": ...}.
    """
    from data_loader import fetch_data, get_live_price
    from indicators import calculate_indicators, generate_signals_and_score
    from kap_news import get_sentiment_summary
    from patterns import detect_candlestick_patterns
    from support_resistance import calculate_best_zones
    from takas_engine import get_takas_data

    # 1. Veri Çek
    df = fetch_data(sym, interval="1d", period="1y")
    if df.empty or len(df) < 50:
        return {"error": "Yetersiz veri"}
    df = df.copy()

    # 1.1 Haber Duygusu Çek (Gemini AI)
    sent_score, news_list = get_sentiment_summary(sym)
    sent_100 = (sent_score + 1) * 50

    df = calculate_indicators(df, ticker=sym)
    sig = generate_signals_and_score(df, ticker=sym, market_regime=market_regime, sentiment_score=sent_score)

    core_score = sig.get('core_score', 50)
    core_decision = sig.get('core_decision', sig.get('decision', 'Nötr'))

    short_term_score = sig.get('short_term', {}).get('score', 50)
    medium_term_score = sig.get('medium_term', {}).get('score', 50)
    long_term_score = sig.get('long_term', {}).get('score', 50)

    # 2. Canlı Fiyat
    live_px = get_live_price(sym)
    if live_px <= 0:
        live_px = df['Close'].iloc[-1]

    # 3. Teknik Skor (0-100)
    tech_score = sig['score']

    # 4. Momentum Trendi (Son 5 gün ortalama RSI eğimi)
    momentum_bonus = 0
    if 'RSI_14' in df.columns and len(df) >= 6:
        rsi_last5 = df['RSI_14'].iloc[-5:].dropna()
        if len(rsi_last5) >= 2:
            rsi_slope = rsi_last5.iloc[-1] - rsi_last5.iloc[0]
            if rsi_slope > 5:
                momentum_bonus = 10
            elif rsi_slope > 0:
                momentum_bonus = 5

    # 5. Hacim Patlaması Bonusu
    volume_bonus = 0
    if len(df) >= 11:
        avg_vol = df['Volume'].iloc[-11:-1].mean()
        today_vol = df['Volume'].iloc[-1]
        if avg_vol > 0 and today_vol > avg_vol * 1.5:
            if df['Close'].iloc[-1] > df['Open'].iloc[-1]:
                volume_bonus = 15
            else:
                volume_bonus = 5

    # 6. Çoklu Zaman Dilimi Bonusu
    tf_bonus = 0
    df_1h = fetch_data(sym, interval="1h", period="1mo")
    if not df_1h.empty and len(df_1h) >= 20:
        df_1h = calculate_indicators(df_1h)
        sig_1h = generate_signals_and_score(df_1h)
        if tf_substring_al:
            d_ok = "AL" in sig['decision']
            d1h_ok = "AL" in sig_1h['decision']
        else:
            d_ok = sig['decision'] in ["Al", "Güçlü Al"]
            d1h_ok = sig_1h['decision'] in ["Al", "Güçlü Al"]
        if d_ok and d1h_ok:
            tf_bonus = 15
        elif d_ok or d1h_ok:
            tf_bonus = 5

    # 7. Formasyon Bonusu
    pattern_bonus = 0
    pattern_text = "-"
    p_res = detect_candlestick_patterns(df)
    if p_res and p_res.get('summary') and "tespit edilmedi" not in p_res.get('summary'):
        pattern_text = p_res['summary'].splitlines()[0].replace('*', '').strip()
        if any(w in pattern_text.lower() for w in ['boğa', 'çekiç', 'yutan', 'sabah']):
            pattern_bonus = 10

    # 8. Destek Yakınlık Bonusu
    support_bonus = 0
    zones = calculate_best_zones(df)
    dist_sup_pct = None
    dist_res_pct = None
    if zones.get('best_buy_zones'):
        sup = zones['best_buy_zones'][0][1]
        dist_sup_pct = ((live_px - sup) / live_px) * 100
        if dist_sup_pct < 3:
            support_bonus = 10
    if zones.get('best_sell_zones'):
        res_p = zones['best_sell_zones'][0][1]
        dist_res_pct = ((res_p - live_px) / live_px) * 100

    # 9. Haber Duygu Analizi
    news_bonus = 0
    is_bear = market_regime['is_bear'] if market_regime else False
    price_below_sma50 = live_px < df['SMA_50'].iloc[-1] if 'SMA_50' in df.columns else False
    if sent_100 > 70:
        news_bonus = 5 if (is_bear and price_below_sma50) else 10
    elif sent_100 > 55:
        news_bonus = 2 if (is_bear and price_below_sma50) else 5
    elif sent_100 < 30:
        news_bonus = -15 if is_bear else -10

    # Dipten Dönüş Bonusu (RSI 35 altı)
    reversal_bonus = 0
    reversal_text = "-"
    if 'RSI_14' in df.columns and len(df) >= 3:
        rsi_today = df['RSI_14'].iloc[-1]
        rsi_yest = df['RSI_14'].iloc[-2]
        if pd.notna(rsi_today) and pd.notna(rsi_yest):
            if rsi_yest < 35 and rsi_today > rsi_yest:
                reversal_bonus = 15
                reversal_text = "🔥 Dipten Dönüş"

    # Yabancı Takas Bonusu
    takas_bonus = 0
    takas = get_takas_data(sym)
    fr_ratio = takas.get('foreign_ratio', 0)
    fr_change = takas.get('daily_change', 0)
    if fr_ratio > 40:
        takas_bonus += 15
    elif fr_ratio > 20:
        takas_bonus += 7
    if fr_change > 0.5:
        takas_bonus += 15
    elif fr_change > 0.1:
        takas_bonus += 5
    elif fr_change < -0.5:
        takas_bonus -= 15

    return {
        "error": None,
        "df": df, "sig": sig, "live_px": live_px, "tech_score": tech_score,
        "core_score": core_score, "core_decision": core_decision,
        "short_term_score": short_term_score, "medium_term_score": medium_term_score,
        "long_term_score": long_term_score,
        "momentum_bonus": momentum_bonus, "volume_bonus": volume_bonus, "tf_bonus": tf_bonus,
        "pattern_bonus": pattern_bonus, "pattern_text": pattern_text,
        "support_bonus": support_bonus, "zones": zones,
        "dist_sup_pct": dist_sup_pct, "dist_res_pct": dist_res_pct,
        "news_bonus": news_bonus, "news_list": news_list, "sent_100": sent_100,
        "is_bear": is_bear, "price_below_sma50": price_below_sma50,
        "reversal_bonus": reversal_bonus, "reversal_text": reversal_text,
        "takas_bonus": takas_bonus, "fr_ratio": fr_ratio, "fr_change": fr_change,
    }


def compute_finalize_inputs(df, live_px, zones, market_regime):
    """finalize_composite için gerekli skaler girdileri df/zones/market'tan çıkarır
    (veri bağımlı; değerler verbatim taşınmıştır)."""
    from indicators import calculate_indicators

    has_5d = (len(df) >= 5) and bool(market_regime) and ('xu100_5d_chg' in (market_regime or {}))
    rr_has = bool(zones.get('best_buy_zones') and zones.get('best_sell_zones'))

    # MTF (haftalık) RSI
    rsi_1w = None
    try:
        df_1w = df.resample('W').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
        if len(df_1w) > 14:
            df_1w = calculate_indicators(df_1w)
            rsi_1w = df_1w['RSI_14'].iloc[-1] if 'RSI_14' in df_1w.columns else 50
    except Exception:
        rsi_1w = None

    range_px = (df['High'].iloc[-1] - df['Low'].iloc[-1])
    upper_shadow = ((df['High'].iloc[-1] - df['Close'].iloc[-1]) / range_px) if range_px > 0 else None

    ema20 = df['EMA_20'].iloc[-1] if 'EMA_20' in df.columns else 0
    dist_ema20 = ((live_px - ema20) / ema20) if ema20 > 0 else None

    rsi_last = df['RSI_14'].iloc[-1] if ('RSI_14' in df.columns and pd.notna(df['RSI_14'].iloc[-1])) else None

    return {
        "live_px": live_px,
        "has_5d": has_5d,
        "xu100_5d_chg": market_regime.get('xu100_5d_chg') if has_5d else None,
        "sym_5d": (((live_px - df['Close'].iloc[-5]) / df['Close'].iloc[-5]) * 100) if has_5d else None,
        "rr_has": rr_has,
        "rr_sup": zones['best_buy_zones'][0][1] if rr_has else None,
        "rr_res": zones['best_sell_zones'][0][1] if rr_has else None,
        "rsi_1w": rsi_1w,
        "upper_shadow": upper_shadow,
        "dist_ema20": dist_ema20,
        "rsi_last": rsi_last,
        "daily_chg": (market_regime.get('daily_chg', 0) if market_regime else None),
    }


def finalize_composite(composite, inp, *, sent_100, is_bear, price_below_sma50,
                       core_decision, clamp_100_after_alpha, summary):
    """
    SAF fonksiyon: kompozit skora alpha bonusu + tüm veto/filtreleri uygular,
    0-100'e sıkıştırır ve nihai 'karar'ı belirler.
    `summary` verilen listeye açıklama mesajları eklenir (yan etki).
    `clamp_100_after_alpha`: 15 Gün motoru alpha'dan hemen sonra min(100) uygular.
    Dönüş: (composite_final, rr_ratio, alpha_text, karar)
    """
    # Alpha (Göreceli Güç)
    alpha_text = "-"
    alpha_bonus = 0
    if inp["has_5d"]:
        xu100_5d_chg = inp["xu100_5d_chg"]
        sym_5d = inp["sym_5d"]
        alpha_val = sym_5d - xu100_5d_chg
        alpha_text = f"{alpha_val:+.1f}%"
        if xu100_5d_chg < -1.0 and sym_5d > -0.5:
            alpha_bonus = 20
            summary.append(f"\n💪 Endeksten Güçlü Ayrışma (Alpha: {alpha_text})")
    composite += alpha_bonus

    if clamp_100_after_alpha:
        composite = min(100.0, composite)

    # Risk/Getiri (R/R) Cezası
    rr_ratio = 0.0
    if inp["rr_has"]:
        risk = inp["live_px"] - inp["rr_sup"]
        reward = inp["rr_res"] - inp["live_px"]
        if risk > 0:
            rr_ratio = reward / risk
            if rr_ratio < 2.0:
                composite -= 30
                summary.append(f"\n⛔ Risk/Getiri Çok Düşük (R/R: {rr_ratio:.2f}). -30 Ceza!")
        elif risk <= 0:
            rr_ratio = 5.0

    # MTF VETO (Haftalık Şişme)
    if inp["rsi_1w"] is not None and inp["rsi_1w"] > 80:
        composite -= 30
        summary.append(f"\n⛔ MTF VETO: Haftalık RSI ({inp['rsi_1w']:.1f}) Çok Şişkin. Düzeltme Riski!")

    # AI VETO
    if sent_100 < 20:
        composite -= 50
        summary.append("\n🚨 AI VETO: Kara Bulut (Çok Negatif Haberler)")

    # Gölge Analizi (Zirve Reddi)
    if inp["upper_shadow"] is not None and inp["upper_shadow"] > 0.5:
        composite *= 0.85
        summary.append("\n⚠️ Üst fitil baskısı (Zirve Reddi) tespit edildi.")

    # Overextension (EMA20'den uzaklık)
    if inp["dist_ema20"] is not None and inp["dist_ema20"] > 0.12:
        composite *= 0.9
        summary.append(f"\n🧲 EMA 20'den çok uzak (%{inp['dist_ema20']*100:.1f}), düzeltme riski.")

    # Ayı Piyasası & SMA 50 Penaltısı
    if is_bear and price_below_sma50:
        composite *= 0.85

    composite = min(100, max(0, round(composite, 1)))

    # Karar Mekanizması (RSI Doygunluk + Endeks Freni)
    karar = core_decision
    if composite >= 70 and inp["rsi_last"] is not None and inp["rsi_last"] > 65:
        karar = "🧘 Doygunluk Bölgesi"
        summary.append("\n🧘 RSI Doygunluğu: Kar satışı gelebilir.")
    if inp["daily_chg"] is not None and inp["daily_chg"] < -2.0:
        if any(w in karar for w in ["Trend", "Lideri", "Potansiyeli"]):
            karar = "⚠️ Bekle (Endeks Freni)"

    return composite, rr_ratio, alpha_text, karar
