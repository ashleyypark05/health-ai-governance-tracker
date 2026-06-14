"""
Build (and optionally send) the monthly Pulse digest email.

Reuses the same title/summary/preview logic as the app's Monthly Digest
tab (see pipeline/digest.py), so the email matches what subscribers see
on the site.

Usage:
  python pipeline/send_digest.py            # create a draft post in Beehiiv
  python pipeline/send_digest.py --preview  # write HTML to pipeline/digest_preview.html

Schedule this with cron or GitHub Actions to run on the 14th of each
month — a day ahead of the 15th send date referenced in the app's
subscription copy, leaving time to review the draft.

Required env vars (.env):
  OPENAI_API_KEY          for the LLM-written summary (falls back to a
                           templated summary if unset)
  BEEHIIV_API_KEY, BEEHIIV_PUB_ID   to create the digest as a draft post
  PULSE_APP_URL           link target for "Read the full digest →"
                           (defaults to https://pulse-tracker.streamlit.app)

The post is created with status "draft" — review and send it from the
Beehiiv dashboard rather than auto-publishing. Subject line, preview
text, and thumbnail are pre-filled.
"""
import argparse
import os
import sys
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from digest import month_developments, digest_title, digest_summary, email_subject, email_preview_text, render_email_html
from scrapers.utils import DB_PATH

THUMBNAIL_URL = "https://raw.githubusercontent.com/ashleyypark05/health-ai-governance-tracker/main/pipeline/assets/pulse_thumbnail.png"


def load_df():
    import sqlite3
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""SELECT id,source_name,source_url,title,date_published,
        summary,domain_tag,action_tag,stakeholder_tag,relevance_amc,relevance_payer,
        relevance_dh,date_scraped FROM developments WHERE summary IS NOT NULL
        ORDER BY date_published DESC,date_scraped DESC""", conn)
    conn.close()
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="Write HTML to a file instead of sending")
    args = parser.parse_args()

    load_dotenv()

    now = datetime.now()
    month_label = now.strftime("%B %Y")
    df = load_df()
    mo = month_developments(df, now)

    title = digest_title(mo)
    summary = digest_summary(mo, month_label)
    subject = email_subject(mo, month_label)
    preview_text = email_preview_text(mo)
    digest_url = os.environ.get("PULSE_APP_URL", "https://pulse-tracker.streamlit.app")
    html = render_email_html(mo, month_label, now.year, title=title, summary=summary, digest_url=digest_url)

    print(f"Subject: {subject}")
    print(f"Preview: {preview_text}")
    print(f"Title:   {title}")
    print(f"Summary: {summary}\n")

    if args.preview:
        out_path = os.path.join(os.path.dirname(__file__), "digest_preview.html")
        with open(out_path, "w") as f:
            f.write(html)
        print(f"Preview written to {out_path}")
        return

    bk = os.environ.get("BEEHIIV_API_KEY", "")
    bp = os.environ.get("BEEHIIV_PUB_ID", "")
    if not (bk and bp):
        print("BEEHIIV_API_KEY/BEEHIIV_PUB_ID not set — skipping send. Use --preview to write HTML locally.")
        return

    resp = requests.post(
        f"https://api.beehiiv.com/v2/publications/{bp}/posts",
        headers={"Authorization": f"Bearer {bk}", "Content-Type": "application/json"},
        json={
            "title": subject,
            "subtitle": title,
            "content_html": html,
            "status": "draft",
            "platform": "email",
            "email_subject_line": subject,
            "email_preview_text": preview_text,
            "thumbnail_image_url": THUMBNAIL_URL,
        },
        timeout=15,
    )
    resp.raise_for_status()
    print("Digest post created in Beehiiv (status: draft). Review and send from the Beehiiv dashboard.")


if __name__ == "__main__":
    main()
