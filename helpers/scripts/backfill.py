"""
Manual Backfill — Seeds your DB with real health AI policy developments
=====================================================================
These are drawn directly from the Manatt Health AI Policy Tracker (April 2026)
plus additional 2025-2026 developments. This gives you ~40 real rows to
prompt-engineer against in Week 2.

Run once: python scripts/backfill.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from scrapers.utils import insert_development

BACKFILL_DATA = [
    # ── FEDERAL: FDA ──────────────────────────────────────────────
    {
        "source_name": "FDA",
        "source_url": "https://www.fda.gov/medical-devices/software-medical-device-samd/clinical-decision-support-software",
        "title": "FDA Revised Final Guidance: Clinical Decision Support (CDS) Software",
        "date_published": "2026-01-06",
        "raw_text": "FDA published revised final guidance on Clinical Decision Support Software, expanding categories of AI-enabled CDS tools that fall outside FDA device regulation. The CDS guidance removes the prior interpretation that software providing risk scores or differential diagnoses automatically constitutes a regulated device; if a clinician can independently review the basis for a recommendation, the tool may fall outside FDA jurisdiction. FDA Commissioner Dr. Martin Makary announced the changes and indicated FDA is developing a new risk-based AI framework emphasizing post-market monitoring over premarket approval."
    },
    {
        "source_name": "FDA",
        "source_url": "https://www.fda.gov/medical-devices/digital-health-center-excellence/general-wellness-policy-low-risk-devices",
        "title": "FDA Revised Final Guidance: General Wellness Policy for Low Risk Devices",
        "date_published": "2026-01-06",
        "raw_text": "FDA expanded categories of consumer wearables that fall outside FDA device regulation. The guidance expands the scope of low-risk wellness devices that can be marketed without FDA premarket clearance or approval, including AI-enabled consumer health monitoring tools."
    },
    {
        "source_name": "FDA / EMA",
        "source_url": "https://www.fda.gov/news-events/press-announcements/fda-ema-jointly-publish-good-ai-practice-principles",
        "title": "FDA and EMA Jointly Publish Ten Principles for Good AI Practice in Medicines Lifecycle",
        "date_published": "2026-01-14",
        "raw_text": "FDA and the European Medicines Agency (EMA) jointly published ten principles for good AI practice in the medicines lifecycle, intended to guide AI use in evidence generation and safety monitoring and to underpin future international AI guidance in both jurisdictions."
    },
    {
        "source_name": "FDA / CMMI",
        "source_url": "https://www.fda.gov/medical-devices/digital-health-center-excellence/tempo-pilot",
        "title": "FDA TEMPO Pilot: Enforcement Discretion for Digital Health Devices in ACCESS Model",
        "date_published": "2026-03-02",
        "raw_text": "FDA began reaching out to device manufacturers regarding participation in the TEMPO Pilot, operated in conjunction with the CMMI ACCESS Model. The pilot permits manufacturers to offer digital health devices to ACCESS model participants under FDA enforcement discretion of certain premarket authorization requirements. This creates a de facto regulatory relief program for qualifying devices."
    },
    # ── FEDERAL: CMS ──────────────────────────────────────────────
    {
        "source_name": "CMS",
        "source_url": "https://www.cms.gov/digital-health-tech/medicare-app-library",
        "title": "CMS Launches Medicare App Library with Conversational AI Assistant Category",
        "date_published": "2026-02-23",
        "raw_text": "CMS launched the Medicare App Library, a centralized vetted directory of digital health tools available to Medicare beneficiaries. One of three designated use cases is 'Conversational AI Assistants,' defined as AI-powered personalized health guidance tools that access beneficiaries' medical history for symptom checking, care planning and chronic disease support. Requirements include clear AI-generated result indicators and disclaimers distinguishing educational content from clinical guidance. Apps are vetted by third-party organizations (DiMe or CARIN Alliance) rather than CMS directly."
    },
    {
        "source_name": "CMS",
        "source_url": "https://www.federalregister.gov/documents/2026/02/23/cms-ai-plan-selection-rfi",
        "title": "CMS RFI: AI and Machine Learning for Medicare Beneficiary Plan Selection",
        "date_published": "2026-02-23",
        "raw_text": "CMS issued a Request for Information seeking AI and machine learning tools to improve Medicare beneficiary plan selection, including improvements to Medicare.gov, the Plan Finder tool and the 1-800-MEDICARE call center. Comment period closed March 31, 2026."
    },
    {
        "source_name": "CMS",
        "source_url": "https://www.federalregister.gov/documents/2026/02/23/cms-6098-nc",
        "title": "CMS CRUSH Initiative RFI: AI-Powered Fraud Detection and Beneficiary Reporting",
        "date_published": "2026-02-23",
        "raw_text": "CMS published an RFI (CMS-6098-NC) soliciting stakeholder feedback on potential regulatory changes for the Comprehensive Regulation to Uncover Suspicious Healthcare (CRUSH) initiative, with comments due March 30, 2026. The CRUSH RFI includes AI-adjacent content around AI-powered fraud detection tools and beneficiary reporting mechanisms."
    },
    # ── FEDERAL: ONC ──────────────────────────────────────────────
    {
        "source_name": "ONC",
        "source_url": "https://www.healthit.gov/topic/laws-regulation-and-policy/hti-5",
        "title": "ONC HTI-5 Proposed Rule: Would Remove AI Model Card Transparency Requirements for CDS",
        "date_published": "2025-12-29",
        "raw_text": "ONC published HTI-5 Proposed Rule ('Health Data, Technology, and Interoperability: Deregulatory Actions to Unleash Prosperity'), with comment period closing February 27, 2026. Proposes to remove 34 of 60 health IT certification criteria and revise seven others. Critically, proposes to remove Biden-era AI model card transparency requirements for CDS algorithms — among the only existing federal transparency guardrails specific to health AI. Cites EO 14192 ('Unleashing Prosperity Through Deregulation') as a basis."
    },
    {
        "source_name": "ONC",
        "source_url": "https://www.healthit.gov/topic/laws-regulation-and-policy/hti-2-withdrawal",
        "title": "ONC HTI-2 Withdrawal Proposed Rule: Would Eliminate Voluntary AI Certification Pathways",
        "date_published": "2025-12-29",
        "raw_text": "ONC published HTI-2 Withdrawal Proposed Rule concurrently with HTI-5, which would eliminate non-finalized provisions from the August 2024 Biden-era interoperability rulemaking, including proposals to expand data exchange and establish voluntary AI certification pathways."
    },
    # ── FEDERAL: HHS ──────────────────────────────────────────────
    {
        "source_name": "HHS / ONC",
        "source_url": "https://www.federalregister.gov/documents/2026/02/hhs-ai-clinical-care-rfi",
        "title": "HHS RFI: Accelerating AI Adoption in Clinical Care — Barriers, Governance, Reimbursement",
        "date_published": "2026-02-01",
        "raw_text": "HHS and the Office of the Deputy Secretary, in collaboration with ASTP/ONC, published an RFI seeking public comment on steps HHS can take to accelerate the adoption and use of AI in clinical care. HHS sought feedback on regulatory barriers, reimbursement challenges, governance frameworks, and liability issues. Comment period closed February 23, 2026."
    },
    # ── FEDERAL: OMB ──────────────────────────────────────────────
    {
        "source_name": "OMB",
        "source_url": "https://www.whitehouse.gov/omb/memoranda/m-26-04",
        "title": "OMB Memo M-26-04: Requires HHS, CMS, FDA to Include 'Unbiased AI' Principles in LLM Contracts",
        "date_published": "2025-12-11",
        "raw_text": "OMB Memorandum M-26-04 'Increasing Public Trust in Artificial Intelligence Through Unbiased AI Principles' requires all executive agencies — including HHS, CMS and FDA — to include contractual requirements in new LLM procurements addressing compliance with two 'Unbiased AI Principles': (1) truth-seeking and (2) ideological neutrality. Agencies must modify existing LLM contracts to the extent practicable and update procurement policies by March 11, 2026. Explicitly does not govern agencies' own regulatory actions regarding non-agency uses of AI."
    },
    # ── FEDERAL: ARPA-H ───────────────────────────────────────────
    {
        "source_name": "ARPA-H",
        "source_url": "https://arpa-h.gov/research-and-funding/advocate",
        "title": "ARPA-H Launches ADVOCATE: First FDA-Authorized Agentic AI for Cardiovascular Clinical Care",
        "date_published": "2026-01-31",
        "raw_text": "ARPA-H launched the Agentic AI-Enabled Cardiovascular Care Transformation (ADVOCATE) model, a 39-month, two-phase initiative to develop and deploy the first FDA-authorized agentic AI system for clinical care. ADVOCATE will fund two systems: (1) a patient-facing AI agent capable of autonomously adjusting appointments, medications, diet and exercise; (2) and a supervisory AI 'overseer' to monitor deployed agents for continued safety and efficacy. ARPA-H anticipates selecting award teams by June 2026."
    },
    # ── WHITE HOUSE / CONGRESS ────────────────────────────────────
    {
        "source_name": "White House",
        "source_url": "https://www.whitehouse.gov/briefing-room/presidential-actions/2025/12/national-policy-framework-ai",
        "title": "EO 14365: White House Directs DOJ to Challenge 'Onerous' State AI Laws",
        "date_published": "2025-12-01",
        "raw_text": "Executive Order 14365, 'Ensuring a National Policy Framework for Artificial Intelligence,' directed the DOJ to establish an AI Litigation Task Force to challenge 'onerous' state AI laws and instructed the Secretary of Commerce to publish an evaluation of such laws. Colorado SB 205 was explicitly called out. DOJ established the AI Litigation Task Force on January 9, 2026."
    },
    {
        "source_name": "White House",
        "source_url": "https://www.whitehouse.gov/national-policy-framework-ai-march-2026",
        "title": "White House National Policy Framework for AI: Sector-Specific Regulation, Sandboxes, Preemption",
        "date_published": "2026-03-20",
        "raw_text": "The White House released its National Policy Framework for Artificial Intelligence. The framework focuses on federal control over AI development legislation, supports sector-specific regulation by federal agencies (potentially spurring increased activity by FDA, CMS, ONC and FTC), and signals support for new AI sandbox programs. Preserves meaningful room for states to regulate AI use in areas of traditional state police power. Most immediate pressure on Congress relates to protecting minors interacting with AI systems."
    },
    {
        "source_name": "Congress",
        "source_url": "https://www.congress.gov/bill/119th-congress/house-bill/7757",
        "title": "House Energy and Commerce Advances KIDS Act and SAFE BOTs Act with AI Chatbot Guardrails",
        "date_published": "2026-03-05",
        "raw_text": "Republican members of the House Energy and Commerce Committee advanced a children's online safety package, including HR 7757 (the KIDS Act) and HR 6489 (the SAFE BOTs Act), with guardrails for AI chatbots. These bills require chatbots to disclose AI status at prescribed cadence, prohibit chatbots from representing themselves as licensed professionals, include minor-specific protections, and mandate referral to mental health crisis resources. Bipartisan negotiations broke down over preemption language that would have limited states' ability to pass stronger laws."
    },
    # ── STATE: SIGNED INTO LAW ────────────────────────────────────
    {
        "source_name": "Indiana Legislature",
        "source_url": "https://iga.in.gov/legislative/2026/bills/house/1271",
        "title": "Indiana HB 1271 (Enacted 3/4/2026): Prohibits AI-Only Claim Downcoding by Insurers",
        "date_published": "2026-03-04",
        "raw_text": "Indiana HB 1271 enacted March 4, 2026, effective July 1, 2026. Prohibits health insurers from using AI as the sole basis to downcode a claim without review of the covered individual's medical record. Requires insurers to disclose when AI is used in a downcoding decision or adverse prior authorization determination, and notify providers when a claim is downcoded. Prohibits targeted or discriminatory downcoding against providers treating patients with complex or chronic conditions."
    },
    {
        "source_name": "Utah Legislature",
        "source_url": "https://le.utah.gov/~2026/bills/static/SB0319.html",
        "title": "Utah SB 319 (Enacted 3/19/2026): Insurers Must Disclose AI Use in Prior Authorization Reviews",
        "date_published": "2026-03-19",
        "raw_text": "Utah SB 319 enacted March 19, 2026, effective January 1, 2027. Requires insurers to publicly disclose if AI is used to review authorization requests and to issue a disclosure notifying the Department of Insurance, providers, and enrollees of the use of AI to review authorization requests."
    },
    {
        "source_name": "Tennessee Legislature",
        "source_url": "https://wapp.capitol.tn.gov/apps/BillInfo/Default.aspx?BillNumber=SB1580",
        "title": "Tennessee SB 1580 (Enacted, Effective 7/1/2026): Prohibits Chatbots from Posing as Licensed Professionals",
        "date_published": "2026-03-15",
        "raw_text": "Tennessee SB 1580 enacted, effective July 1, 2026. Prohibits chatbot proprietors from allowing their AI chatbot to represent itself as a licensed professional, including medical professionals. Aligns with Illinois HB 1806 (effective 8/1/2025) and California AB 489 (effective 1/1/2026)."
    },
    {
        "source_name": "Idaho Legislature",
        "source_url": "https://legislature.idaho.gov/sessioninfo/2026/legislation/SB1297/",
        "title": "Idaho SB 1297 (Enacted, Effective 7/1/2027): Minor-Specific AI Chatbot Protections",
        "date_published": "2026-02-20",
        "raw_text": "Idaho SB 1297 enacted, effective July 1, 2027. Establishes minor-specific protections for AI chatbot users, including age verification requirements, more frequent disclosures that a user is interacting with AI, restrictions on content that can be generated for minors, and requirements for parental monitoring tools."
    },
    {
        "source_name": "Oregon Legislature",
        "source_url": "https://olis.oregonlegislature.gov/liz/2026R1/Measures/Overview/SB1546",
        "title": "Oregon SB 1546 (Enacted, Effective 1/1/2027): Chatbots Must Detect Mental Health Crises",
        "date_published": "2026-03-10",
        "raw_text": "Oregon SB 1546 enacted, effective January 1, 2027. Requires chatbot operators to ensure their AI chatbot is capable of detecting mental health crises (including self-harm and suicidal ideation) and implements an appropriate response, including referring users to crisis resources or suicide hotlines. Includes minor-specific protections and age verification requirements."
    },
    # ── STATE: INTRODUCED / PENDING ──────────────────────────────
    {
        "source_name": "Colorado Legislature",
        "source_url": "https://leg.colorado.gov/bills/sb25-205",
        "title": "Colorado SB 205 Revision (Proposed): Broadens HIPAA Carve-Out for Health AI Transparency",
        "date_published": "2026-03-01",
        "raw_text": "Colorado AI Policy Work Group unanimously released a proposed bill to revise SB 205 before it goes into effect June 30, 2026. Most notably for health care stakeholders, this proposed bill broadens the narrow HIPAA carve-out for non-high-risk AI recommendations to exempt all HIPAA-covered entities and business associates from most obligations, only requiring them to provide patients with general notice that they use advanced technologies. Eliminates anti-discrimination duties, removes comprehensive risk management and annual impact assessment requirements, and simplifies consumer appeal rights."
    },
    {
        "source_name": "California Legislature",
        "source_url": "https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=202520260AB2575",
        "title": "California AB 2575 (Introduced): Clinician Failure to Override AI Cannot Sever Developer Liability",
        "date_published": "2026-02-15",
        "raw_text": "California AB 2575 introduced, would prohibit deployers or developers of AI that are alleged to have caused harm from asserting as a defense that a licensed health care professional's failure to override the AI output severs the developer's or deployer's liability as a superseding cause."
    },
    {
        "source_name": "California Legislature",
        "source_url": "https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=202520260AB2431",
        "title": "California AB 2431 (Introduced): Prohibits AI-Only Claim Downcoding Without Physician Review",
        "date_published": "2026-01-28",
        "raw_text": "California AB 2431 introduced, would prohibit health insurers from using AI as the sole basis to downcode a claim without oversight by a licensed physician. Part of a 2026 trend: downcoding-focused bills introduced across California, Connecticut, Illinois, Indiana, Maryland, Missouri and Oregon."
    },
    {
        "source_name": "New York Legislature",
        "source_url": "https://nyassembly.gov/leg/?bn=AB8884",
        "title": "New York AB 8884 (Introduced): Strict Liability for Large-Scale AI Model Developers",
        "date_published": "2026-02-01",
        "raw_text": "New York AB 8884 introduced, would establish strict liability standards for developers of large-scale AI models when those models cause harm to people who are not direct users of the model. Developers are strictly liable for all injuries to a non-user if proximately caused by an AI tool whose actions would constitute negligence if conducted by a human."
    },
    {
        "source_name": "Virginia Legislature",
        "source_url": "https://lis.virginia.gov/cgi-bin/legp604.exe?ses=261&typ=bil&val=SB269",
        "title": "Virginia SB 269 (Introduced): Clinician Oversight and Patient Consent Required for AI in Mental Health",
        "date_published": "2026-01-15",
        "raw_text": "Virginia SB 269 introduced, aligning with Illinois HB 1806. Would allow providers to use AI to provide administrative or supplementary support as long as the provider maintains responsibility for the AI's output and obtains affirmative patient consent before using AI tools in clinical context. Prohibits providers from using AI to make independent therapeutic decisions or generate treatment plans without oversight from a licensed clinician."
    },
    {
        "source_name": "Illinois Legislature",
        "source_url": "https://www.ilga.gov/legislation/billstatus.asp?DocNum=3590&GAID=18&GA=104&DocTypeID=SB",
        "title": "Illinois SB 3590 (Introduced): Liability Standards for Developers of High-Impact AI Systems Including Medical Devices",
        "date_published": "2026-02-10",
        "raw_text": "Illinois SB 3590 introduced, would set legal standards for liability for developers and deployers of high-impact AI systems, including systems used as a medical device."
    },
    # ── REGULATORY SANDBOXES ──────────────────────────────────────
    {
        "source_name": "Utah OAIP",
        "source_url": "https://aipolicy.utah.gov/regulatory-mitigation/legion-health",
        "title": "Utah OAIP Regulatory Relief Agreement with Legion Health for AI-Native Psychiatric Prescription Renewals",
        "date_published": "2026-03-01",
        "raw_text": "Utah's Office of Artificial Intelligence Policy (OAIP) announced their fourth regulatory relief agreement with Legion Health, an 'AI-native' digital health/psychiatry company. Under its agreement with OAIP, Legion Health will provide prescription refills for non-controlled, maintenance psychiatric medications (e.g., SSRIs for depression and anxiety) in a three-phased approach with clinical oversight requirements."
    },
    {
        "source_name": "Arizona Legislature",
        "source_url": "https://www.azleg.gov/legtext/57leg/2R/bills/HB4080P.htm",
        "title": "Arizona HB 4080 (Introduced): AI Sandbox Pilot for Nursing-Adjacent AI Tasks",
        "date_published": "2026-02-05",
        "raw_text": "Arizona HB 4080 would establish a pilot program testing innovative AI that performs nursing-adjacent tasks or workflows. Applicants must have an agreement with an accredited nursing school for evaluation and oversight."
    },
    # ── EARLIER 2025 REFERENCE LAWS ───────────────────────────────
    {
        "source_name": "Illinois Legislature",
        "source_url": "https://www.ilga.gov/legislation/billstatus.asp?DocNum=1806&GAID=17&GA=103&DocTypeID=HB",
        "title": "Illinois HB 1806 (Effective 8/1/2025): Mental Health AI Oversight and Chatbot Prohibition on Posing as Clinicians",
        "date_published": "2025-08-01",
        "raw_text": "Illinois HB 1806 effective August 1, 2025. Prohibits chatbots from representing themselves as licensed mental health providers. Allows providers to use AI for administrative or supplementary support as long as the provider maintains responsibility for the AI's output and obtains patient consent. Prohibits providers from using AI to make independent therapeutic decisions or generate treatment plans without oversight from a licensed clinician. This is one of the most-cited reference laws in 2026 state AI legislation."
    },
    {
        "source_name": "Texas Legislature",
        "source_url": "https://capitol.texas.gov/BillLookup/History.aspx?LegSess=89R&Bill=HB149",
        "title": "Texas HB 149 (Effective 1/1/2026): AI Disclosure Requirements for Clinicians",
        "date_published": "2025-06-22",
        "raw_text": "Texas HB 149 enacted June 22, 2025, effective January 1, 2026. Requires clinicians to disclose to patients when AI is used in their care. Establishes an AI regulatory sandbox program. Multiple states have introduced bills in 2026 that include provisions aligned with Texas HB 149."
    },
    {
        "source_name": "California Legislature",
        "source_url": "https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=202520260SB243",
        "title": "California SB 243 (Effective 1/1/2026): AI Chatbot Mental Health Crisis Detection and Minor Protections",
        "date_published": "2026-01-01",
        "raw_text": "California SB 243 effective January 1, 2026. Requires chatbot operators to detect mental health and suicidal ideation in users and implement appropriate responses including crisis referrals. Establishes guardrails for users under 18. This is the most-cited reference law in 2026 chatbot legislation across 36+ states."
    },
]

def run_backfill():
    print(f"Loading {len(BACKFILL_DATA)} known health AI policy developments...\n")
    inserted = 0
    skipped = 0
    for record in BACKFILL_DATA:
        if insert_development(record):
            inserted += 1
        else:
            skipped += 1
    print(f"\n{'─'*50}")
    print(f"Backfill complete: {inserted} inserted, {skipped} already existed.")

if __name__ == "__main__":
    run_backfill()
