import pandas as pd
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import os
from database import engine
from sqlalchemy import text
import concurrent.futures
from datetime import datetime
import pytz

TR_TZ = pytz.timezone("Europe/Istanbul")
from data_loader import fetch_data, get_live_price
from indicators import (calculate_indicators, generate_signals_and_score, 
                        calculate_volume_confirmation, check_bottom_reversal, get_market_regime)
from kap_news import get_sentiment_summary
from fundamental_analyzer import get_fundamental_data
from patterns import detect_candlestick_patterns
from support_resistance import calculate_best_zones
from screener import get_sector, BIST30_SYMBOLS, BIST100_SYMBOLS, BIST_ALL_SYMBOLS
from takas_engine import get_takas_data
from top_picks_common import (save_picks_history, get_history_dates, get_picks_by_date,
                              compute_base, compute_finalize_inputs, finalize_composite,
                              compute_risk_position)

_HISTORY_TABLE = "top_picks_15d_history"

def save_top_picks_history(username: str, results: list):
    """Top 5 sonuçlarını veritabanına JSON olarak kaydeder."""
    save_picks_history(_HISTORY_TABLE, username, results)

def get_top_picks_history_dates(username: str) -> list:
    """Kaydedilmiş analiz tarihlerini id ve run_date olarak döndürür."""
    return get_history_dates(_HISTORY_TABLE, username)

def get_top_picks_by_date(username: str, history_id: int) -> list:
    """Belirli bir ID'deki analiz sonuçlarını döndürür."""
    return get_picks_by_date(_HISTORY_TABLE, username, history_id)


# Eski kelime bazlı sentiment fonksiyonu kaldırıldı (kap_news modülüne taşındı)


# ============================================================
# DERİN ANALİZ FONKSİYONU (Tek Hisse)
# ============================================================

def deep_analyze_stock(sym: str, market_regime: dict = None) -> dict:
    """
    Tek bir hisseyi tüm boyutlarıyla derinlemesine analiz eder.
    Teknik indikatörler + Formasyon + Destek/Direnç + Haber Duygusu + ML benzeri skorlama
    """
    result = {"ticker": sym, "error": None, "summary": ""}

    # --- ORTAK ÖN-HAZIRLIK (top_picks_common.compute_base) ---
    ctx = compute_base(sym, market_regime, tf_substring_al=True)
    if ctx.get("error"):
        result["error"] = ctx["error"]
        return result

    df = ctx["df"]; sig = ctx["sig"]; live_px = ctx["live_px"]
    tech_score = ctx["tech_score"]; core_decision = ctx["core_decision"]
    short_term_score = ctx["short_term_score"]
    medium_term_score = ctx["medium_term_score"]; long_term_score = ctx["long_term_score"]
    momentum_bonus = ctx["momentum_bonus"]; volume_bonus = ctx["volume_bonus"]; tf_bonus = ctx["tf_bonus"]
    pattern_bonus = ctx["pattern_bonus"]; pattern_text = ctx["pattern_text"]
    support_bonus = ctx["support_bonus"]; zones = ctx["zones"]
    dist_sup_pct = ctx["dist_sup_pct"]; dist_res_pct = ctx["dist_res_pct"]
    news_bonus = ctx["news_bonus"]; news_list = ctx["news_list"]; sent_100 = ctx["sent_100"]
    is_bear = ctx["is_bear"]; price_below_sma50 = ctx["price_below_sma50"]
    reversal_bonus = ctx["reversal_bonus"]; reversal_text = ctx["reversal_text"]
    takas_bonus = ctx["takas_bonus"]; fr_ratio = ctx["fr_ratio"]; fr_change = ctx["fr_change"]

    # 10. Kesişim (Confluence) Bonusları - Swing Trade Özel (15 Gün motoruna özgü)
    macd_bonus = 0
    bb_bonus = 0
    stoch_bonus = 0
    rsi_div_bonus = 0

    if len(df) >= 15:
        # a) MACD Golden Cross
        if 'MACDh' in df.columns:
            macdh_today = df['MACDh'].iloc[-1]
            macdh_yest = df['MACDh'].iloc[-2]
            if pd.notna(macdh_today) and pd.notna(macdh_yest):
                if macdh_yest <= 0 and macdh_today > 0:
                    macd_bonus = 10
                    
        # b) Bollinger Squeeze & Temas
        if all(c in df.columns for c in ['BBL_20_2.0', 'BBU_20_2.0', 'BBM_20_2.0']):
            bbl = df['BBL_20_2.0'].iloc[-1]
            bbu = df['BBU_20_2.0'].iloc[-1]
            bbm = df['BBM_20_2.0'].iloc[-1]
            low_price = df['Low'].iloc[-1]
            if pd.notna(bbl) and pd.notna(bbm) and bbm > 0:
                bandwidth = (bbu - bbl) / bbm
                if bandwidth < 0.10: # Squeeze
                    bb_bonus += 5
                if low_price <= bbl * 1.01: # Alt banda temas
                    bb_bonus += 5
                    
        # c) Stochastic Aşırı Satım Dönüşü
        if 'STOCHk_14_3_3' in df.columns and 'STOCHd_14_3_3' in df.columns:
            k_today = df['STOCHk_14_3_3'].iloc[-1]
            d_today = df['STOCHd_14_3_3'].iloc[-1]
            k_yest = df['STOCHk_14_3_3'].iloc[-2]
            d_yest = df['STOCHd_14_3_3'].iloc[-2]
            if pd.notna(k_today) and pd.notna(d_today) and k_yest < 20:
                if k_yest < d_yest and k_today > d_today:
                    stoch_bonus = 15
                    
        # d) RSI Pozitif Uyumsuzluk (14 Günlük Periyot)
        if 'RSI_14' in df.columns:
            w1 = df.iloc[-14:-7]
            w2 = df.iloc[-7:]
            if not w1.empty and not w2.empty:
                min_c1 = w1['Close'].min()
                min_c2 = w2['Close'].min()
                min_r1 = w1['RSI_14'].min()
                min_r2 = w2['RSI_14'].min()
                # Fiyatın yeni dibi eskisinden daha düşükse ama RSI'ın yeni dibi DAHA YÜKSEKSE
                if min_c2 < min_c1 and min_r2 > min_r1 and min_r2 < 45:
                    rsi_div_bonus = 15

    # (Dipten Dönüş ve Yabancı Takas bonusları compute_base içinde hesaplanır.)

    confluence_total = macd_bonus + bb_bonus + stoch_bonus + rsi_div_bonus

    # ============================================================
    # KOMPOZİT SKOR HESAPLAMA (Stratejik Seçki 15 GÜN / KISA VADE)
    # ============================================================
    if is_bear:
        composite = (
            short_term_score * 0.55 +
            (50 + momentum_bonus) * 0.10 +
            (50 + volume_bonus) * 0.05 +
            (50 + tf_bonus) * 0.05 +
            (50 + pattern_bonus) * 0.05 +
            (50 + support_bonus) * 0.05 +
            sent_100 * 0.05 +
            (50 + reversal_bonus) * 0.10
        )
    else:
        composite = (
            short_term_score * 0.60 +
            (50 + momentum_bonus) * 0.10 +
            (50 + volume_bonus) * 0.10 +
            (50 + tf_bonus) * 0.05 +
            (50 + pattern_bonus) * 0.05 +
            (50 + support_bonus) * 0.05 +
            sent_100 * 0.05
        )
    
    # Yeni eklenen Confluence bonuslarını ana skora ekle
    composite += confluence_total
    
    # Kesişim Özeti Mesajları
    if macd_bonus > 0: result["summary"] += "\n🎯 MACD: Altın Kesişim (Golden Cross)"
    if bb_bonus > 0: result["summary"] += "\n💥 Bollinger: Daralma (Squeeze) / Alt Bant Tepkisi"
    if stoch_bonus > 0: result["summary"] += "\n⚡ Stochastic: Aşırı Satımdan Kesişim Dönüşü"
    if rsi_div_bonus > 0: result["summary"] += "\n💎 RSI: Pozitif Uyumsuzluk Tespiti"
    if pattern_bonus > 0: result["summary"] += f"\n🕯️ Mum Formasyonu: {pattern_text}"

    # Alpha + tüm veto/filtreler + nihai karar (ortak & denklik-testli finalize_composite)
    # 15 Gün motoru: alpha sonrası min(100) (clamp_100_after_alpha=True) ve mesajlar
    # sonuç özetine eklenir.
    _inp = compute_finalize_inputs(df, live_px, zones, market_regime)
    _fin_msgs = []
    composite, rr_ratio, alpha_text, karar = finalize_composite(
        composite, _inp, sent_100=sent_100, is_bear=is_bear,
        price_below_sma50=price_below_sma50, core_decision=core_decision,
        clamp_100_after_alpha=True, summary=_fin_msgs,
    )
    result["summary"] += "".join(_fin_msgs)

    # V6 HİBRİT SKOR ENTEGRASYONU
    try:
        fund_data = get_fundamental_data(sym)
        tem_skor = fund_data.get('fundamental_score', 50)
    except Exception:
        fund_data = {"pe": 0, "pb": 0, "div_yield": 0, "fundamental_score": 50, "status": "Veri Yok"}
        tem_skor = 50
    
    # KISA VADE (15D): %85 Teknik/Momentum Kompozit + Sadece %15 Temel Not
    v6_score = round((composite * 0.85) + (tem_skor * 0.15), 1)

    # Risk Yönetimi: Konviksiyon (V6) ağırlıklı önerilen pozisyon büyüklüğü
    # Ağırlık = (%1 risk bütçesi / stop mesafesi) × (V6 / 100), maks %25
    sl_level = sig.get('risk', {}).get('SL', 0) or 0
    risk_position = compute_risk_position(live_px, sl_level, v6_score)

    # Detay sözlüğü
    rsi_val = df['RSI_14'].iloc[-1] if 'RSI_14' in df.columns and pd.notna(df['RSI_14'].iloc[-1]) else None
    macd_val = df['MACDh'].iloc[-1] if 'MACDh' in df.columns and pd.notna(df['MACDh'].iloc[-1]) else None

    result.update({
        "fiyat": round(live_px, 2),
        "rr_ratio": round(rr_ratio, 2) if 'rr_ratio' in locals() else 0,
        "alpha_text": alpha_text if 'alpha_text' in locals() else "-",
        "sektor": get_sector(sym),
        "kompozit_skor": v6_score,
        "V6 Hibrit Skor": v6_score,
        "teknik_skor": composite,
        "temel_skor": tem_skor,
        "pe": fund_data.get('pe', 0),
        "pb": fund_data.get('pb', 0),
        "div_yield": fund_data.get('div_yield', 0),
        "temel_durum": fund_data.get('status', 'Normal'),
        "graham_value": fund_data.get('graham_value', 0),
        "pgs": sig.get('pgs', 50),
        "karar": karar,
        "rsi": round(rsi_val, 1) if rsi_val else "-",
        "macd_hist": round(macd_val, 3) if macd_val else "-",
        "momentum_bonus": momentum_bonus,
        "volume_bonus": volume_bonus,
        "tf_bonus": tf_bonus,
        "pattern_text": pattern_text,
        "pattern_bonus": pattern_bonus,
        "support_bonus": support_bonus,
        "dist_support_pct": round(dist_sup_pct, 1) if dist_sup_pct else "-",
        "dist_resist_pct": round(dist_res_pct, 1) if dist_res_pct else "-",
        "reversal": reversal_text,
        "reversal_bonus": reversal_bonus,
        "news_sentiment": round(sent_100, 1),
        "news_pos": len([x for x in news_list if x['score'] > 0]),
        "news_neg": len([x for x in news_list if x['score'] < 0]),
        "news_headlines": [x['title'] for x in news_list[:3]],
        "news_bonus": news_bonus,
        "takas_ratio": fr_ratio,
        "takas_change": fr_change,
        "takas_bonus": takas_bonus,
        "short_term_score": short_term_score,
        "risk_details": sig.get('risk', {}),
        "risk_position": risk_position,
        "summary": result.get("summary", "") + "\n" + sig.get('summary', '')
    })
    return result


# ============================================================
# TOP 5 İNCELEME - ANA FONKSİYON
# ============================================================

def find_top_picks(symbol_list: list = None, top_n: int = 5, progress_bar=None) -> list:
    """
    Verilen hisse listesini derinlemesine analiz edip,
    yükselme potansiyeli en yüksek ilk N hisseyi döndürür.
    """
    if symbol_list is None:
        symbol_list = BIST30_SYMBOLS

    # Market Rejimi Hesapla (Bir kere)
    xu100_df = fetch_data("XU100", interval="1d", period="1y")
    market_regime = get_market_regime(xu100_df)

    all_results = []
    total = len(symbol_list)

    # ThreadPoolExecutor ile paralel asenkron tarama
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Gelecekteki taskları başlat
        future_to_sym = {executor.submit(deep_analyze_stock, sym, market_regime): sym for sym in symbol_list}
        
        completed = 0
        for future in concurrent.futures.as_completed(future_to_sym):
            sym = future_to_sym[future]
            try:
                res = future.result()
                if res.get('error') is None:
                    all_results.append(res)
            except Exception as exc:
                pass
            
            completed += 1
            if progress_bar:
                progress_bar.progress(completed / total, text=f"🔬 Asenkron Tarama: {sym} incelendi... ({completed}/{total})")

    # V5 güncelleme: Sadece alım yönelimli adayları sırala (doğruluk odaklı filtre)
    def _eligible(row: dict) -> bool:
        karar = str(row.get("karar", "")).lower()
        if any(x in karar for x in ("sat", "veto", "bekle", "doygun")):
            return False
        if row.get("kompozit_skor", 0) < 55:
            return False
        # Hem 'pgs' hem de tarama sözlüğünde kullanılan 'Güven Skoru (PGS)' anahtarını destekle
        pgs_val = row.get("pgs", row.get("Güven Skoru (PGS)", 50))
        if pgs_val < 40:
            return False
        return any(x in karar for x in ("al", "güçlü", "guclu", "lider", "potansiyel", "trend", "momentum", "pozitif"))

    filtered = [r for r in all_results if _eligible(r)]
    
    # İstenen sayı (top_n) kadar hisse bulamadıysa, katı filtreye takılan ama puanı fena olmayanları da havuza ekle
    if len(filtered) < top_n:
        others = [r for r in all_results if r not in filtered and r.get("kompozit_skor", 0) >= 40]
        pool = filtered + others
    else:
        pool = filtered
        
    # Kompozit skor ve Piyasa Gücü Skoruna (pgs) göre sırala
    pool.sort(key=lambda x: (x.get("kompozit_skor", 0), x.get("pgs", 0)), reverse=True)
    return pool[:top_n]
