from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import text
from database import engine
from api.auth_routes import get_current_user

router = APIRouter(prefix="/api/alarms", tags=["alarms"])


class AlarmCreate(BaseModel):
    ticker: str
    condition: str        # "price_above" | "price_below" | "rsi_above" | "rsi_below"
    target_value: float
    note: Optional[str] = ""


@router.get("/")
def list_alarms(current_user: str = Depends(get_current_user)):
    """Giriş yapan kullanıcının tüm alarmlarını listeler."""
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id, ticker, condition, target_value, status, note, created_at, triggered_at
                FROM user_alarms
                WHERE username = :u
                ORDER BY created_at DESC
            """),
            {"u": current_user}
        ).fetchall()

    alarms = []
    for r in rows:
        alarms.append({
            "id": r[0],
            "ticker": r[1],
            "condition": r[2],
            "target_value": r[3],
            "status": r[4],
            "note": r[5],
            "created_at": str(r[6]) if r[6] else "",
            "triggered_at": str(r[7]) if r[7] else "",
        })
    return {"alarms": alarms}


@router.post("/")
def create_alarm(req: AlarmCreate, current_user: str = Depends(get_current_user)):
    """Yeni alarm kaydeder."""
    valid_conditions = ["price_above", "price_below", "rsi_above", "rsi_below"]
    if req.condition not in valid_conditions:
        raise HTTPException(status_code=400, detail=f"Geçersiz koşul. Geçerli seçenekler: {valid_conditions}")

    ticker = req.ticker.upper().strip()
    if not ticker:
        raise HTTPException(status_code=400, detail="Hisse kodu boş olamaz.")

    with engine.begin() as conn:
        if engine.name == "postgresql":
            result = conn.execute(
                text("""
                    INSERT INTO user_alarms (username, ticker, condition, target_value, status, note)
                    VALUES (:u, :t, :c, :v, 'active', :n)
                    RETURNING id
                """),
                {"u": current_user, "t": ticker, "c": req.condition, "v": req.target_value, "n": req.note or ""}
            )
            new_id = result.fetchone()[0]
        else:
            conn.execute(
                text("""
                    INSERT INTO user_alarms (username, ticker, condition, target_value, status, note)
                    VALUES (:u, :t, :c, :v, 'active', :n)
                """),
                {"u": current_user, "t": ticker, "c": req.condition, "v": req.target_value, "n": req.note or ""}
            )
            new_id = conn.execute(text("SELECT last_insert_rowid()")).scalar()

    return {"ok": True, "id": new_id, "message": f"{ticker} için alarm kuruldu."}


@router.delete("/{alarm_id}")
def delete_alarm(alarm_id: int, current_user: str = Depends(get_current_user)):
    """Alarmı siler. Sadece kendi alarmlarını silebilir."""
    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT id FROM user_alarms WHERE id=:id AND username=:u"),
            {"id": alarm_id, "u": current_user}
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Alarm bulunamadı veya size ait değil.")
        conn.execute(text("DELETE FROM user_alarms WHERE id=:id"), {"id": alarm_id})

    return {"ok": True, "message": "Alarm silindi."}


CONDITION_LABELS = {
    "price_above": "Fiyat Şunu Geçerse ↑",
    "price_below": "Fiyat Şuna Düşerse ↓",
    "rsi_above": "RSI Şunun Üzerindeyse (Aşırı Alım)",
    "rsi_below": "RSI Şunun Altındaysa (Aşırı Satım)",
}

@router.get("/conditions")
def get_conditions():
    """Kullanılabilir alarm koşullarını döner."""
    return {"conditions": [{"value": k, "label": v} for k, v in CONDITION_LABELS.items()]}
