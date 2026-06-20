from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Request
from top_picks_15d import find_top_picks, get_top_picks_by_date, get_top_picks_history_dates, save_top_picks_history
from api.auth_routes import get_current_user
from limiter import limiter
# from core.analysis_service import calculate_top_picks_15d  # REMOVED

router = APIRouter(prefix="/api/top-picks-15d", tags=["Top Picks 15D"])

@router.get("/history-dates")
def fetch_history_dates(current_user: str = Depends(get_current_user)):
    dates = get_top_picks_history_dates(current_user)
    return {"dates": dates}

@router.get("/history/{history_id}")
def fetch_history_by_id(history_id: int, current_user: str = Depends(get_current_user)):
    data = get_top_picks_by_date(current_user, history_id)
    return {"data": data}

from pydantic import BaseModel

import uuid
from fastapi import BackgroundTasks

class ScanRequest(BaseModel):
    top_n: int = 5
    pool: str = "BIST30" # BIST30, BIST100, ALL

scan_tasks = {}

class APIProgressBar:
    def __init__(self, task_id: str):
        self.task_id = task_id
    def progress(self, val: float, text: str = ""):
        if self.task_id in scan_tasks:
            scan_tasks[self.task_id]["progress"] = val * 100
            scan_tasks[self.task_id]["text"] = text

@router.post("/scan")
@limiter.limit("5/minute")
def start_top_picks(request: Request, req: ScanRequest, background_tasks: BackgroundTasks, current_user: str = Depends(get_current_user)):
    task_id = str(uuid.uuid4())
    scan_tasks[task_id] = {"status": "running", "progress": 0, "text": "Tarama Başlatılıyor...", "results": [], "username": current_user}
    
    def run_scan():
        from screener import BIST30_SYMBOLS, BIST100_SYMBOLS, BIST_ALL_SYMBOLS
        try:
            pb = APIProgressBar(task_id)
            
            symbols = BIST30_SYMBOLS
            if req.pool == "BIST100":
                symbols = BIST100_SYMBOLS
            elif req.pool == "ALL":
                symbols = BIST_ALL_SYMBOLS
                
            results = find_top_picks(symbol_list=symbols, top_n=req.top_n, progress_bar=pb)
            
            import pandas as pd
            import numpy as np
            if results:
                df = pd.DataFrame(results)
                df = df.replace([np.inf, -np.inf], np.nan).fillna("-")
                results = df.to_dict(orient="records")
            
            save_top_picks_history(current_user, results)
            scan_tasks[task_id]["status"] = "completed"
            scan_tasks[task_id]["results"] = results
            scan_tasks[task_id]["progress"] = 100
            scan_tasks[task_id]["text"] = "Tamamlandı!"
        except Exception as e:
            scan_tasks[task_id]["status"] = "error"
            scan_tasks[task_id]["text"] = f"Hata oluştu: {str(e)}"
            
    background_tasks.add_task(run_scan)
    return {"task_id": task_id}

@router.get("/scan/progress/{task_id}")
def check_scan_progress(task_id: str, current_user: str = Depends(get_current_user)):
    task_data = scan_tasks.get(task_id)
    if not task_data:
        return {"status": "not_found"}
    if task_data.get("username") != current_user:
        raise HTTPException(status_code=403, detail="Erişim reddedildi")
    return task_data

from fastapi.responses import StreamingResponse
import io
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import ta

@router.get("/chart/{ticker}")
def get_patlama_chart(ticker: str, current_user: str = Depends(get_current_user)):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        df.dropna(inplace=True)
        
        if len(df) < 20:
             raise HTTPException(status_code=400, detail="Not enough data points")

        df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
        df['BBU'] = ta.volatility.bollinger_hband(df['Close'], window=20, window_dev=2)
        df['BBL'] = ta.volatility.bollinger_lband(df['Close'], window=20, window_dev=2)

        macd = ta.trend.MACD(df['Close'], window_slow=26, window_fast=12, window_sign=9)
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Hist'] = macd.macd_diff()

        # Keep last 3 months for better zoom
        df = df.iloc[-60:]

        apds = [
            mpf.make_addplot(df['BBU'], color='gray', alpha=0.5, linestyle='--'),
            mpf.make_addplot(df['BBL'], color='gray', alpha=0.5, linestyle='--'),
            mpf.make_addplot(df['SMA_20'], color='orange', alpha=0.8),
            mpf.make_addplot(df['MACD_Hist'], type='bar', width=0.7, panel=1,
                             color=['green' if val >= 0 else 'red' for val in df['MACD_Hist']],
                             alpha=0.8, ylabel='MACD'),
            mpf.make_addplot(df['MACD'], panel=1, color='blue', secondary_y=False),
            mpf.make_addplot(df['MACD_Signal'], panel=1, color='orange', secondary_y=False)
        ]

        mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350',
                                   edge='inherit', wick='inherit',
                                   volume='in', ohlc='i')
        s  = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=True, 
                                facecolor='#131722', edgecolor='#b2b5be', figcolor='#131722', 
                                gridcolor='#2a2e39', rc={'text.color': 'white', 'axes.labelcolor': 'white', 'xtick.color': 'white', 'ytick.color': 'white'})

        buf = io.BytesIO()
        mpf.plot(df, type='candle', style=s,
                 addplot=apds,
                 volume=False,
                 title=f"{ticker} - Swing Trade (MACD & BB)",
                 figsize=(12, 8),
                 panel_ratios=(3, 1),
                 tight_layout=True,
                 savefig=buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
