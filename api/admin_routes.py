"""
Admin API Routes
Tüm endpoint'ler get_current_admin dependency ile korunmaktadır.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import text
from database import engine
from api.auth_routes import get_current_admin
from auth import log_action, hash_password

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ─────────────────────────────────────────────────────────────────────────────
# 1. GET /api/admin/users  — Tüm kullanıcılar + alarm sayıları
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/users")
def list_users(admin: str = Depends(get_current_admin)):
    """Tüm kullanıcıları kayıt tarihi ve aktif alarm sayılarıyla listeler."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT
                u.username,
                u.email,
                u.role,
                u.is_active,
                u.last_active,
                u.created_at,
                u.ai_quota,
                u.phone,
                COUNT(a.id) AS alarm_count
            FROM users u
            LEFT JOIN user_alarms a
                ON a.username = u.username AND a.status = 'active'
            GROUP BY u.username, u.email, u.phone, u.role, u.is_active, u.last_active, u.created_at, u.ai_quota
            ORDER BY u.created_at DESC
        """)).fetchall()

    return {
        "users": [
            {
                "username":    r[0],
                "email":       r[1] or "",
                "role":        r[2] or "user",
                "is_active":   r[3] if r[3] is not None else True,
                "last_active": str(r[4]) if r[4] else None,
                "created_at":  str(r[5]) if r[5] else None,
                "ai_quota":    r[6] or 0,
                "phone":       r[7] or "",
                "alarm_count": r[8] or 0,
            }
            for r in rows
        ]
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. PUT /api/admin/users/{username}/status  — Kullanıcı durumu / rol değiştir
# ─────────────────────────────────────────────────────────────────────────────
class UserStatusUpdate(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = None   # "user" | "admin"
    ai_quota: Optional[int] = None
    email: Optional[str] = None
    password: Optional[str] = None
    phone: Optional[str] = None


@router.put("/users/{username}/status")
def update_user_status(
    username: str,
    body: UserStatusUpdate,
    admin: str = Depends(get_current_admin),
):
    """Kullanıcıyı askıya al veya rolünü değiştir."""
    if username == admin:
        # Kendi rolünü veya durumunu değiştiremez, ama kendi kotasını artırabilir.
        if body.role is not None or body.is_active is not None:
            raise HTTPException(status_code=400, detail="Kendi rolünüzü veya durumunuzu değiştiremezsiniz.")

    if body.role and body.role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Geçersiz rol. 'user' veya 'admin' olmalı.")

    updates = []
    params: dict = {"u": username}

    if body.is_active is not None:
        updates.append("is_active = :is_active")
        params["is_active"] = body.is_active

    if body.role is not None:
        updates.append("role = :role")
        params["role"] = body.role

    if body.ai_quota is not None:
        updates.append("ai_quota = :ai_quota")
        params["ai_quota"] = body.ai_quota

    if body.email is not None:
        updates.append("email = :email")
        params["email"] = body.email

    if body.phone is not None:
        updates.append("phone = :phone")
        params["phone"] = body.phone

    if body.password:
        if len(body.password) < 6:
            raise HTTPException(status_code=400, detail="Şifre en az 6 karakter olmalıdır.")
        new_hash = hash_password(body.password)
        updates.append("password_hash = :password_hash")
        params["password_hash"] = new_hash

    if not updates:
        raise HTTPException(status_code=400, detail="Güncellenecek alan belirtilmedi.")

    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT username FROM users WHERE username=:u"), {"u": username}
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

        conn.execute(
            text(f"UPDATE users SET {', '.join(updates)} WHERE username=:u"),
            params,
        )

    detail_str = ", ".join(
        [f"is_active={body.is_active}" if body.is_active is not None else "",
         f"role={body.role}" if body.role else ""]
    ).strip(", ")
    log_action(admin, "ADMIN_UPDATE_USER", f"{username} → {detail_str}", level="INFO")

    return {"ok": True, "message": f"{username} güncellendi."}


# ─────────────────────────────────────────────────────────────────────────────
# 3. GET /api/admin/active-sessions  — Son 15 dk aktif kullanıcılar
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/active-sessions")
def active_sessions(admin: str = Depends(get_current_admin)):
    """Son 15 dakika içinde işlem yapmış kullanıcıları döner."""
    with engine.connect() as conn:
        if engine.name == "postgresql":
            rows = conn.execute(text("""
                SELECT username, role, last_active
                FROM users
                WHERE last_active >= NOW() - INTERVAL '15 minutes'
                ORDER BY last_active DESC
            """)).fetchall()
        else:
            rows = conn.execute(text("""
                SELECT username, role, last_active
                FROM users
                WHERE last_active >= datetime('now', '-15 minutes')
                ORDER BY last_active DESC
            """)).fetchall()

    return {
        "active_sessions": [
            {"username": r[0], "role": r[1] or "user", "last_active": str(r[2])}
            for r in rows
        ],
        "count": len(rows),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. GET /api/admin/logs  — Sistem logları (filtreleme + sayfalama)
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/logs")
def get_logs(
    level:    Optional[str] = Query(None, description="INFO | WARNING | ERROR"),
    username: Optional[str] = Query(None),
    page:     int           = Query(1, ge=1),
    per_page: int           = Query(50, ge=1, le=200),
    admin:    str           = Depends(get_current_admin),
):
    """Sistem loglarını filtreli ve sayfalı döner."""
    conditions = []
    params: dict = {}

    if level:
        conditions.append("level = :level")
        params["level"] = level.upper()
    if username:
        conditions.append("username = :username")
        params["username"] = username

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    offset = (page - 1) * per_page
    params.update({"limit": per_page, "offset": offset})

    with engine.connect() as conn:
        total = conn.execute(
            text(f"SELECT COUNT(*) FROM system_logs {where_clause}"), params
        ).scalar()

        rows = conn.execute(
            text(f"""
                SELECT id, username, action, details, level, created_at
                FROM system_logs
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            params,
        ).fetchall()

    return {
        "total":   total,
        "page":    page,
        "pages":   (total + per_page - 1) // per_page if total else 1,
        "logs": [
            {
                "id":         r[0],
                "username":   r[1] or "—",
                "action":     r[2],
                "details":    r[3] or "",
                "level":      r[4] or "INFO",
                "created_at": str(r[5]) if r[5] else "",
            }
            for r in rows
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. GET /api/admin/stats  — Özet istatistikler (dashboard kartları)
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/stats")
def get_stats(admin: str = Depends(get_current_admin)):
    """Admin dashboard için özet metrikler."""
    with engine.connect() as conn:
        total_users  = conn.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
        active_users = conn.execute(text("SELECT COUNT(*) FROM users WHERE is_active=TRUE")).scalar() or 0
        total_alarms = conn.execute(text("SELECT COUNT(*) FROM user_alarms WHERE status='active'")).scalar() or 0

        if engine.name == "postgresql":
            online_now = conn.execute(text("""
                SELECT COUNT(*) FROM users
                WHERE last_active >= NOW() - INTERVAL '15 minutes'
            """)).scalar() or 0
            errors_today = conn.execute(text("""
                SELECT COUNT(*) FROM system_logs
                WHERE level='ERROR' AND created_at >= CURRENT_DATE
            """)).scalar() or 0
        else:
            online_now = conn.execute(text("""
                SELECT COUNT(*) FROM users
                WHERE last_active >= datetime('now', '-15 minutes')
            """)).scalar() or 0
            errors_today = conn.execute(text("""
                SELECT COUNT(*) FROM system_logs
                WHERE level='ERROR' AND date(created_at) = date('now')
            """)).scalar() or 0

    return {
        "total_users":  total_users,
        "active_users": active_users,
        "total_alarms": total_alarms,
        "online_now":   online_now,
        "errors_today": errors_today,
    }
