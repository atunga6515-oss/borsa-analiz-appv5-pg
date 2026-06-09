from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from pydantic import BaseModel
from database import engine
from api.auth_routes import get_current_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/robot", tags=["Robot"])

class RobotStartRequest(BaseModel):
    initial_balance: float = 1000000.0
    duration_days: int = 5

@router.post("/start")
def start_robot(req: RobotStartRequest, current_user: str = Depends(get_current_user)):
    with engine.begin() as conn:
        # Önceden aktif olan varsa durdur
        conn.execute(
            text("UPDATE robot_sessions SET status = 'stopped' WHERE username = :u AND status = 'active'"),
            {"u": current_user}
        )
        
        # Yeni robot oluştur
        now = datetime.now()
        end_date = now + timedelta(days=req.duration_days)
        
        conn.execute(
            text("""
                INSERT INTO robot_sessions (username, start_date, end_date, initial_balance, current_balance, status)
                VALUES (:u, :sd, :ed, :ib, :cb, 'active')
            """),
            {"u": current_user, "sd": now, "ed": end_date, "ib": req.initial_balance, "cb": req.initial_balance}
        )
        
    return {"message": "Robot başarıyla başlatıldı!"}

@router.post("/stop")
def stop_robot(current_user: str = Depends(get_current_user)):
    with engine.begin() as conn:
        active_session = conn.execute(
            text("SELECT id FROM robot_sessions WHERE username = :u AND status = 'active'"),
            {"u": current_user}
        ).fetchone()
        
        if not active_session:
            raise HTTPException(status_code=400, detail="Aktif bir robot seansı bulunamadı.")
            
        session_id = active_session[0]
        
        # Elindeki tüm hisseleri sat ve seansı kapat
        from api.robot_engine import get_live_price
        portfolio = conn.execute(
            text("SELECT id, ticker, adet FROM robot_portfolio WHERE session_id = :sid"),
            {"sid": session_id}
        ).fetchall()
        
        current_balance = conn.execute(
            text("SELECT current_balance FROM robot_sessions WHERE id = :sid"),
            {"sid": session_id}
        ).scalar()
        
        for item in portfolio:
            port_id, ticker, adet = item
            live_price = get_live_price(ticker)
            if live_price <= 0:
                live_price = 1.0 # Fallback
            
            sell_val = live_price * adet
            commission = sell_val * 0.002
            current_balance += (sell_val - commission)
            
            conn.execute(
                text("""
                    INSERT INTO robot_trades (session_id, ticker, type, price, adet, reason)
                    VALUES (:sid, :t, 'SELL', :p, :a, 'Kullanıcı Tarafından Zorunlu Durdurma')
                """),
                {"sid": session_id, "t": ticker, "p": live_price, "a": adet}
            )
            
        conn.execute(text("DELETE FROM robot_portfolio WHERE session_id = :sid"), {"sid": session_id})
        conn.execute(
            text("UPDATE robot_sessions SET status = 'stopped', current_balance = :b WHERE id = :sid"),
            {"b": current_balance, "sid": session_id}
        )

    return {"message": "Robot durduruldu ve elindeki hisseler satıldı."}

@router.get("/status")
def get_robot_status(current_user: str = Depends(get_current_user)):
    with engine.connect() as conn:
        session = conn.execute(
            text("SELECT id, start_date, end_date, initial_balance, current_balance, status FROM robot_sessions WHERE username = :u ORDER BY id DESC LIMIT 1"),
            {"u": current_user}
        ).fetchone()
        
        if not session:
            return {"active": False}
            
        session_id, start_date, end_date, initial_balance, current_balance, status = session
        
        portfolio = conn.execute(
            text("SELECT ticker, adet, alis_fiyati, alis_tarihi FROM robot_portfolio WHERE session_id = :sid"),
            {"sid": session_id}
        ).fetchall()
        
        trades = conn.execute(
            text("SELECT ticker, type, price, adet, date, reason FROM robot_trades WHERE session_id = :sid ORDER BY date DESC"),
            {"sid": session_id}
        ).fetchall()

    port_list = []
    total_portfolio_value = 0.0
    from api.robot_engine import get_live_price
    for p in portfolio:
        t, a, af, at = p
        lp = get_live_price(t)
        if lp <= 0:
            lp = af
        val = lp * a
        total_portfolio_value += val
        port_list.append({
            "ticker": t,
            "adet": a,
            "alis_fiyati": af,
            "anlik_fiyat": lp,
            "kar_zarar_yuzde": ((lp - af) / af) * 100 if af > 0 else 0,
            "toplam_deger": val,
            "tarih": str(at)
        })

    total_commission_paid = 0.0
    total_trades_count = len(trades)
    
    trade_list = []
    for t, ty, pr, ad, d, r in trades:
        val = pr * ad
        comm = val * 0.002
        total_commission_paid += comm
        trade_list.append({"ticker": t, "type": ty, "price": pr, "adet": ad, "date": str(d), "reason": r})

    total_assets = current_balance + total_portfolio_value
    pnl_pct = ((total_assets - initial_balance) / initial_balance) * 100

    return {
        "active": status == "active",
        "status": status,
        "initial_balance": initial_balance,
        "current_balance": current_balance,
        "total_assets": total_assets,
        "pnl_pct": pnl_pct,
        "total_commission_paid": total_commission_paid,
        "total_trades_count": total_trades_count,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "portfolio": port_list,
        "trades": trade_list
    }
