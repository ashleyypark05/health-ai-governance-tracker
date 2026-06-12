"""
Shared utilities for all scrapers.
"""
import sqlite3
import hashlib
import json
import os
import re
import requests
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "helpers", "data", "tracker.db")
LINK_REPORT_PATH = os.path.join(os.path.dirname(__file__), "..", "helpers", "data", "link_check_report.json")

LINK_CHECK_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HealthAIPolicyTracker/1.0)"
}

# Sites that block scripted requests (403) even though the link works fine
# in a browser. Don't flag these as broken.
BOT_BLOCKED_DOMAINS = ("congress.gov",)

def get_db():
    return sqlite3.connect(DB_PATH)

def make_hash(source_url: str, title: str) -> str:
    """Deduplication hash — same URL + title = same item."""
    return hashlib.md5(f"{source_url}|{title}".encode()).hexdigest()

def insert_development(record: dict) -> bool:
    """
    Insert a development record. Returns True if inserted, False if duplicate.
    Required keys: source_name, source_url, title
    Optional keys: date_published, raw_text
    """
    conn = get_db()
    c = conn.cursor()

    content_hash = make_hash(record["source_url"], record["title"])

    try:
        c.execute("""
            INSERT INTO developments
                (source_name, source_url, title, date_published, raw_text, content_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            record["source_name"],
            record["source_url"],
            record["title"],
            record.get("date_published"),
            record.get("raw_text"),
            content_hash
        ))
        conn.commit()
        print(f"  [+] Inserted: {record['title'][:80]}")
        return True
    except sqlite3.IntegrityError:
        # Duplicate — already exists
        return False
    finally:
        conn.close()

def clean_text(text: str) -> str:
    """Normalize whitespace in scraped text."""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def count_developments():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM developments")
    n = c.fetchone()[0]
    conn.close()
    return n

def check_existing_urls(timeout=15, report_path=LINK_REPORT_PATH):
    """
    Re-check every stored source_url for redirects (e.g. a federal agency
    reorganized its site and the old page now forwards to a new one) and
    for broken links (404/410/etc).

    - If a URL now resolves to a different final URL, update source_url
      (and content_hash, since it's derived from source_url|title) in place.
    - If a URL errors out or returns 4xx/5xx, it's left untouched. A flat
      404 with no redirect (e.g. a site that restructured without setting
      up forwarding) can't be auto-resolved — there's no hint of where the
      content moved to, so it's written to report_path for manual review
      instead.
    - URLs on BOT_BLOCKED_DOMAINS that return 403 are treated as "blocked,
      probably fine" rather than broken, since those sites reject scripted
      requests but work in a browser.

    Returns (updated_count, broken_list).
    """
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, source_url, title FROM developments")
    rows = c.fetchall()

    updated = 0
    broken = []
    blocked = []

    for dev_id, url, title in rows:
        if not url:
            continue
        try:
            r = requests.get(url, headers=LINK_CHECK_HEADERS, timeout=timeout, allow_redirects=True)
        except requests.RequestException as e:
            broken.append((dev_id, url, str(e)))
            continue

        if r.status_code == 403 and any(d in url for d in BOT_BLOCKED_DOMAINS):
            blocked.append((dev_id, url))
            continue

        if r.status_code >= 400:
            broken.append((dev_id, url, r.status_code))
            continue

        final_url = r.url
        if final_url != url:
            new_hash = make_hash(final_url, title)
            try:
                c.execute(
                    "UPDATE developments SET source_url = ?, content_hash = ? WHERE id = ?",
                    (final_url, new_hash, dev_id)
                )
            except sqlite3.IntegrityError:
                # Another row already has this hash — update the URL only
                c.execute(
                    "UPDATE developments SET source_url = ? WHERE id = ?",
                    (final_url, dev_id)
                )
            updated += 1
            print(f"  [migrated] id={dev_id}: {url} -> {final_url}")

    conn.commit()
    conn.close()

    if broken:
        print(f"\n  [!] {len(broken)} URL(s) returned errors — review manually:")
        for dev_id, url, status in broken:
            print(f"    id={dev_id} status={status} url={url}")

    if blocked:
        print(f"\n  [i] {len(blocked)} URL(s) blocked scripted requests (likely fine in a browser):")
        for dev_id, url in blocked:
            print(f"    id={dev_id} url={url}")

    if report_path:
        with open(report_path, "w") as f:
            json.dump({
                "checked_at": datetime.utcnow().isoformat() + "Z",
                "checked": len(rows),
                "migrated": updated,
                "broken": [{"id": i, "url": u, "status": s} for i, u, s in broken],
                "blocked": [{"id": i, "url": u} for i, u in blocked],
            }, f, indent=2)

    print(f"\n  Checked {len(rows)} existing URLs — {updated} migrated, {len(broken)} broken, {len(blocked)} blocked")
    return updated, broken
