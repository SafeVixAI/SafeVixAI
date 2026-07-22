# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""
Enterprise ChromaDB Legal + Medical Ingestion
==============================================
Ingests ALL sources into ChromaDB:
  1. MV Act 1988 key sections (hardcoded enterprise-grade text)
  2. MV Amendment 2019 — from downloaded PDF (if available) + hardcoded
  3. State overrides CSV
  4. WHO Trauma Care Guidelines — from downloaded PDF (if available)
  5. First Aid JSON (20 WHO articles)

Run: python backend/scripts/ingest_legal_chromadb.py
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    print("Install chromadb: pip install chromadb")
    sys.exit(1)

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR    = Path(__file__).parent          # scripts/data/
BACKEND_DIR   = Path(__file__).resolve().parents[2]  # backend/
CHROMA_PATH   = BACKEND_DIR / "chroma_db"
CHALLAN_CSV   = BACKEND_DIR / "datasets" / "challan" / "state_overrides.csv"
FIRST_AID_JSON = BACKEND_DIR.parent / "frontend" / "public" / "offline-data" / "first-aid.json"

# Dataset Hub paths for downloaded PDFs
HUB_ROOT      = BACKEND_DIR.parent.parent / "SafeVixAI-Dataset-Hub"
HUB_LEGAL_DIR = HUB_ROOT / "scripts" / "scripts" / "chatbot_service" / "data" / "legal"
HUB_MED_DIR   = HUB_ROOT / "scripts" / "scripts" / "chatbot_service" / "data" / "medical"
MV_ACT_PDF    = HUB_LEGAL_DIR / "mv_act_1988_full.pdf"
MV_AMEND_PDF  = HUB_LEGAL_DIR / "mv_amendment_act_2019.pdf"
WHO_PDF       = HUB_MED_DIR   / "who_trauma_care_guidelines.pdf"

# ── MV Act 1988 Key Sections ──────────────────────────────────────────────────
MV_ACT_1988_SECTIONS = [
    {
        "id": "mva-1988-s112",
        "section": "Section 112 — Limits of Speed",
        "content": (
            "Section 112 of the Motor Vehicles Act 1988 sets maximum speed limits. "
            "Urban area roads: 50 km/h for LMV; 40 km/h for HMV. "
            "National and State highways: 100 km/h for LMV; 65 km/h for HMV; 60 km/h for medium goods. "
            "State governments may fix lower speeds for specific routes. "
            "Fine: Rs.1,000-Rs.2,000 for first offense; Rs.2,000-Rs.4,000 for repeat."
        ),
        "act": "Motor Vehicles Act 1988", "category": "speeding",
    },
    {
        "id": "mva-1988-s129",
        "section": "Section 129 — Wearing of Protective Headgear",
        "content": (
            "Section 129 mandates every person driving or riding a motorcycle on any public road "
            "shall wear a protective helmet conforming to BIS standards. Helmet must be securely fastened. "
            "Fine: Rs.1,000 for non-wearing. Pillion passenger without helmet: Rs.1,000. "
            "Disqualification from driving for 3 months may be imposed on repeat offense."
        ),
        "act": "Motor Vehicles Act 1988", "category": "helmet",
    },
    {
        "id": "mva-1988-s138",
        "section": "Section 138 — Regulation of Traffic",
        "content": (
            "Section 138 empowers state governments to make traffic rules. "
            "Red light jumping: Rs.5,000 fine under MV Amendment 2019. "
            "Wrong side driving: Rs.5,000. "
            "No seatbelt: Rs.1,000. "
            "Mobile phone while driving: Rs.5,000 (repeat: Rs.10,000)."
        ),
        "act": "Motor Vehicles Act 1988", "category": "traffic_signal",
    },
    {
        "id": "mva-1988-s185",
        "section": "Section 185 — Driving by a Drunken Person",
        "content": (
            "Section 185 prohibits driving under influence of alcohol or drugs. "
            "BAC exceeding 30mg per 100ml of blood is an offense. "
            "First offense: imprisonment up to 6 months OR fine up to Rs.10,000 or both. "
            "Second offense within 3 years: imprisonment up to 2 years AND fine up to Rs.15,000. "
            "Driving license suspension for 6 months minimum on first conviction."
        ),
        "act": "Motor Vehicles Act 1988", "category": "drunk_driving",
    },
    {
        "id": "mva-1988-s194",
        "section": "Section 194 — Using Vehicle Exceeding Permissible Weight",
        "content": (
            "Section 194 addresses overloaded vehicles. "
            "Fine: Rs.20,000 for first offense, plus Rs.2,000 per additional tonne. "
            "Repeat offense: Rs.25,000 + per-tonne rate. "
            "State government may detain vehicle until excess load is unloaded."
        ),
        "act": "Motor Vehicles Act 1988", "category": "overloading",
    },
    {
        "id": "mva-1988-s196",
        "section": "Section 196 — Driving Without Insurance",
        "content": (
            "Section 196 mandates third-party insurance for all motor vehicles. "
            "Driving without valid third-party insurance: "
            "Fine Rs.2,000 and/or imprisonment up to 3 months for first offense. "
            "Repeat: Rs.4,000 and/or 3 months. Cognizable offense — police can arrest without warrant."
        ),
        "act": "Motor Vehicles Act 1988", "category": "no_insurance",
    },
    {
        "id": "mva-1988-s177",
        "section": "Section 177 — General Provisions for Punishment",
        "content": (
            "Section 177 general punishment for traffic violations not covered by specific sections. "
            "Fine: Rs.500 for first offense; Rs.1,500 for subsequent offenses. "
            "Driving license in violation of conditions: Rs.5,000."
        ),
        "act": "Motor Vehicles Act 1988", "category": "general",
    },
    {
        "id": "mva-1988-s134",
        "section": "Section 134 — Duty of Driver in Case of Accident",
        "content": (
            "Section 134: driver involved in accident must secure medical attention for injured. "
            "Driver must not flee the scene. Must report to nearest police station within 24 hours "
            "if any person was killed or injured. "
            "Failure to report: imprisonment up to 3 months or fine up to Rs.500. "
            "Hit and run cases: victim compensation from Solatium Fund."
        ),
        "act": "Motor Vehicles Act 1988", "category": "accident_duty",
    },
    {
        "id": "mva-1988-s181",
        "section": "Section 181 — Driving Without Licence",
        "content": (
            "Section 181: driving without a valid driving licence is an offense. "
            "Fine: Rs.5,000 (MV Amendment 2019 — was Rs.500). "
            "Unlicensed minor driving: Guardian or owner liable — Rs.25,000 fine, "
            "3 years imprisonment, minor treated as adult under JJ Act for this purpose."
        ),
        "act": "Motor Vehicles Act 1988", "category": "no_licence",
    },
    {
        "id": "mva-1988-s184",
        "section": "Section 184 — Dangerous Driving",
        "content": (
            "Section 184: dangerous driving which endangers public safety. "
            "First offense: imprisonment up to 1 year OR fine Rs.1,000-Rs.5,000. "
            "Repeat within 3 years: imprisonment up to 2 years. "
            "Racing on public roads: imprisonment up to 1 year OR fine up to Rs.5,000."
        ),
        "act": "Motor Vehicles Act 1988", "category": "dangerous_driving",
    },
    # ── MV Amendment Act 2019 ──────────────────────────────────────────────────
    {
        "id": "mva-2019-s119",
        "section": "MV Amendment 2019 — Complete Updated Fines Schedule",
        "content": (
            "Motor Vehicles (Amendment) Act 2019 significantly increased fines: "
            "Drunk driving: Rs.10,000 first offense, Rs.15,000 repeat (was Rs.2,000); "
            "Speeding: Rs.1,000-Rs.2,000 (was Rs.400); "
            "Red light jumping: Rs.5,000 (was Rs.1,000); "
            "No helmet: Rs.1,000 + 3-month license suspension (was Rs.100); "
            "No seatbelt: Rs.1,000 (was Rs.100); "
            "Dangerous driving: Rs.5,000 (was Rs.1,000); "
            "Mobile phone while driving: Rs.5,000 first, Rs.10,000 repeat (was Rs.1,000); "
            "No licence: Rs.5,000 (was Rs.500); "
            "No insurance: Rs.2,000 first, Rs.4,000 repeat (was Rs.1,000); "
            "Overloading 2-wheelers: Rs.2,000 + license disqualification 3 months; "
            "Juvenile driving: Guardian liable Rs.25,000, 3 years jail."
        ),
        "act": "MV Amendment Act 2019", "category": "general",
    },
    {
        "id": "mva-2019-golden-hour",
        "section": "MV Amendment 2019 — Good Samaritan Protection",
        "content": (
            "Good Samaritan provisions under MV Amendment 2019: "
            "Person who voluntarily helps accident victim in good faith cannot be subject to "
            "civil or criminal liability. Cannot be detained at hospital or police station. "
            "Police cannot compel Good Samaritan to be a witness. "
            "Hospital cannot demand payment before emergency treatment within first 24 hours. "
            "Cashless treatment for road accident victims within golden hour."
        ),
        "act": "MV Amendment Act 2019", "category": "good_samaritan",
    },
    {
        "id": "mva-2019-compensation",
        "section": "MV Amendment 2019 — Hit and Run Compensation",
        "content": (
            "Hit and run compensation under MV Amendment Act 2019: "
            "Death in hit and run: Rs.2,00,000 (was Rs.25,000). "
            "Grievous hurt in hit and run: Rs.50,000 (was Rs.12,500). "
            "Paid from Motor Vehicle Accident Fund maintained by Government of India. "
            "Claim to be filed within 6 months to Claim Enquiry Officer."
        ),
        "act": "MV Amendment Act 2019", "category": "compensation",
    },
    # ── State Overrides (inline) ───────────────────────────────────────────────
    {
        "id": "state-delhi-helmet",
        "content": (
            "Delhi: Helmet fine Rs.1,000 per Central Act. No separate state override. "
            "E-challan via automated CCTV cameras in Delhi NCR. "
            "Delhi traffic police issues challan via Parivahan portal."
        ),
        "act": "Delhi Motor Vehicle Rules", "category": "helmet",
    },
    {
        "id": "state-tamil-nadu-speed",
        "content": (
            "Tamil Nadu: Speed limits on National Highways: 80 km/h LMV, 60 km/h HMV. "
            "Urban area speed limit: 50 km/h. "
            "Speeding fine: Rs.1,000-Rs.2,000 per central act."
        ),
        "act": "Tamil Nadu Motor Vehicles Rules", "category": "speeding",
    },
    {
        "id": "state-maharashtra-drunk",
        "content": (
            "Maharashtra: Drunk driving fine Rs.10,000 + license suspension 6 months first offense. "
            "Repeat within 3 years: license cancellation + imprisonment up to 2 years. "
            "Breathalyzer test mandatory on NH and expressways."
        ),
        "act": "Maharashtra Motor Vehicles Rules", "category": "drunk_driving",
    },
    {
        "id": "state-karnataka-mobile",
        "content": (
            "Karnataka: Mobile phone use while driving Rs.5,000 per MV Amendment 2019. "
            "Bangalore Traffic Police operates automated challan system via CCTV. "
            "Challan sent to vehicle owner via SMS within 48 hours."
        ),
        "act": "Karnataka Motor Vehicles Rules", "category": "mobile_phone",
    },
    {
        "id": "state-up-overload",
        "content": (
            "Uttar Pradesh: Overloading fine Rs.20,000 + Rs.2,000 per extra tonne. "
            "Frequent night raids on NH-19, NH-58, NH-24 for overloaded trucks. "
            "Vehicle detained at nearest weighbridge until excess load removed."
        ),
        "act": "Uttar Pradesh Motor Vehicles Rules", "category": "overloading",
    },
]

# ── PDF Text Extraction Helper ────────────────────────────────────────────────
def extract_pdf_chunks(pdf_path: Path, tag: str, chunk_size: int = 800) -> list[dict]:
    """Extract text from PDF and split into chunks for ChromaDB."""
    try:
        import pdfplumber
    except ImportError:
        print(f"  [SKIP PDF] pdfplumber not installed. Skipping {pdf_path.name}")
        return []

    if not pdf_path.exists() or pdf_path.stat().st_size < 10000:
        print(f"  [SKIP PDF] Not found or too small ({pdf_path.stat().st_size if pdf_path.exists() else 0}B): {pdf_path.name}")
        return []

    chunks = []
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text() or ""
                full_text += text + "\n"

        # Split into chunks
        words = full_text.split()
        chunk_words = chunk_size // 6  # ~6 chars per word average
        for i in range(0, len(words), chunk_words):
            chunk = " ".join(words[i : i + chunk_words])
            if len(chunk) > 100:  # skip tiny chunks
                chunks.append({
                    "id": f"{tag}-chunk-{i}",
                    "content": chunk,
                    "act": tag,
                    "category": "full_pdf",
                })

        print(f"  [PDF] Extracted {len(chunks)} chunks from {pdf_path.name}")
    except Exception as e:
        print(f"  [WARN PDF] Could not parse {pdf_path.name}: {e} — skipping")

    return chunks


# ── First Aid JSON Loader ────────────────────────────────────────────────────
def load_first_aid_docs() -> list[dict]:
    """Load all 20 WHO-based first aid articles from first-aid.json."""
    if not FIRST_AID_JSON.exists():
        print(f"  [SKIP] first-aid.json not found at {FIRST_AID_JSON}")
        return []

    with open(FIRST_AID_JSON, encoding="utf-8") as f:
        articles = json.load(f)

    docs = []
    for article in articles:
        title = article.get("title", "First Aid")
        steps = article.get("steps", [])

        def step_text(s):
            if isinstance(s, str):
                return s
            if isinstance(s, dict):
                return s.get("instruction") or s.get("text") or str(s)
            return str(s)

        content = f"{title}: " + " | ".join(step_text(s) for s in steps)
        docs.append({
            "id": f"firstaid-{article.get('id', len(docs))}",
            "content": content,
            "act": "WHO First Aid Guidelines",
            "category": "first_aid",
        })

    print(f"  [OK] Loaded {len(docs)} first-aid articles from first-aid.json")
    return docs


# ── Main Ingest ───────────────────────────────────────────────────────────────
def ingest_to_chromadb() -> None:
    CHROMA_PATH.mkdir(exist_ok=True)

    print(f"[CHROMA] Connecting to ChromaDB at: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        print("[OK] Using SentenceTransformer all-MiniLM-L6-v2 embeddings")
    except Exception:
        ef = embedding_functions.DefaultEmbeddingFunction()
        print("[WARN] Using default embeddings (install sentence-transformers for better accuracy)")

    # ── Legal collection ───────────────────────────────────────────────────────
    legal_col = client.get_or_create_collection(
        name="legal_knowledge",
        embedding_function=ef,
        metadata={"description": "India Motor Vehicles Act + Amendment 2019 + State Rules"},
    )

    all_legal = list(MV_ACT_1988_SECTIONS)  # start with hardcoded

    # Add CSV state overrides
    if CHALLAN_CSV.exists():
        with open(CHALLAN_CSV, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                all_legal.append({
                    "id": f"csv-state-{i}",
                    "content": (
                        f"State: {row.get('state','?')} | "
                        f"Offense: {row.get('offense_type','?')} | "
                        f"Fine: Rs.{row.get('fine_amount','?')} | "
                        f"Section: {row.get('mv_act_section','N/A')}"
                    ),
                    "act": "State Override CSV",
                    "category": row.get("offense_type", "general"),
                })
        print(f"  [OK] Loaded {i+1} state override rows from CSV")

    # Add PDF chunks for MV Act 1988 full text (if downloaded)
    all_legal += extract_pdf_chunks(MV_ACT_PDF, "MV Act 1988 Full PDF")

    # Add PDF chunks for MV Amendment 2019 (if downloaded)
    all_legal += extract_pdf_chunks(MV_AMEND_PDF, "MV Amendment Act 2019 PDF")

    legal_col.upsert(
        ids=[d["id"] for d in all_legal],
        documents=[d["content"] for d in all_legal],
        metadatas=[{"act": d.get("act",""), "category": d.get("category",""), "section": d.get("section","")} for d in all_legal],
    )
    print(f"[OK] Legal collection: {len(all_legal)} documents ingested")

    # ── Medical / First Aid collection ─────────────────────────────────────────
    medical_col = client.get_or_create_collection(
        name="medical_knowledge",
        embedding_function=ef,
        metadata={"description": "WHO First Aid Guidelines + Trauma Care"},
    )

    all_medical = load_first_aid_docs()
    all_medical += extract_pdf_chunks(WHO_PDF, "WHO Trauma Care Guidelines PDF")

    if all_medical:
        medical_col.upsert(
            ids=[d["id"] for d in all_medical],
            documents=[d["content"] for d in all_medical],
            metadatas=[{"act": d.get("act",""), "category": d.get("category","")} for d in all_medical],
        )
        print(f"[OK] Medical collection: {len(all_medical)} documents ingested")

    # ── Verification ──────────────────────────────────────────────────────────
    print("\n[TEST] Verification queries:")
    q1 = legal_col.query(query_texts=["drunk driving fine india"], n_results=2)
    print(f"  'drunk driving': {q1['documents'][0][0][:80]}...")
    q2 = legal_col.query(query_texts=["helmet not wearing penalty"], n_results=1)
    print(f"  'helmet penalty': {q2['documents'][0][0][:80]}...")
    if all_medical:
        q3 = medical_col.query(query_texts=["how to do CPR"], n_results=1)
        print(f"  'CPR steps': {q3['documents'][0][0][:80]}...")

    print("\n[DONE] ChromaDB enterprise ingestion complete.")
    print(f"  Legal documents: {legal_col.count()}")
    print(f"  Medical documents: {medical_col.count() if all_medical else 0}")


if __name__ == "__main__":
    ingest_to_chromadb()
