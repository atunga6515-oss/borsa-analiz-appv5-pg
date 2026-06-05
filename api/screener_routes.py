from fastapi import APIRouter, Depends, BackgroundTasks
import uuid
from pydantic import BaseModel
import pandas as pd
import numpy as np
from screener import (
    run_screener, get_scan_history,
    get_watchlist, add_to_watchlist, remove_from_watchlist, 
    BIST30_SYMBOLS, BIST100_SYMBOLS, BIST_ALL_SYMBOLS
)
from api.auth_routes import get_current_user

router = APIRouter(prefix="/api/screener", tags=["screener"])

scan_tasks = {}

class APIProgressBar:
    def __init__(self, task_id: str):
        self.task_id = task_id
        
    def progress(self, val: float, text: str = ""):
        if self.task_id in scan_tasks:
            scan_tasks[self.task_id]["progress"] = val * 100
            scan_tasks[self.task_id]["text"] = text

def bg_run_screener(task_id: str, symbols: list, username: str):
    try:
        scan_tasks[task_id]["status"] = "running"
        scan_tasks[task_id]["progress"] = 0
        scan_tasks[task_id]["text"] = "Tarama başlatılıyor..."
        
        pb = APIProgressBar(task_id)
        df = run_screener(symbols, username, progress_bar=pb)
        
        if isinstance(df, pd.DataFrame):
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.fillna("-")
            scan_tasks[task_id]["results"] = df.to_dict(orient="records")
        else:
            scan_tasks[task_id]["results"] = []
            
        scan_tasks[task_id]["progress"] = 100
        scan_tasks[task_id]["text"] = "Tarama tamamlandı!"
        scan_tasks[task_id]["status"] = "completed"
        
    except Exception as e:
        scan_tasks[task_id]["status"] = "error"
        scan_tasks[task_id]["text"] = f"Hata: {str(e)}"
        scan_tasks[task_id]["results"] = []

class WatchlistAddRequest(BaseModel):
    ticker: str

class ScanRequest(BaseModel):
    scan_mode: str = "BIST30" # BIST30, BIST100, BIST_ALL

@router.get("/history")
def fetch_history(days_back: int = 7, current_user: str = Depends(get_current_user)):
    df = get_scan_history(current_user, days_back)
    if isinstance(df, pd.DataFrame):
        return {"data": df.to_dict(orient="records")}
    return {"data": []}

@router.post("/scan")
def start_scan(background_tasks: BackgroundTasks, req: ScanRequest = None, current_user: str = Depends(get_current_user)):
    mode = req.scan_mode if req else "BIST30"
    
    symbols_to_scan = BIST30_SYMBOLS
    if mode == "BIST100":
        symbols_to_scan = BIST100_SYMBOLS
    elif mode == "BIST_ALL":
        symbols_to_scan = BIST_ALL_SYMBOLS
        
    task_id = str(uuid.uuid4())
    scan_tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "text": "Sıraya alındı...",
        "results": []
    }
    
    background_tasks.add_task(bg_run_screener, task_id, symbols_to_scan, current_user)
    
    return {"task_id": task_id, "status": "started"}

@router.get("/scan/progress/{task_id}")
def check_scan_progress(task_id: str):
    if task_id not in scan_tasks:
        return {"status": "not_found"}
        
    task_data = scan_tasks[task_id]
    if task_data["status"] == "completed":
        # Görev tamamlandıysa sonuçları dön ve memory'den sil
        res = task_data["results"]
        del scan_tasks[task_id]
        return {"status": "completed", "progress": 100, "text": "Tamamlandı", "data": res}
        
    return {
        "status": task_data["status"],
        "progress": task_data["progress"],
        "text": task_data["text"]
    }

@router.get("/watchlist")
def fetch_watchlist(current_user: str = Depends(get_current_user)):
    wl = get_watchlist(current_user)
    # Convert dataframe to list of dicts if needed
    if isinstance(wl, pd.DataFrame):
        return {"watchlist": wl.to_dict(orient="records")}
    return {"watchlist": wl}

@router.post("/watchlist")
def add_watchlist_item(req: WatchlistAddRequest, current_user: str = Depends(get_current_user)):
    add_to_watchlist(current_user, req.ticker)
    return {"status": "success", "ticker": req.ticker}

@router.delete("/watchlist/{ticker}")
def remove_watchlist_item(ticker: str, current_user: str = Depends(get_current_user)):
    remove_from_watchlist(current_user, ticker)
    return {"status": "success", "ticker": ticker}
