import pandas as pd
import numpy as np
from indicators import generate_signals_and_score, calculate_indicators

def run_advanced_backtest(
    df_full: pd.DataFrame, 
    initial_capital: float = 100000.0, 
    commission_rate: float = 0.002, 
    lookback_days: int = 180,
    buy_threshold: float = 65.0,
    sell_threshold: float = 45.0,
    stop_loss_pct: float = 5.0,
    take_profit_pct: float = 15.0,
    slippage_pct: float = 0.0
):
    """
    Gelişmiş Portföy Simülasyonu.
    (Güven Skoru >= buy_threshold "AL" -> Tam bakiye ile hisse alınır. 
    Skor < sell_threshold "SAT" -> Eldeki hisseler satılarak nakde dönülür)
    Ayrıca Stop-Loss ve Take-Profit içerir.
    Komisyon (%0.2 varsayılan) hesaba katılır. Max Drawdown, Win Rate, vb hesaplanır.
    """
    if len(df_full) < lookback_days + 50:
         return {"error": "Backtest için yeterli veri yok."}

    # ÇOK ÖNEMLİ: DataFrame üzerindeki indikatörleri backteste başlamadan önce hesapla!
    df_full = calculate_indicators(df_full)

    start_idx = len(df_full) - lookback_days
    if start_idx < 50: start_idx = 50 
    
    capital = initial_capital
    position = 0 # Adet
    entry_price = 0.0 # Maliyet
    trades = []
    
    equity_curve = []
    
    # Optimizasyon: Her gün için skoru önceden hesaplayıp bir listeye/diziye koyalım
    # Böylece döngü içinde tekrar tekrar current_slice oluşturmayız.
    # Bu, vektörizasyona yakın bir hız sağlar.
    scores = np.zeros(len(df_full))
    
    # 50. günden itibaren skorları hesapla
    for i in range(start_idx, len(df_full)):
        # generate_signals_and_score normalde tüm df'yi bekler ama sadece son satıra bakar.
        # Hızlandırmak için df_full'dan o güne kadar olanı veriyoruz. 
        # (Yine de calculate_100_indicators içinde if check'leri sayesinde eskisinden çok daha hızlı)
        result = generate_signals_and_score(df_full.iloc[:i+1])
        scores[i] = result['score']
    
    for i in range(start_idx, len(df_full)):
        
        score = scores[i]
        
        current_price = df_full['Close'].iloc[i]
        high_price = df_full['High'].iloc[i]
        low_price = df_full['Low'].iloc[i]
        date = df_full.index[i]
        
        sell_reason = ""
        should_sell = False
        
        # SATIM KONTROLÜ (Açık Pozisyon Varsa)
        if position > 0:
            # 1. Take Profit Kontrolü (Gün içi Gördüğü En Yüksek Fiyat hedefe ulaştı mı?)
            if high_price >= entry_price * (1 + (take_profit_pct / 100.0)):
                should_sell = True
                sell_reason = "Take Profit"
                # Gerçekçi olması için tam take_profit seviyesinden satıldığını varsayıyoruz (gap up yoksa)
                current_price = max(entry_price * (1 + (take_profit_pct / 100.0)), df_full['Open'].iloc[i])
            
            # 2. Stop Loss Kontrolü (Gün içi Gördüğü En Düşük Fiyat stop'a değdi mi?)
            elif low_price <= entry_price * (1 - (stop_loss_pct / 100.0)):
                should_sell = True
                sell_reason = "Stop Loss"
                # Stop seviyesinden satıldığını varsayıyoruz
                current_price = min(entry_price * (1 - (stop_loss_pct / 100.0)), df_full['Open'].iloc[i])
            
            # 3. Sinyal Satışı
            elif score < sell_threshold:
                should_sell = True
                sell_reason = "Signal"
                
        if should_sell:
            sell_price = current_price * (1 - (slippage_pct / 100.0))
            gross_value = position * sell_price
            cost = gross_value * commission_rate
            capital = capital + gross_value - cost
            
            # Kâr/Zarar hesabı (yüzde)
            trade_return = ((sell_price - entry_price) / entry_price) * 100
            
            trades.append({
                'Date': date, 
                'Type': 'SELL', 
                'Price': sell_price, 
                'Score': score,
                'Reason': sell_reason,
                'ReturnPct': trade_return
            })
            position = 0
            entry_price = 0.0

        # ALIM KARARI
        if score >= buy_threshold and position == 0:
            execution_price = current_price * (1 + (slippage_pct / 100.0))
            effective_price = execution_price * (1 + commission_rate)
            qty = capital / effective_price
            cost = qty * execution_price * commission_rate
            position = qty
            entry_price = execution_price
            capital = capital - (qty * execution_price) - cost
            trades.append({
                'Date': date, 
                'Type': 'BUY', 
                'Price': execution_price, 
                'Score': score,
                'Reason': 'Signal'
            })
            
        # Equity'i kaydet (Nakit + Hissenin o anki değeri)
        current_equity = capital + (position * df_full['Close'].iloc[i])
        equity_curve.append({'Date': date, 'Equity': current_equity})

    # Son gün hala pozisyondaysa çıkmış gibi varsayıp nihai equity hesaplayalım
    final_equity = capital + (position * df_full['Close'].iloc[-1])
    
    equity_df = pd.DataFrame(equity_curve).set_index('Date')
    
    # Drawdown Hesaplama
    equity_df['Peak'] = equity_df['Equity'].cummax()
    equity_df['Drawdown'] = (equity_df['Equity'] - equity_df['Peak']) / equity_df['Peak']
    max_drawdown = equity_df['Drawdown'].min() * 100
    
    total_return = ((final_equity - initial_capital) / initial_capital) * 100
    
    # Buy and Hold (Al-Tut) kıyaslaması
    buy_hold_qty = initial_capital / df_full['Close'].iloc[start_idx]
    bh_final = buy_hold_qty * df_full['Close'].iloc[-1]
    bh_return = ((bh_final - initial_capital) / initial_capital) * 100

    # Risksiz Getiri ve Alfa Hesaplamaları
    risk_free_annual = 40.0 # BIST için ortalama yıllık risksiz mevduat getirisi varsayımı
    risk_free_period = risk_free_annual * (lookback_days / 365)
    alpha = total_return - bh_return
    alpha_rf = total_return - risk_free_period

    # Yeni Finansal Metrikler
    closed_trades = [t for t in trades if t['Type'] == 'SELL']
    total_trades_count = len(closed_trades)
    
    win_trades = sum(1 for t in closed_trades if t['ReturnPct'] > 0)
    loss_trades = total_trades_count - win_trades
    win_rate = (win_trades / total_trades_count * 100) if total_trades_count > 0 else 0.0
    
    gross_profit = sum(t['ReturnPct'] for t in closed_trades if t['ReturnPct'] > 0)
    gross_loss = abs(sum(t['ReturnPct'] for t in closed_trades if t['ReturnPct'] < 0))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.9 if gross_profit > 0 else 0.0)
    
    # Sharpe Ratio (Basit günlük getiri standard sapması üzerinden yıllık)
    equity_df['Daily_Return'] = equity_df['Equity'].pct_change()
    daily_rf = (risk_free_annual / 100.0) / 252
    excess_returns = equity_df['Daily_Return'] - daily_rf
    sharpe_ratio = 0.0
    if excess_returns.std() > 0:
        sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
        
    # Sortino Ratio (Sadece negatif getirilerin standart sapması)
    negative_returns = excess_returns[excess_returns < 0]
    sortino_ratio = 0.0
    downside_std = np.sqrt(np.mean(negative_returns**2))
    if downside_std > 0:
        sortino_ratio = (excess_returns.mean() / downside_std) * np.sqrt(252)

    return {
        "final_equity": final_equity,
        "total_return_pct": total_return,
        "max_drawdown_pct": max_drawdown,
        "buy_and_hold_return_pct": bh_return,
        "risk_free_return_pct": risk_free_period,
        "alpha_bh": alpha,
        "alpha_rf": alpha_rf,
        "number_of_trades": total_trades_count,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "sharpe_ratio": sharpe_ratio,
        "sortino_ratio": sortino_ratio,
        "equity_curve": equity_df.drop(columns=['Daily_Return'], errors='ignore'),
        "trades": trades
    }
