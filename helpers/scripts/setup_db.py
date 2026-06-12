"""
Run this once to initialize the database.
Usage: python scripts/setup_db.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tracker.db")

def setup():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS developments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Source metadata
            source_name     TEXT NOT NULL,
            source_url      TEXT NOT NULL,
            title           TEXT NOT NULL,
            date_published  TEXT,
            date_scraped    TEXT NOT NULL DEFAULT (date('now')),

            -- Raw content
            raw_text        TEXT,

            -- LLM-generated fields (populated in Week 2)
            summary         TEXT,
            domain_tag      TEXT,   -- clinical_care | payor_utilization | transparency_consent |
                                    -- chatbot_mental_health | liability | regulatory_sandbox |
                                    -- data_privacy_hipaa | federal_framework | general_health_ai
            action_tag      TEXT,   -- new_law | proposed_rule | guidance_update | enforcement |
                                    -- rfi_comment | research_program | executive_action | court_action
            stakeholder_tag TEXT,   -- health_system | payer | digital_health_vendor |
                                    -- academic_medical_center | all

            -- Relevance scores (populated in Week 2)
            relevance_amc   INTEGER,  -- 1-5: Academic Medical Center relevance
            relevance_payer INTEGER,  -- 1-5: Payer relevance
            relevance_dh    INTEGER,  -- 1-5: Digital health vendor relevance

            -- Deduplication
            content_hash    TEXT UNIQUE
        )
    """)

    # Index for fast filtering
    c.execute("CREATE INDEX IF NOT EXISTS idx_domain ON developments(domain_tag)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_action ON developments(action_tag)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_date ON developments(date_published)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_source ON developments(source_name)")

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    setup()
