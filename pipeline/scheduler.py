"""
Daily scheduler — runs scrape pipeline then summarization.
Run this in the background: python pipeline/scheduler.py

For production: use GitHub Actions (see .github/workflows/daily-pipeline.yml
and .github/workflows/monthly-digest.yml) instead of this script.
"""
import schedule
import time
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def daily_job():
    print(f"\n{'='*60}")
    print(f"Daily run starting: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")

    # Step 1: Scrape all sources
    from helpers.scrapers import run_all_scrapers
    run_all_scrapers()

    # Step 2: Summarize anything new (no limit — process everything)
    from content.summarize import run_summarization
    run_summarization()

    print(f"\nDaily run complete: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    print("Scheduler starting. Will run daily at 7:00 AM.")
    print("Running once immediately to verify setup...\n")

    daily_job()  # run immediately on start

    schedule.every().day.at("07:00").do(daily_job)

    while True:
        schedule.run_pending()
        time.sleep(60)
