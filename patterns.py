import pandas as pd
import numpy as np

def detect_candlestick_patterns(df: pd.DataFrame) -> dict:
    """
    DataFrame içindeki son 'window' kadarki mumları inceleyip,
    özel mum formasyonlarını tespit eder.
    Sinyalleri son 3 gün içindekileri önceliklendirerek raporlar.
    """
    if df.empty or len(df) < 5:
        return {}

    patterns_detected = []
    
    # Sadece son 3 günün analizini yap
    recent_df = df.tail(3).copy()
    
    for i in range(len(recent_df)):
        idx = recent_df.index[i]
        date_str = str(idx.date()) if hasattr(idx, 'date') else str(idx)
        
        row = recent_df.iloc[i]
        
        # O, H, L, C
        O = row['Open']
        H = row['High']
        L = row['Low']
        C = row['Close']
        
        body = abs(C - O)
        upper_shadow = H - max(O, C)
        lower_shadow = min(O, C) - L
        
        is_bullish = C > O
        is_bearish = C < O
        
        body_percent = body / (O + 0.0001) * 100
        
        # 1. Doji (Vücut çok küçük)
        if body_percent < 0.1:
            patterns_detected.append(f"{date_str} - Kararsızlık Mumu (Doji)")
            
        # 2. Çekiç (Hammer) - Alt gölge çok uzun, üst gölge kısa, küçük - orta vücut
        if is_bullish and lower_shadow > (2 * body) and upper_shadow < (0.2 * body):
            patterns_detected.append(f"{date_str} - Boğa Yükseliş Sinyali: Çekiç (Hammer)")
            
        # Kayan Yıldız (Shooting Star) - Üst gölge çok uzun, alt gölge kısa
        if is_bearish and upper_shadow > (2 * body) and lower_shadow < (0.2 * body):
            patterns_detected.append(f"{date_str} - Ayı Düşüş Sinyali: Kayan Yıldız (Shooting Star)")

        # Engulfing (Yutan Boğa/Ayı) check requires previous day
        if i > 0:
            prev_row = recent_df.iloc[i-1]
            prev_O, prev_C = prev_row['Open'], prev_row['Close']
            prev_is_bullish = prev_C > prev_O
            prev_is_bearish = prev_C < prev_O
            
            # Yutan Boğa (Bullish Engulfing)
            if prev_is_bearish and is_bullish:
                if O < prev_C and C > prev_O:
                    patterns_detected.append(f"{date_str} - Güçlü Boğa Sinyali: Yutan Küme (Bullish Engulfing)")
                    
            # Yutan Ayı (Bearish Engulfing)
            if prev_is_bullish and is_bearish:
                if O > prev_C and C < prev_O:
                    patterns_detected.append(f"{date_str} - Güçlü Ayı Sinyali: Yutan Satış (Bearish Engulfing)")

    # Sadece en güncel patternları dön veya summary olarak birleştir
    result = {}
    if patterns_detected:
        result['summary'] = "\n".join(patterns_detected)
    else:
        result['summary'] = "Son günlerde belirgin bir mum formasyonu tespit edilmedi."

    return result


def detect_bull_flag(df: pd.DataFrame, lookback: int = 20) -> dict:
    """
    Boğa Flaması (Bull Flag) tespiti — kısa vadeli devam formasyonu.

    Döküman kuralları:
      • Sert bir yükseliş "direği" (flagpole): kısa sürede güçlü yükseliş.
      • Ardından hafif aşağı eğimli/yatay daralan konsolidasyon ("bayrak").
      • Geri çekilme derinliği direğin %50'sini aşmamalı (ideal: ≤ %38.2).
    """
    out = {"detected": False, "score": 0, "summary": ""}
    if df is None or df.empty or len(df) < lookback + 2:
        return out

    sub = df.tail(lookback)
    high = sub['High'].values
    low = sub['Low'].values
    close = sub['Close'].values
    n = len(sub)

    # 1) Direğin tepesi: bayrak için son 2 barı ayırarak penceredeki en yüksek nokta
    peak_i = int(np.argmax(high[: n - 2]))
    pole_top = float(high[peak_i])
    flag_len = (n - 1) - peak_i
    # Bayrak (konsolidasyon) süresi makul olmalı
    if flag_len < 2 or flag_len > 12:
        return out

    # 2) Direğin tabanı: tepeden en fazla 8 bar geriye bakarak en düşük dip
    #    (Böylece "direk" en fazla 8 barlık SERT bir yükseliş olur.)
    pole_window_lo = low[max(0, peak_i - 8): peak_i + 1]
    pole_start = float(pole_window_lo.min())
    if pole_start <= 0:
        return out

    pole_gain = (pole_top - pole_start) / pole_start
    # Sert ve hızlı direk şartı
    if pole_gain < 0.15:
        return out

    # 3) Geri çekilme derinliği (bayraktaki en düşük dip, direğe göre)
    flag_low = float(low[peak_i:].min())
    pole_range = pole_top - pole_start
    if pole_range <= 0:
        return out
    retrace = (pole_top - flag_low) / pole_range
    if retrace > 0.5:             # çok derin -> momentum kaybı, bayrak değil
        return out

    # Fiyat hâlâ direğin tepesine yakın/üstünde mi (yapı bozulmamış)
    last = float(close[-1])
    if last < pole_start:         # tüm kazanç geri verilmiş
        return out

    if retrace <= 0.382:
        score = 18
        summary = f"🚩 Boğa Flaması (Bull Flag) — ideal sığ geri çekilme (%{retrace*100:.0f} ≤ %38.2), güçlü devam beklentisi"
    else:
        score = 12
        summary = f"🚩 Boğa Flaması (Bull Flag) — sağlıklı konsolidasyon (geri çekilme %{retrace*100:.0f})"

    out.update({
        "detected": True,
        "score": score,
        "pole_gain_pct": round(pole_gain * 100, 1),
        "retrace_pct": round(retrace * 100, 1),
        "flag_bars": flag_len,
        "summary": summary,
    })
    return out
