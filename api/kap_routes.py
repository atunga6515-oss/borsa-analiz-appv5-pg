from fastapi import APIRouter
from kap_news import get_sentiment_summary, fetch_kap_news
from api.auth_routes import get_current_user
from fastapi import Depends

router = APIRouter(prefix="/api/kap", tags=["kap"])

@router.get("/{ticker}")
def fetch_kap_sentiment(ticker: str, current_user: str = Depends(get_current_user)):
    avg_score, results = get_sentiment_summary(ticker.upper())
    return {
        "avg_score": avg_score,
        "results": results
    }

@router.get("/raw/{ticker}")
def fetch_raw_kap(ticker: str, current_user: str = Depends(get_current_user)):
    news = fetch_kap_news(ticker.upper())
    return {"news": news}
