import logging
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database import engine
from sqlalchemy import text
from api.email_service import send_subscription_warning_email
from api.robot_engine import process_robot_core_loop, process_robot_hourly_scan

logger = logging.getLogger(__name__)

def check_subscriptions():
    """Günlük abonelik kontrollerini yapar."""
    logger.info("Abonelik kontrolü başlatıldı...")
    
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # timezone-naive UTC
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
    
    # Her gün saat 00:00'da hisse isimlerini günceller
    from api.symbol_service import update_bist_symbols
    scheduler.add_job(
        update_bist_symbols,
        CronTrigger(hour=0, minute=0),
        id="daily_symbol_update",
        replace_existing=True
    )
    
    # Robot Çekirdek Döngüsü (Mikro - 5 dk'da bir - Pazartesi-Cuma, 10:00 - 17:55)
    scheduler.add_job(
        process_robot_core_loop,
        CronTrigger(day_of_week="mon-fri", hour="10-17", minute="*/5"),
        id="robot_core_cycle",
        replace_existing=True
    )
    
    # Robot Makro Tarama (Saatlik Watchlist - Pazartesi-Cuma, 10:00 - 17:00 arası her saat başı)
    scheduler.add_job(
        process_robot_hourly_scan,
        CronTrigger(day_of_week="mon-fri", hour="10-17", minute="0"),
        id="robot_macro_cycle",
        replace_existing=True
    )

    # --- SİNYAL KARNESİ (Model Scorecard) ---
    from scorecard import run_daily_snapshot, score_matured_signals
    # Günlük snapshot: hafta içi, piyasa kapanışından sonra (18:30 TR)
    scheduler.add_job(
        run_daily_snapshot,
        CronTrigger(day_of_week="mon-fri", hour=18, minute=30, timezone="Europe/Istanbul"),
        id="scorecard_daily_snapshot",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=3600,
    )
    # Vadesi dolan sinyalleri puanla: her gün 19:30 TR
    scheduler.add_job(
        score_matured_signals,
        CronTrigger(hour=19, minute=30, timezone="Europe/Istanbul"),
        id="scorecard_daily_scoring",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=3600,
    )

    scheduler.start()
    logger.info("Background scheduler başlatıldı.")
