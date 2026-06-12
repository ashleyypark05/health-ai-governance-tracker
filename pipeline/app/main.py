import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
import sys
import requests as http_requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from digest import DOMAIN_LABELS, month_developments, digest_title, digest_summary

load_dotenv()

st.set_page_config(
    page_title="Pulse — Health AI Policy Tracker",
    page_icon="⚕",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "started" not in st.session_state:
    st.session_state.started = False

# ── DATA ─────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "helpers", "data", "tracker.db")

@st.cache_resource
def get_conn():
    if not os.path.exists(DB_PATH): return None
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

@st.cache_data(ttl=300)
def load_data():
    c = get_conn()
    if not c: return pd.DataFrame()
    return pd.read_sql_query("""SELECT id,source_name,source_url,title,date_published,
        summary,domain_tag,action_tag,stakeholder_tag,relevance_amc,relevance_payer,
        relevance_dh,date_scraped FROM developments WHERE summary IS NOT NULL
        ORDER BY date_published DESC,date_scraped DESC""", c)

DL = DOMAIN_LABELS
DC = {"clinical_care":"var(--dom-teal)","payor_utilization":"var(--dom-champagne)","transparency_consent":"var(--dom-sky)",
      "chatbot_mental_health":"var(--dom-mint)","liability":"var(--dom-bronze)","regulatory_sandbox":"var(--dom-forest)",
      "data_privacy_hipaa":"var(--dom-slate)","federal_framework":"var(--dom-navy)","general_health_ai":"var(--dom-grey)"}
AL = {"new_law":"New Law","proposed_rule":"Proposed Rule","final_rule":"Final Rule",
      "guidance_update":"Guidance Update","enforcement":"Enforcement","rfi_comment":"RFI / Comment",
      "research_program":"Research Program","executive_action":"Executive Action",
      "court_action":"Court Action","introduced_bill":"Introduced Bill","industry_report":"Industry Report"}
SOURCES = ["FDA Digital Health","FDA AI/ML Medical Devices","CMS Newsroom","ONC / HealthIT.gov",
           "Federal Register (HHS/FDA/CMS)","HHS Newsroom","NCSL State AI Tracker",
           "California Legislature","Colorado Legislature","Manatt Health","AHA News","NIST AI RMF","STAT News"]

df = load_data()
N  = len(df) if not df.empty else 31
EN = int(len(df[df["action_tag"]=="new_law"])) if not df.empty else 6

def rdot(s):
    if not s: return ""
    s = int(s)
    cls = "tag tag-amc tag-amc-5" if s==5 else "tag tag-amc"
    return f'<span class="{cls}">AMC {s}/5</span>'

def card(row):
    d  = row.get("domain_tag") or "general_health_ai"
    a  = row.get("action_tag") or ""
    u  = row.get("source_url") or ""
    ac = "tag-law" if a=="new_law" else "tag-act"
    lh = f'<a class="sl" href="{u}" target="_blank">View source →</a>' if u else ""
    ah = rdot(row.get("relevance_amc"))
    st.markdown(f"""<div class="dc"><div class="dct dc-{d}"></div><div class="dcb">
      <div class="cm">{row.get('source_name','')} · {row.get('date_published','')}</div>
      <div class="ct">{row.get('title','')}</div>
      <div class="cs">{row.get('summary','')}</div>
      <div class="cf"><span class="tag tg">{DL.get(d,d)}</span>
        <span class="tag {ac}">{AL.get(a,a)}</span>
        <span class="rb">{ah}</span>{lh}</div>
    </div></div>""", unsafe_allow_html=True)

def footer(light=False):
    bg = "var(--bg)" if light else "var(--navy)"
    copy_c = "var(--muted)" if light else "rgba(255,255,255,.65)"
    logo_c = "var(--navy)" if light else "#fff"
    st.markdown(f"""<div class="ft" style="background:{bg}">
      <div style="font-family:'Inter',sans-serif;font-weight:600;font-size:.63rem;letter-spacing:.08em;text-transform:uppercase;color:{copy_c}">
        © {datetime.now().year} Pulse · Health AI Policy Tracker · Updated daily</div>
      <div style="font-family:'Michroma',sans-serif;font-size:1.33rem;color:{logo_c};display:flex;align-items:center;gap:.4rem">Pulse<span style="width:.223em;height:.223em;background:#00C2A8;border-radius:50%;display:inline-block;flex-shrink:0"></span></div>
    </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════
# LANDING
# ════════════════════════════════════════════════════
if not st.session_state.started:
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300..800;1,300..800&family=Michroma&display=swap');
*{box-sizing:border-box}
html,body,.stApp{margin:0;padding:0;background:#04080F !important;overflow-x:hidden;font-family:'Inter',sans-serif}
#MainMenu,footer,header{visibility:hidden}
.block-container{padding:0!important;max-width:100%!important}
.main .block-container{padding:0!important}
section[data-testid="stSidebar"]{display:none}

@keyframes hb{
  0%  {box-shadow:0 0 0 0 rgba(0,194,168,.6)}
  30% {box-shadow:0 0 0 10px rgba(0,194,168,.2)}
  50% {box-shadow:0 0 0 5px rgba(0,194,168,.1)}
  65% {box-shadow:0 0 0 14px rgba(0,194,168,.12)}
  100%{box-shadow:0 0 0 0 rgba(0,194,168,0)}
}

/* Landing layout — vertical block fills viewport, .land grows to fill
   remaining space so the button (a separate sibling element) stays
   within the first viewport instead of being pushed below the fold */
[data-testid="stVerticalBlock"]{min-height:100vh;display:flex;flex-direction:column}
.element-container:has(.land){flex:1;display:flex;flex-direction:column;position:relative}
.land{
  min-height:100vh; width:100%;
  background:
    radial-gradient(ellipse at 30% 40%,#0d2a6e 0%,transparent 60%),
    radial-gradient(ellipse at 75% 25%,#091a4f 0%,transparent 55%),
    #04080F;
  display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  padding:4rem 2rem;
}
@media(min-width:1024px){.land{padding:8rem 6rem}}
@media(min-width:1440px){.land{padding:12rem 8rem}}
.lhero{display:flex;flex-direction:column;width:fit-content}
.lrow{display:flex;align-items:center;gap:0}
.llogo{flex-shrink:0}
.lname{
  font-family:'Michroma',sans-serif;
  font-size:clamp(2.38rem,7vw,3.85rem);color:#fff;
  letter-spacing:0;line-height:1;
  display:flex;align-items:center;gap:.4rem;
}
.ldot{width:.223em;height:.223em;background:#00C2A8;border-radius:50%;flex-shrink:0;margin-left:12px}
.lecg{flex:0 0 19.55rem;width:19.55rem;padding:0 2rem;display:flex;align-items:center}
@media(min-width:1024px){.lecg{flex-basis:23.06rem;width:23.06rem}}
@media(min-width:1440px){.lecg{flex-basis:39.02rem;width:39.02rem}}
.lecg svg{width:100%;height:40px;overflow:visible}
/* invisible placeholder — reserves the Get Started button's footprint
   inside .lrow so the row's height/centering accounts for it, and the
   real (absolutely-positioned) button lines up with this spot */
.lbtn-ghost{
  visibility:hidden;flex-shrink:0;
  font-family:'Inter',sans-serif;font-weight:700;font-size:clamp(.95rem,1.6vw,1.15rem);
  letter-spacing:.02em;white-space:nowrap;
  padding:.85rem 2.4rem;border:1px solid transparent;border-radius:999px;
}
@media(max-width:768px){
  html,body,.stApp{
    background:
      radial-gradient(ellipse at 30% 40%,#0d2a6e 0%,transparent 60%),
      radial-gradient(ellipse at 75% 25%,#091a4f 0%,transparent 55%),
      #04080F !important;
  }
  [data-testid="stVerticalBlock"]{justify-content:center}
  .element-container:has(.land){flex:0 0 auto}
  .land{min-height:0;padding-bottom:0;background:transparent}
  .lhero{width:100%}
  .lrow{width:100%}
  .lbtn-ghost{display:none}
  .lecg{flex:1;width:auto;padding:0 1rem}
}
.ltag{
  font-family:'Inter',sans-serif;
  font-size:clamp(1rem,2.2vw,1.25rem);font-weight:300;
  color:rgba(255,255,255,.85);
  letter-spacing:-.01em;line-height:1.4;
  margin-top:1.5rem;
  text-align:center;
  margin-left:0;width:100%;
}

/* Streamlit button — overlays the .lbtn-ghost spot on desktop (same row
   as the logo/ECG line); drops below the tagline, centered, on mobile */
.element-container:has(div[data-testid="stButton"]){
  position:absolute;top:calc(50% - 4.2rem);right:calc(50% - 22.19rem);
  width:auto!important;max-width:none!important;
}
@media(min-width:1024px){.element-container:has(div[data-testid="stButton"]){right:calc(50% - 24.79rem)}}
@media(min-width:1440px){.element-container:has(div[data-testid="stButton"]){right:calc(50% - 33.13rem)}}
@media(max-width:768px){
  .element-container:has(div[data-testid="stButton"]){
    position:static;padding:1.5rem 1.5rem 2.5rem;
    display:flex;justify-content:center;
    width:100%!important;max-width:100%!important;
  }
}
div[data-testid="stButton"]{width:auto!important;max-width:none!important;display:block}
@media(max-width:768px){
  div[data-testid="stButton"]{width:100%!important;max-width:100%!important;display:flex;justify-content:center}
}
div[data-testid="stButton"] button{
  background:transparent!important;color:#fff!important;
  border:1px solid rgba(255,255,255,.55)!important;
  border-radius:999px!important;padding:.85rem 2.4rem!important;
  font-family:'Inter',sans-serif!important;
  font-size:clamp(.95rem,1.6vw,1.15rem)!important;font-weight:700!important;
  white-space:nowrap!important;letter-spacing:.02em!important;
  animation:hb 2s ease-in-out infinite!important;
  transition:background .25s,color .25s,border-color .25s!important;
}
div[data-testid="stButton"] button:hover{
  background:#fff!important;color:#0B2545!important;
  border-color:#fff!important;animation:none!important;
}
@media(max-width:768px){
  div[data-testid="stButton"] button{font-size:1rem!important;padding:.5rem 1.5rem!important}
}
</style>
<div class="land">
  <div class="lhero">
    <div class="lrow">
      <div class="llogo">
        <div class="lname">Pulse <span class="ldot"></span></div>
      </div>
      <div class="lecg">
        <svg viewBox="0 0 400 44" fill="none" preserveAspectRatio="none">
          <line x1="0" y1="22" x2="185" y2="22" stroke="rgba(255,255,255,.22)" stroke-width="1.5"/>
          <polyline points="185,22 215,22 232,3 242,41 250,9 258,36 266,22 280,22"
            stroke="#00C2A8" stroke-width="2" fill="none"
            stroke-linecap="round" stroke-linejoin="round"/>
          <line x1="280" y1="22" x2="400" y2="22" stroke="rgba(255,255,255,.22)" stroke-width="1.5"/>
        </svg>
      </div>
      <div class="lbtn-ghost">Get Started</div>
    </div>
    <div class="ltag">Health AI Policy Tracker<br>In Your Pocket.</div>
  </div>
</div>
""", unsafe_allow_html=True)

    if st.button("Get Started"):
        st.session_state.started = True
        st.rerun()


# ════════════════════════════════════════════════════
# MAIN APP
# ════════════════════════════════════════════════════
else:
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300..800;1,300..800&family=Michroma&display=swap');
*{box-sizing:border-box}
html,body,.stApp{margin:0;padding:0;background:#F0F4F9!important;overflow-x:hidden}
[class*="css"]{font-family:'Inter',sans-serif}
#MainMenu,footer,header{visibility:hidden}
.block-container{padding:0!important;max-width:100%!important}
.main .block-container{padding: 0!important}
section[data-testid="stSidebar"]{display:none}

:root{
  --navy:#0B2545; --sky:#1B6CA8; --teal:#00C2A8;
  --bg:#F0F4F9; --soft:#DDE8F2; --border:#C5D6E8;
  --muted:#4E6A84; --white:#FFFFFF;

  /* DOMAIN PALETTE — design tokens for policy-domain color coding.
     Mint/teal + champagne families layered over the core navy/sky tones,
     reserved for tagging the 9 policy domains across cards, tables and digest. */
  --dom-teal:#00C2A8; --dom-mint:#5FD9C4; --dom-forest:#0E8C77;
  --dom-sky:#1B6CA8; --dom-slate:#7C96B5; --dom-navy:#0B2545;
  --dom-champagne:#CBA876; --dom-bronze:#9C7B53; --dom-grey:#A9B8C9;

  /* RELEVANCE SCALE — light-to-dark mint gradient for the 1-5 relevance
     score tiers, all read with --navy text for a consistent look. */
  --rel-1:#EFFBF8; --rel-2:#DAF6EF; --rel-3:#AFE9DB; --rel-4:#7EDDC7; --rel-5:#4BC8AB;
}

/* NAV — fixed to top of viewport so it stays visible while content scrolls */
.nav{background:var(--navy);
  position:fixed;top:0;left:0;z-index:201;width:100%}
.navi{max-width:1160px;margin:0 auto;padding:1rem 3rem;
  display:flex;align-items:center;gap:.8rem}
@media(max-width:480px){.navi{padding:.75rem 1.25rem;gap:.5rem}}
.nlogo{font-family:'Michroma',sans-serif;font-size:2.24rem;
  color:#fff;letter-spacing:0;line-height:1}
.ndot{width:8px;height:8px;background:var(--teal);border-radius:50%;flex-shrink:0;
  align-self:center;position:relative;top:.2rem}
.ndiv{width:1px;height:18px;background:rgba(255,255,255,.2);flex-shrink:0;
  align-self:center;position:relative;top:.2rem}
.ntag{font-size:.9rem;color:rgba(255,255,255,.65);align-self:center;position:relative;top:.2rem}

/* TABS — fixed below .nav, align with .navi's left edge and widen tab spacing.
   [data-baseweb="tab-panel"] gets matching padding-top to reserve the space
   that .nav + the tab-list used to occupy in normal flow. */
[data-baseweb="tab-list"]{
  position:fixed;top:67.84375px;left:0;right:0;z-index:200;
  background:var(--navy);width:100%;
  padding:0 max(3rem, calc((100% - 1160px) / 2 + 3rem)) 2px;
  gap:2.25rem;
}
[data-baseweb="tab-list"] [data-baseweb="tab"]{font-size:1.8375rem;color:rgba(255,255,255,.65)}
[data-baseweb="tab-list"] [data-baseweb="tab"] p{color:inherit}
[data-baseweb="tab-list"] [data-baseweb="tab"][aria-selected="true"]{color:var(--teal)}
[data-baseweb="tab-highlight"]{background-color:var(--teal)!important}
[data-baseweb="tab-border"]{background-color:rgba(255,255,255,.08)!important}
[data-baseweb="tab-panel"]{padding-top:109.84375px}
@media(max-width:480px){
  [data-baseweb="tab-list"]{top:59.84375px;padding:0 1.25rem 2px}
  [data-baseweb="tab-list"] [data-baseweb="tab"]{font-size:1.225rem}
  [data-baseweb="tab-panel"]{padding-top:101.84375px}
}

/* FOOTER */
.ft{background:var(--navy);padding:2rem 3rem;
  display:flex;align-items:center;justify-content:space-between;margin-top:4rem}
div:has(.ssm) + div .ft{margin-top:0}
@media(max-width:480px){.ft{padding:1.5rem 1.25rem;flex-direction:column;gap:1rem;align-items:flex-start}}
@media(max-width:480px){.ft > div:first-child{font-size:.5rem!important;white-space:nowrap}}

/* HERO */
.hero{padding:3.5rem 3rem 4rem;max-width:1160px;margin:0 auto;position:relative}
.hey{font-family:'Inter',sans-serif;font-size:0.9rem;font-weight:700;
  letter-spacing:.14em;text-transform:uppercase;color:var(--teal);margin-bottom:1.2rem}
.hh{font-family:'Inter',sans-serif;font-weight:800;
  font-size:clamp(2.4rem,4.5vw,4rem);line-height:1.04;
  color:var(--navy);letter-spacing:-.03em;margin-bottom:1.84rem}
.hh em{font-style:italic;color:var(--navy);font-weight:300}
.hb{font-size:1.05rem;color:var(--navy);line-height:1.75;max-width:600px;margin-bottom:1.84rem}
.hba{font-size:1.05rem;color:var(--navy);line-height:1.75;max-width:600px}
.hba span{color:var(--teal);font-weight:600}
@media(max-width:768px){
  .hero{padding:1.55rem 2rem 2.67rem}
  .hey{font-weight:800}
  .hh{font-size:2.8rem;line-height:1.3}
  .hh em{font-weight:500;font-size:2rem}
}

/* HERO MOSAIC — decorative mint/navy/champagne blob cluster filling
   the empty space beside the hero copy on wide viewports only.
   Organic border-radius "blob" shapes morph and drift for a flowy,
   abstract feel, with overlapping circles for depth. */
.hmos{position:absolute;right:1rem;top:50%;transform:translateY(-50%);
  width:330px;height:330px;display:none;pointer-events:none}
@media(min-width:1200px){.hmos{display:block}}
.hmos span{position:absolute;mix-blend-mode:multiply}
.hmos .c1{width:220px;height:220px;top:-10px;right:10px;opacity:.5;
  background:radial-gradient(circle at 50% 50%,transparent 32%,var(--teal) 100%);
  border-radius:62% 38% 55% 45%/55% 45% 60% 40%;
  animation:flow-a 16s ease-in-out infinite, morph-a 22s ease-in-out infinite}
.hmos .c2{width:170px;height:170px;bottom:0;right:140px;opacity:.55;
  background:radial-gradient(circle at 50% 50%,transparent 32%,var(--navy) 100%);
  border-radius:42% 58% 68% 32%/45% 60% 40% 55%;
  animation:flow-b 18s ease-in-out infinite, morph-b 24s ease-in-out infinite}
.hmos .c3{width:120px;height:120px;bottom:-10px;right:-10px;opacity:.5;
  background:radial-gradient(circle at 50% 50%,transparent 32%,var(--dom-mint) 100%);
  border-radius:55% 45% 40% 60%/60% 50% 50% 40%;
  animation:flow-c 13s ease-in-out infinite, morph-c 19s ease-in-out infinite}
.hmos .c4{width:58px;height:58px;border:2px solid var(--sky);background:transparent;
  border-radius:50%;top:122px;right:0;opacity:.7;animation:flow-d 11s ease-in-out infinite}
.hmos .c5{width:46px;height:46px;top:30px;right:200px;opacity:.55;
  background:radial-gradient(circle at 50% 50%,transparent 32%,var(--dom-champagne) 100%);
  border-radius:50%;animation:flow-c 12s ease-in-out infinite reverse}
@keyframes flow-a{
  0%{transform:translate(0,0)}25%{transform:translate(-22px,16px)}
  50%{transform:translate(-10px,32px)}75%{transform:translate(14px,10px)}
  100%{transform:translate(0,0)}
}
@keyframes flow-b{
  0%{transform:translate(0,0)}25%{transform:translate(18px,-14px)}
  50%{transform:translate(28px,4px)}75%{transform:translate(6px,-20px)}
  100%{transform:translate(0,0)}
}
@keyframes flow-c{
  0%{transform:translate(0,0)}33%{transform:translate(14px,-18px)}
  66%{transform:translate(-12px,-8px)}100%{transform:translate(0,0)}
}
@keyframes flow-d{0%,100%{transform:translate(0,0)}50%{transform:translate(-16px,18px)}}
@keyframes morph-a{0%,100%{border-radius:62% 38% 55% 45%/55% 45% 60% 40%}50%{border-radius:48% 52% 42% 58%/50% 60% 42% 55%}}
@keyframes morph-b{0%,100%{border-radius:42% 58% 68% 32%/45% 60% 40% 55%}50%{border-radius:58% 42% 50% 50%/55% 45% 55% 45%}}
@keyframes morph-c{0%,100%{border-radius:55% 45% 40% 60%/60% 50% 50% 40%}50%{border-radius:40% 60% 55% 45%/45% 55% 60% 40%}}

/* STATS */
.ss{background:var(--navy)}
.si{max-width:1200px;margin:0 auto;display:grid;
  grid-template-columns:repeat(4,1fr);padding:0 3rem}
@media(max-width:768px){.si{grid-template-columns:repeat(2,1fr);padding:0 1.5rem}}
.sc{padding:2.8rem 2rem;border-right:1px solid rgba(255,255,255,.1)}
.sc:first-child{padding-left:0}.sc:last-child{border-right:none}
@media(max-width:768px){
  .sc{padding:2rem 1.2rem}
  .sc:nth-child(2n){border-right:none}
  .sc:nth-child(-n+2){border-bottom:1px solid rgba(255,255,255,.1)}
}
.sn{font-family:'Michroma',sans-serif;font-size:2.6rem;color:#fff;line-height:1;margin-bottom:.4rem;display:flex;align-items:baseline;gap:.3rem}
.sp{color:var(--teal);font-family:'Inter',sans-serif;font-weight:800;font-size:1.8rem}
.sl2{font-family:'Inter',sans-serif;font-size:.78rem;font-weight:700;
  color:rgba(255,255,255,.85);text-transform:uppercase;letter-spacing:.04em;margin-bottom:.25rem}
.sb{font-size:.82rem;color:var(--teal);font-weight:500}

/* DIVIDER */
.div{border:none;border-top:1px solid var(--border);margin:0}

/* HOME SECTIONS */
.hs{padding:5rem 3rem;max-width:1160px;margin:0 auto}
.hsw{padding:5rem 0;background:#fff}
.hswi{max-width:1160px;margin:0 auto;padding:0 3rem}
@media(max-width:768px){.hs{padding:3rem 1.5rem}.hsw{padding:3rem 0}.hswi{padding:0 1.5rem}}
@media(max-width:480px){.hs{padding:2rem 1rem}.hsw{padding:2rem 0}.hswi{padding:0 1rem}}
.hs-src{padding-bottom:.725rem}
.sey{font-family:'Inter',sans-serif;font-size:.7rem;font-weight:700;
  letter-spacing:.14em;text-transform:uppercase;color:var(--teal);margin-bottom:.5rem}
.st{font-family:'Inter',sans-serif;
  font-size:clamp(1.6rem,3vw,2.2rem);font-weight:800;
  color:var(--navy);letter-spacing:-.02em;line-height:1.15;margin-bottom:2rem}

/* TAB CONTENT WRAPPER — applied to the Guide/Tracker/Digest tab panels
   (Home contains .hero and self-centers via .hero/.hs/.hsw etc, so it's excluded) */
[data-baseweb="tab-panel"]:not(:has(.hero)) > div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"]{
  max-width:1160px;margin:0 auto;padding:2.5rem 3rem 0}
@media(max-width:768px){
  [data-baseweb="tab-panel"]:not(:has(.hero)) > div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"]{padding:1.5rem 1.5rem 0}
}
@media(max-width:480px){
  [data-baseweb="tab-panel"]:not(:has(.hero)) > div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"]{padding:1.25rem 1rem 0}
}
/* FOOTER full-bleed on Guide/Tracker/Digest, breaking out of the centered tabwrap */
[data-baseweb="tab-panel"]:not(:has(.hero)) .ft{
  width:100vw;margin-left:calc(50% - 50vw);margin-right:calc(50% - 50vw)
}
/* Streamlit sets inline pixel widths on element-containers based on the
   pre-constraint viewport; force them back to the new narrower parent */
[data-baseweb="tab-panel"]:not(:has(.hero)) [data-testid="stVerticalBlock"] .element-container,
[data-baseweb="tab-panel"]:not(:has(.hero)) [data-testid="stVerticalBlock"] .stMarkdown,
[data-baseweb="tab-panel"]:not(:has(.hero)) [data-testid="stVerticalBlock"] [data-testid="stMarkdownContainer"]{
  width:100%!important;max-width:100%!important;
}

/* USER GUIDE PAGE TITLE/SUBTITLE */
.gpt{font-family:'Inter',sans-serif;font-size:2.2rem;font-weight:800;
  color:var(--navy);letter-spacing:-.02em;margin-bottom:.7rem}
.gps{font-size:.98rem;color:var(--muted);line-height:1.75;margin-bottom:2.5rem;max-width:none}

/* WHO */
.wg{display:grid;grid-template-columns:repeat(3,1fr);gap:1.4rem}
@media(max-width:1024px){.wg{grid-template-columns:repeat(2,1fr)}}
@media(max-width:480px){.wg{grid-template-columns:1fr}}
.wc{background:var(--bg);border:1px solid var(--border);border-radius:14px;
  padding:2rem 2.2rem;transition:all .2s;cursor:default}
.wc:hover{border-color:var(--sky);box-shadow:0 10px 30px rgba(11,37,69,.09);transform:translateY(-3px)}
.wi{color:var(--navy);margin-bottom:1rem}
.wi svg{width:28px;height:28px;display:block}
.wt{font-size:1.05rem;font-weight:700;color:var(--navy);margin-bottom:.5rem}
.wb{font-size:.9rem;color:var(--muted);line-height:1.7}

/* HOW */
.hg{display:grid;grid-template-columns:repeat(4,1fr);
  border:1px solid var(--border);border-radius:14px;overflow:hidden}
@media(max-width:768px){.hg{grid-template-columns:repeat(2,1fr)}}
.hp{padding:2.2rem;border-right:1px solid var(--border);background:#fff;transition:background .2s}
.hp:last-child{border-right:none}
.hp:hover{background:var(--bg)}
@media(max-width:768px){
  .hp:nth-child(2n){border-right:none}
  .hp:nth-child(-n+2){border-bottom:1px solid var(--border)}
}
.hn{font-family:'Inter',sans-serif;font-size:1.6rem;font-weight:800;
  color:var(--border);margin-bottom:.8rem}
.ht{font-size:1rem;font-weight:700;color:var(--navy);margin-bottom:.4rem}
.hbd{font-size:.88rem;color:var(--muted);line-height:1.65}

/* SOURCES MARQUEE */
.ssm{background:var(--navy);overflow:hidden;width:100%;padding:2.6rem 0}
.ssm-track{display:flex;gap:.6rem;width:max-content;
  animation:ssm-scroll 50s linear infinite}
.ssm:hover .ssm-track{animation-play-state:paused}
.ssm-chip{font-family:'Inter',sans-serif;font-size:.8rem;font-weight:600;letter-spacing:.06em;
  text-transform:uppercase;background:transparent;border:1px solid rgba(0,194,168,.35);
  border-radius:5px;padding:.5rem 1.1rem;color:var(--teal);
  white-space:nowrap;flex-shrink:0}
@keyframes ssm-scroll{from{transform:translateX(0)}to{transform:translateX(-50%)}}

/* GUIDE */
.gh{font-family:'Inter',sans-serif;font-size:1.6rem;font-weight:800;
  color:var(--navy);margin:4.5rem 0 .9rem;padding-top:3.5rem;border-top:2px solid var(--border)}
.gh:first-of-type{border-top:none;padding-top:0;margin-top:0}
.gl{font-size:.98rem;color:var(--muted);line-height:1.75;margin-bottom:1.5rem}

/* SOURCES SUMMARY BOX — succinct "where this comes from" callout */
.srcbox{background:var(--navy);border-radius:14px;padding:2.2rem 2.5rem;margin-bottom:2.5rem}
.srcbox-eyebrow{font-family:'Inter',sans-serif;font-size:1.6rem;font-weight:800;
  color:#fff;letter-spacing:-.02em;margin-bottom:.7rem}
.srcbox-text{font-size:.98rem;color:rgba(255,255,255,.7);line-height:1.75;max-width:none}
.srcbox-text strong{color:#fff}
@media(max-width:768px){.srcbox{padding:1.5rem 1.5rem}}
.gtb{width:100%;border-collapse:collapse;font-size:.9rem;
  border:1px solid var(--border);border-radius:10px;overflow:hidden;margin-bottom:2rem}
.gtb th{font-family:'Inter',sans-serif;font-size:.63rem;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted);background:var(--soft);
  text-align:left;padding:.85rem 1.2rem;border-bottom:1px solid var(--border)}
.gtb td{padding:.9rem 1.2rem;border-bottom:1px solid var(--border);
  color:#2d4255;vertical-align:top;line-height:1.6}
.gtb tr:last-child td{border-bottom:none}
.gtb td:first-child{font-family:'Inter',sans-serif;font-size:.73rem;
  color:var(--navy);white-space:nowrap;font-weight:600}
.gtb tr:hover td{background:var(--soft)}
.dsw{display:inline-block;width:10px;height:10px;border-radius:2px;
  margin-right:8px;vertical-align:middle}
.cdg{border:2px solid var(--border);border-top:4px solid var(--sky);
  border-radius:12px;padding:2rem 2.2rem;background:#fff;margin-bottom:2rem}
@media(max-width:480px){.cdg{padding:1.5rem 1.4rem}}
.dr{display:flex;align-items:flex-start;gap:1rem;margin-bottom:1.3rem}
.dr:last-child{margin-bottom:0}
.dn{width:30px;height:30px;border-radius:50%;background:var(--navy);color:#fff;
  font-family:'Inter',sans-serif;font-size:.72rem;font-weight:700;
  display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:2px}
.dlb{font-weight:700;color:var(--navy);font-size:.92rem;margin-bottom:.2rem}
.dds{font-size:.87rem;color:var(--muted);line-height:1.55}
.rg{display:grid;grid-template-columns:50px 1fr;
  border:1px solid var(--border);border-radius:10px;overflow:hidden;margin-bottom:2rem}
.rs{font-family:'Inter',sans-serif;font-weight:700;color:var(--navy);font-size:1rem;
  padding:1rem;border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:center}
.rs-1{background:var(--rel-1)}
.rs-2{background:var(--rel-2)}
.rs-3{background:var(--rel-3)}
.rs-4{background:var(--rel-4)}
.rs-5{background:var(--rel-5)}
.rd{padding:1rem 1.2rem;font-size:.9rem;color:#2d4255;
  border-bottom:1px solid var(--border);line-height:1.6}
.rs:last-of-type,.rd:last-of-type{border-bottom:none}

/* TRACKER */
.fb-marker{display:none}
div[data-testid="stVerticalBlock"]:has(> div.element-container > div.stMarkdown .fb-marker){
  background:#fff;border:1px solid var(--border);border-radius:14px;
  padding:1.6rem 2rem;margin-bottom:2rem}
@media(max-width:768px){
  div[data-testid="stVerticalBlock"]:has(> div.element-container > div.stMarkdown .fb-marker){padding:1.2rem 1.25rem}
}
.frl{font-family:'Inter',sans-serif;font-size:.63rem;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted);margin-bottom:.5rem}
.sr{display:flex;gap:.6rem;margin-bottom:1.5rem;flex-wrap:wrap}
.sp2{background:#fff;border:1px solid var(--border);border-radius:999px;
  padding:.3rem 1rem;font-size:.78rem;color:var(--muted);font-family:'Inter',sans-serif;font-weight:500}
.sp2 strong{color:var(--navy)}
@media(max-width:480px){
  div[role="radiogroup"]{flex-direction:column!important;align-items:flex-start!important;gap:.5rem!important}
}
.dc{background:#fff;border:1px solid var(--border);border-radius:14px;
  overflow:hidden;margin-bottom:1.2rem;transition:box-shadow .2s,transform .15s}
.dc:hover{box-shadow:0 8px 32px rgba(11,37,69,.1);transform:translateY(-2px)}
.dct{height:5px;width:100%}
.dc-clinical_care{background:var(--dom-teal)}.dc-payor_utilization{background:var(--dom-champagne)}
.dc-transparency_consent{background:var(--dom-sky)}.dc-chatbot_mental_health{background:var(--dom-mint)}
.dc-liability{background:var(--dom-bronze)}.dc-regulatory_sandbox{background:var(--dom-forest)}
.dc-data_privacy_hipaa{background:var(--dom-slate)}.dc-federal_framework{background:var(--dom-navy)}
.dc-general_health_ai{background:var(--dom-grey)}
.dcb{padding:1.6rem 1.8rem}
@media(max-width:480px){.dcb{padding:1.2rem 1.3rem}}

/* DOWNLOAD BUTTON ICON — minimalistic line icon (matches .wi svg style)
   replacing the emoji glyph in st.download_button labels */
[data-testid="stDownloadButton"] button{display:inline-flex;align-items:center;gap:.5rem}
[data-testid="stDownloadButton"] button::before{
  content:'';display:inline-block;flex-shrink:0;width:1em;height:1em;
  background-color:currentColor;
  mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/%3E%3Cpolyline points='7 10 12 15 17 10'/%3E%3Cline x1='12' y1='15' x2='12' y2='3'/%3E%3C/svg%3E") no-repeat center/contain;
  -webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/%3E%3Cpolyline points='7 10 12 15 17 10'/%3E%3Cline x1='12' y1='15' x2='12' y2='3'/%3E%3C/svg%3E") no-repeat center/contain;
}
.cm{font-family:'Inter',sans-serif;font-size:.68rem;font-weight:500;color:#8aa4bd;
  letter-spacing:.04em;text-transform:uppercase;margin-bottom:.55rem}
.ct{font-family:'Inter',sans-serif;font-size:1.1rem;font-weight:700;
  color:var(--navy);margin-bottom:.65rem;line-height:1.3}
.cs{font-size:.93rem;color:#3d5166;line-height:1.74;margin-bottom:1rem}
.cf{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;
  padding-top:.9rem;border-top:1px solid var(--border)}
.tag{font-family:'Inter',sans-serif;font-size:.63rem;padding:.22rem .65rem;
  border-radius:5px;letter-spacing:.04em;text-transform:uppercase;font-weight:600}
.tg{background:var(--soft);color:#4e6a84;border:1px solid var(--border)}
.tag-act{background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe}
.tag-law{background:#f0fdf4;color:#15803d;border:1px solid #bbf7d0}
.tag-amc{background:#f0fdfa;color:#0f766e;border:1px solid #99f6e4}
@keyframes amc-beat{
  0%  {box-shadow:0 0 0 0 rgba(0,194,168,.55)}
  30% {box-shadow:0 0 0 8px rgba(0,194,168,.18)}
  50% {box-shadow:0 0 0 4px rgba(0,194,168,.09)}
  65% {box-shadow:0 0 0 11px rgba(0,194,168,.1)}
  100%{box-shadow:0 0 0 0 rgba(0,194,168,0)}
}
.tag-amc-5{animation:amc-beat 2s ease-in-out infinite}
.rb{display:flex;align-items:center;margin-left:auto}
.sl{font-family:'Inter',sans-serif;font-size:.8rem;color:var(--sky);
  text-decoration:none;font-weight:600;margin-left:1rem}
.sl:hover{color:var(--navy)}
@media(max-width:768px){
  .rb{margin-left:0}
  .sl{margin-left:auto}
}
.es{text-align:center;padding:6rem 2rem;color:#94a3b8;font-size:1.1rem}

/* DIGEST */
.dh{background:var(--navy);border-radius:14px;padding:3rem 3.5rem;margin-bottom:3rem}
@media(max-width:768px){.dh{padding:2rem 1.5rem}}
.dhe{font-family:'Inter',sans-serif;font-size:1.16rem;font-weight:400;letter-spacing:.14em;
  text-transform:uppercase;color:var(--teal);margin-bottom:.7rem}
@media(max-width:768px){
  .dhe-sep{display:none}
  .dhe-month{display:block}
}
.dht{font-family:'Inter',sans-serif;font-size:1.9rem;font-weight:800;
  color:#fff;margin-bottom:.9rem;letter-spacing:-.02em;line-height:1.2;max-width:none}
.dhb{font-size:.98rem;color:rgba(255,255,255,.6);line-height:1.72;max-width:none}
.dds2{margin-bottom:3.5rem}
.ddh{display:flex;align-items:center;gap:.8rem;padding:1.1rem 1.6rem;
  background:var(--soft);border:1px solid var(--border);border-bottom:none;
  border-radius:10px 10px 0 0}
.ddd{width:11px;height:11px;border-radius:50%;flex-shrink:0;
  border:1px solid rgba(11,37,69,.08)}
.ddd-clinical_care{background:var(--dom-teal)}
.ddd-payor_utilization{background:var(--dom-champagne)}
.ddd-transparency_consent{background:var(--dom-sky)}
.ddd-chatbot_mental_health{background:var(--dom-mint)}
.ddd-liability{background:var(--dom-bronze)}
.ddd-regulatory_sandbox{background:var(--dom-forest)}
.ddd-data_privacy_hipaa{background:var(--dom-slate)}
.ddd-federal_framework{background:var(--dom-navy)}
.ddd-general_health_ai{background:var(--dom-grey)}
.ddn{font-family:'Inter',sans-serif;font-size:1.05rem;font-weight:700;color:var(--navy)}
.ddcw{border:1px solid var(--border);border-top:none;border-radius:0 0 10px 10px;overflow:hidden}
.ddc{background:#fff;padding:1.6rem 1.8rem;border-bottom:1px solid var(--border);transition:background .15s}
.ddc:last-child{border-bottom:none}
.ddc:hover{background:var(--soft)}
.ddct{font-family:'Inter',sans-serif;font-weight:700;color:var(--navy);
  font-size:1.1rem;margin-bottom:.5rem;line-height:1.35}
.ddcs{font-size:.93rem;color:#3d5166;line-height:1.72;margin-bottom:.65rem}
.ddcl{font-family:'Inter',sans-serif;font-size:.8rem;color:var(--sky);
  text-decoration:none;font-weight:600}
.subbox{background:var(--navy);padding:3.5rem;border-radius:14px;margin-top:2.5rem;margin-bottom:1.8rem}
.subt{font-family:'Inter',sans-serif;font-size:1.6rem;font-weight:800;
  color:#fff;margin-bottom:.5rem}
.subb{font-size:1.05rem;color:rgba(255,255,255,.55);line-height:1.72;margin-bottom:.8rem}
.subd{font-family:'Inter',sans-serif;font-size:.87rem;font-weight:500;letter-spacing:.06em;
  color:var(--teal);text-transform:uppercase}
@media(max-width:768px){.subbox{padding:2rem 1.5rem}.subb{font-size:.98rem}.subd{font-size:.8rem}}
button[kind="primary"],button[kind="primaryFormSubmit"]{color:var(--navy)!important}
</style>""", unsafe_allow_html=True)

    # NAV
    st.markdown("""<div class="nav"><div class="navi">
      <span class="nlogo">Pulse</span>
      <span class="ndot"></span>
      <span class="ndiv"></span>
      <span class="ntag">Health AI Policy Tracker</span>
    </div></div>""", unsafe_allow_html=True)

    tab_home, tab_guide, tab_tracker, tab_digest = st.tabs(
        ["Home", "User Guide", "Tracker", "Monthly Digest"])

    # ── HOME ──────────────────────────────────
    with tab_home:
        st.markdown(f"""
        <div class="hero">
          <div class="hey">Health AI Policy Intelligence</div>
          <div class="hh">The policy is moving.<br><em>Are you keeping up?</em></div>
          <div class="hb">43 states introduced over 240 health AI bills in 2026 alone. Federal agencies — FDA, CMS, ONC, HHS — are issuing guidance, withdrawing rules, and launching programs at a pace no individual can manually track.</div>
          <div class="hba">Pulse monitors the full landscape of health AI governance and delivers it <span>summarized, tagged, and ready to act on.</span></div>
          <div class="hmos" aria-hidden="true">
            <span class="c1"></span><span class="c2"></span><span class="c3"></span><span class="c4"></span><span class="c5"></span>
          </div>
        </div>
        <div class="ss"><div class="si">
          <div class="sc"><div class="sn">{N}<span class="sp">+</span></div><div class="sl2">Tracked Developments</div><div class="sb">Growing Daily</div></div>
          <div class="sc"><div class="sn">{EN}</div><div class="sl2">Laws Enacted 2025–26</div><div class="sb">With Compliance Obligations</div></div>
          <div class="sc"><div class="sn">43</div><div class="sl2">States with Active Bills</div><div class="sb">Only WY and ND Inactive</div></div>
          <div class="sc"><div class="sn">13</div><div class="sl2">Sources Live Monitored</div><div class="sb">Federal + State + Industry</div></div>
        </div></div>
        <hr class="div">
        <div class="hs">
          <div class="st">Built for everyone working in Health AI</div>
          <div class="wg">
            <div class="wc"><div class="wi"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg></div><div class="wt">Builders & Developers</div><div class="wb">Check whether the product you're building triggers state disclosure laws, prior auth rules, or FDA device regulation — before you ship.</div></div>
            <div class="wc"><div class="wi"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="3" width="16" height="18" rx="1"/><path d="M12 8v6"/><path d="M9 11h6"/><path d="M9 21v-4h6v4"/></svg></div><div class="wt">Health Systems & HDOs</div><div class="wb">Understand which new laws require compliance action now, which are still proposals, and what clinical AI governance obligations are emerging in your states.</div></div>
            <div class="wc"><div class="wi"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="16" y2="17"/></svg></div><div class="wt">Policy & Strategy Teams</div><div class="wb">Brief leadership on the state of play in minutes. Every development summarized for a CMO/GC audience — no law degree or Federal Register subscription required.</div></div>
          </div>
        </div>
        <hr class="div">
        <div class="hsw"><div class="hswi">
          <div class="st">Four steps, zero noise</div>
          <div class="hg">
            <div class="hp"><div class="hn">01</div><div class="ht">Scrape</div><div class="hbd">Automated pipeline checks FDA, CMS, ONC, state legislatures, and policy bodies daily.</div></div>
            <div class="hp"><div class="hn">02</div><div class="ht">Summarize</div><div class="hbd">Each development gets a 2–3 sentence summary naming the agency, rule, effective date, and required action.</div></div>
            <div class="hp"><div class="hn">03</div><div class="ht">Tag</div><div class="hbd">Domain, action type, and relevance scores 1–5 for health systems, payers, and digital health vendors.</div></div>
            <div class="hp"><div class="hn">04</div><div class="ht">Deliver</div><div class="hbd">Browse the tracker, filter by stakeholder type, or subscribe to the monthly digest on the 15th.</div></div>
          </div>
        </div></div>
        <hr class="div">
        <div class="hs hs-src">
          <div class="st">Sources Monitored</div>
        </div>
        <div class="ssm"><div class="ssm-track">
          {''.join(f'<span class="ssm-chip">{s}</span>' for s in SOURCES)}{''.join(f'<span class="ssm-chip">{s}</span>' for s in SOURCES)}
        </div></div>
        """, unsafe_allow_html=True)
        footer(light=True)

    # ── USER GUIDE ────────────────────────────
    with tab_guide:
        st.markdown("""<div class="gpt">How to read Pulse</div>
        <div class="gps">Each entry represents a discrete health AI policy development — a law enacted, a rule proposed, guidance issued, or a program launched. Summarized in plain language and tagged so you can filter to what's relevant.</div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="srcbox"><div class="srcbox-eyebrow">Where this comes from</div><div class="srcbox-text">Pulse monitors <strong>13 sources across three tiers</strong> — federal agencies (FDA, CMS, ONC, HHS), state legislatures (CA, CO, NCSL), and policy &amp; industry trackers (Manatt, AHA, NIST, STAT) — checked daily and summarized by AI.</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="gh">Reading a card</div><div class="gl">Every development appears as a card. Each numbered element is explained below.</div>', unsafe_allow_html=True)
        st.markdown("""<div class="cdg">
          <div class="dr"><div class="dn">1</div><div><div class="dlb">Colored top bar</div><div class="dds">Domain color — scan by policy area at a glance.</div></div></div>
          <div class="dr"><div class="dn">2</div><div><div class="dlb">Source · Date</div><div class="dds">Originating agency or legislature and publication date.</div></div></div>
          <div class="dr"><div class="dn">3</div><div><div class="dlb">Title</div><div class="dds">What happened in plain language. Includes bill number or rule name.</div></div></div>
          <div class="dr"><div class="dn">4</div><div><div class="dlb">Summary</div><div class="dds">2–3 sentences for a CMO/GC audience. Names the agency, rule, effective date, and required action. Flags whether a bill is enacted or still introduced.</div></div></div>
          <div class="dr"><div class="dn">5</div><div><div class="dlb">Domain tag · Action tag</div><div class="dds">Policy domain and type of action. Green = enacted law requiring compliance attention now.</div></div></div>
          <div class="dr"><div class="dn">6</div><div><div class="dlb">AMC score · View source →</div><div class="dds">Relevance 1–5 for Academic Medical Centers. Links to the original document.</div></div></div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="gh">Policy domains</div><div class="gl">Use the Domain filter in the Tracker to narrow to the area most relevant to your work.</div>', unsafe_allow_html=True)
        dr = "".join(f'<tr><td><span class="dsw" style="background:{DC.get(k,"#ccc")}"></span>{v}</td><td>{d}</td></tr>' for k,v,d in [
            ("clinical_care","Clinical Care","AI in clinical decisions, patient consent, clinician oversight mandates."),
            ("payor_utilization","Payor / Utilization Mgmt","Prior authorization denials, claim downcoding by AI. Indiana enacted the first downcoding prohibition law in 2026."),
            ("transparency_consent","Transparency & Consent","Patient disclosure requirements, AI model cards, ONC transparency rules."),
            ("chatbot_mental_health","Chatbot / Mental Health","AI chatbot regulation, mental health crisis detection, minor protections."),
            ("liability","Liability","Developer and deployer liability standards, product liability, AI LEAD Act."),
            ("regulatory_sandbox","Regulatory Sandbox","State/federal sandbox programs, FDA TEMPO pilot, Utah OAIP agreements."),
            ("data_privacy_hipaa","Data Privacy / HIPAA","HIPAA enforcement, OCR actions, health data sharing rules."),
            ("federal_framework","Federal Framework","White House EOs, OMB memos, Congressional bills, federal preemption."),
            ("general_health_ai","General Health AI","Developments spanning multiple domains or with broad applicability.")])
        st.markdown(f'<table class="gtb"><thead><tr><th>Domain</th><th>What it covers</th></tr></thead><tbody>{dr}</tbody></table>', unsafe_allow_html=True)

        st.markdown('<div class="gh">Action types</div><div class="gl">Critical for knowing whether something requires immediate compliance attention or is still a proposal.</div>', unsafe_allow_html=True)
        ar = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k,v in [
            ("New Law ✦","Signed into law — green tag. Review effective date; compliance obligations may apply now."),
            ("Introduced Bill","Introduced but not yet passed. Watch, don't act yet."),
            ("Proposed Rule","NPRM — accepting public comment. Not yet final or binding."),
            ("Final Rule","Final and binding. Review compliance timeline."),
            ("Guidance Update","Not legally binding but signals enforcement intent."),
            ("RFI / Comment","Opportunity to submit public comment and shape the final rule."),
            ("Research Program","Federal initiative. Track for funding and emerging standards."),
            ("Executive Action","White House EO or OMB memo. Sets direction for HHS, FDA, CMS."),
            ("Enforcement","Investigation, settlement, or court action. Active regulatory attention.")])
        st.markdown(f'<table class="gtb"><thead><tr><th>Action type</th><th>What it means for you</th></tr></thead><tbody>{ar}</tbody></table>', unsafe_allow_html=True)

        st.markdown('<div class="gh">Relevance scores</div><div class="gl">Every development is scored 1–5 for Academic Medical Centers, Payers/Insurers, and Digital Health Vendors. Scores are assigned by an AI model (GPT-4.1) immediately after summarization, using the rubric below applied independently to each stakeholder type — so the same development can score differently for each (e.g. a payer utilization-management rule may score 5 for Payers but 2 for Digital Health Vendors). Higher tiers are highlighted to surface what needs attention first.</div>', unsafe_allow_html=True)
        rr = "".join(f'<div class="rs rs-{s}">{s}</div><div class="rd">{d}</div>' for s,d in [
            ("5","Direct compliance obligation or major strategic implication — act now."),
            ("4","Requires awareness and likely internal review."),
            ("3","Worth monitoring. May affect operations indirectly."),
            ("2","Peripheral relevance. Background awareness only."),
            ("1","Not relevant to this stakeholder type.")])
        st.markdown(f'<div class="rg">{rr}</div>', unsafe_allow_html=True)
        footer()

    # ── TRACKER ───────────────────────────────
    with tab_tracker:
        if df.empty:
            st.markdown('<div class="es">No developments found.</div>', unsafe_allow_html=True)
        else:
            with st.container():
                st.markdown('<div class="fb-marker"></div><div class="frl">Search & filter</div>', unsafe_allow_html=True)
                c1,c2,c3 = st.columns([3,2,2])
                with c1: search = st.text_input("Search", placeholder="e.g. Indiana, prior authorization, chatbot", label_visibility="collapsed")
                with c2:
                    doms = sorted(df["domain_tag"].dropna().unique())
                    do = ["All domains"]+[DL.get(d,d) for d in doms]
                    sdl = st.selectbox("Domain", do, label_visibility="collapsed")
                    sd = None if sdl=="All domains" else doms[do.index(sdl)-1]
                with c3:
                    acts = sorted(df["action_tag"].dropna().unique())
                    ao = ["All action types"]+[AL.get(a,a) for a in acts]
                    sal = st.selectbox("Action type", ao, label_visibility="collapsed")
                    sa = None if sal=="All action types" else acts[ao.index(sal)-1]
                st.markdown('<div class="frl" style="margin-top:.8rem">Refine</div>', unsafe_allow_html=True)
                c4,c5,c6 = st.columns([2,2,2])
                with c4:
                    so = ["All sources"]+sorted(df["source_name"].dropna().unique())
                    ss = st.selectbox("Source", so, label_visibility="collapsed")
                with c5: df2 = st.selectbox("Date range", ["All time","Last 30 days","Last 90 days","Last 7 days"], label_visibility="collapsed")
                with c6: ma = st.slider("Min AMC", 1, 5, 1, label_visibility="collapsed")
                st.markdown('<div class="frl" style="margin-top:.8rem">Sort relevance for</div>', unsafe_allow_html=True)
                sk = st.radio("Stakeholder", ["Academic Medical Center","Payer / Insurer","Digital Health Vendor"], horizontal=True, label_visibility="collapsed")

            rc = {"Academic Medical Center":"relevance_amc","Payer / Insurer":"relevance_payer","Digital Health Vendor":"relevance_dh"}[sk]
            f = df.copy()
            if search:
                m = f["title"].str.contains(search,case=False,na=False)|f["summary"].str.contains(search,case=False,na=False)|f["source_name"].str.contains(search,case=False,na=False)
                f = f[m]
            if sd: f = f[f["domain_tag"]==sd]
            if sa: f = f[f["action_tag"]==sa]
            if ss!="All sources": f = f[f["source_name"]==ss]
            f = f[f["relevance_amc"].fillna(0)>=ma]
            if df2!="All time":
                days = {"Last 7 days":7,"Last 30 days":30,"Last 90 days":90}[df2]
                co = (datetime.now()-timedelta(days=days)).strftime("%Y-%m-%d")
                f = f[f["date_published"].fillna(f["date_scraped"])>=co]
            f = f.sort_values(rc,ascending=False,na_position="last")
            hr2 = len(f[f[rc].fillna(0)>=4])
            en2 = len(f[f["action_tag"]=="new_law"])
            st.markdown(f'<div class="sr"><div class="sp2">Showing <strong>{len(f)}</strong></div><div class="sp2"><strong>{hr2}</strong> high relevance</div><div class="sp2"><strong>{en2}</strong> enacted laws</div></div>', unsafe_allow_html=True)
            if f.empty:
                st.markdown('<div class="es">No developments match your filters.</div>', unsafe_allow_html=True)
            else:
                for _,row in f.iterrows(): card(row.to_dict())
                st.markdown("---")
                csv = f[["source_name","title","date_published","summary","domain_tag","action_tag","relevance_amc","relevance_payer","relevance_dh","source_url"]].to_csv(index=False)
                st.download_button("Export as CSV", data=csv, file_name=f"pulse_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
        footer()

    # ── MONTHLY DIGEST ────────────────────────
    with tab_digest:
        now = datetime.now()
        mo = month_developments(df, now)
        month_label = now.strftime('%B %Y')

        dht_text = digest_title(mo)

        @st.cache_data(ttl=3600, show_spinner=False)
        def _cached_digest_summary(mo_df, m_label):
            return digest_summary(mo_df, m_label)
        dhb_text = _cached_digest_summary(mo, month_label)

        st.markdown(f"""<div class="dh">
          <div class="dhe">Monthly Digest<span class="dhe-sep"> · </span><span class="dhe-month">{month_label}</span></div>
          <div class="dht">{dht_text}</div>
          <div class="dhb">{dhb_text}</div>
        </div>""", unsafe_allow_html=True)

        if not mo.empty:
            for dom,grp in mo.groupby("domain_tag"):
                lbl = DL.get(dom,dom)
                ch = ""
                for _,row in grp.head(3).iterrows():
                    u = row.get("source_url","")
                    lk = f'<a class="ddcl" href="{u}" target="_blank">View source →</a>' if u else ""
                    ch += f'<div class="ddc"><div class="ddct">{row["title"]}</div><div class="ddcs">{row["summary"]}</div>{lk}</div>'
                st.markdown(f'<div class="dds2"><div class="ddh"><span class="ddd ddd-{dom}"></span><span class="ddn">{lbl}</span></div><div class="ddcw">{ch}</div></div>', unsafe_allow_html=True)
            lines = ["PULSE — HEALTH AI POLICY DIGEST",f"{now.strftime('%B %Y')} Edition","="*58,""]
            for dom,grp in mo.groupby("domain_tag"):
                lines += [f"── {DL.get(dom,dom).upper()}",""]
                for _,row in grp.head(3).iterrows():
                    lines += [f"  {row['title']}",f"  {row['summary']}"]
                    if row.get("source_url"): lines.append(f"  → {row['source_url']}")
                    lines.append("")
            st.download_button("Download digest (.txt)", data="\n".join(lines), file_name=f"pulse_digest_{now.strftime('%Y%m')}.txt", mime="text/plain")

        BK = os.environ.get("BEEHIIV_API_KEY","")
        BP = os.environ.get("BEEHIIV_PUB_ID","")
        st.markdown("""<div class="subbox"><div class="subt">Have the newest updates delivered right into your inbox</div>
          <div class="subb">Just one email, the month's most important health AI policy developments — tagged, summarized, and ready to act on.</div>
          <div class="subd">✦ Every 15th &nbsp;·&nbsp; ✦ Unsubscribe anytime &nbsp;·&nbsp; ✦ Stay ahead of industry news</div></div>""", unsafe_allow_html=True)
        with st.form("sub"):
            em = st.text_input("Email address", placeholder="you@organization.org")
            rl = st.selectbox("I work in", ["Select your role","Health system / Academic medical center","Digital health / AI company","Health plan / Payer","Policy / Government","Research / Academia","Consulting / Law","Other"])
            if st.form_submit_button("Subscribe to monthly digest →", type="primary"):
                if em and "@" in em and rl!="Select your role":
                    cn = get_conn()
                    if cn:
                        try:
                            cn.execute("CREATE TABLE IF NOT EXISTS subscribers (id INTEGER PRIMARY KEY, email TEXT UNIQUE, role TEXT, subscribed_at TEXT)")
                            cn.execute("INSERT OR IGNORE INTO subscribers (email,role,subscribed_at) VALUES (?,?,?)",(em,rl,now.isoformat()))
                            cn.commit()
                        except: pass
                    if BK and BP:
                        try: http_requests.post(f"https://api.beehiiv.com/v2/publications/{BP}/subscriptions",headers={"Authorization":f"Bearer {BK}","Content-Type":"application/json"},json={"email":em,"reactivate_existing":False,"send_welcome_email":True},timeout=5)
                        except: pass
                    n15 = (now.replace(day=1)+timedelta(days=32)).replace(day=15).strftime("%B 15")
                    st.success(f"✓ Subscribed. You'll receive the {n15} digest at {em}.")
                else: st.warning("Please enter a valid email and select your role.")
        footer()