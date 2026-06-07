from fastapi import APIRouter, HTTPException, Depends, status, Response, Request, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from auth import verify_login, register_user, get_user_role, touch_last_active, log_action
import os
from limiter import limiter

IS_PROD = os.getenv("ENV", "development").lower() == "production"

# ── Security config ──────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "borsa-v5-secret-key-change-in-prod":
    raise ValueError("KRITIK GÜVENLİK HATASI: JWT_SECRET_KEY çevresel değişkeni (.env) ayarlanmamış veya varsayılan değer kullanılıyor! Lütfen güçlü bir gizli anahtar ayarlayın.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 gün

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


# ── Token helpers ─────────────────────────────────────────────────────────────
class Token(BaseModel):
    """Eski model - geriye dönüş uyumluluğu için saklanıyor."""
    access_token: str = ""  # Cookie-only modelde boş
    token_type: str
    username: str
    role: str

class LoginResponse(BaseModel):
    """Cookie-only auth model."""
    token_type: str
    username: str
    role: str


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ── Dependencies ──────────────────────────────────────────────────────────────
def get_current_user(request: Request, token: str = Depends(oauth2_scheme)) -> str:
    """JWT'den kullanıcı adını çözer ve geçerliliğini denetler."""
    # Cookie'den de token okumayı destekle
    cookie_token = request.cookies.get("access_token")
    actual_token = token or cookie_token
    
    if not actual_token:
        raise HTTPException(status_code=401, detail="Token bulunamadı")

    try:
        payload = jwt.decode(actual_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Geçersiz token")
            
        # Check active status from DB
        from database import engine
        from sqlalchemy import text
        from datetime import datetime
        with engine.connect() as conn:
            user = conn.execute(
                text("SELECT is_active, subscription_expires_at FROM users WHERE username=:u"), {"u": username}
            ).fetchone()
            
        if not user or not user[0]:
            raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı veya hesap pasif durumda")
            
        # Abonelik kontrolü (Sadece eğer tarih belirlenmişse)
        if user[1]:
            # SQLite string dönebilir, Postgres datetime dönebilir
            exp_date = user[1]
            if isinstance(exp_date, str):
                try:
                    exp_date = datetime.fromisoformat(exp_date.replace('Z', '+00:00'))
                    # timezone naive/aware karmaşasını önlemek için basitleştirme:
                    exp_date = exp_date.replace(tzinfo=None)
                except Exception:
                    pass
            if isinstance(exp_date, datetime):
                if datetime.utcnow() > exp_date:
                    raise HTTPException(status_code=403, detail="Abonelik süreniz dolmuştur.")

        touch_last_active(username)
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token doğrulanamadı",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_admin(current_user: str = Depends(get_current_user)) -> str:
    """Kullanıcının admin rolüne sahip olduğunu doğrular."""
    role = get_user_role(current_user)
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gereklidir.",
        )
    return current_user


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/token", response_model=LoginResponse)
@limiter.limit("5/minute")
def login_for_access_token(request: Request, response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    if not verify_login(form_data.username, form_data.password):
        log_action(form_data.username, "LOGIN_FAIL", "Hatalı şifre", level="WARNING")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı",
            headers={"WWW-Authenticate": "Bearer"},
        )
    role = get_user_role(form_data.username)
    access_token = create_access_token(data={"sub": form_data.username, "role": role})
    log_action(form_data.username, "LOGIN", "Başarılı giriş")
    touch_last_active(form_data.username)
    
    # HttpOnly Cookie ayarlama
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=IS_PROD  # Prod ortamında True (HTTPS zorunlu)
    )
    
    # access_token body'de döndürme (cookie-only model)
    return {
        "token_type": "bearer",
        "username": form_data.username,
        "role": role,
    }

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=IS_PROD
    )
    return {"status": "success"}


@router.get("/me")
def read_users_me(current_user: str = Depends(get_current_user)):
    from auth import get_user_role, get_user_quota
    role = get_user_role(current_user)
    quota = get_user_quota(current_user)
    return {"username": current_user, "role": role, "ai_quota": quota}


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = ""


@router.post("/register")
def register(req: RegisterRequest, current_user: str = Depends(get_current_user)):
    role = get_user_role(current_user)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Sadece admin yetkisine sahip kullanıcılar yeni kayıt oluşturabilir.")
    
    result = register_user(req.username, req.password, req.email or "")
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "status": "success",
        "message": f"{req.username} başarıyla oluşturuldu."
    }
