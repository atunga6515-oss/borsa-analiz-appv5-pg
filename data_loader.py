import yfinance as yf
import pandas as pd
import numpy as np
import os
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta, timezone
import pytz
from cache_utils import ttl_cache
from database import engine
from sqlalchemy import text
# Timezone Ayarı
TR_TZ = pytz.timezone("Europe/Istanbul")

def get_istanbul_now():
    """Türkiye yerel saatini döndürür (BIST seansları için kritik)."""
    return datetime.now(TR_TZ)

# ============================================================
# Veritabanı Yönetimi (SQLAlchemy)
# ============================================================

def _get_yf_session():
    """Yahoo Finance için basitleştirilmiş tarayıcı kimliği."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    return session

def _make_ticker(symbol: str) -> str:
    """Kullanıcının girdiği koda .IS ekler, ancak global sembollere dokunmaz."""
    symbol_upper = symbol.upper().strip()
    if symbol_upper.endswith('.IS') or any(x in symbol_upper for x in ['=', '^', '-']):
        return symbol_upper
    return f"{symbol_upper}.IS"

def _save_to_db(df: pd.DataFrame, ticker: str, interval: str):
    """DataFrame'i veritabanına yazar (DB dialectine göre toplu/bulk Upsert)."""
    if df.empty:
        return
        
    # Sütun adlarını veritabanı şemasına uygun hale getirelim
    df_db = df.copy()
    df_db = df_db.rename(columns={
        'Open': 'open', 'High': 'high', 'Low': 'low', 
        'Close': 'close', 'Adj Close': 'adj_close', 'Volume': 'volume'
    })
    
    if 'adj_close' not in df_db.columns:
        df_db['adj_close'] = df_db.get('close', 0.0)
        
    df_db['ticker'] = ticker
    df_db['interval'] = interval
    
    # Tarihi index'ten veya Date sütunundan çekip 'date' yapalım
    if isinstance(df_db.index, pd.DatetimeIndex) or getattr(df_db.index, 'name', None) in ['Date', 'date']:
        df_db['date'] = df_db.index
        # Index type datetime ise string'e çevir:
        if isinstance(df_db.index, pd.DatetimeIndex):
             df_db['date'] = df_db['date'].dt.strftime('%Y-%m-%d')
        else:
             df_db['date'] = df_db['date'].astype(str)
        df_db = df_db.reset_index(drop=True)
    elif 'Date' in df_db.columns:
        df_db['date'] = df_db['Date'].astype(str)
        
    cols = ['ticker', 'date', 'interval', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
    df_db = df_db[[c for c in cols if c in df_db.columns]]
    df_db = df_db.fillna(0.0)
    
    if engine.name == 'postgresql':
        from sqlalchemy.dialects.postgresql import insert
        def psql_upsert(table, conn, keys, data_iter):
            data = [dict(zip(keys, row)) for row in data_iter]
            stmt = insert(table.table).values(data)
            stmt = stmt.on_conflict_do_update(
                index_elements=['ticker', 'date', 'interval'],
                set_={c.key: c for c in stmt.excluded if c.key not in ['ticker', 'date', 'interval']}
            )
            conn.execute(stmt)
            
        # Toplu yazma operasyonu
        df_db.to_sql('ohlcv', engine, if_exists='append', index=False, method=psql_upsert, chunksize=500)
    else:
        # SQLite fallback: hızlı execute_many insert/replace
        with engine.begin() as conn:
            records = df_db.to_dict('records')
            q = text("""
                INSERT OR REPLACE INTO ohlcv
                (ticker, date, interval, open, high, low, close, adj_close, volume)
                VALUES (:ticker, :date, :interval, :open, :high, :low, :close, :adj_close, :volume)
            """)
            conn.execute(q, records)

def _load_from_db(ticker: str, interval: str) -> pd.DataFrame:
    """Veritabanından o ticker'ın tüm kayıtlı verisini DataFrame olarak döndürür."""
    query = "SELECT date, open, high, low, close, adj_close, volume FROM ohlcv WHERE ticker=%(t)s AND interval=%(i)s ORDER BY date" if engine.name == 'postgresql' else "SELECT date, open, high, low, close, adj_close, volume FROM ohlcv WHERE ticker=? AND interval=? ORDER BY date"
    
    with engine.connect() as conn:
        if engine.name == 'postgresql':
            df = pd.read_sql_query(query, conn, params={"t": ticker, "i": interval})
        else:
            df = pd.read_sql_query(query, conn, params=(ticker, interval))
            
    if df.empty:
        return pd.DataFrame()
    
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df.columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    return df

def _get_last_date_in_db(ticker: str, interval: str) -> str:
    """Veritabanında bu ticker için kayıtlı en son tarihi döndürür."""
    with engine.connect() as conn:
        cursor = conn.execute(
            text("SELECT MAX(date) FROM ohlcv WHERE ticker=:t AND interval=:i"),
            {"t": ticker, "i": interval}
        )
        result = cursor.fetchone()[0]
    return result


def _download_from_yfinance(ticker: str, interval: str, start: str = None, period: str = None) -> pd.DataFrame:
    """yfinance'ten veri indirir. Başarısız olursa oturumsuz deneme yapar."""
    session = _get_yf_session()
    
    # 1. Deneme: Sessiz (Custom Session ile)
    try:
        if start:
            data = yf.download(ticker, start=start, interval=interval,
                               group_by="ticker", progress=False,
                               auto_adjust=False, repair=True, 
                               session=session, threads=False)
        else:
            data = yf.download(ticker, period=period or "90d", interval=interval,
                               group_by="ticker", progress=False,
                               auto_adjust=False, repair=True, 
                               session=session, threads=False)

        if not data.empty:
            return _clean_yf_data(data, ticker)
    except:
        pass

    # 2. Deneme: Yalın (Oturumsuz - Fallback)
    try:
        time.sleep(0.5)
        if start:
            data = yf.download(ticker, start=start, interval=interval,
                               group_by="ticker", progress=False,
                               auto_adjust=False, repair=True, threads=False)
        else:
            data = yf.download(ticker, period=period or "90d", interval=interval,
                               group_by="ticker", progress=False,
                               auto_adjust=False, repair=True, threads=False)
        return _clean_yf_data(data, ticker)
    except:
        return pd.DataFrame()

def _clean_yf_data(data: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """yfinance verisini temizler ve MultiIndex ise düzleştirir."""
    if data.empty:
        return pd.DataFrame()
        
    if isinstance(data.columns, pd.MultiIndex):
        if ticker in data.columns.get_level_values(1):
            data = data.xs(ticker, axis=1, level=1)
        elif ticker in data.columns.get_level_values(0):
            data = data.xs(ticker, axis=1, level=0)
        else:
            data.columns = data.columns.droplevel(1)
            
    data.ffill(inplace=True)
    data.dropna(inplace=True)
    return data


# ============================================================
# ANA FONKSİYONLAR (Dışarıya açık API)
# ============================================================

@ttl_cache(ttl_seconds=300)
def fetch_data(symbol: str, interval: str = "1d", period: str = "1y") -> pd.DataFrame:
    """
    Akıllı veri çekme fonksiyonu:
    1. Veritabanında veri var mı kontrol eder.
    2. Varsa, veri miktarının periyot (period) için yeterli olup olmadığını kontrol eder. 
       Örn: "5y" istenmişse ama DB'de "1y" varsa tamamını baştan çeker.
    3. Yeterli geçmiş varsa, sadece son tarihten bugüne kadar olan eksikleri tamamlar.
    """
    auto_cleanup_db() # Veritabanı temizliği kontrolü
    ticker = _make_ticker(symbol)

    # Önce DB'den tüm mevcut veriyi çekmeyi deneyelim
    db_df = _load_from_db(ticker, interval)

    # İstenen periyodun tahmini işlem günü sayısını bulalım
    required_rows = 0
    if "y" in period:
        required_rows = int(period.replace('y','')) * 250
    elif "mo" in period:
        required_rows = int(period.replace('mo','')) * 21

    if db_df.empty:
        # Veritabanında hiç veri yok
        df_new = _download_from_yfinance(ticker, interval, period=period)
        if not df_new.empty:
            _save_to_db(df_new, ticker, interval)
    elif len(db_df) < required_rows * 0.85: # %15 tolerans payı
        # DB'de veri var ama istenen kadar geçmişe gitmiyor (Örn: DB'de 1 yıl var, backtest 5 yıl istiyor)
        df_new = _download_from_yfinance(ticker, interval, period=period)
        if not df_new.empty:
            _save_to_db(df_new, ticker, interval)
    else:
        # DB'de yeterli geçmiş veri var. Sadece son güncellemeleri alalım.
        last_date = _get_last_date_in_db(ticker, interval)
        if last_date:
            last_dt = datetime.strptime(last_date, "%Y-%m-%d").replace(tzinfo=TR_TZ)
            today = get_istanbul_now()
            
            # 1 günden fazla fark varsa yeni günleri çek
            if (today - last_dt).days >= 1:
                start_date = (last_dt + timedelta(days=1)).strftime("%Y-%m-%d")
                df_new = _download_from_yfinance(ticker, interval, start=start_date)
                if not df_new.empty:
                    _save_to_db(df_new, ticker, interval)

    # Veritabanındaki güncel halini döndür
    final_df = _load_from_db(ticker, interval)
    
    # Anlık fiyat uyumsuzluğunu (Dashboard vs Analiz) gidermek için günün son mumunu anlık API'den yama yap
    if interval == "1d":
        try:
            live_df = _download_from_yfinance(ticker, interval="1d", period="1d")
            if not live_df.empty:
                live_idx = live_df.index[-1]
                if not final_df.empty and live_idx in final_df.index:
                    # Var olan o günün mumunu taze live mumuyla güncelle
                    final_df.loc[live_idx] = live_df.iloc[-1]
                else:
                    # Yeni bir gün mumu ise dataframe'in sonuna ekle
                    final_df = pd.concat([final_df, live_df])
        except Exception as e:
            pass
            
    return final_df


@ttl_cache(ttl_seconds=300)
def fetch_multiple_close_prices(symbols: list, interval: str = "1d", period: str = "1mo") -> pd.DataFrame:
    """
    Korelasyon/Screener hesabı için birden fazla hissenin kapanış fiyatını çeker.
    Her biri için SQLite cache'i kullanır.
    """
    close_frames = {}
    for s in symbols:
        df = fetch_data(s, interval, period)
        if not df.empty and 'Close' in df.columns:
            ticker = _make_ticker(s)
            close_frames[ticker] = df['Close']

    if not close_frames:
        return pd.DataFrame()

    result = pd.DataFrame(close_frames)
    result.dropna(inplace=True)
    return result


@ttl_cache(ttl_seconds=300)
def fetch_weekly_data(symbol: str, period: str = "2y") -> pd.DataFrame:
    """
    Öncelikle Multi-Timeframe analiz (MTF) için haftalık veri çeker.
    fetch_data altyapısını kullanarak veritabanına kaydeder/önbellekler.
    """
    # 2 yıl = 104 hafta. Haftalık analizler için bu periyot uygundur.
    return fetch_data(symbol, interval="1wk", period=period)


def get_db_stats() -> dict:
    """Veritabanı istatistiklerini döndürür (uygulama arayüzünde göstermek için)."""
    try:
        with engine.connect() as conn:
            total_rows = conn.execute(text("SELECT COUNT(*) FROM ohlcv")).fetchone()[0]
            unique_tickers = conn.execute(text("SELECT COUNT(DISTINCT ticker) FROM ohlcv")).fetchone()[0]
            
            db_size_mb = 0
            if engine.name == 'postgresql':
                db_size = conn.execute(text("SELECT pg_database_size(current_database())")).fetchone()[0]
                db_size_mb = db_size / (1024 * 1024)
            else:
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bist_cache.db")
                if os.path.exists(db_path):
                    db_size_mb = os.path.getsize(db_path) / (1024 * 1024)
                    
        return {
            "total_rows": total_rows,
            "unique_tickers": unique_tickers,
            "db_size_mb": round(db_size_mb, 2)
        }
    except Exception:
        return {"total_rows": 0, "unique_tickers": 0, "db_size_mb": 0}

def get_ticker_db_info(symbol: str) -> dict:
    """Belirli bir hissenin DB'deki en eski, en yeni tarihini ve satır sayısını döndürür."""
    if not symbol:
        return {}
    ticker = _make_ticker(symbol)
    try:
        with engine.connect() as conn:
            res = conn.execute(
                text("SELECT MIN(date), MAX(date), COUNT(*) FROM ohlcv WHERE ticker=:t"), 
                {"t": ticker}
            ).fetchone()
            
        if res and res[2] > 0:
            return {
                "first_date": res[0],
                "last_date": res[1],
                "row_count": res[2]
            }
    except Exception:
        pass
    return {}

def clear_db():
    """Veritabanını tamamen temizler (Reset butonu için)."""
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM ohlcv"))
    except Exception:
        pass

def auto_cleanup_db(days: int = 30):
    """30 günden eski tarama geçmişini otomatik temizler."""
    try:
        cutoff_date = (get_istanbul_now() - timedelta(days=days)).strftime("%Y-%m-%d")
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM scan_history WHERE scan_date < :c"), {"c": cutoff_date})
    except Exception:
        pass

def get_live_price(symbol: str) -> float:
    """Veritabanını (Cache) tamamen pas geçip, yfinance üzerinden anlık en son fiyatı çeker."""
    ticker = _make_ticker(symbol)
    session = _get_yf_session()
    
    def _safe_get(p, iv):
        # 1. Deneme: Session ile
        try:
            d = yf.download(ticker, period=p, interval=iv, progress=False, 
                             group_by="ticker", auto_adjust=False, repair=True, 
                             session=session, threads=False)
            if not d.empty: return d
        except: pass
        
        # 2. Deneme: Yalın
        try:
            time.sleep(0.3)
            d = yf.download(ticker, period=p, interval=iv, progress=False, 
                             group_by="ticker", auto_adjust=False, repair=True, threads=False)
            return d
        except: return pd.DataFrame()

    try:
        data = _safe_get("1d", "1m")
        data = _clean_yf_data(data, ticker)
                
        if not data.empty and 'Close' in data.columns:
            return float(data['Close'].iloc[-1])
            
        # 1 dakikalık veri bulunamadıysa günlük veriden en son fiyatı çekmeyi dene
        data = _safe_get("5d", "1d")
        data = _clean_yf_data(data, ticker)
        if not data.empty and 'Close' in data.columns:
            return float(data['Close'].iloc[-1])
            
        return 0.0
    except Exception:
        return 0.0

def get_live_price_with_change(symbol: str) -> tuple:
    """Anlık fiyatı ve dünkü kapanışa göre değişim miktarını döndürür. (Fiyat, Değişim)"""
    ticker = _make_ticker(symbol)
    session = _get_yf_session()
    try:
        data = yf.download(ticker, period="5d", interval="1d", progress=False, group_by="ticker", auto_adjust=False, repair=True, session=session)
        if isinstance(data.columns, pd.MultiIndex):
            if ticker in data.columns.get_level_values(1):
                data = data.xs(ticker, axis=1, level=1)
            elif ticker in data.columns.get_level_values(0):
                data = data.xs(ticker, axis=1, level=0)
            else:
                data.columns = data.columns.droplevel(1)
                
        # Boş (NaN) verileri temizle
        data = data.dropna(subset=['Close'])
        
        if not data.empty and len(data) >= 2:
            current_price = float(data['Close'].iloc[-1])
            prev_price = float(data['Close'].iloc[-2])
            change = current_price - prev_price
            return current_price, change
        elif not data.empty:
            return float(data['Close'].iloc[-1]), 0.0
            
        return 0.0, 0.0
    except Exception:
        return 0.0, 0.0



