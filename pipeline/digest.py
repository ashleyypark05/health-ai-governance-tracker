"""
Monthly digest content generation — shared between the Streamlit app's
Monthly Digest tab (pipeline/app/main.py) and the automated email send
job (pipeline/send_digest.py).

Produces, from a dataframe of `developments` rows:
  - digest_title()    the dynamic headline ("31 health AI policy
                       developments this month, led by X and Y.")
  - digest_summary()  a 3-4 sentence hook + summary of the month,
                       written by an LLM (falls back to a templated
                       summary if OPENAI_API_KEY is unavailable)
  - top_developments() the highest-relevance items, for preview cards
  - email_subject() / render_email_html()  full email content built
                       from the above
"""
import os
from datetime import datetime, timedelta

import pandas as pd

DOMAIN_LABELS = {
    "clinical_care": "Clinical Care",
    "payor_utilization": "Payor / Utilization Mgmt",
    "transparency_consent": "Transparency & Consent",
    "chatbot_mental_health": "Chatbot / Mental Health",
    "liability": "Liability",
    "regulatory_sandbox": "Regulatory Sandbox",
    "data_privacy_hipaa": "Data Privacy / HIPAA",
    "federal_framework": "Federal Framework",
    "general_health_ai": "General Health AI",
}


# ── MONTH WINDOW ────────────────────────────────
def month_window(now=None):
    """Start date (YYYY-MM-DD) of the digest window — first of the previous month."""
    now = now or datetime.now()
    return (now.replace(day=1) - timedelta(days=1)).replace(day=1).strftime("%Y-%m-%d")


def month_developments(df, now=None):
    """Developments published since month_window(), or the highest-relevance
    items overall if nothing falls in that window."""
    if df.empty:
        return pd.DataFrame()
    pms = month_window(now)
    mo = df[df["date_published"].fillna(df["date_scraped"]) >= pms].sort_values(
        "relevance_amc", ascending=False)
    if mo.empty:
        mo = df.sort_values("relevance_amc", ascending=False)
    return mo


# ── TITLE ────────────────────────────────────────
def digest_title(mo):
    if mo.empty:
        return "New health AI policy developments, organized by domain."
    n_dev = len(mo)
    top_doms = [DOMAIN_LABELS.get(d, d) for d in mo["domain_tag"].value_counts().index[:2]]
    if len(top_doms) >= 2:
        lead = f"{top_doms[0]} and {top_doms[1]}"
    elif top_doms:
        lead = top_doms[0]
    else:
        lead = "multiple domains"
    return f"{n_dev} health AI policy development{'s' if n_dev != 1 else ''} this month, led by {lead}."


def digest_lead_domains(mo, n=2):
    """Short ' & '-joined domain phrase for subject lines."""
    if mo.empty:
        return "Health AI Policy"
    doms = [DOMAIN_LABELS.get(d, d) for d in mo["domain_tag"].value_counts().index[:n]]
    return " & ".join(doms) if doms else "Health AI Policy"


# ── TOP DEVELOPMENTS (for preview cards) ─────────
def top_developments(mo, n=3, stakeholder_col="relevance_amc"):
    if mo.empty:
        return []
    top = mo.sort_values(stakeholder_col, ascending=False, na_position="last").head(n)
    out = []
    for _, row in top.iterrows():
        out.append({
            "title": row.get("title", ""),
            "summary": row.get("summary", ""),
            "domain_tag": row.get("domain_tag", "general_health_ai"),
            "domain_label": DOMAIN_LABELS.get(row.get("domain_tag"), row.get("domain_tag", "")),
            "source_name": row.get("source_name", ""),
            "source_url": row.get("source_url", ""),
            "relevance_amc": row.get("relevance_amc"),
        })
    return out


# ── HOOK + SUMMARY (LLM, with templated fallback) ─
_SUMMARY_SYSTEM_PROMPT = """You are writing the opening summary for "Pulse," a monthly health AI \
policy digest read by health system executives, payers, and digital health companies. \
Write 3-4 sentences in plain, confident language. Open with a one-sentence hook naming \
the month's dominant theme. Then summarize the breadth of activity and flag anything \
requiring compliance attention. End with a pointer to what to watch. Do not use filler \
phrases like "this digest covers" or "in this edition," do not start with "This month," \
and do not use markdown."""

_SUMMARY_PROMPT_TEMPLATE = """{month} edition. {n} health AI policy development{n_s} tracked.
{enacted} enacted law{enacted_s} with potential compliance obligations.
{high_rel} development{high_rel_s} scored high relevance (4-5/5) for academic medical centers.

Developments by domain:
{dom_lines}

Top developments this month:
{top_lines}

Write the 3-4 sentence summary now."""


def _get_llm_client():
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=key, base_url="https://litellm.oit.duke.edu/v1")
    except Exception:
        return None


def _plural(n):
    return "" if n == 1 else "s"


def _llm_summary(client, mo, month_label):
    n = len(mo)
    enacted = int((mo["action_tag"] == "new_law").sum())
    high_rel = int((mo["relevance_amc"].fillna(0) >= 4).sum())
    dom_counts = mo["domain_tag"].value_counts()
    dom_lines = "\n".join(f"- {DOMAIN_LABELS.get(d, d)}: {c}" for d, c in dom_counts.items())
    top5 = mo.sort_values("relevance_amc", ascending=False, na_position="last").head(5)
    top_lines = "\n".join(
        f"- [{DOMAIN_LABELS.get(r['domain_tag'], r['domain_tag'])}] {r['title']}"
        for _, r in top5.iterrows())

    prompt = _SUMMARY_PROMPT_TEMPLATE.format(
        month=month_label, n=n, n_s=_plural(n),
        enacted=enacted, enacted_s=_plural(enacted),
        high_rel=high_rel, high_rel_s=_plural(high_rel),
        dom_lines=dom_lines, top_lines=top_lines,
    )
    resp = client.chat.completions.create(
        model="GPT 4.1",
        messages=[
            {"role": "system", "content": _SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=220,
    )
    return resp.choices[0].message.content.strip()


def _fallback_summary(mo):
    n = len(mo)
    enacted = int((mo["action_tag"] == "new_law").sum())
    high_rel = int((mo["relevance_amc"].fillna(0) >= 4).sum())
    top_doms = [DOMAIN_LABELS.get(d, d) for d in mo["domain_tag"].value_counts().index[:2]]
    lead = " and ".join(top_doms) if top_doms else "multiple domains"

    parts = [f"{n} health AI policy development{_plural(n)} were tracked this month, led by activity in {lead}."]
    if enacted:
        verb = "were" if enacted != 1 else "was"
        parts.append(f"{enacted} new law{_plural(enacted)} {verb} enacted with potential compliance "
                      f"obligations for health systems and digital health vendors.")
    if high_rel:
        parts.append(f"{high_rel} development{_plural(high_rel)} scored high relevance (4-5/5) for "
                      f"academic medical centers and warrant a closer look.")
    parts.append("Browse the developments below for the full list, tagged and summarized by domain.")
    return " ".join(parts)


def digest_summary(mo, month_label, use_llm=True):
    """3-4 sentence hook + summary of the month. Used for both the
    Monthly Digest tab body text and the email digest."""
    if mo.empty:
        return ("No new health AI policy developments were tracked this period. Check back "
                "after the next scrape cycle, or browse the full tracker for prior updates.")
    if use_llm:
        client = _get_llm_client()
        if client:
            try:
                return _llm_summary(client, mo, month_label)
            except Exception:
                pass
    return _fallback_summary(mo)


# ── EMAIL ────────────────────────────────────────
def email_subject(mo, month_label):
    return f"Pulse — {month_label} Digest: {digest_lead_domains(mo, n=2)}"


def email_preview_text(mo):
    """Short preheader shown next to the subject line in inbox previews."""
    if mo.empty:
        return "No new health AI policy developments were tracked this period."
    n = len(mo)
    enacted = int((mo["action_tag"] == "new_law").sum())
    if enacted:
        return (f"{n} development{_plural(n)} tracked this month, including "
                f"{enacted} newly enacted law{_plural(enacted)} with compliance implications.")
    return digest_title(mo)


def render_email_html(mo, month_label, year, title=None, summary=None, top=None, digest_url=None):
    title = title if title is not None else digest_title(mo)
    summary = summary if summary is not None else digest_summary(mo, month_label)
    top = top if top is not None else top_developments(mo, n=3)
    digest_url = digest_url or os.environ.get("PULSE_APP_URL", "https://pulse-tracker.streamlit.app")

    preview_html = ""
    for d in top:
        src = (f'<a href="{d["source_url"]}" style="color:#1B6CA8;text-decoration:none;'
               f'font-weight:600;font-size:13px">View source →</a>') if d["source_url"] else ""
        preview_html += f"""
        <tr><td style="padding:0 0 16px">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #C5D6E8;border-radius:10px">
            <tr><td style="padding:18px 20px">
              <div style="font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#00C2A8;margin-bottom:6px">{d['domain_label']}</div>
              <div style="font-size:15px;font-weight:700;color:#0B2545;margin-bottom:6px;line-height:1.35">{d['title']}</div>
              <div style="font-size:13px;color:#3d5166;line-height:1.6;margin-bottom:8px">{d['summary']}</div>
              {src}
            </td></tr>
          </table>
        </td></tr>"""

    return f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300..800;1,300..800&family=Michroma&display=swap">
  </head>
  <body style="margin:0;padding:0;background:#F0F4F9;font-family:Helvetica,Arial,sans-serif">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F0F4F9">
      <tr><td align="center" style="padding:32px 16px">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:14px;overflow:hidden">
          <tr><td style="background:#0B2545;padding:24px 32px">
            <div>
              <span style="font-family:'Michroma','Inter',Helvetica,Arial,sans-serif;font-size:24px;color:#ffffff;letter-spacing:-.02em;vertical-align:middle">Pulse</span>
              <span style="display:inline-block;vertical-align:middle;width:6px;height:6px;background:#00C2A8;border-radius:50%;margin-left:6px"></span>
            </div>
            <div style="font-family:'Inter',Helvetica,Arial,sans-serif;font-size:12px;color:rgba(255,255,255,.65);margin-top:4px">Health AI Policy Tracker — In Your Pocket</div>
          </td></tr>
          <tr><td style="padding:32px 32px 8px">
            <div style="font-size:12px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#00C2A8;margin-bottom:10px">Monthly Digest · {month_label}</div>
            <div style="font-size:24px;font-weight:800;color:#0B2545;line-height:1.25;margin-bottom:14px">{title}</div>
            <div style="font-size:15px;color:#3d5166;line-height:1.7;margin-bottom:24px">{summary}</div>
          </td></tr>
          <tr><td style="padding:0 32px">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              {preview_html}
            </table>
          </td></tr>
          <tr><td align="center" style="padding:8px 32px 36px">
            <a href="{digest_url}" style="display:inline-block;background:#00C2A8;color:#0B2545;font-weight:700;font-size:15px;text-decoration:none;padding:14px 36px;border-radius:999px">Read the full digest →</a>
          </td></tr>
          <tr><td style="background:#0B2545;padding:24px 32px;text-align:center">
            <div style="font-family:'Michroma','Inter',Helvetica,Arial,sans-serif;font-size:16px;color:#ffffff;letter-spacing:-.02em">Pulse <span style="display:inline-block;vertical-align:middle;width:6px;height:6px;background:#00C2A8;border-radius:50%;margin-left:2px"></span></div>
            <div style="font-family:'Inter',Helvetica,Arial,sans-serif;font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.65);margin-top:8px">© {year} Pulse · Health AI Policy Tracker · Updated daily</div>
          </td></tr>
        </table>
      </td></tr>
    </table>
  </body>
</html>"""
