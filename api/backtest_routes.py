from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from advanced_backtest import run_advanced_backtest
from data_loader import fetch_data
import pandas as pd
import math
import numpy as np
from api.auth_routes import get_current_user
from limiter import limiter

router = APIRouter(prefix="/api/backtest", tags=["backtest"])

class BacktestRequest(BaseModel):
    ticker: str
    initial_capital: float = 100000.0
    commission_rate: float = 0.002
    lookback_days: int = 180
    buy_threshold: float = 65.0
    sell_threshold: float = 45.0
    stop_loss_pct: float = 5.0
    take_profit_pct: float = 15.0

@router.post("/")
@limiter.limit("10/minute")
def run_backtest(request: Request, req: BacktestRequest, current_user: str = Depends(get_current_user)):
    # Veri çekimi: "2y" periodu indikator ve backtest için yeterlidir.
    df = fetch_data(req.ticker.upper(), interval="1d", period="2y")
    if df.empty:
        return {"error": "Veri bulunamadı."}
        
    result = run_advanced_backtest(
        df_full=df, 
        initial_capital=req.initial_capital,
        commission_rate=req.commission_rate,
        lookback_days=req.lookback_days,
        buy_threshold=req.buy_threshold,
        sell_threshold=req.sell_threshold,
        stop_loss_pct=req.stop_loss_pct,
        take_profit_pct=req.take_profit_pct
    )
    
    if "error" in result:
        return result
        
    # JSON serileştirmesi için Pandas tiplerini düzelt
    equity_curve = result["equity_curve"].reset_index()
    # Tarih formatını string yap
    equity_curve["Date"] = equity_curve["Date"].dt.strftime("%Y-%m-%d")
    equity_curve = equity_curve.replace({np.nan: None})
    
    trades = []
    for t in result["trades"]:
        t_copy = t.copy()
        t_copy["Date"] = t_copy["Date"].strftime("%Y-%m-%d") if hasattr(t_copy["Date"], "strftime") else str(t_copy["Date"])
        trades.append(t_copy)
    
    return {
        "final_equity": result["final_equity"],
        "total_return_pct": result["total_return_pct"],
        "max_drawdown_pct": result["max_drawdown_pct"],
        "buy_and_hold_return_pct": result["buy_and_hold_return_pct"],
        "risk_free_return_pct": result["risk_free_return_pct"],
        "alpha_bh": result["alpha_bh"],
        "alpha_rf": result["alpha_rf"],
        "number_of_trades": result["number_of_trades"],
        "win_rate": result["win_rate"],
        "profit_factor": result["profit_factor"],
        "sharpe_ratio": result["sharpe_ratio"],
        "sortino_ratio": result["sortino_ratio"],
        "trades": trades,
        "equity_curve": equity_curve.to_dict(orient="records")
    }

from strategy_comparator import compare_strategies

class CompareRequest(BaseModel):
    ticker: str
    period: str = "1y"

@router.post("/compare")
def run_compare(req: CompareRequest, current_user: str = Depends(get_current_user)):
    # Eğer kullanıcı virgülle ayırdıysa sadece ilkini alıyoruz, çünkü comparator 1 df bekliyor
    first_ticker = req.ticker.split(",")[0].strip().upper()
    df = fetch_data(first_ticker, interval="1d", period=req.period)
    if df.empty:
        return {"error": f"{first_ticker} için veri bulunamadı."}
        
    comp_df = compare_strategies(df)
    if comp_df.empty:
        return {"error": "Karşılaştırma hesaplanamadı."}
        
    # Replace NaN with None for JSON serialization
    comp_df = comp_df.replace({np.nan: None})
    return {"data": comp_df.to_dict(orient="records")}
