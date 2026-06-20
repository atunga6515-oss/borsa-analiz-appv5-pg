import numpy as np
import pandas as pd
from scipy.optimize import minimize
from data_loader import fetch_data

def optimize_portfolio(tickers, risk_profile='Medium', lookback_days=365):
    """
    Markowitz Modern Portföy Teorisi'ne göre optimize edilmiş ağırlıkları bulur.
    Risk Profile: Low, Medium, High
    """
    if not tickers or len(tickers) < 2:
        return {"error": "Optimizasyon için en az 2 hisse seçmelisiniz."}

    # Tarihi verileri çek
    data_dict = {}
    for ticker in tickers:
        df = fetch_data(ticker, period="1y")
        if df is not None and not df.empty:
            data_dict[ticker] = df['Close']
    
    if len(data_dict) < 2:
        return {"error": "Yeterli tarihsel veri bulunamadı."}

    price_df = pd.DataFrame(data_dict).dropna()
    
    if len(price_df) < 50:
        return {"error": "Fiyat serisi çok kısa, sağlıklı optimizasyon yapılamaz."}

    # Günlük getiriler
    returns = price_df.pct_change().dropna()
    mean_returns = returns.mean()
    cov_matrix = returns.cov()
    num_assets = len(price_df.columns)

    # Risksiz getiri (Yıllık bazda sabit - Örn: %40)
    risk_free_rate_annual = 0.40  

    def portfolio_annualised_performance(weights, mean_returns, cov_matrix):
        returns_p = np.sum(mean_returns * weights) * 252
        std_p = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(252)
        return std_p, returns_p

    # Optimizasyon hedefleri
    def neg_sharpe_ratio(weights, mean_returns, cov_matrix, rf_annual):
        p_var, p_ret = portfolio_annualised_performance(weights, mean_returns, cov_matrix)
        return -(p_ret - rf_annual) / p_var

    def portfolio_variance(weights, mean_returns, cov_matrix):
        return portfolio_annualised_performance(weights, mean_returns, cov_matrix)[0]

    def portfolio_return(weights, mean_returns, cov_matrix):
        return -portfolio_annualised_performance(weights, mean_returns, cov_matrix)[1]

    # Kısıtlamalar (Ağırlıklar toplamı 1 olmalı)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    
    # Her bir hisse %0 ile %100 arasında pay alabilir
    bounds = tuple((0.0, 1.0) for asset in range(num_assets))
    
    # Başlangıç tahmini (Eşit ağırlık)
    init_guess = num_assets * [1. / num_assets,]

    if risk_profile == 'High':
        # Maksimum Getiri (Sadece Mean'i maksimize et)
        opt_result = minimize(portfolio_return, init_guess, args=(mean_returns, cov_matrix), method='SLSQP', bounds=bounds, constraints=constraints)
    elif risk_profile == 'Low':
        # Minimum Varyans (Sadece Riski minimize et)
        opt_result = minimize(portfolio_variance, init_guess, args=(mean_returns, cov_matrix), method='SLSQP', bounds=bounds, constraints=constraints)
    else:
        # Maksimum Sharpe Optimizasyonu
        opt_result = minimize(neg_sharpe_ratio, init_guess, args=(mean_returns, cov_matrix, risk_free_rate_annual), method='SLSQP', bounds=bounds, constraints=constraints)

    if not opt_result.success:
        return {"error": "Optimizasyon algoritması yakınsayamadı."}

    # Ağırlıkları sözlüğe çevir
    weights = opt_result.x
    
    # %1'den küçük ağırlıkları 0 yap ve yeniden normalize et
    cleaned_weights = np.where(weights < 0.01, 0, weights)
    cleaned_weights = cleaned_weights / np.sum(cleaned_weights)
    
    result_weights = {}
    for idx, ticker in enumerate(price_df.columns):
        if cleaned_weights[idx] > 0:
            result_weights[ticker] = round(cleaned_weights[idx] * 100, 2)
            
    # Eğer her şey 0'landıysa eşit ağırlık ver
    if sum(result_weights.values()) == 0:
        for ticker in price_df.columns:
            result_weights[ticker] = round((1.0 / num_assets) * 100, 2)
            
    expected_vol, expected_ret = portfolio_annualised_performance(cleaned_weights, mean_returns, cov_matrix)

    return {
        "status": "success",
        "weights": result_weights,
        "metrics": {
            "expected_annual_return_pct": round(expected_ret * 100, 2),
            "expected_annual_volatility_pct": round(expected_vol * 100, 2),
            "sharpe_ratio": round((expected_ret - risk_free_rate_annual) / expected_vol, 2) if expected_vol > 0 else 0
        }
    }
