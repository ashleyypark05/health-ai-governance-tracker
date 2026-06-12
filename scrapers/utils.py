"""
Shared utilities for all scrapers.
"""
import sqlite3
import hashlib
import os
import re
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "helpers", "data", "tracker.db")

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
