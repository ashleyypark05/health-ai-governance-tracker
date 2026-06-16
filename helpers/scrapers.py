"""
Health AI Governance Policy Tracker — Scrapers
==============================================
Sources organized by agency/type.
Each scraper returns a list of dicts ready for insert_development().

Run all: python scrapers/scrapers.py
Run one: python scrapers/scrapers.py --source fda
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import feedparser
import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scrapers.utils import insert_development, clean_text, count_developments, check_existing_urls

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HealthAIPolicyTracker/1.0)"
}

# ──────────────────────────────────────────────
# FEDERAL AGENCY SCRAPERS
# ──────────────────────────────────────────────

def scrape_fda_digital_health():
    """
    FDA Digital Health Center of Excellence — AI/ML-enabled SaMD guidance,
    RFCs, PCCP submissions, CDS software guidance.
    Scrapes the DHCoE landing page and filters for AI/ML-relevant links.
    """
    items = []
    url = "https://www.fda.gov/medical-devices/digital-health-center-excellence"
    ai_url_kws = ["artificial-intell", "machine-learning", "clinical-decision",
                  "pccp", "samd", "software-medical", "measuring-and-evaluating"]
    ai_title_kws = ["artificial intelligence", "machine learning", "ai-enabled", "ai/ml",
                    "software as a medical", "clinical decision", "pccp",
                    "digital health and ai", "request for public comment",
                    "measuring and evaluating", "marketing submission recommendations",
                    "lifecycle management"]
    exclude_url_kws = ["/about-", "/services", "/terms", "/faq", "/network-",
                       "/advisory-", "/research-and-partner", "/what-is-",
                       "/policy-navigator", "/ask-", "/request-a-speaker",
                       "/wireless-", "/augmented-", "/regulatory-accelerat",
                       "/diagnostic-data", "/medical-device-inter", "/request-a-"]
    seen_urls = set()
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        main = soup.find("main") or soup.find(id="main-content")
        if not main:
            return items
        for a in main.find_all("a", href=True):
            title = clean_text(a.get_text())
            href = a["href"]
            if len(title) < 20:
                continue
            if any(ex in href for ex in exclude_url_kws):
                continue
            url_match = any(kw in href.lower() for kw in ai_url_kws)
            title_match = any(kw in title.lower() for kw in ai_title_kws)
            if not (url_match or title_match):
                continue
            if not href.startswith("http"):
                href = "https://www.fda.gov" + href
            if href in seen_urls:
                continue
            seen_urls.add(href)
            items.append({
                "source_name": "FDA Digital Health",
                "source_url": href,
                "title": title,
                "raw_text": title
            })
    except Exception as e:
        print(f"  [!] FDA Digital Health error: {e}")
    return items[:10]


def scrape_fda_ai_ml_action_plan():
    """
    FDA AI/ML Action Plan page — new guidances, frameworks, enforcement discretion.
    Covers: CDS Software guidance, General Wellness guidance, risk-based AI framework.
    """
    items = []
    url = "https://www.fda.gov/medical-devices/software-medical-device-samd/artificial-intelligence-and-machine-learning-aiml-enabled-medical-devices"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("div.lcds-main-content a[href]"):
            title = clean_text(a.get_text())
            if len(title) < 15 or len(title) > 300:
                continue
            href = a["href"]
            if not href.startswith("http"):
                href = "https://www.fda.gov" + href
            items.append({
                "source_name": "FDA AI/ML Medical Devices",
                "source_url": href,
                "title": title,
                "raw_text": title
            })
    except Exception as e:
        print(f"  [!] FDA AI/ML page error: {e}")
    return items[:15]


def scrape_cms_newsroom():
    """
    CMS Newsroom RSS — press releases on AI tools, prior auth, Medicare App Library,
    CRUSH initiative, ACCESS Model, plan selection AI.
    """
    items = []
    feed_url = "https://www.cms.gov/newsroom/rss/newsroom-rss-feed"
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:30]:
            title = entry.get("title", "")
            # Filter to AI-relevant items only
            ai_keywords = ["artificial intelligence", " AI ", "machine learning",
                          "digital health", "algorithm", "prior authorization",
                          "chatbot", "clinical decision"]
            if not any(kw.lower() in title.lower() or
                      kw.lower() in entry.get("summary", "").lower()
                      for kw in ai_keywords):
                continue
            items.append({
                "source_name": "CMS Newsroom",
                "source_url": entry.get("link", ""),
                "title": clean_text(title),
                "date_published": entry.get("published", ""),
                "raw_text": clean_text(entry.get("summary", ""))
            })
    except Exception as e:
        print(f"  [!] CMS Newsroom error: {e}")
    return items


def scrape_onc_news():
    """
    ONC (Office of National Coordinator) — HTI rulemaking, AI certification,
    interoperability, CDS transparency requirements.
    Scrapes healthit.gov/news/ links embedded in the ONC news page
    (the listing itself is JS-rendered, but news item hrefs appear in static HTML).
    """
    import re as _re
    items = []
    url = "https://healthit.gov/news/"
    seen = set()
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            # Keep only actual news article URLs (not the news index itself)
            if "healthit.gov/news/" not in href and not (
                href.startswith("/news/") and len(href) > 7
            ):
                continue
            title_raw = clean_text(a.get_text())
            if len(title_raw) < 15:
                continue
            if href.startswith("/"):
                href = "https://healthit.gov" + href
            if href in seen:
                continue
            seen.add(href)
            # Some links embed date at start: "June 25, 2026Title text..."
            date_pub = None
            date_match = _re.match(r"^([A-Z][a-z]+ \d+, \d{4})(.*)", title_raw)
            if date_match:
                date_pub = date_match.group(1)
                title_raw = clean_text(date_match.group(2))
            if len(title_raw) < 10:
                continue
            items.append({
                "source_name": "ONC/HealthIT.gov",
                "source_url": href,
                "title": title_raw,
                "date_published": date_pub,
                "raw_text": title_raw
            })
    except Exception as e:
        print(f"  [!] ONC error: {e}")
    return items[:20]


def scrape_federal_register_health_ai():
    """
    Federal Register API — proposed rules, final rules, RFIs from
    HHS, FDA, CMS, ONC, OCR with AI-related content.
    Returns last 90 days of results.
    """
    items = []
    agencies = ["health-and-human-services-department",
                "food-and-drug-administration",
                "centers-for-medicare-medicaid-services",
                "office-for-civil-rights-hhs"]
    search_terms = ["artificial intelligence", "machine learning", "clinical decision support",
                   "algorithmic", "automated decision"]

    api_url = "https://www.federalregister.gov/api/v1/documents.json"
    params = {
        "conditions[term]": "artificial intelligence health",
        "conditions[agencies][]": agencies,
        "conditions[type][]": ["RULE", "PRORULE", "NOTICE"],
        "per_page": 20,
        "order": "newest",
        "fields[]": ["title", "document_number", "html_url", "publication_date",
                    "abstract", "type", "agency_names"]
    }
    try:
        r = requests.get(api_url, params=params, headers=HEADERS, timeout=15)
        data = r.json()
        for doc in data.get("results", []):
            title = doc.get("title", "")
            abstract = doc.get("abstract", "") or ""
            items.append({
                "source_name": f"Federal Register ({', '.join(doc.get('agency_names', [])[:2])})",
                "source_url": doc.get("html_url", ""),
                "title": clean_text(title),
                "date_published": doc.get("publication_date"),
                "raw_text": clean_text(f"{title}. {abstract}")
            })
    except Exception as e:
        print(f"  [!] Federal Register API error: {e}")
    return items


def scrape_hhs_news():
    """
    HHS.gov newsroom — Secretary statements, RFIs on AI in clinical care,
    ASTP/ONC joint publications, OMB memos affecting HHS.
    """
    items = []
    feed_url = "https://www.hhs.gov/rss/news.xml"
    try:
        feed = feedparser.parse(feed_url)
        ai_keywords = ["artificial intelligence", "machine learning", "digital health",
                      "algorithm", "clinical decision", "health technology", "AI"]
        for entry in feed.entries[:40]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            if not any(kw.lower() in title.lower() or kw.lower() in summary.lower()
                      for kw in ai_keywords):
                continue
            items.append({
                "source_name": "HHS Newsroom",
                "source_url": entry.get("link", ""),
                "title": clean_text(title),
                "date_published": entry.get("published", ""),
                "raw_text": clean_text(f"{title}. {summary}")
            })
    except Exception as e:
        print(f"  [!] HHS Newsroom error: {e}")
    return items


# ──────────────────────────────────────────────
# STATE LEGISLATION SCRAPERS
# ──────────────────────────────────────────────

def scrape_ncsl_health_ai():
    """
    Google News: state health AI legislation — replaces the defunct NCSL tracker.
    Covers enacted and proposed state bills on AI in healthcare, chatbots,
    prior auth, mental health AI, clinical decision support, regulatory sandboxes.
    """
    items = []
    feed_url = (
        "https://news.google.com/rss/search"
        "?q=health+AI+legislation+state+bill+regulation&hl=en-US&gl=US&ceid=US:en"
    )
    health_kws = ["health", "medical", "clinical", "patient", "hospital", "insurance",
                  "prior auth", "chatbot", "mental health", "prescri", "medicare",
                  "medicaid", "physician", "provider", "hipaa", "digital health"]
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:40]:
            title_raw = entry.get("title", "")
            # Strip " - Source Name" suffix Google News appends
            title = title_raw.rsplit(" - ", 1)[0].strip() if " - " in title_raw else title_raw
            title = clean_text(title).rstrip(" -").strip()
            summary = clean_text(entry.get("summary", ""))
            if not any(kw in (title + summary).lower() for kw in health_kws):
                continue
            if len(title) < 20:
                continue
            items.append({
                "source_name": "State Health AI News",
                "source_url": entry.get("link", ""),
                "title": title,
                "date_published": entry.get("published", ""),
                "raw_text": clean_text(f"{title}. {summary}")
            })
    except Exception as e:
        print(f"  [!] State Health AI News error: {e}")
    return items[:20]


def scrape_california_leginfo():
    """
    California Legislative Information — high-signal state for health AI.
    Tracks: AI transparency bills, chatbot rules, health AI liability (AB 2575),
    payor prior auth (AB 2431), CDS tools.
    Uses search for 'artificial intelligence health'.
    """
    items = []
    url = "https://leginfo.legislature.ca.gov/faces/billSearchClient.xhtml"
    params = {
        "session_year": "20252026",
        "house": "Both",
        "author": "All",
        "lawCode": "All",
        "billNum": "",
        "keyword": "artificial intelligence health",
        "searchType": "BILL"
    }
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        for row in soup.select("table.billList tr")[1:]:
            cells = row.find_all("td")
            if len(cells) < 3:
                continue
            a = cells[0].find("a")
            if not a:
                continue
            bill_num = clean_text(a.get_text())
            description = clean_text(cells[2].get_text()) if len(cells) > 2 else ""
            href = a.get("href", "")
            if not href.startswith("http"):
                href = "https://leginfo.legislature.ca.gov" + href
            items.append({
                "source_name": "California Legislature",
                "source_url": href,
                "title": f"CA {bill_num}: {description[:120]}",
                "raw_text": clean_text(f"California {bill_num}. {description}")
            })
    except Exception as e:
        print(f"  [!] CA Legislature error: {e}")
    return items[:20]


def scrape_colorado_legislature():
    """
    Colorado Legislature — SB 205 revision is the most-watched state health AI bill.
    Covers: HIPAA carve-out for HIPAA-covered entities, consumer rights, disclosure.
    """
    items = []
    url = "https://leg.colorado.gov/bill-search?field_sessions=20251&field_chamber=All&field_bill_type=All&field_subjects=6761"
    # 6761 = Technology subject tag on CO leg site
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for article in soup.select("article.bill-item, .view-content .views-row"):
            a = article.find("a")
            if not a:
                continue
            title = clean_text(a.get_text())
            href = a.get("href", "")
            if not href.startswith("http"):
                href = "https://leg.colorado.gov" + href
            summary_el = article.find(class_=lambda x: x and "summary" in str(x))
            raw = clean_text(summary_el.get_text()) if summary_el else title
            health_kws = ["health", "medical", "hipaa", "patient", "provider",
                         "insurance", "clinical", "chatbot"]
            if not any(k in raw.lower() or k in title.lower() for k in health_kws):
                continue
            items.append({
                "source_name": "Colorado Legislature",
                "source_url": href,
                "title": title,
                "raw_text": raw
            })
    except Exception as e:
        print(f"  [!] Colorado Legislature error: {e}")
    return items[:15]


# ──────────────────────────────────────────────
# INDUSTRY / POLICY AGGREGATOR SCRAPERS
# ──────────────────────────────────────────────

def scrape_stat_health_ai():
    """
    STAT News health AI coverage — high-quality journalism on FDA decisions,
    clinical AI adoption, policy developments. RSS feed.
    """
    items = []
    feed_url = "https://www.statnews.com/category/health-tech/feed/"
    try:
        feed = feedparser.parse(feed_url)
        ai_kws = ["artificial intelligence", " AI ", "machine learning",
                 "algorithm", "clinical decision", "prior authorization",
                 "FDA", "CMS", "regulation"]
        for entry in feed.entries[:20]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            if not any(kw.lower() in title.lower() or kw.lower() in summary.lower()
                      for kw in ai_kws):
                continue
            items.append({
                "source_name": "STAT News",
                "source_url": entry.get("link", ""),
                "title": clean_text(title),
                "date_published": entry.get("published", ""),
                "raw_text": clean_text(f"{title}. {summary}")
            })
    except Exception as e:
        print(f"  [!] STAT News error: {e}")
    return items


def scrape_manatt_health():
    """
    Google News: federal health AI policy and governance — replaces the defunct
    Manatt Health newsletters URL. Covers FDA/CMS/ONC/HHS AI guidance,
    federal AI governance frameworks, health AI regulation and enforcement.
    """
    items = []
    feed_url = (
        "https://news.google.com/rss/search"
        "?q=health+AI+policy+FDA+CMS+ONC+HHS+governance+regulation&hl=en-US&gl=US&ceid=US:en"
    )
    federal_kws = ["fda", "cms", "onc", "hhs", "nih", "federal", "agency", "guidance",
                   "rule", "regulation", "policy", "governance", "framework",
                   "artificial intelligence", "machine learning", "algorithm",
                   "prior auth", "clinical decision", "digital health", "ai "]
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:40]:
            title_raw = entry.get("title", "")
            title = title_raw.rsplit(" - ", 1)[0].strip() if " - " in title_raw else title_raw
            title = clean_text(title).rstrip(" -").strip()
            summary = clean_text(entry.get("summary", ""))
            if not any(kw.lower() in (title + summary).lower() for kw in federal_kws):
                continue
            if len(title) < 20:
                continue
            items.append({
                "source_name": "Federal Health AI News",
                "source_url": entry.get("link", ""),
                "title": title,
                "date_published": entry.get("published", ""),
                "raw_text": clean_text(f"{title}. {summary}")
            })
    except Exception as e:
        print(f"  [!] Federal Health AI News error: {e}")
    return items[:20]


def scrape_aha_news():
    """
    American Hospital Association — tracks hospital/health system perspective
    on AI regulation, CMS rules, prior auth, clinical AI governance.
    """
    items = []
    feed_url = "https://www.aha.org/news/rss.xml"
    try:
        feed = feedparser.parse(feed_url)
        ai_kws = ["artificial intelligence", "machine learning", "algorithm",
                 "digital health", "prior authorization", "clinical decision"]
        for entry in feed.entries[:30]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            if not any(kw.lower() in title.lower() or kw.lower() in summary.lower()
                      for kw in ai_kws):
                continue
            items.append({
                "source_name": "AHA News",
                "source_url": entry.get("link", ""),
                "title": clean_text(title),
                "date_published": entry.get("published", ""),
                "raw_text": clean_text(f"{title}. {summary}")
            })
    except Exception as e:
        print(f"  [!] AHA error: {e}")
    return items


def scrape_nist_ai():
    """
    NIST AI news updates — AI RMF profiles, trustworthy AI research,
    health sector AI evaluations (CAISI), AI consortium, bias and safety.
    Uses the NIST news page filtered to the AI topic (topic 2753736).
    """
    items = []
    url = "https://www.nist.gov/news-events/news-updates/topic/2753736"
    health_ai_kws = [
        "health", "medical", "clinical", "patient", "drug", "hospital", "care",
        "fda", "cms", "hipaa", "ai rmf", "risk management", "trustworth",
        "bias", "safety", "evaluation", "benchmark", "caisi", "consortium",
        "algorithm", "machine learning", "artificial intelligence", "generative"
    ]
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for art in soup.select("article"):
            h3 = art.find("h3")
            a = h3.find("a") if h3 else None
            if not a:
                continue
            title = clean_text(a.get_text())
            if len(title) < 15:
                continue
            href = a["href"]
            if not href.startswith("http"):
                href = "https://www.nist.gov" + href
            t = art.find("time")
            date_pub = t.get("datetime", "")[:10] if t else None
            if not any(kw in title.lower() for kw in health_ai_kws):
                continue
            # Skip job postings
            if any(skip in title.lower() for skip in ["usajobs", "position for", "we are hiring"]):
                continue
            items.append({
                "source_name": "NIST AI",
                "source_url": href,
                "title": title,
                "date_published": date_pub,
                "raw_text": title
            })
    except Exception as e:
        print(f"  [!] NIST AI error: {e}")
    return items[:15]


# ──────────────────────────────────────────────
# ORCHESTRATOR
# ──────────────────────────────────────────────

SCRAPERS = {
    "fda":              scrape_fda_digital_health,
    "fda_aiml":         scrape_fda_ai_ml_action_plan,
    "cms":              scrape_cms_newsroom,
    "onc":              scrape_onc_news,
    "federal_register": scrape_federal_register_health_ai,
    "hhs":              scrape_hhs_news,
    "ncsl":             scrape_ncsl_health_ai,
    "california":       scrape_california_leginfo,
    "colorado":         scrape_colorado_legislature,
    "stat":             scrape_stat_health_ai,
    "manatt":           scrape_manatt_health,
    "aha":              scrape_aha_news,
    "nist":             scrape_nist_ai,
}

def run_all_scrapers(sources=None):
    targets = {k: v for k, v in SCRAPERS.items()
               if sources is None or k in sources}
    total_new = 0
    before = count_developments()

    for name, fn in targets.items():
        print(f"\n[{name.upper()}] Scraping...")
        try:
            items = fn()
            print(f"  Found {len(items)} items")
            inserted = sum(1 for item in items if insert_development(item))
            print(f"  Inserted {inserted} new items")
            total_new += inserted
        except Exception as e:
            print(f"  [!] Scraper failed: {e}")

    after = count_developments()
    print(f"\n{'─'*50}")
    print(f"Run complete. {after - before} new developments added. Total: {after}")

    print(f"\n{'─'*50}")
    print("Checking existing source URLs for migrations / broken links...")
    check_existing_urls()

    return total_new


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", nargs="+",
                       help=f"Sources to run. Options: {', '.join(SCRAPERS.keys())}")
    args = parser.parse_args()
    run_all_scrapers(sources=args.source)
