from fastapi import APIRouter
from takas_engine import get_takas_data

router = APIRouter(prefix="/api/takas", tags=["takas"])

from api.auth_routes import get_current_user
from fastapi import Depends

@router.get("/{ticker}")
def fetch_takas(ticker: str, current_user: str = Depends(get_current_user)):
    data = get_takas_data(ticker.upper())
    return data
