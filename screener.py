import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
import os
from datetime import datetime
import pytz
from database import engine
from sqlalchemy import text
from datetime import datetime
import pytz

TR_TZ = pytz.timezone("Europe/Istanbul")
from concurrent.futures import ThreadPoolExecutor, as_completed
from data_loader import fetch_data, get_live_price
from indicators import (calculate_indicators, generate_signals_and_score, 
                        detect_rsi_divergence, calculate_volume_confirmation,
                        get_market_regime, check_bottom_reversal,
                        calculate_vwap, check_volatility_squeeze,
                        detect_liquidity_sweep, calculate_obv_divergence)
from patterns import detect_candlestick_patterns
from support_resistance import calculate_best_zones

from takas_engine import get_takas_data

# ============================================================
# BIST HİSSE LİSTELERİ
# ============================================================

BIST30_SYMBOLS = [
    "AKBNK", "ALARK", "ARCLK", "ASELS", "ASTOR", "BIMAS", "EKGYO", "ENKAI",
    "EREGL", "FROTO", "GARAN", "GUBRF", "HEKTS", "ISCTR", "KCHOL", "KONTR",
    "KOZAA", "KOZAL", "KRDMD", "ODAS", "OYAKC", "PETKM", "PGSUS", "SAHOL",
    "SASA", "SISE", "TCELL", "THYAO", "TOASO", "TUPRS", "YKBNK"
]

BIST100_SYMBOLS = BIST30_SYMBOLS + [
    "AEFES", "AFYON", "AGESA", "AHGAZ", "AKCNS", "AKFGY", "AKSA", "AKSEN",
    "AKYHO", "ALGYO", "ALTNY", "ALYAG", "ANSGR", "AGHOL", "AYDEM", "BASGZ",
    "BIENY", "BINHO", "BRISA", "BRYAT", "BTCIM", "BUCIM", "CANTE", "CCOLA",
    "CEMTS", "CIMSA", "CWENE", "DOAS", "DOHOL", "EGEEN", "ENJSA", "ESEN",
    "EUPWR", "GENIL", "GLYHO", "GOLTS", "GOZDE", "GRSEL", "GSDHO", "GESAN",
    "HALKB", "HUNER", "ISGYO", "ISMEN", "KAYSE", "KERVT", "KLSER", "KMPUR",
    "KORDS", "KOZAA", "LMKDC", "LOGO", "MAVI", "MGROS", "MIATK", "NETAS",
    "OTKAR", "PAPIL", "PATEK", "PEKGY", "QUAGR", "RGYAS", "RUBNS", "SARKY",
    "SELEC", "SKBNK", "SMRTG", "SOKM", "TAVHL", "TKFEN", "TKNSA", "TMSN",
    "TRGYO", "TURSG", "ULKER", "VAKBN", "VESBE", "VESTL", "YEOTK", "ZOREN"
]

BIST_ALL_SYMBOLS = list(set(BIST100_SYMBOLS + [
    "ACSEL", "ADEL", "ADESE", "ADGYO", "AEFES", "AFYON", "AGESA", "AGHOL",
    "AHGAZ", "AHSGY", "AKCNS", "AKFGY", "AKFYE", "AKGRT", "AKMGY", "AKSA",
    "AKSEN", "AKSGY", "AKSUE", "AKYHO", "ALCTL", "ALGYO", "ALKA", "ALKIM",
    "ALMAD", "ALTNY", "ALYAG", "ANELE", "ANGEN", "ANHYT", "ANSGR", "ARASE",
    "ARCLK", "ARDYZ", "ARENA", "ARSAN", "ARTMS", "ARZUM", "ATAGY", "ATAKP",
    "ATATP", "AVHOL", "AVOD", "AVPGY", "AVTUR", "AYCES", "AYDEM", "AYEN",
    "AYES", "AYGAZ", "AZTEK", "BAGFS", "BAKAB", "BALAT", "BANVT", "BARMA",
    "BASCM", "BASGZ", "BAYRK", "BERA", "BEYAZ", "BIENY", "BIGCH", "BIMAS",
    "BINHO", "BIOEN", "BIZIM", "BLCYT", "BMSCH", "BMSTL", "BNTAS", "BOBET",
    "BORLS", "BORSK", "BOSSA", "BRISA", "BRKSN", "BRKVY", "BRLSM", "BRMEN",
    "BRSAN", "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BURCE", "BURVA", "CANTE",
    "CASA", "CCOLA", "CELHA", "CEMTS", "CEOEM", "CFRSA", "CGSGY", "CIMSA",
    "CINFO", "CLEBI", "CMBTN", "CONSE", "COSMO", "CRDFA", "CRFSA", "CUSAN",
    "CVKMD", "CWENE", "DAGHL", "DAGI", "DAPGM", "DARDL", "DENGE", "DERHL",
    "DERIM", "DESA", "DESPC", "DEVA", "DGATE", "DGNMO", "DIRIT", "DITAS",
    "DMRGD", "DMSAS", "DNISI", "DOAS", "DOBUR", "DOCO", "DOGUB", "DOHOL",
    "DOKTA", "DURDO", "DYOBY", "DZGYO", "EBEBK", "ECILC", "ECZYT", "EDIP",
    "EFORC", "EGEEN", "EGEPO", "EGGUB", "EGPRO", "EGSER", "EKGYO", "EKIZ",
    "EKOS", "EKSUN", "ELITE", "EMKEL", "EMNIS", "ENERY", "ENJSA", "ENKAI",
    "ENSRI", "EPLAS", "ERBOS", "EREGL", "ERSU", "ESEN", "ETILR", "EUPWR",
    "EUREN", "EUYO", "EYGYO", "FADE", "FENER", "FLAP", "FONET", "FORMT",
    "FORTE", "FRIGO", "FROTO", "FZLGY", "GARAN", "GARFA", "GEDIK", "GEDZA",
    "GENIL", "GENTS", "GEREL", "GESAN", "GIPTS", "GLBMD", "GLCVY", "GLYHO",
    "GMTAS", "GOKNR", "GOLTS", "GOODY", "GOZDE", "GRSEL", "GRTRK", "GSDDE",
    "GSDHO", "GSRAY", "GUBRF", "GWIND", "GZNMI", "HALKB", "HATEK", "HDFGS",
    "HEDEF", "HEKTS", "HKTM", "HLGYO", "HTTBT", "HUBVC", "HUNER", "HURGZ",
    "ICBCT", "ICUGS", "IDEAS", "IEYHO", "IHEVA", "IHGZT", "IHLAS", "IHLGM",
    "IHYAY", "IMASM", "INDES", "INFO", "INGRM", "INTEM", "INVEO", "INVES",
    "IPEKE", "ISBIR", "ISBTR", "ISCTR", "ISDMR", "ISFIN", "ISGSY", "ISGYO",
    "ISKPL", "ISKUR", "ISMEN", "ISSEN", "ITTFH", "IZFAS", "IZINV", "IZMDC",
    "JANTS", "KAPLM", "KAREL", "KARSN", "KARTN", "KARYE", "KATMR", "KAYSE",
    "KCHOL", "KENT", "KERVT", "KFEIN", "KGYO", "KIMMR", "KLGYO", "KLMSN",
    "KLNMA", "KLRHO", "KLSER", "KLSYN", "KMPUR", "KNFRT", "KONKA", "KONTR",
    "KONYA", "KORDS", "KOZAA", "KOZAL", "KRDMA", "KRDMB", "KRDMD", "KRGYO",
    "KRONT", "KRPLS", "KRSTL", "KRTEK", "KRVGD", "KTLEV", "KTSKR", "KUNDL",
    "KUVVA", "KUYAS", "KZBGY", "KZGYO", "LIDER", "LIDFA", "LILAK", "LINK",
    "LKMNH", "LMKDC", "LOGO", "LUKSK", "MAALT", "MACKO", "MAKIM", "MANAS",
    "MARBL", "MARKA", "MARTI", "MAVI", "MEDTR", "MEGAP", "MEKAG", "MERCN",
    "MERIT", "MERKO", "METRO", "METUR", "MGROS", "MHRGY", "MIATK", "MNDRS",
    "MNDTR", "MOBTL", "MOGAN", "MPARK", "MRDIN", "MRGYO", "MRSHL", "MSGYO",
    "MTRKS", "MTRYO", "MZHLD", "NATEN", "NETAS", "NIBAS", "NTGAZ", "NTHOL",
    "NUGYO", "NUHCM", "OBAMS", "ODAS", "OFSYM", "ONCSM", "ORCAY", "ORGE",
    "ORSBU", "OSTIM", "OTKAR", "OTTO", "OYAKC", "OYLUM", "OYYAT", "OZGYO",
    "OZKGY", "PAMEL", "PAPIL", "PARSN", "PASEU", "PATEK", "PCILT", "PEKGY",
    "PENGD", "PENTA", "PETKM", "PETUN", "PGSUS", "PINSU", "PKART", "PKENT",
    "PLTUR", "PNLSN", "PNSUT", "POLHO", "POLTK", "PRDGS", "PRKAB", "PRKME",
    "PRZMA", "PSDTC", "QUAGR", "RALYH", "RAYSG", "REEDR", "RGYAS", "RODRG",
    "RTALB", "RUBNS", "RYGYO", "RYSAS", "SAFKR", "SAHOL", "SAMAT", "SANEL",
    "SANFM", "SANKO", "SARKY", "SASA", "SAYAS", "SDTTR", "SEGYO", "SEKFK",
    "SEKUR", "SELEC", "SELGD", "SELVA", "SENVP", "SERVE", "SILVR", "SISE",
    "SKBNK", "SKYLP", "SMART", "SMRTG", "SNGYO", "SNICA", "SOKM", "SONME",
    "SRVGY", "SUNTK", "SUWEN", "TABGD", "TARKM", "TATGD", "TAVHL", "TCELL",
    "TEZOL", "THYAO", "TKFEN", "TKNSA", "TLMAN", "TMSN", "TOASO", "TRCAS",
    "TRGYO", "TRILC", "TSGYO", "TSKB", "TTKOM", "TTRAK", "TUKAS", "TUPRS",
    "TUREX", "TURSG", "ULKER", "ULUFA", "ULUSE", "ULUUN", "UMPAS", "UNLU",
    "USAK", "UZERB", "VAKBN", "VAKFN", "VAKKO", "VBTYZ", "VERTU", "VESBE",
    "VESTL", "VKFYO", "VKGYO", "VRGYO", "YAPRK", "YATAS", "YEOTK", "YESIL",
    "YGYO", "YKBNK", "YKSLN", "YUNSA", "YYLGD", "ZEDUR", "ZOREN", "ZRGYO"
]))

# ============================================================
# SEKTÖR HARİTASI (YENİ - Özellik 1)
# ============================================================

SECTOR_MAP = {
    "Bankacılık": ["AKBNK", "GARAN", "HALKB", "ISCTR", "VAKBN", "YKBNK", "SKBNK", "TSKB", "KLNMA"],
    "Holding": ["KCHOL", "SAHOL", "DOHOL", "GSDHO", "AGHOL", "GLYHO", "NTHOL", "INVEO"],
    "Enerji": ["AKSEN", "AYDEM", "ENJSA", "EUPWR", "CWENE", "ENKAI", "AYEN", "ZOREN", "ODAS"],
    "Havacılık & Ulaşım": ["THYAO", "PGSUS", "TAVHL", "CLEBI", "FROTO", "TOASO", "DOAS", "OTKAR"],
    "Demir-Çelik & Maden": ["EREGL", "KRDMD", "KOZAL", "KOZAA", "ISDMR", "CEMTS", "BRSAN"],
    "Perakende & Gıda": ["BIMAS", "SOKM", "MGROS", "ULKER", "CCOLA", "BANVT", "PNSUT", "TATGD"],
    "Teknoloji": ["ASELS", "LOGO", "NETAS", "ARENA", "INDES", "KRONT", "DGATE", "FONET", "PAPIL"],
    "İnşaat & GYO": ["EKGYO", "TRGYO", "ISGYO", "ALGYO", "KGYO", "SNGYO", "ENKAI"],
    "Kimya & Petrokimya": ["PETKM", "TUPRS", "SASA", "GUBRF", "HEKTS", "BAGFS", "ALKIM"],
    "Cam & Seramik": ["SISE", "TRKCM", "CIMSA", "BTCIM", "BUCIM", "BSOKE", "NUHCM"],
    "Tekstil & Moda": ["MAVI", "VAKKO", "BRISA", "BOSSA", "YUNSA", "DESA", "YATAS"],
    "Sigorta": ["AGESA", "ANSGR", "TURSG", "AKGRT", "ANHYT"],
    "Telekomünikasyon": ["TCELL", "TTKOM"],
}

def get_sector(symbol: str) -> str:
    """Hissenin sektörünü döndürür."""
    for sector, symbols in SECTOR_MAP.items():
        if symbol in symbols:
            return sector
    return "Diğer"

def get_sector_list() -> list:
    """Tüm sektör isimlerini döndürür."""
    return ["Tümü"] + sorted(SECTOR_MAP.keys()) + ["Diğer"]

def filter_by_sector(symbol_list: list, sector: str) -> list:
    """Belirtilen sektöre göre hisse listesini filtreler."""
    if sector == "Tümü":
        return symbol_list
    if sector == "Diğer":
        all_mapped = set()
        for syms in SECTOR_MAP.values():
            all_mapped.update(syms)
        return [s for s in symbol_list if s not in all_mapped]
    return [s for s in symbol_list if s in SECTOR_MAP.get(sector, [])]


# ============================================================
# TARAMA GEÇMİŞİ (YENİ - Özellik 2)
# ============================================================

def save_scan_results(results_df: pd.DataFrame, username: str):
    """Tarama sonuçlarını veritabanına kaydeder."""
    if results_df.empty:
        return
    today = datetime.now(TR_TZ).strftime("%Y-%m-%d")
    with engine.begin() as conn:
        # Bugünün eski kayıtlarını sil (her taramada güncelle)
        conn.execute(text("DELETE FROM scan_history WHERE scan_date=:d AND username=:u"), {"d": today, "u": username})
        for _, row in results_df.iterrows():
            conn.execute(
                text("INSERT INTO scan_history (username, scan_date, ticker, score, decision, price, pct_change, smc_bos, intermediate_target) VALUES (:u, :d, :t, :s, :dec, :p, :pct, :smc, :itg)"),
                {"u": username, "d": today, "t": row.get('Hisse',''), "s": row.get('V6 Hibrit Skor',0), 
                 "dec": row.get('Piyasa Kararı',''), "p": row.get('Fiyat', 0), "pct": row.get('Değişim (%)',0),
                 "smc": row.get('Düzen Kırılımı', '-'), "itg": float(row.get('Ara Hedef (₺)', 0)) if str(row.get('Ara Hedef (₺)', '0')).replace('.','',1).isdigit() else 0.0}
            )

def get_scan_history(username: str, days_back: int = 7) -> pd.DataFrame:
    """Belirli kullanıcıya ait son N günlük tarama geçmişini döndürür."""
    with engine.connect() as conn:
        query = "SELECT * FROM scan_history WHERE username=%(u)s ORDER BY scan_date DESC, score DESC" if engine.name == 'postgresql' else "SELECT * FROM scan_history WHERE username=? ORDER BY scan_date DESC, score DESC"
        df = pd.read_sql_query(query, conn, params={"u": username} if engine.name == 'postgresql' else (username,))
    return df

def get_persistent_signals(username: str, min_days: int = 2) -> pd.DataFrame:
    """Kullanıcıya özel ardışık günlerde aynı yönde sinyal veren hisseleri bulur."""
    with engine.connect() as conn:
        query = """SELECT ticker, decision, COUNT(DISTINCT scan_date) as gun_sayisi, 
           ROUND(AVG(score),1) as ort_skor,
           MIN(scan_date) as ilk_tarih, MAX(scan_date) as son_tarih
           FROM scan_history
           WHERE decision NOT IN ('Nötr', '⚖️ Nötr / Konsolidasyon', 'Hata', 'Veri Yetersiz') AND username=%(u)s
           GROUP BY ticker, decision
           HAVING COUNT(DISTINCT scan_date) >= %(m)s
           ORDER BY gun_sayisi DESC, ort_skor DESC""" if engine.name == 'postgresql' else """SELECT ticker, decision, COUNT(DISTINCT scan_date) as gun_sayisi, 
           ROUND(AVG(score),1) as ort_skor,
           MIN(scan_date) as ilk_tarih, MAX(scan_date) as son_tarih
           FROM scan_history
           WHERE decision NOT IN ('Nötr', '⚖️ Nötr / Konsolidasyon', 'Hata', 'Veri Yetersiz') AND username=?
           GROUP BY ticker, decision
           HAVING COUNT(DISTINCT scan_date) >= ?
           ORDER BY gun_sayisi DESC, ort_skor DESC"""
        
        df = pd.read_sql_query(query, conn, params={"u": username, "m": min_days} if engine.name == 'postgresql' else (username, min_days))
    return df


# ============================================================
# WATCHLIST - İzleme Listesi (YENİ - Özellik 8)
# ============================================================

# ============================================================
# WATCHLIST - İzleme Listesi (YENİ - Özellik 8)
# ============================================================

def add_to_watchlist(username: str, ticker: str, note: str = ""):
    try:
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO watchlist (username, ticker, added_date, note) VALUES (:u,:t,:d,:n)"),
                          {"u": username, "t": ticker, "d": datetime.now(TR_TZ).strftime("%Y-%m-%d %H:%M"), "n": note})
    except Exception as e:
        print(f"Watchlist insert error: {e}")
        raise e

def remove_from_watchlist(username: str, ticker: str):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM watchlist WHERE username=:u AND ticker=:t"), {"u": username, "t": ticker})

def get_watchlist(username: str) -> pd.DataFrame:
    with engine.connect() as conn:
        query = "SELECT * FROM watchlist WHERE username=%(u)s ORDER BY added_date DESC" if engine.name == 'postgresql' else "SELECT * FROM watchlist WHERE username=? ORDER BY added_date DESC"
        df = pd.read_sql_query(query, conn, params={"u": username} if engine.name == 'postgresql' else (username,))
    return df


# ============================================================
# MARKET STRUCTURE (SMC) & ARA HEDEFLER
# ============================================================
def detect_market_structure_break(df, order=10):
    if len(df) < order * 2:
        return {"bos_detected": False, "last_peak": None, "last_trough": None, "historical_breaks": []}
        
    closes = df['Close'].values
    highs = df['High'].values
    lows = df['Low'].values
    
    peak_indices = argrelextrema(highs, np.greater, order=order)[0]
    trough_indices = argrelextrema(lows, np.less, order=order)[0]
    
    if len(peak_indices) == 0:
        return {"bos_detected": False, "last_peak": None, "last_trough": None, "historical_breaks": []}
        
    last_peak_idx = peak_indices[-1]
    last_peak_price = highs[last_peak_idx]
    
    last_trough_price = None
    if len(trough_indices) > 0:
        last_trough_idx = trough_indices[-1]
        last_trough_price = lows[last_trough_idx]
        
    bos_detected = False
    current_close = closes[-1]
    
    if last_peak_idx < len(df) - 1:
        if current_close > last_peak_price:
            bos_detected = True
            
    historical_breaks = []
    # Son 5 zirveyi kontrol et
    for p_idx in peak_indices[-5:]:
        p_price = highs[p_idx]
        p_date_str = str(df.index[p_idx]).split(' ')[0] if hasattr(df, 'index') else str(p_idx)
        if 'Date' in df.columns:
             p_date_str = str(df['Date'].iloc[p_idx]).split(' ')[0]
             
        future_closes = closes[p_idx+1:]
        break_idx = np.where(future_closes > p_price)[0]
        if len(break_idx) > 0:
            b_idx = p_idx + 1 + break_idx[0]
            b_date_str = str(df.index[b_idx]).split(' ')[0] if hasattr(df, 'index') else str(b_idx)
            if 'Date' in df.columns:
                 b_date_str = str(df['Date'].iloc[b_idx]).split(' ')[0]
            historical_breaks.append({
                "peak_date": p_date_str,
                "peak_price": float(p_price),
                "break_date": b_date_str,
                "broken": True
            })
        else:
            historical_breaks.append({
                "peak_date": p_date_str,
                "peak_price": float(p_price),
                "break_date": "-",
                "broken": False
            })
            
    return {
        "bos_detected": bos_detected,
        "last_peak": float(last_peak_price),
        "last_trough": float(last_trough_price) if last_trough_price else None,
        "historical_breaks": historical_breaks
    }

# ============================================================
# TEKİL HİSSE ANALİZ FONKSİYONU (Paralel tarama için)
# ============================================================

def _analyze_single_stock(sym: str, market_regime: dict = None) -> dict:
    """Tek bir hisseyi analiz eder ve sonuç sözlüğü döndürür. ThreadPool için."""
    try:
        df = fetch_data(sym, interval="1d", period="1y")
        if df.empty or len(df) < 50:
            return None
            
        df = df.copy()
        df = calculate_indicators(df, ticker=sym)
        last = df.iloc[-1]
        sig = generate_signals_and_score(df, ticker=sym, market_regime=market_regime)
        if sig.get('decision') == 'Hata':
             return None
        
        # Fiyat & Değişim (SSOT kullanarak)
        from data_loader import get_batch_live_prices
        ssot = get_batch_live_prices([sym]).get(sym, {})
        display_price = ssot.get("price", df['Close'].iloc[-1])
        pct_change = ssot.get("change", ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100 if len(df) >= 2 else 0)

        # Hacim Analizi (Yeni - Detaylı)
        vol_conf = calculate_volume_confirmation(df, is_bear=market_regime['is_bear'] if market_regime else False)
        vol_ratio = round(vol_conf['ratio'], 2)
        vol_text = f"{vol_ratio}x ({vol_conf['status']})"

        # ==========================================
        # SMC: Düzen Kırılımı (BOS) ve Ara Hedefler
        # ==========================================
        smc_structure = detect_market_structure_break(df, order=10)
        duzen_kirilimi = "Kırılım 🔥" if smc_structure["bos_detected"] else "-"
        
        # ATR Bazlı Ara Hedef (tp_intermediate_atr) = 1.5 * ATR
        atr_val = df['ATR_14'].iloc[-1] if 'ATR_14' in df.columns else 0
        tp_intermediate_atr = round(display_price + (1.5 * atr_val), 2) if atr_val > 0 else 0
        
        # Zirve Bazlı Ara Hedef
        tp_intermediate_resistance = smc_structure["last_peak"] if smc_structure["last_peak"] else 0
        
        # Ekranda Gösterilecek Ara Hedef
        ara_hedef_str = f"{tp_intermediate_resistance:.2f}" if tp_intermediate_resistance > display_price else f"{tp_intermediate_atr:.2f}"


        # Zirve Uzaklığı (Yeni)
        day_high = last['High']
        dist_from_high = 0
        if day_high > 0:
            dist_from_high = ((day_high - display_price) / day_high) * 100
        
        # Trend Gücü (ADX)
        ad_val = last.get('ADX_14', 0)
        adx_text = f"{round(ad_val, 1)} (Güçlü)" if ad_val > 25 else f"{round(ad_val, 1)} (Zayıf)"

        # Uyumsuzluk (Yeni)
        div_status = detect_rsi_divergence(df)
        div_text = div_status if div_status != "Normal" else "-"

        # Trend Onayı (EMA 200)
        ema200_status = "BULLish 🚀" if display_price > df['EMA_200'].iloc[-1] else "BEARish 🐻" if pd.notna(df['EMA_200'].iloc[-1]) else "-"

        # Formasyon
        pattern_text = "-"
        p_res = detect_candlestick_patterns(df)
        if p_res and p_res.get('summary') and "tespit edilmedi" not in p_res.get('summary'):
            pattern_text = p_res['summary'].splitlines()[0].replace('*', '').replace('Tespit edildi: ', '').strip()

        # Dipten Dönüş (Geliştirilmiş Hibrit Mantık)
        reversal_res = check_bottom_reversal(df)
        reversal = reversal_res.get('summary', reversal_res.get('text', '-')) if reversal_res['detected'] else "-"

        # Destek/Direnç
        zones = calculate_best_zones(df)
        dist_sup = "-"
        dist_res = "-"
        d_pct = 999.0 # Varsayılan olarak destekten çok uzak / destek yok
        if zones.get('supports'):
            sup = zones['supports'][0][1] # (label, price) tuple
            d_pct = ((display_price - sup) / display_price) * 100
            dist_sup = f"%{d_pct:.1f}" if d_pct > 0 else "Destekte"
        if zones.get('resistances'):
            res_price = zones['resistances'][0][1]
            r_pct = ((res_price - display_price) / display_price) * 100
            dist_res = f"%{r_pct:.1f}" if r_pct > 0 else "Dirençte"

        # 1H Uyum
        df_1h = fetch_data(sym, interval="1h", period="1mo")
        trend_uyum = "Tekil"
        if not df_1h.empty and len(df_1h) >= 20:
            df_1h = df_1h.copy()
            df_1h = calculate_indicators(df_1h)
            sig_1h = generate_signals_and_score(df_1h)
            if sig['decision'] in ["Al", "Güçlü Al"] and sig_1h['decision'] in ["Al", "Güçlü Al"]:
                trend_uyum = "✅ Çift AL (1D+1H)"
            elif sig['decision'] in ["Sat", "Güçlü Sat"] and sig_1h['decision'] in ["Sat", "Güçlü Sat"]:
                trend_uyum = "❌ Çift SAT (1D+1H)"
            else:
                trend_uyum = "⚠️ Karışık"

        # ==========================================
        # QUANTUM INDICATORS (SMC, Squeeze, VWAP)
        # ==========================================
        # SMC / Liquidity Sweep
        smc_res = detect_liquidity_sweep(df)
        smc_text = smc_res['summary'] if smc_res['detected'] else "-"
        
        # Volatility Squeeze
        sq_res = check_volatility_squeeze(df)
        sq_text = "Sıkışma 🔥" if sq_res['is_squeezing'] else "Ateşlendi 🚀" if sq_res['is_firing'] else "-"
        
        # OBV Divergence
        obv_res = calculate_obv_divergence(df)
        obv_text = "Gizli Toplama 💹" if obv_res['detected'] else "-"
        
        # VWAP Kontrolü
        vwap_val = df['VWAP_5'].iloc[-1] if 'VWAP_5' in df.columns else display_price
        vwap_dist = ((display_price - vwap_val) / vwap_val) * 100
        
        # Alpha (Göreceli Güç)
        alpha_text = "-"
        if market_regime and 'xu100_5d_chg' in market_regime:
            xu100_5d_chg = market_regime['xu100_5d_chg']
            sym_5d = ((display_price - df['Close'].iloc[-5]) / df['Close'].iloc[-5]) * 100 if len(df) >= 5 else 0
            alpha_val = sym_5d - xu100_5d_chg
            alpha_text = f"{alpha_val:+.1f}%"

        rsi_val = df['RSI_14'].iloc[-1] if 'RSI_14' in df.columns else None
        sector = get_sector(sym)

        # ==========================================
        # V6 HİBRİT TEMEL ANALİZ (YENİ)
        # ==========================================
        try:
            from fundamental_analyzer import get_fundamental_data
            fund_data = get_fundamental_data(sym)
        except Exception:
            fund_data = {"pe": 0.0, "pb": 0.0, "div_yield": 0.0, "graham_value": 0.0, "fundamental_score": 50, "status": "Veri Yok"}
            
        tek_skor = sig['score']
        tem_skor = fund_data['fundamental_score']
        core_score = sig.get('core_score', 50)
        core_decision = sig.get('core_decision', sig.get('decision', 'Nötr'))
        
        # V6 HİBRİT SKOR: %40 Core (SSOT), %30 Modül Overlay (Teknik), %30 Temel
        v6_hybrid_score = round((core_score * 0.4) + (tek_skor * 0.3) + (tem_skor * 0.3), 1)
        
        # Graham Güvenlik Marjı / Potansiyel (%)
        g_val = fund_data.get('graham_value', 0.0)
        g_pot = 0.0
        # g_val string (N/A) olabilir, kontrol et
        if isinstance(g_val, (int, float)) and g_val > 0 and display_price > 0:
            g_pot = round(((g_val - display_price) / display_price) * 100, 1)

        # Takas Verisi (Yabancı Oranı)
        takas = get_takas_data(sym)
        foreign_ratio = takas.get('foreign_ratio', 0.0)

        # Desteğe Yakınlık Skoru (0-100)
        # Tam destekte veya altındaysa 100 puan, her %1 uzaklaşma için -10 puan
        sup_score = max(0.0, 100.0 - (d_pct * 10.0)) if d_pct >= 0 else 100.0
        
        # Sinyal Bonusları
        trend_bonus = 10.0 if "Çift AL" in trend_uyum else 0.0
        smc_bonus = 5.0 if smc_res['detected'] else 0.0
        obv_bonus = 5.0 if obv_res['detected'] else 0.0
        
        # Ensemble Güven Skoru
        ensemble_score = (v6_hybrid_score * 0.40) + (sig['pgs'] * 0.40) + (sup_score * 0.20) + trend_bonus + smc_bonus + obv_bonus
        ensemble_score = round(min(100.0, max(0.0, ensemble_score)), 1)

        return {
            "Hisse": sym,
            "Fiyat": round(display_price, 2),
            "Değişim (%)": round(pct_change, 2),
            "Göreceli Güç (Alpha)": alpha_text,
            "Ensemble Güven Skoru": ensemble_score,
            "V6 Hibrit Skor": v6_hybrid_score,
            "Yabancı Oranı (%)": round(foreign_ratio, 1),
            "Takas Değişimi (%)": round(takas.get('daily_change', 0.0), 2),
            "Risk/Ödül (R/R)": round(sig.get('rr_ratio', 0), 2),
            "SMC / Stop Avı": smc_text,
            "Sıkışma Durumu": sq_text,
            "Hacim Diverjans": obv_text,
            "VWAP Uzaklık": f"%{vwap_dist:.1f}",
            "Piyasa Kararı": core_decision,
            "Güven Skoru (PGS)": sig['pgs'],
            "ADX": round(float(last.get('ADX_14', 0)), 1),
            "1D+1H Uyum": trend_uyum,
            "RSI": round(rsi_val, 1) if rsi_val and pd.notna(rsi_val) else "-",
            "Desteğe Uzaklık": dist_sup,
            "Dirence Uzaklık": dist_res,
            "Teknik Potansiyel": tek_skor,
            "Temel Not": tem_skor,
            "Temel Durum": fund_data.get('status', 'Normal'),
            "PD/DD": fund_data.get('pb', 0),
            "F/K": fund_data.get('pe', 0),
            "Sektör": sector,
            "Düzen Kırılımı": duzen_kirilimi,
            "Ara Hedef (₺)": ara_hedef_str
        }
    except Exception as e:
        import traceback
        import logging
        logging.error(f"Error in _analyze_single_stock for {sym}: {str(e)}")
        traceback.print_exc()
        return None

# ============================================================
# ANA TARAYICI FONKSİYONU (Paralel + Sektör + Geçmiş Kayıt)
# ============================================================

def run_screener(symbol_list: list, username: str, progress_bar=None, max_workers: int = 5) -> pd.DataFrame:
    """
    Paralel çoklu iş parçacığı ile hisseleri tarar.
    Sonuçları otomatik olarak SQLite'a kaydeder.
    """
    results = []
    total = len(symbol_list)
    completed = 0

    # 1. Piyasa Rejimi Onayı (BIST 100 Analizi)
    xu100_df = fetch_data("XU100", interval="1d", period="1y")
    market_regime = get_market_regime(xu100_df)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_sym = {executor.submit(_analyze_single_stock, sym, market_regime): sym for sym in symbol_list}
        
        for future in as_completed(future_to_sym):
            completed += 1
            sym = future_to_sym[future]
            try:
                result = future.result()
                if result is not None:
                    results.append(result)
                
                if progress_bar:
                    progress_bar.progress(completed / total, text=f"{sym} tarandı ({completed}/{total})")
            except Exception:
                pass
            
    if not results:
        return pd.DataFrame()
        
    res_df = pd.DataFrame(results)
    res_df = res_df.sort_values(by="Ensemble Güven Skoru", ascending=False).reset_index(drop=True)
    
    # Tarama sonuçlarını SQLite'a kaydet (Özellik 2)
    save_scan_results(res_df, username)
    
    return res_df
