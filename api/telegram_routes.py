from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from telegram_utils import send_telegram_report

router = APIRouter()

class TelegramMessage(BaseModel):
    message: str

@router.post("/send")
def send_telegram(payload: TelegramMessage):
    result = send_telegram_report(payload.message)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return {"status": "success", "message": "Telegram mesaji gonderildi."}
