"""
auto_scheduler.py

Automatically runs the full pipeline on a recurring schedule.

Default: every 1 hour.
Override with env var: PIPELINE_INTERVAL_HOURS=2

Usage:
    cd /path/to/australian_market_intelligence
    PYTHONPATH=src python src/auto_scheduler.py

    # Run every 2 hours instead:
    PIPELINE_INTERVAL_HOURS=2 PYTHONPATH=src python src/auto_scheduler.py

Stop:
    Ctrl+C
"""

import os
import sys
import time
import logging
from datetime import datetime

import schedule

from run_full_pipeline import run_full_pipeline

# Always run from project root — same reason as run_full_pipeline.py
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)


# ─────────────────────────────────────────────
# Logging — separate scheduler log
# ─────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/scheduler.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("scheduler")


# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
INTERVAL_HOURS = int(os.environ.get("PIPELINE_INTERVAL_HOURS", 1))


# ─────────────────────────────────────────────
# Scheduled job
# ─────────────────────────────────────────────
def scheduled_run():
    """Called by the scheduler every INTERVAL_HOURS hours."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log.info(f"⏰  Scheduled run triggered at {now}")

    try:
        success = run_full_pipeline()
        if success:
            log.info("✅  Pipeline run completed successfully.")
        else:
            log.error("❌  Pipeline run finished with errors. Check logs/pipeline.log.")
    except Exception as e:
        log.error(f"❌  Unexpected error during pipeline run: {e}")

    # Show when next run is
    next_run = schedule.next_run()
    if next_run:
        log.info(f"⏳  Next run scheduled at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}\n")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    log.info("\n" + "═" * 60)
    log.info("  Australian Market Intelligence — Auto Scheduler")
    log.info(f"  Interval : every {INTERVAL_HOURS} hour(s)")
    log.info(f"  Started  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("  Stop     : Ctrl+C")
    log.info("═" * 60 + "\n")

    # Run immediately on startup so we don't wait an hour for first data
    log.info("▶  Running pipeline immediately on startup...\n")
    scheduled_run()

    # Set up recurring schedule
    schedule.every(INTERVAL_HOURS).hours.do(scheduled_run)

    log.info(f"⏰  Scheduler active — next automatic run in {INTERVAL_HOURS} hour(s).\n")

    # Keep the process alive; check for pending jobs every minute
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            # Log unexpected errors in the scheduler loop but keep running
            log.error(f"Scheduler loop error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("\n⏹  Scheduler stopped by user. Goodbye.\n")
        sys.exit(0)
