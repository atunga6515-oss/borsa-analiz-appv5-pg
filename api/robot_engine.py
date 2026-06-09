import logging
from datetime import datetime
from sqlalchemy import text
from database import engine
import pandas as pd

from data_loader import fetch_data, get_live_price
from signals_engine import generate_historical_signals
from screener import BIST100_SYMBOLS

logger = logging.getLogger(__name__)

def determine_position_size(vote_strength: float) -> float:
    """
    Güven seviyesine (vote_strength) göre yatırılacak sermaye yüzdesini belirler.
    Minimum %10, Maksimum %30.
    """
    # 60 ile 100 arasındaki bir gücü 10 ile 30 arasına mapliyoruz
    pct = 10.0 + ((vote_strength - 50.0) / 50.0) * 20.0
    return max(10.0, min(30.0, pct))

def process_robot_sales():
    """Her 10 dakikada bir çalışarak portföydeki hisseleri kontrol eder ve gerekirse satar."""
    now = datetime.now()
    try:
        with engine.begin() as conn:
            # Aktif seansları bul
            active_sessions = conn.execute(
                text("SELECT id, current_balance, end_date FROM robot_sessions WHERE status = 'active'")
            ).fetchall()
            
            if not active_sessions:
                return

            for session in active_sessions:
                session_id = session[0]
                current_balance = session[1]
                end_date_str = session[2]
                
                # Bitiş tarihi geldi mi?
                is_expired = False
                if isinstance(end_date_str, str):
                    try:
                        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
                        is_expired = now >= end_date
                    except:
                        pass
                elif isinstance(end_date_str, datetime):
                    is_expired = now >= end_date_str

                # Portföyü getir
                portfolio = conn.execute(
                    text("SELECT id, ticker, adet, alis_fiyati FROM robot_portfolio WHERE session_id = :sid"),
                    {"sid": session_id}
                ).fetchall()

                total_sold_value = 0.0

                for item in portfolio:
                    port_id, ticker, adet, alis_fiyati = item
                    
                    # Eğer süre bittiyse zorunlu sat
                    should_sell = is_expired
                    reason = "Süre Doldu (Zorunlu Kapanış)"
                    
                    # Süre bitmediyse teknik analiz yap
                    if not should_sell:
                        df = fetch_data(ticker, "1d", "6mo")
                        if df is not None and not df.empty:
                            df, _, _ = generate_historical_signals(df, "Dengeli")
                            last_row = df.iloc[-1]
                            
                            # Güçlü Sat (Sell Vote Strength > 60)
                            sell_vote = float(last_row.get('Sell_Vote_Strength', 0.0))
                            if sell_vote >= 60.0 or not pd.isna(last_row.get('Sell_Signal')):
                                should_sell = True
                                reason = f"Teknik Sat Sinyali (Güç: %{sell_vote})"
                    
                    if should_sell:
                        # Satış işlemi
                        live_price = get_live_price(ticker)
                        if live_price <= 0:
                            live_price = float(df.iloc[-1]['Close']) if 'df' in locals() and df is not None else alis_fiyati

                        sell_value = live_price * adet
                        commission = sell_value * 0.002
                        net_sell_value = sell_value - commission
                        total_sold_value += net_sell_value
                        
                        # Trade geçmişine ekle
                        conn.execute(
                            text("""
                                INSERT INTO robot_trades (session_id, ticker, type, price, adet, reason)
                                VALUES (:sid, :t, 'SELL', :p, :a, :r)
                            """),
                            {"sid": session_id, "t": ticker, "p": live_price, "a": adet, "r": reason}
                        )
                        
                        # Portföyden sil
                        conn.execute(
                            text("DELETE FROM robot_portfolio WHERE id = :id"),
                            {"id": port_id}
                        )
                        logger.info(f"[ROBOT] {ticker} SATILDI. Neden: {reason}")

                # Bakiyeyi güncelle
                if total_sold_value > 0:
                    new_balance = current_balance + total_sold_value
                    conn.execute(
                        text("UPDATE robot_sessions SET current_balance = :b WHERE id = :id"),
                        {"b": new_balance, "id": session_id}
                    )
                    current_balance = new_balance

                # Eğer expire olduysa session'ı kapat
                if is_expired:
                    conn.execute(
                        text("UPDATE robot_sessions SET status = 'completed' WHERE id = :id"),
                        {"id": session_id}
                    )
                    logger.info(f"[ROBOT] Seans {session_id} süresi dolduğu için kapatıldı.")

    except Exception as e:
        logger.error(f"[ROBOT] Satış döngüsü hatası: {e}")

def process_robot_buys():
    """Her 1 saatte bir çalışarak piyasayı tarar ve 'Güçlü Al' verenleri alır."""
    try:
        with engine.begin() as conn:
            active_sessions = conn.execute(
                text("SELECT id, initial_balance, current_balance FROM robot_sessions WHERE status = 'active'")
            ).fetchall()
            
            if not active_sessions:
                return

        # Piyasayı tara
        buy_candidates = []
        for ticker in BIST100_SYMBOLS:
            df = fetch_data(ticker, "1d", "6mo")
            if df is not None and not df.empty:
                df, _, _ = generate_historical_signals(df, "Dengeli")
                last_row = df.iloc[-1]
                buy_vote = float(last_row.get('Buy_Vote_Strength', 0.0))
                
                if buy_vote >= 60.0 or not pd.isna(last_row.get('Buy_Signal')):
                    buy_candidates.append({
                        "ticker": ticker,
                        "vote": buy_vote,
                        "price": float(last_row.get('Close', 0.0))
                    })
                    
        # En güçlüden en zayıfa sırala
        buy_candidates.sort(key=lambda x: x["vote"], reverse=True)

        with engine.begin() as conn:
            for session in active_sessions:
                session_id = session[0]
                initial_balance = session[1]
                current_balance = session[2]

                # Eldeki hisseleri al
                held_tickers = [row[0] for row in conn.execute(
                    text("SELECT ticker FROM robot_portfolio WHERE session_id = :sid"),
                    {"sid": session_id}
                ).fetchall()]

                for candidate in buy_candidates:
                    ticker = candidate["ticker"]
                    if ticker in held_tickers:
                        continue # Zaten var
                        
                    live_price = get_live_price(ticker)
                    if live_price <= 0:
                        live_price = candidate["price"]

                    # Pozisyon büyüklüğü hesapla (Maksimum %30, minimum %10)
                    pct_to_allocate = determine_position_size(candidate["vote"])
                    target_investment = initial_balance * (pct_to_allocate / 100.0)

                    # Eğer nakit bakiye yetersizse tüm parayı (veya alabileceği kadarını) bas (en az 1000 TL kalmışsa)
                    investment_amount = min(target_investment, current_balance)
                    
                    if investment_amount < 1000:
                        continue # Bakiye bitmiş
                        
                    # Komisyon dahil alınabilecek miktar: adet * fiyat * 1.002 <= investment_amount
                    adet = int(investment_amount // (live_price * 1.002))
                    if adet <= 0:
                        continue

                    total_cost = adet * live_price
                    commission = total_cost * 0.002
                    net_cost = total_cost + commission
                    
                    # Alım İşlemi
                    conn.execute(
                        text("""
                            INSERT INTO robot_portfolio (session_id, ticker, adet, alis_fiyati)
                            VALUES (:sid, :t, :a, :p)
                        """),
                        {"sid": session_id, "t": ticker, "a": adet, "p": live_price}
                    )
                    
                    # Log Trade
                    reason = f"Güçlü Al Sinyali (Güç: %{candidate['vote']:.1f}, Sermaye Dağılımı: %{pct_to_allocate:.1f})"
                    conn.execute(
                        text("""
                            INSERT INTO robot_trades (session_id, ticker, type, price, adet, reason)
                            VALUES (:sid, :t, 'BUY', :p, :a, :r)
                        """),
                        {"sid": session_id, "t": ticker, "p": live_price, "a": adet, "r": reason}
                    )
                    
                    # Bakiyeyi güncelle
                    current_balance -= net_cost
                    conn.execute(
                        text("UPDATE robot_sessions SET current_balance = :b WHERE id = :id"),
                        {"b": current_balance, "id": session_id}
                    )
                    
                    logger.info(f"[ROBOT] {ticker} ALINDI. Adet: {adet}, Fiyat: {live_price}, Komisyon: {commission:.2f}, Kalan Bakiye: {current_balance:.2f}")
                    held_tickers.append(ticker)

    except Exception as e:
        logger.error(f"[ROBOT] Alış döngüsü hatası: {e}")
