from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from telegram_utils import send_telegram_report

router = APIRouter()

class TelegramMessage(BaseModel):
    message: str

from api.auth_routes import get_current_user
from fastapi import Depends

@router.post("/send")
def send_telegram(payload: TelegramMessage, current_user: str = Depends(get_current_user)):
    result = send_telegram_report(payload.message)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return {"status": "success", "message": "Telegram mesaji gonderildi."}
