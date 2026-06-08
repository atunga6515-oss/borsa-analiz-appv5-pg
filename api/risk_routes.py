from fastapi import APIRouter, Depends, HTTPException
import pandas as pd
import numpy as np
from database import engine
from portfolio import acik_pozisyonlar
from api.auth_routes import get_current_user
from data_loader import fetch_data
from indicators import calculate_indicators
import yfinance as yf

router = APIRouter(prefix="/api/risk", tags=["risk"])

@router.get("/")
def get_portfolio_risk(current_user: str = Depends(get_current_user)):
    df_pos = acik_pozisyonlar(current_user)
    
    if df_pos.empty:
        return {
            "status": "empty",
            "message": "Risk analizi için önce portföyünüze hisse ekleyin.",
            "data": {
                "portfolio_beta": 0,
                "portfolio_var": 0,
                "stop_loss_suggestions": []
            }
        }
    
    bench_df = fetch_data("XU100.IS", period="1y")
    if bench_df is None or bench_df.empty:
        # Fallback if XU100.IS is not available
        bench_df = fetch_data("TCELL.IS", period="1y") # dummy fallback

    if bench_df is None or bench_df.empty:
        bench_returns = pd.Series([0.0])
        bench_var = 0.0
    else:
        bench_returns = bench_df['Close'].pct_change().dropna()
        bench_returns = bench_returns[~bench_returns.index.duplicated(keep='last')]
        bench_var = bench_returns.var()
    
    positions = df_pos.to_dict(orient="records")
    adets = {p['ticker']: float(p['adet']) for p in positions}
    
    # We will build a common dataframe for returns to calculate VaR
    returns_dict = {}
    current_prices = {}
    total_portfolio_value = 0
    
    stop_loss_suggestions = []
    betas = {}
    
    for pos in positions:
        ticker = pos['ticker']
        adet = float(pos['adet'])
        alis_fiyati = float(pos['alis_fiyati'])
        
        # Fetch 1y data
        df = fetch_data(ticker, period="1y")
        if df is None or df.empty:
            continue
            
        # Calculate indicators to get ATR
        try:
            df_ind = calculate_indicators(df.copy(), ticker)
            if not df_ind.empty and 'ATRr_14' in df_ind.columns:
                atr = df_ind['ATRr_14'].iloc[-1]
            else:
                atr = df['Close'].iloc[-1] * 0.03 # Fallback 3% ATR
        except Exception:
            atr = df['Close'].iloc[-1] * 0.03
            
        current_price = df['Close'].iloc[-1]
        current_prices[ticker] = current_price
        
        position_value = adet * current_price
        total_portfolio_value += position_value
        
        # Returns for Beta & VaR
        ticker_returns = df['Close'].pct_change().dropna()
        ticker_returns = ticker_returns[~ticker_returns.index.duplicated(keep='last')]
        returns_dict[ticker] = ticker_returns
        
        # Calculate individual Beta
        aligned = pd.concat([ticker_returns, bench_returns], axis=1, join='inner').dropna()
        if len(aligned) > 30 and bench_var > 0:
            cov = aligned.iloc[:, 0].cov(aligned.iloc[:, 1])
            beta = cov / bench_var
        else:
            beta = 1.0 # fallback
            
        betas[ticker] = beta
        
        # Stop-Loss logic
        stop_loss = round(current_price - (atr * 1.5), 2)
        
        if current_price < alis_fiyati:
            risk_level = "Yüksek"
        elif current_price < stop_loss + (atr * 0.5):
            risk_level = "Orta"
        else:
            risk_level = "Düşük"
            
        stop_loss_suggestions.append({
            "ticker": ticker,
            "alis_maliyeti": alis_fiyati,
            "anlik_fiyat": round(current_price, 2),
            "onerilen_stop": stop_loss,
            "risk_durumu": risk_level,
            "adet": adet
        })
        
    if total_portfolio_value == 0:
        return {
            "status": "success",
            "data": {
                "portfolio_beta": 1.0,
                "portfolio_var": 0,
                "stop_loss_suggestions": []
            }
        }
        
    # Calculate Portfolio Beta
    portfolio_beta = 0
    for ticker, beta in betas.items():
        weight = (current_prices[ticker] * adets[ticker]) / total_portfolio_value
        portfolio_beta += beta * weight
        
    # Calculate VaR (Historical Simulation)
    returns_df = pd.DataFrame(returns_dict).fillna(0)
    # Weights series
    weights = []
    for col in returns_df.columns:
        w = (current_prices[col] * adets[col]) / total_portfolio_value
        weights.append(w)
        
    weights_series = pd.Series(weights, index=returns_df.columns)
    
    if not returns_df.empty:
        portfolio_daily_returns = returns_df.dot(weights_series)
        # 5th percentile (95% confidence)
        var_95_pct = np.percentile(portfolio_daily_returns, 5) * 100
    else:
        var_95_pct = 0
        
    return {
        "status": "success",
        "data": {
            "portfolio_beta": round(portfolio_beta, 2),
            "portfolio_var": round(var_95_pct, 2),
            "stop_loss_suggestions": stop_loss_suggestions
        }
    }
