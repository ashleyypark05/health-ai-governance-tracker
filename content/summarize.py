"""
Health AI Governance Tracker — Summarization & Tagging Pipeline
==============================================================
Reads rows with null summaries from SQLite, sends t0 OPENAI API,
writes back summary, domain_tag, action_tag, stakeholder_tag,
and relevance scores.

Usage:
  python scripts/summarize.py                    # process all unsummarized
  python scripts/summarize.py --limit 10         # process first 10 (for testing)
  python scripts/summarize.py --rerun-id 42      # reprocess a specific row
"""

from urllib import response

from openai import OpenAI
import sqlite3
import json
import time
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scrapers.utils import DB_PATH

# ──────────────────────────────────────────────
# DOMAIN + ACTION TAXONOMIES
# (derived from Manatt Health AI Policy Tracker
#  and actual 2025-2026 health AI policy themes)
# ──────────────────────────────────────────────

DOMAIN_TAGS = [
    "clinical_care",             # AI in clinical decisions, oversight, patient consent
    "payor_utilization",         # Prior auth, downcoding, utilization management
    "transparency_consent",      # Patient disclosure, AI model cards, ONC requirements
    "chatbot_mental_health",     # AI chatbots, mental health, minors, chatbot liability
    "liability",                 # Developer/deployer liability, product liability, AI LEAD Act
    "regulatory_sandbox",        # State/federal sandbox programs, Utah OAIP, FDA TEMPO
    "data_privacy_hipaa",        # HIPAA enforcement, data sharing, OCR actions
    "federal_framework",         # White House EOs, OMB memos, Congress, preemption
    "general_health_ai",         # Doesn't fit above but clearly health AI-related
]

ACTION_TAGS = [
    "new_law",           # Bill signed into law
    "proposed_rule",     # NPRM, proposed regulation
    "final_rule",        # Final rule published
    "guidance_update",   # Agency guidance, FAQ, policy statement
    "enforcement",       # Enforcement action, investigation, settlement
    "rfi_comment",       # Request for information or public comment
    "research_program",  # Federal research initiative (ARPA-H, NIH, etc.)
    "executive_action",  # Executive order, OMB memo, White House action
    "court_action",      # Litigation, court ruling, DOJ action
    "introduced_bill",   # Bill introduced, not yet passed
    "industry_report",   # Trade association, law firm, think tank analysis
]

STAKEHOLDER_TAGS = [
    "health_system",             # Hospitals, IDNs, academic medical centers
    "payer",                     # Health insurance, MCOs, Medicaid managed care
    "digital_health_vendor",     # AI tool developers, digital health companies
    "provider_practice",         # Physicians, clinicians, small/mid practices
    "patient_consumer",          # Patient rights, consumer protections
    "all",                       # Broad applicability
]

# ──────────────────────────────────────────────
# PROMPTS
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior health AI policy analyst briefing the Chief Medical Officer and General Counsel of a large academic medical center. Your audience has deep clinical expertise but limited time — they need to know what happened, what agency or legislature did it, and what it means for their institution specifically.

Your summaries must be:
- Specific: name the agency, the rule, the bill number, the effective date
- Actionable: flag if this requires a compliance review, contract update, or policy change
- Honest about uncertainty: if a bill is only introduced (not passed), say so clearly
- Free of filler phrases like "this is significant" or "it is important to note"

Never begin a summary with "This development" or "This update." Start with the actor: "FDA updated...", "Indiana enacted...", "CMS proposed..."."""

SUMMARY_PROMPT_TEMPLATE = """Summarize the following health AI policy development in exactly 2-3 sentences for a CMO/GC briefing.

Source: {source_name}
URL: {source_url}
Title: {title}
Content: {raw_text}

Write 2-3 sentences only. Be specific and concrete."""

TAGGING_PROMPT_TEMPLATE = """Classify this health AI policy development.

Title: {title}
Summary: {summary}
Source: {source_name}

Return ONLY a JSON object with exactly these keys:
{{
  "domain_tag": <one of: {domain_tags}>,
  "action_tag": <one of: {action_tags}>,
  "stakeholder_tag": <one of: {stakeholder_tags}>,
  "relevance_amc": <integer 1-5: how relevant to an Academic Medical Center>,
  "relevance_payer": <integer 1-5: how relevant to a Health Payer/Insurer>,
  "relevance_dh": <integer 1-5: how relevant to a Digital Health AI Vendor>,
  "relevance_notes": <one sentence explaining the scores, especially if asymmetric>
}}

Relevance scale:
5 = Direct compliance obligation or major strategic implication
4 = Requires awareness and likely internal review
3 = Worth monitoring; may affect operations indirectly
2 = Peripheral relevance; background awareness only
1 = Not relevant to this stakeholder type

Return only the JSON object. No explanation, no markdown, no backticks."""


# ──────────────────────────────────────────────
# CORE PIPELINE
# ──────────────────────────────────────────────

def get_client():
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY not set in .env")
    return OpenAI(
        api_key=key,
        base_url="https://litellm.oit.duke.edu/v1"
    )


def call_openai(client, prompt: str, max_tokens: int = 400, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="GPT 4.1", 
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"    Retry {attempt+1}/{retries} after {wait}s: {e}")
                time.sleep(wait)
            else:
                raise


def summarize_row(client, row: dict) -> dict:
    """Generate summary + tags for a single development. Returns update dict."""
    title = row["title"] or ""
    raw_text = row["raw_text"] or title
    source_name = row["source_name"] or ""
    source_url = row["source_url"] or ""

    # Truncate raw_text to avoid token limits (keep first 2000 chars)
    raw_text_trimmed = raw_text[:2000]

    # Step 1: Generate summary
    summary_prompt = SUMMARY_PROMPT_TEMPLATE.format(
        source_name=source_name,
        source_url=source_url,
        title=title,
        raw_text=raw_text_trimmed
    )
    summary = call_openai(client, summary_prompt, max_tokens=200)

    # Step 2: Generate tags + relevance scores
    tag_prompt = TAGGING_PROMPT_TEMPLATE.format(
        title=title,
        summary=summary,
        source_name=source_name,
        domain_tags=", ".join(DOMAIN_TAGS),
        action_tags=", ".join(ACTION_TAGS),
        stakeholder_tags=", ".join(STAKEHOLDER_TAGS)
    )
    tag_response = call_openai(client, tag_prompt, max_tokens=300)

    # Parse JSON — strip markdown fences if present
    tag_response = tag_response.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    tags = json.loads(tag_response)

    return {
        "summary": summary,
        "domain_tag": tags.get("domain_tag"),
        "action_tag": tags.get("action_tag"),
        "stakeholder_tag": tags.get("stakeholder_tag"),
        "relevance_amc": tags.get("relevance_amc"),
        "relevance_payer": tags.get("relevance_payer"),
        "relevance_dh": tags.get("relevance_dh"),
    }


def write_updates(row_id: int, updates: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE developments SET
            summary         = ?,
            domain_tag      = ?,
            action_tag      = ?,
            stakeholder_tag = ?,
            relevance_amc   = ?,
            relevance_payer = ?,
            relevance_dh    = ?
        WHERE id = ?
    """, (
        updates["summary"],
        updates["domain_tag"],
        updates["action_tag"],
        updates["stakeholder_tag"],
        updates["relevance_amc"],
        updates["relevance_payer"],
        updates["relevance_dh"],
        row_id
    ))
    conn.commit()
    conn.close()


def run_summarization(limit: int = None, rerun_id: int = None):
    """Main pipeline. Processes unsummarized rows or reruns a specific ID."""
    from dotenv import load_dotenv
    load_dotenv()

    client = get_client()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if rerun_id:
        c.execute("SELECT * FROM developments WHERE id = ?", (rerun_id,))
    else:
        query = "SELECT * FROM developments WHERE summary IS NULL ORDER BY date_scraped DESC"
        if limit:
            query += f" LIMIT {limit}"
        c.execute(query)

    rows = c.fetchall()
    conn.close()

    if not rows:
        print("No unsummarized rows found.")
        return

    print(f"Processing {len(rows)} rows...")
    successes, failures = 0, 0

    for i, row in enumerate(rows, 1):
        row = dict(row)
        print(f"\n[{i}/{len(rows)}] {row['source_name']}: {row['title'][:70]}...")
        try:
            updates = summarize_row(client, row)
            write_updates(row["id"], updates)
            print(f"    ✓ {updates['domain_tag']} | {updates['action_tag']} | AMC:{updates['relevance_amc']}")
            successes += 1
            # Rate limit: ~20 req/min (two API calls per row)
            time.sleep(3)
        except json.JSONDecodeError as e:
            print(f"    ✗ JSON parse error: {e}")
            failures += 1
        except Exception as e:
            print(f"    ✗ Error: {e}")
            failures += 1

    print(f"\n{'─'*50}")
    print(f"Done. {successes} succeeded, {failures} failed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Max rows to process")
    parser.add_argument("--rerun-id", type=int, help="Reprocess a specific row ID")
    args = parser.parse_args()
    run_summarization(limit=args.limit, rerun_id=args.rerun_id)
