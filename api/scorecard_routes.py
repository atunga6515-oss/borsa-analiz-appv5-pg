from fastapi import APIRouter, Depends, HTTPException
from api.auth_routes import get_current_user
from scorecard import get_scorecard_summary, get_live_progress, run_daily_snapshot, score_matured_signals

router = APIRouter(prefix="/api/scorecard", tags=["scorecard"])


@router.get("/summary")
def scorecard_summary(current_user: str = Depends(get_current_user)):
    """Sinyal Karnesi özeti: skor bandı + Boğa Flaması bazında isabet/getiri."""
    return get_scorecard_summary()


@router.get("/live")
def scorecard_live(current_user: str = Depends(get_current_user)):
    """Devam eden (vadesi dolmamış) sinyallerin anlık/gerçekleşmemiş getirisi (haftalara göre)."""
    return get_live_progress()


@router.post("/run-snapshot")
def trigger_snapshot(current_user: str = Depends(get_current_user)):
    """Manuel snapshot tetikleme (test/yönetici amaçlı)."""
    try:
        n = run_daily_snapshot()
        return {"status": "ok", "inserted": n}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-scoring")
def trigger_scoring(current_user: str = Depends(get_current_user)):
    """Manuel puanlama tetikleme (vadesi dolan sinyaller)."""
    try:
        n = score_matured_signals()
        return {"status": "ok", "scored": n}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
