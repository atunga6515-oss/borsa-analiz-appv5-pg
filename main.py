from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from auth import init_auth_db
from api.auth_routes import router as auth_router
from api.screener_routes import router as screener_router
from api.portfolio_routes import router as portfolio_router
from api.top_picks_routes import router as top_picks_router
from api.top_picks_15d_routes import router as top_picks_15d_router
from api.takas_routes import router as takas_router
from api.kap_routes import router as kap_router
from api.data_routes import router as data_router
from api.backtest_routes import router as backtest_router
from api.analysis_routes import router as analysis_router
from api.telegram_routes import router as telegram_routes
from api.alarm_routes import router as alarm_router
from api.admin_routes import router as admin_router
from api.ai_routes import router as ai_router
from api.market_routes import router as market_router
from api.alpharank_routes import router as alpharank_router
from api.risk_routes import router as risk_router
from api.robot_routes import router as robot_router
from api.scorecard_routes import router as scorecard_router
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from limiter import limiter
import os

# Initialize FastAPI app
app = FastAPI(
    title="AlfaBIST API",
    description="Backend API for AlfaBIST Terminal",
    version="1.0.0",
)

# Rate Limiting (Brute force & Abuse protection)
# Limiter is imported from limiter.py
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add CORS Middleware to allow requests from the Next.js frontend
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    allowed_origins = [orig.strip() for orig in allowed_origins_env.split(",") if orig.strip()]
else:
    allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()
    init_auth_db()
    from scheduler import start_scheduler
    start_scheduler()
    print("Database and scheduler initialized successfully.")

app.include_router(auth_router)
app.include_router(screener_router)
app.include_router(portfolio_router)
app.include_router(top_picks_router)
app.include_router(top_picks_15d_router)
app.include_router(takas_router)
app.include_router(kap_router)
app.include_router(data_router)
app.include_router(backtest_router)
app.include_router(analysis_router)
app.include_router(alarm_router)
app.include_router(admin_router)
app.include_router(telegram_routes, prefix="/api/telegram", tags=["telegram"])
app.include_router(ai_router)
app.include_router(market_router)
app.include_router(alpharank_router, prefix="/api/alpharank", tags=["AlphaRank"])
app.include_router(risk_router)
app.include_router(robot_router)
app.include_router(scorecard_router)

@app.get("/")
def root():
    return {"status": "ok", "message": "AlfaBIST API is running on FastAPI"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
