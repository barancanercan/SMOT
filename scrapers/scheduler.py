#!/usr/bin/env python3
"""
S.A.M - Otomatik Scrape Scheduler
Her sabah 10:00 (Europe/Istanbul) tüm Twitter + Instagram verilerini çeker.

Kullanım:
    python -m scrapers.scheduler          # foreground
    nohup python -m scrapers.scheduler &  # background
"""

import os
import sys
import signal
import logging
import logging.handlers
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# ── Log kurulumu ─────────────────────────────────────────────────────────────
LOG_DIR = os.path.join(PROJECT_ROOT, "data", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "scheduler.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=3),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("Scheduler")

try:
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger
except ImportError:
    logger.error("apscheduler kurulu değil. Çalıştır: pip install apscheduler")
    sys.exit(1)


# ── Görevler ─────────────────────────────────────────────────────────────────
def run_twitter_scrape():
    logger.info("=" * 60)
    logger.info(f"Twitter scrape başlıyor: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    try:
        from scrapers.batch_twitter import main as twitter_main
        twitter_main()
        logger.info("Twitter scrape tamamlandı ✅")
    except Exception as e:
        logger.error(f"Twitter scrape HATA: {e}")


def run_instagram_scrape():
    logger.info(f"Instagram scrape başlıyor: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    try:
        from scrapers.batch_instagram import main as ig_main
        ig_main()
        logger.info("Instagram scrape tamamlandı ✅")
    except Exception as e:
        logger.error(f"Instagram scrape HATA: {e}")


def run_daily_scrape():
    """Her sabah 10:00'da çalışan ana görev"""
    logger.info("=" * 60)
    logger.info(f"GÜNLÜK SCRAPE BAŞLIYOR — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    run_twitter_scrape()
    run_instagram_scrape()
    logger.info("=" * 60)
    logger.info("GÜNLÜK SCRAPE TAMAMLANDI")
    logger.info("=" * 60)


# ── Scheduler ────────────────────────────────────────────────────────────────
scheduler = BlockingScheduler(timezone="Europe/Istanbul")


def shutdown(signum, frame):
    logger.info(f"Signal {signum} alındı, scheduler durduruluyor...")
    scheduler.shutdown(wait=False)
    sys.exit(0)


def main():
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # Her sabah 10:00 Europe/Istanbul
    scheduler.add_job(
        run_daily_scrape,
        CronTrigger(hour=10, minute=0, timezone="Europe/Istanbul"),
        id="daily_scrape",
        name="S.A.M Günlük Scrape",
        misfire_grace_time=3600,  # 1 saat içinde kaçırılmış iş yeniden çalışır
    )

    next_run = scheduler.get_job("daily_scrape").next_run_time
    logger.info(f"Scheduler başlatıldı. Sonraki çalışma: {next_run}")
    logger.info("Durdurmak için Ctrl+C veya SIGTERM gönderin.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler durduruldu.")


if __name__ == "__main__":
    main()
