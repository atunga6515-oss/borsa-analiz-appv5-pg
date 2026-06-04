from fastapi import APIRouter
from takas_engine import get_takas_data

router = APIRouter(prefix="/api/takas", tags=["takas"])

@router.get("/{ticker}")
def fetch_takas(ticker: str):
    data = get_takas_data(ticker.upper())
    return data
