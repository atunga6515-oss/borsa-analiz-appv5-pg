import logging
import concurrent.futures
from datetime import datetime, timedelta
from sqlalchemy import text
from database import engine
import pandas as pd
import yfinance as yf

from screener import BIST100_SYMBOLS
from data_loader import fetch_data, get_live_price
from signals_engine import generate_historical_signals

logger = logging.getLogger(__name__)

# Fallback mechanism if live price is <= 0
def get_safe_live_price(ticker: str, fallback_price: float) -> float:
    lp = get_live_price(ticker)
    if lp is None or lp <= 0:
        return fallback_price
    return lp

# --- 1. HOURLY MACRO SCAN (WATCHLIST) ---
def _scan_macro_ticker(ticker: str):
    df = fetch_data(ticker, "1d", "6mo")
    if df is not None and not df.empty:
        df, _, _ = generate_historical_signals(df, "Dengeli")
        last_row = df.iloc[-1]
        buy_vote = float(last_row.get('Buy_Vote_Strength', 0.0))
        if buy_vote >= 60.0 or not pd.isna(last_row.get('Buy_Signal')):
            return {"ticker": ticker, "vote": buy_vote}
    return None

def process_robot_hourly_scan():
    """Saatlik makro tarama. BIST100'de günlükte Güçlü Al verenleri watchlist'e yazar."""
    logger.info("[ROBOT] Saatlik Makro Tarama (Watchlist) Başlıyor...")
    
    # Sadece aktif robot seansı varsa tarama yap (Gereksiz API yükünü önlemek için)
    with engine.connect() as conn:
        active = conn.execute(text("SELECT id FROM robot_sessions WHERE status = 'active' LIMIT 1")).fetchone()
        if not active:
            logger.info("[ROBOT] Aktif seans yok, tarama atlandı.")
            return

    results = []
    # ThreadPoolExecutor ile asenkron / paralel tarama
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(_scan_macro_ticker, t): t for t in BIST100_SYMBOLS}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
                
    # Veritabanında watchlist'i temizle ve yenilerini ekle
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM robot_watchlist"))
        for r in results:
            conn.execute(
                text("INSERT INTO robot_watchlist (ticker, vote_strength) VALUES (:t, :v)"),
                {"t": r["ticker"], "v": r["vote"]}
            )
    
    logger.info(f"[ROBOT] Saatlik Tarama Tamamlandı. {len(results)} hisse watchlist'e eklendi.")

# --- 2. 5 MINUTE MICRO LOOP (BUY/SELL) ---

def _fetch_5m_data(tickers: list) -> dict:
    """Belirtilen hisselerin 5 dakikalık verilerini toplu yfinance kullanarak asenkron çeker."""
    if not tickers:
        return {}
    
    tickers_is = [t + ".IS" for t in tickers]
    df = yf.download(tickers_is, interval="5m", period="5d", progress=False, group_by="ticker")
    
    data_dict = {}
    if len(tickers) == 1:
        t = tickers[0]
        t_is = t + ".IS"
        if not df.empty and t_is not in df.columns: # Single index if 1 ticker
             df_clean = df.dropna(subset=['Close'])
             if not df_clean.empty:
                 data_dict[t] = df_clean
    else:
        for t in tickers:
            t_is = t + ".IS"
            if t_is in df.columns.levels[0]:
                df_t = df[t_is].dropna(subset=['Close'])
                if not df_t.empty:
                    data_dict[t] = df_t
    return data_dict

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def _analyze_5m_buy(df: pd.DataFrame) -> bool:
    """RSI 50'yi yukarı kesiyorsa ve hacim ortalamanın üstündeyse Al."""
    if len(df) < 15:
        return False
        
    df = df.copy()
    df['RSI'] = calculate_rsi(df['Close'])
    df['Vol_MA'] = df['Volume'].rolling(10).mean()
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    # RSI kesişimi (önceki < 50, şimdiki > 50) ve Hacim > Ortalama Hacim
    if pd.isna(last['RSI']) or pd.isna(prev['RSI']):
        return False
        
    rsi_crossed = prev['RSI'] < 50 and last['RSI'] >= 50
    vol_ok = last['Volume'] > last['Vol_MA']
    
    return rsi_crossed and vol_ok

def _analyze_5m_sell(df: pd.DataFrame) -> bool:
    """Aşırı alım (RSI > 70) varsa Sat (SL ve TP dışındaki teknik sat)"""
    if len(df) < 15:
        return False
    df = df.copy()
    df['RSI'] = calculate_rsi(df['Close'])
    last = df.iloc[-1]
    
    if not pd.isna(last['RSI']) and last['RSI'] >= 70:
        return True
    return False

def get_mode_limits(mode: str):
    if mode == "Temkinli": return 2.0, -1.0 # TP %, SL %
    if mode == "Agresif": return 5.0, -3.0
    return 3.0, -1.5 # Normal

def process_robot_core_loop():
    """Her 5 dakikada bir çalışır. Watchlist'ten alım arar, portföyden satış arar."""
    now = datetime.now()
    
    try:
        with engine.begin() as conn:
            active_sessions = conn.execute(
                text("SELECT id, current_balance, end_date, mode, max_positions FROM robot_sessions WHERE status = 'active'")
            ).fetchall()
            
            if not active_sessions:
                return

            # Watchlist'i al
            watchlist = [row[0] for row in conn.execute(text("SELECT ticker FROM robot_watchlist")).fetchall()]
            
            # Portföydeki tüm eşsiz hisseleri al
            portfolio_items = conn.execute(
                text("SELECT session_id, id, ticker, adet, alis_fiyati FROM robot_portfolio")
            ).fetchall()
            
            port_tickers = list(set([row[2] for row in portfolio_items]))
            
        # Toplu 5 dakikalık veri çek (Asenkron)
        all_tickers_to_fetch = list(set(watchlist + port_tickers))
        data_5m = _fetch_5m_data(all_tickers_to_fetch)
        
        with engine.begin() as conn:
            for session in active_sessions:
                session_id, current_balance, end_date_str, mode, max_positions = session
                
                # Check expiration
                is_expired = False
                if isinstance(end_date_str, str):
                    try:
                        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S.%f")
                    except:
                        try:
                            end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
                        except:
                            end_date = now
                    is_expired = now >= end_date
                elif isinstance(end_date_str, datetime):
                    is_expired = now >= end_date_str

                tp_pct, sl_pct = get_mode_limits(mode)

                # 1. SATIŞ KONTROLÜ (Exit)
                my_portfolio = [p for p in portfolio_items if p[0] == session_id]
                total_sold_value = 0.0
                
                held_tickers = []
                for p in my_portfolio:
                    port_id = p[1]
                    ticker = p[2]
                    adet = p[3]
                    alis = p[4]
                    
                    df = data_5m.get(ticker)
                    last_close = float(df.iloc[-1]['Close']) if df is not None and not df.empty else alis
                    
                    live_price = get_safe_live_price(ticker, fallback_price=last_close)
                    
                    pnl_pct = ((live_price - alis) / alis) * 100 if alis > 0 else 0
                    
                    should_sell = is_expired
                    reason = "Süre Doldu (Zorunlu Kapanış)"
                    
                    if not should_sell:
                        # TP / SL Kontrolü
                        if pnl_pct >= tp_pct:
                            should_sell = True
                            reason = f"Take Profit (Kar Al) Hedefi: %{pnl_pct:.2f}"
                        elif pnl_pct <= sl_pct:
                            should_sell = True
                            reason = f"Stop Loss (Zarar Kes) Tetiklendi: %{pnl_pct:.2f}"
                        elif df is not None and _analyze_5m_sell(df):
                            should_sell = True
                            reason = "Aşırı Alım (RSI > 70) Teknik Çıkış"
                        elif mode == "Agresif" and pnl_pct < 0:
                            # Fırsat Maliyeti: Agresif modda zarardayken watchlist'te sağlam hisse varsa sat
                            if watchlist: 
                                should_sell = True
                                reason = "Fırsat Maliyeti (Zararına Kesip Yeni Fırsata Geçiş)"
                    
                    if should_sell:
                        sell_value = live_price * adet
                        commission = sell_value * 0.002
                        net_sell_value = sell_value - commission
                        total_sold_value += net_sell_value
                        
                        conn.execute(
                            text("INSERT INTO robot_trades (session_id, ticker, type, price, adet, reason) VALUES (:sid, :t, 'SELL', :p, :a, :r)"),
                            {"sid": session_id, "t": ticker, "p": live_price, "a": adet, "r": reason}
                        )
                        conn.execute(text("DELETE FROM robot_portfolio WHERE id = :id"), {"id": port_id})
                        logger.info(f"[ROBOT] {ticker} SATILDI. Neden: {reason}")
                    else:
                        held_tickers.append(ticker)
                        
                current_balance += total_sold_value
                
                # Update Session if changed
                if total_sold_value > 0:
                    conn.execute(text("UPDATE robot_sessions SET current_balance = :b WHERE id = :id"), {"b": current_balance, "id": session_id})
                
                if is_expired:
                    conn.execute(text("UPDATE robot_sessions SET status = 'completed' WHERE id = :id"), {"id": session_id})
                    continue

                # 2. ALIŞ KONTROLÜ (Entry)
                open_positions = len(held_tickers)
                if open_positions >= max_positions:
                    continue # Kapasite dolu
                
                # Kasayı boş yuvalara böl
                available_slots = max_positions - open_positions
                slot_budget = current_balance / available_slots
                
                for ticker in watchlist:
                    if ticker in held_tickers:
                        continue
                        
                    if current_balance < 1000:
                        break # Bakiye bitti
                        
                    df = data_5m.get(ticker)
                    if df is not None and _analyze_5m_buy(df):
                        # Alım sinyali!
                        last_close = float(df.iloc[-1]['Close'])
                        live_price = get_safe_live_price(ticker, fallback_price=last_close)
                        
                        investment = min(slot_budget, current_balance)
                        adet = int(investment // (live_price * 1.002))
                        if adet <= 0:
                            continue
                            
                        net_cost = (adet * live_price) * 1.002
                        
                        conn.execute(
                            text("INSERT INTO robot_portfolio (session_id, ticker, adet, alis_fiyati) VALUES (:sid, :t, :a, :p)"),
                            {"sid": session_id, "t": ticker, "a": adet, "p": live_price}
                        )
                        reason = "5m RSI 50 Yukarı Kesişim & Hacim Onayı"
                        conn.execute(
                            text("INSERT INTO robot_trades (session_id, ticker, type, price, adet, reason) VALUES (:sid, :t, 'BUY', :p, :a, :r)"),
                            {"sid": session_id, "t": ticker, "p": live_price, "a": adet, "r": reason}
                        )
                        
                        current_balance -= net_cost
                        conn.execute(text("UPDATE robot_sessions SET current_balance = :b WHERE id = :id"), {"b": current_balance, "id": session_id})
                        logger.info(f"[ROBOT] {ticker} ALINDI. Adet: {adet}, Fiyat: {live_price}")
                        
                        held_tickers.append(ticker)
                        open_positions += 1
                        slot_budget = current_balance / max(1, (max_positions - open_positions))
                        
                        if open_positions >= max_positions:
                            break # Kapasite doldu

    except Exception as e:
        import traceback
        logger.error(f"[ROBOT] Core loop hatası: {e}")
        traceback.print_exc()
