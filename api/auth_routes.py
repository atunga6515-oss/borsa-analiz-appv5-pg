from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from auth import verify_login, register_user, get_user_role, touch_last_active, log_action
import os

# ── Security config ──────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "borsa-v5-secret-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 gün

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


# ── Token helpers ─────────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ── Dependencies ──────────────────────────────────────────────────────────────
def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """JWT'den kullanıcı adını çözer. Token yoksa geliştirme bypass."""
    if not token:
        return "admin1"  # Dev bypass — prod'da kaldır

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Geçersiz token")
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
@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
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
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": form_data.username,
        "role": role,
    }


@router.get("/me")
def read_users_me(current_user: str = Depends(get_current_user)):
    role = get_user_role(current_user)
    return {"username": current_user, "role": role}


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = ""


@router.post("/register", response_model=Token)
def register(req: RegisterRequest):
    result = register_user(req.username, req.password, req.email or "")
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])
    role = get_user_role(req.username)
    access_token = create_access_token(data={"sub": req.username, "role": role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": req.username,
        "role": role,
    }
