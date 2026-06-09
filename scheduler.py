import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database import engine
from sqlalchemy import text
from api.email_service import send_subscription_warning_email
from api.robot_engine import process_robot_sales, process_robot_buys

logger = logging.getLogger(__name__)

def check_subscriptions():
    """Günlük abonelik kontrollerini yapar."""
    logger.info("Abonelik kontrolü başlatıldı...")
    
    now = datetime.utcnow()
    three_days_later = now + timedelta(days=3)
    
    try:
        with engine.begin() as conn:
            # 1. Süresi dolan kullanıcıları pasife çek
            # Not: subscription_expires_at <= now
            expired_users = conn.execute(
                text("SELECT username FROM users WHERE is_active = TRUE AND subscription_expires_at IS NOT NULL AND subscription_expires_at <= :now"),
                {"now": now}
            ).fetchall()
            
            for (username,) in expired_users:
                conn.execute(
                    text("UPDATE users SET is_active = FALSE WHERE username = :u"),
                    {"u": username}
                )
                logger.info(f"Süresi dolan kullanıcı pasife çekildi: {username}")
                
            # 2. Süresi bitmesine tam 3 gün kalan kullanıcılara mail at
            # (3 günden az ve 2 günden fazla kalanlar - günde 1 kez çalışacağı için)
            warning_start = three_days_later - timedelta(hours=12)
            warning_end = three_days_later + timedelta(hours=12)
            
            warn_users = conn.execute(
                text("""
                    SELECT username, email 
                    FROM users 
                    WHERE is_active = TRUE 
                    AND email IS NOT NULL 
                    AND email != ''
                    AND subscription_expires_at >= :start 
                    AND subscription_expires_at <= :end
                """),
                {"start": warning_start, "end": warning_end}
            ).fetchall()
            
            for username, email in warn_users:
                success = send_subscription_warning_email(email, username, 3)
                if success:
                    logger.info(f"3 gün uyarı maili gönderildi: {username} ({email})")
                    
    except Exception as e:
        logger.error(f"Abonelik kontrolünde hata oluştu: {e}")

def start_scheduler():
    """Uygulama başlarken scheduler'ı başlatır."""
    scheduler = BackgroundScheduler()
    # Her gün saat 02:00'da çalışır
    scheduler.add_job(
        check_subscriptions, 
        CronTrigger(hour=2, minute=0),
        id="daily_subscription_check",
        replace_existing=True
    )
    
    # Robot Satış Kontrolü (Her 10 dakikada bir)
    scheduler.add_job(
        process_robot_sales,
        CronTrigger(minute="*/10"),
        id="robot_sell_cycle",
        replace_existing=True
    )
    
    # Robot Alış Taraması (Her saat başı)
    scheduler.add_job(
        process_robot_buys,
        CronTrigger(minute="0"),
        id="robot_buy_cycle",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Background scheduler başlatıldı.")
