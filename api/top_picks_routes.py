from fastapi import APIRouter, Depends
from top_picks import find_top_picks, get_top_picks_by_date, get_top_picks_history_dates, save_top_picks_history
from api.auth_routes import get_current_user

router = APIRouter(prefix="/api/top_picks", tags=["top_picks"])

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
def start_top_picks(req: ScanRequest, background_tasks: BackgroundTasks, current_user: str = Depends(get_current_user)):
    task_id = str(uuid.uuid4())
    scan_tasks[task_id] = {"status": "running", "progress": 0, "text": "Tarama Başlatılıyor...", "results": []}
    
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
def check_scan_progress(task_id: str):
    return scan_tasks.get(task_id, {"status": "not_found"})
