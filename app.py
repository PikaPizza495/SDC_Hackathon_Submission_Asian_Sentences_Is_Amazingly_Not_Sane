"""
Orbyte InstaQuote: Smart SME Supplier Match & WhatsApp RFQ Automation
"""
import json
import os
import re
import random
import urllib.error
import urllib.request
from datetime import datetime
from urllib.parse import quote

import pandas as pd
import streamlit as st

import orbyte_hub

st.set_page_config(
    page_title="Orbyte | Smart SME Procurement Hub",
    page_icon=":material/hexagon:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# ORBYTE NATIVE DESIGN SYSTEM CSS (Matches image_d9613d.jpg)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: #1E293B !important;
    }

    /* Hide default dark top header bar */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* Main Orbyte Soft Cool-Grey/Blue Canvas */
    .stApp {
        background-color: #F4F7FB !important;
        color: #1E293B !important;
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1220px !important;
    }

    /* --- SIDEBAR: Orbyte Left Navigation --- */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E5EAF2 !important;
        width: 280px !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.25rem !important;
        padding-left: 1.1rem !important;
        padding-right: 1.1rem !important;
    }

    /* Only the controls scroll; the account is a separate, non-scrolling flex child. */
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        height: 100dvh;
        overflow: hidden !important;
        display: flex;
        flex-direction: column;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        flex: 1 1 0;
        min-height: 0;
        overflow: hidden !important;
        display: flex;
        flex-direction: column;
        padding-bottom: 12px;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > div {
        display: flex;
        flex-direction: column;
        flex: 1 1 0;
        min-height: 0;
        overflow: hidden;
    }
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"]:has(.st-key-sidebar-account-footer) {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 1 0;
        height: 100%;
        min-height: 0;
        overflow: hidden;
    }
    section[data-testid="stSidebar"] .st-key-sidebar-scroll-content,
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:has(> .st-key-sidebar-scroll-content) {
        flex: 1 1 0 !important;
        min-height: 0 !important;
        overflow-y: auto !important;
        overflow-x: hidden;
        overscroll-behavior: contain;
        scrollbar-width: thin;
    }
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:has(.st-key-sidebar-account-footer),
    section[data-testid="stSidebar"] .st-key-sidebar-account-footer {
        flex: 0 0 auto;
        min-height: 72px;
        background: #FFFFFF;
    }

    /* Force all inputs, dropdowns, and number boxes to be crisp white (never black!) */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"],
    input,
    textarea {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        border-color: #CBD5E1 !important;
        border-radius: 8px !important;
        font-size: 0.875rem !important;
    }
    /* Dropdown menu popover */
    ul[data-baseweb="menu"],
    div[data-baseweb="popover"] {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
    }
    li[role="option"] {
        color: #1E293B !important;
        background-color: #FFFFFF !important;
    }
    li[role="option"]:hover {
        background-color: #F1F5F9 !important;
    }

    /* Number input +/- buttons */
    button[data-testid="stNumberInputStepDown"],
    button[data-testid="stNumberInputStepUp"] {
        background-color: #F8FAFC !important;
        color: #334155 !important;
        border-color: #CBD5E1 !important;
    }

    /* Labels */
    label, .stWidgetLabel p {
        color: #475569 !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
    }

    /* White Orbyte Cards (st.container(border=True) & st.form) */
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stForm"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E5EAF2 !important;
        border-radius: 12px !important;
        padding: 1.25rem 1.5rem !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03) !important;
    }

    /* Orbyte Primary Button (Deep Sky / Cerulean Blue) */
    div.stButton > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button {
        background-color: #0284C7 !important;
        color: #FFFFFF !important;
        border: 1px solid #0369A1 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 0.5rem 1rem !important;
        box-shadow: 0 1px 2px rgba(2, 132, 199, 0.15) !important;
        transition: all 0.15s ease !important;
    }
    div.stButton > button[kind="primary"] *,
    div[data-testid="stFormSubmitButton"] > button * {
        color: #FFFFFF !important;
    }
    div.stButton > button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #0369A1 !important;
    }

    /* Orbyte outlined secondary button treatment. */
    div.stButton > button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #0369A1 !important;
        border: 1px solid #BAE6FD !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 0.45rem 0.9rem !important;
    }
    div.stButton > button[kind="secondary"] * {
        color: #0369A1 !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #F0F9FF !important;
        border-color: #38BDF8 !important;
    }

    /* Custom HTML Helper Classes for Orbyte Look */
    .orbyte-logo-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 0.85rem;
        margin-bottom: 0.5rem;
    }
    .orbyte-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 1.35rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.03em;
    }
    .orbyte-logo-icon {
        width: 30px;
        height: 30px;
        border-radius: 8px;
        background: linear-gradient(135deg, #0072CE 0%, #00A859 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 800;
        font-size: 1rem;
    }
    .orbyte-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex: 0 0 auto;
        vertical-align: -0.16em;
        line-height: 0;
    }
    .orbyte-icon svg { display: block; }
    .orbyte-nav-current {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #0284C7;
        flex: 0 0 auto;
    }
    .orbyte-nav-tree {
        font-size: 0.86rem;
        color: #475569;
        line-height: 2.1;
        margin-top: 0.5rem;
    }
    .orbyte-nav-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 4px 8px;
        border-radius: 6px;
        color: #475569;
        font-weight: 500;
    }
    .orbyte-nav-sub {
        display: flex;
        align-items: center;
        padding-left: 24px;
        font-size: 0.83rem;
        color: #64748B;
    }
    .orbyte-nav-item > span:first-child,
    .orbyte-nav-active > span:first-child {
        display: inline-flex;
        align-items: center;
    }
    .orbyte-nav-active {
        background-color: #E0F2FE;
        color: #0369A1 !important;
        font-weight: 600;
        border-radius: 6px;
        padding: 4px 10px;
        margin-left: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .orbyte-card {
        background: #FFFFFF;
        border: 1px solid #E5EAF2;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 18px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.02);
    }
    .orbyte-badge-gray {
        background: #F1F5F9;
        color: #475569;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 2px 9px;
        border-radius: 6px;
        margin-left: 8px;
    }
    .orbyte-pill-active {
        background: #E0F2FE;
        color: #0369A1;
        border: 1px solid #7DD3FC;
        padding: 5px 14px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .orbyte-pill-inactive {
        color: #475569;
        padding: 5px 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .orbyte-status-pending {
        background: #E0F2FE;
        color: #0369A1;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.76rem;
        font-weight: 600;
        display: inline-block;
        white-space: nowrap;
    }
    .orbyte-status-approved {
        background: #DCFCE7;
        color: #15803D;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.76rem;
        font-weight: 600;
        display: inline-block;
        white-space: nowrap;
    }
    .orbyte-activity-row {
        display: grid;
        grid-template-columns: minmax(0, 1.6fr) minmax(0, 0.6fr) 160px minmax(0, 0.9fr) 70px;
        align-items: center;
        gap: 12px;
        padding: 11px 4px;
        border-bottom: 1px solid #F1F5F9;
        font-size: 0.84rem;
    }
    @media (max-width: 640px) {
        .orbyte-activity-row {
            grid-template-columns: minmax(0, 1fr) 150px minmax(0, 0.75fr);
            gap: 8px;
        }
        .orbyte-activity-role,
        .orbyte-activity-logged {
            display: none;
        }
    }
    .orbyte-user-footer {
        display: flex;
        align-items: center;
        gap: 10px;
        padding-top: 12px;
        margin-top: 12px;
        border-top: 1px solid #E5EAF2;
    }
    .orbyte-avatar {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: #0284C7;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.85rem;
    }
    /* Keep card borders from being clipped at fractional zoom / odd window sizes */
    [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stMain"] div[data-testid="stColumn"],
    [data-testid="stMain"] div[data-testid="stHorizontalBlock"],
    [data-testid="stMain"] div[data-testid="stElementContainer"] {
        overflow: visible !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        box-sizing: border-box !important;
    }
    .block-container {
        padding-bottom: 4rem !important;  /* room under the last card */
    }
</style>
""", unsafe_allow_html=True)

def svg_icon(name: str, size: int = 18) -> str:
    """Compact inline SVG icon set for custom HTML UI."""
    paths = {
        "layers": '<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5"/><path d="m3 16 9 5 9-5"/>',
        "briefcase": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 12h18M10 12v2h4v-2"/>',
        "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="10" cy="7" r="4"/><path d="M20 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
        "package": '<path d="m12 3 9 5v8l-9 5-9-5V8l9-5Z"/><path d="m3.3 7.7 8.7 5 8.7-5M12 13v8M7.5 5.5l9 5"/>',
        "bolt": '<path d="m13 2-3 8h7l-6 12 2-9H6l7-11Z"/>',
        "clipboard": '<rect x="5" y="5" width="14" height="16" rx="2"/><path d="M9 5.5V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v1.5M8 11h8M8 15h8"/>',
        "receipt": '<path d="M4 3h16v18l-3-2-3 2-2-2-3 2-2-2-3 2V3Z"/><path d="M8 8h8M8 12h8M8 16h4"/>',
        "chart": '<path d="M4 19V5M4 19h17"/><path d="m7 15 4-4 3 2 6-7"/>',
        "settings": '<circle cx="12" cy="12" r="3"/><path d="m19.4 15 .1.1 1.4 1.1-1.4 2.4-1.7-.7a8 8 0 0 1-1.7 1l-.3 1.8h-2.8l-.3-1.8a8 8 0 0 1-1.7-1l-1.7.7-1.4-2.4L7.3 15a7.5 7.5 0 0 1 0-2l-1.4-1.1 1.4-2.4 1.7.7a8 8 0 0 1 1.7-1l.3-1.8h2.8l.3 1.8a8 8 0 0 1 1.7 1l1.7-.7 1.4 2.4-1.4 1.1a7.5 7.5 0 0 1-.1 2Z"/>',
        "chevron": '<path d="m9 18 6-6-6-6"/>',
        "chevron-down": '<path d="m6 9 6 6 6-6"/>',
        "search": '<circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 4.5 4.5"/>',
        "check-circle": '<circle cx="12" cy="12" r="9"/><path d="m8 12 2.5 2.5L16 9"/>',
        "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
        "external": '<path d="M14 3h7v7M10 14 21 3"/><path d="M19 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h6"/>',
    }
    path = paths.get(name, paths["layers"])
    return (
        f'<span class="orbyte-icon" aria-hidden="true"><svg width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        f'stroke-linecap="round" stroke-linejoin="round" focusable="false">{path}</svg></span>'
    )

FALLBACK_SUPPLIERS = [
    {"supplier_code": "SUP-001", "name": "Selangor EcoPack Sdn Bhd", "category": "Packaging", "products": "Kraft Paper Bowls (500ml/750ml) & Eco Containers", "unit": "per piece", "price_min_rm": 0.38, "price_max_rm": 0.65, "moq": 300, "state": "Selangor", "lead_time_days": 2, "reliability_rating": 4.8, "eco_certified": True, "phone": "+60121419610", "email": "sales@selangor-ecopack.example.com", "tags": "bowls,containers,eco,kraft,paper"},
    {"supplier_code": "SUP-016", "name": "Nusantara Coffee Roasters Sdn Bhd", "category": "F&B Ingredients", "products": "Arabica & Liberica Coffee Beans", "unit": "per kg", "price_min_rm": 38.00, "price_max_rm": 55.00, "moq": 10, "state": "Selangor", "lead_time_days": 2, "reliability_rating": 4.9, "eco_certified": True, "phone": "+60192622631", "email": "sales@nusantara-coffee-roasters.example.com", "tags": "arabica,beans,coffee,liberica"},
]

STOPWORDS = {"and", "with", "the", "of", "for", "per", "box", "set", "boxed", "ml", "kg", "mm"}

@st.cache_data(ttl=30)
def load_supplier_data() -> pd.DataFrame:
    db_url = os.environ.get("DATABASE_URL")
    df = None
    if db_url:
        try:
            import psycopg2
            with psycopg2.connect(db_url) as conn:
                df = pd.read_sql("SELECT * FROM suppliers", conn)
        except Exception:
            pass

    if df is None:
        csv_path = os.path.join(os.path.dirname(__file__), "suppliers.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
        else:
            df = pd.DataFrame(FALLBACK_SUPPLIERS)

    df["eco_certified"] = df["eco_certified"].map(lambda v: str(v).strip().lower() in ("true", "t", "yes", "y", "1"))
    for c in ["price_min_rm", "price_max_rm", "reliability_rating"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["moq", "lead_time_days"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    if "tags" not in df.columns:
        df["tags"] = ""
    df["tags"] = df["tags"].fillna("")
    return df

def _init_state():
    defaults = {
        "audit_logs": {},
        "matched_suppliers": None,
        "draft_rfq_message": "",
        "ai_status_msg": "",
        "last_tenant": None,
        "active_request": None,
        "pending_approvals": [],
        "approved_links": [],
        "tenant_store": {},
        "req_id": None,
        "draft_vendor": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()
suppliers_df = load_supplier_data()

def evaluate_suppliers(df: pd.DataFrame, req: dict) -> pd.DataFrame:
    cat_df = df[df["category"] == req["category"]].copy()
    qty = req["quantity"]
    cat_df["est_min_total"] = (cat_df["price_min_rm"] * qty).round(2)
    cat_df["est_max_total"] = (cat_df["price_max_rm"] * qty).round(2)
    cat_df["Meets_MOQ"] = cat_df["moq"] <= qty
    cat_df["Within_Budget"] = cat_df["est_max_total"] <= req["max_budget_rm"]
    cat_df["Meets_Lead_Time"] = cat_df["lead_time_days"] <= req["max_lead_days"]

    req_words = {
        w for w in re.findall(r"[a-zA-Z]+", req["item_name"].lower())
        if len(w) > 2 and w not in STOPWORDS
    }

    scores, reasons, item_matches = [], [], []

    for _, row in cat_df.iterrows():
        score = 50
        why = []

        prod_words = set(re.findall(r"[a-zA-Z]+", f"{row['products']} {row['tags']}".lower()))
        has_keyword_match = bool(req_words & prod_words) if req_words else True
        item_matches.append(has_keyword_match)

        if has_keyword_match:
            score += 20
            why.append("Exact Item")
        else:
            score -= 30
            why.append("Different Item")

        if row["Meets_MOQ"]:
            score += 15
            why.append("MOQ OK")
        else:
            score -= 25
            why.append(f"MOQ ({row['moq']})")

        if row["Within_Budget"]:
            score += 15
            why.append("In Budget")
        else:
            score -= 20
            why.append("Over Budget")

        score += 10 if row["Meets_Lead_Time"] else -10
        why.append(f"{row['lead_time_days']}d Lead")

        score += int((row["reliability_rating"] - 4.0) * 10)
        if req["prefer_eco"] and bool(row["eco_certified"]):
            score += 5
            why.append("Eco")

        scores.append(max(0, min(100, score)))
        reasons.append(" • ".join(why))

    cat_df["Item_Match"] = item_matches
    cat_df["Match_Score"] = scores
    cat_df["Why_Matched"] = reasons
    return cat_df.sort_values(
        by=["Item_Match", "Within_Budget", "Meets_MOQ", "Meets_Lead_Time", "Match_Score"],
        ascending=[False, False, False, False, False],
    )

MAX_AI_CALLS_PER_SESSION = 30  # Hard stop per browser session
MAX_OUTPUT_TOKENS = 180
MAX_REASONING_OUTPUT_TOKENS = 400  # gpt-oss spends tokens "thinking", so it needs more headroom


def _post_json(url: str, headers: dict, payload: dict) -> dict:
    """Single-shot HTTPS POST helper with zero retries."""
    req_obj = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req_obj, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def generate_rfq_text(top: dict, req: dict, lang: str, tone: int, provider: str, api_key: str, tenant_name: str = "Orbyte Procurement"):
    mins, maxs = top["est_min_total"], top["est_max_total"]

    if "Bahasa Melayu Only" in lang:
        fallback_rfq = f"Hi {top['name']},\n\nKami dari {tenant_name} ingin meminta sebut harga:\n• Item: {req['item_name']}\n• Kuantiti: {req['quantity']}\n• Bajet: RM {mins:.2f} – {maxs:.2f}\nBoleh sahkan stok dan penghantaran dalam {req['max_lead_days']} hari?\n\nTerima kasih.\n{tenant_name}"
    elif "English Only" in lang:
        fallback_rfq = f"Hi {top['name']} Team,\n\nWe found you via Orbyte Hub and would like a quote:\n• Item: {req['item_name']}\n• Quantity: {req['quantity']}\n• Budget: RM {mins:.2f} – {maxs:.2f}\nCan you confirm stock and delivery within {req['max_lead_days']} days?\n\nThank you.\n{tenant_name}"
    else:
        fallback_rfq = f"Salam / Hi {top['name']} Team,\n\nKami ingin meminta sebut harga:\n• Item: {req['item_name']}\n• Quantity: {req['quantity']}\n• Budget: RM {mins:.2f} – {maxs:.2f}\nBoleh sahkan stok dan penghantaran dalam {req['max_lead_days']} hari? / Can you confirm stock and delivery?\n\nThank you / Terima kasih.\n{tenant_name}"

    clean_key = (api_key or "").strip()
    if not clean_key:
        return fallback_rfq, "Using built-in Orbyte template (No API Key entered)."

    # Auto-detect provider from key prefix
    if clean_key.startswith("gsk_"):
        provider = "Groq"
    elif clean_key.startswith("sk-or-"):
        provider = "OpenRouter"
    elif clean_key.startswith("AIza"):
        provider = "Gemini"

    # Guardrail 1: identical request already drafted this session -> reuse it (0 tokens)
    cache_key = f"{provider}|{tenant_name}|{top['name']}|{req['item_name']}|{req['quantity']}|{mins}|{maxs}|{lang}|{tone}"
    cache = st.session_state.setdefault("rfq_cache", {})
    used_calls = st.session_state.get("ai_call_count", 0)
    if cache_key in cache:
        return cache[cache_key], f"Loaded from session cache (0 tokens used • {used_calls}/{MAX_AI_CALLS_PER_SESSION} calls)."

    # Guardrail 2: hard cap on AI calls per session
    if used_calls >= MAX_AI_CALLS_PER_SESSION:
        return fallback_rfq, f"AI call limit reached ({MAX_AI_CALLS_PER_SESSION}/{MAX_AI_CALLS_PER_SESSION}). Using built-in template."

    tone_instruction = "formal" if tone <= 2 else ("friendly" if tone >= 4 else "professional")
    prompt = (
        f"Write a concise WhatsApp RFQ ({lang}, {tone_instruction} tone) to {top['name']} "
        f"for {req['quantity']}x {req['item_name']}, budget RM {mins:.2f}-{maxs:.2f}, "
        f"delivery within {req['max_lead_days']} days. Use 'and' not '&'. "
        f"Sign off as '{tenant_name}'. No placeholders. Plain text only."
    )

    skipped: list[str] = []  # why each model was skipped, shown if everything fails

    def _success(text: str, label: str):
        st.session_state.ai_call_count = used_calls + 1
        cache[cache_key] = text
        return text, f"Drafted with {label} ({st.session_state.ai_call_count}/{MAX_AI_CALLS_PER_SESSION} calls used)."

    def _chat_models(url: str, headers: dict, models: list[str]):
        """OpenAI-style chat call (Groq/OpenRouter). Skips a model if it's retired/missing or returns empty text."""
        for model_name in models:
            is_reasoning = "gpt-oss" in model_name
            body = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.6,
                "max_tokens": MAX_REASONING_OUTPUT_TOKENS if is_reasoning else MAX_OUTPUT_TOKENS,
            }
            if is_reasoning and provider == "Groq":
                body["reasoning_effort"] = "low"  # keeps thinking tokens small
            try:
                data = _post_json(url, headers, body)
                choices = data.get("choices", [])
                text = (choices[0].get("message", {}).get("content") or "").strip() if choices else ""
                if text:
                    return _success(text, f"{provider} ({model_name})")
                skipped.append(f"{model_name}: empty reply")
            except urllib.error.HTTPError as he:
                err_body = he.read().decode("utf-8", errors="ignore").lower()
                if he.code == 404 or (he.code == 400 and any(k in err_body for k in ("decommission", "not found", "does not exist", "not_found"))):
                    skipped.append(f"{model_name}: unavailable (HTTP {he.code})")
                    continue
                raise
        return None

    try:
        result = None

        if provider == "Gemini":
            data = _post_json(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                {
                    "Content-Type": "application/json",
                    "x-goog-api-key": clean_key,  # header, so the key never appears in URLs/logs
                    "User-Agent": "Orbyte-InstaQuote/1.0",
                },
                {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": MAX_OUTPUT_TOKENS, "temperature": 0.6},
                },
            )
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts).strip()
                if text:
                    result = _success(text, "Gemini (gemini-2.0-flash)")
                else:
                    skipped.append("gemini-2.0-flash: empty reply")

        elif provider == "Groq":
            result = _chat_models(
                "https://api.groq.com/openai/v1/chat/completions",
                {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {clean_key}",
                    "User-Agent": "Mozilla/5.0 (compatible; OrbyteInstaQuote/1.0)",
                },
                ["openai/gpt-oss-20b", "llama-3.1-8b-instant", "llama-3.3-70b-versatile", "openai/gpt-oss-120b"]
            )

        elif provider == "OpenRouter":
            # ':free' models only, so a paid credit balance is never touched
            result = _chat_models(
                "https://openrouter.ai/api/v1/chat/completions",
                {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {clean_key}",
                    "HTTP-Referer": "https://orbyte.local",
                    "X-Title": "Orbyte InstaQuote",
                    "User-Agent": "Mozilla/5.0 (compatible; OrbyteInstaQuote/1.0)",
                },
                ["meta-llama/llama-3.3-70b-instruct:free", "google/gemma-3-27b-it:free"],
            )

        if result:
            return result

    except urllib.error.HTTPError as he:
        if he.code in (402, 429):
            return fallback_rfq, f"{provider} quota/rate limit reached (HTTP {he.code}). Using built-in template."
        if he.code in (400, 401, 403):
            return fallback_rfq, f"{provider} rejected the request (HTTP {he.code}); check your API key. Using built-in template."
        if he.code == 404:
            return fallback_rfq, f"{provider} model unavailable (HTTP 404). Using built-in template."
        return fallback_rfq, f"{provider} HTTP {he.code}. Using built-in template."
    except Exception:
        return fallback_rfq, f"{provider} connection problem. Using built-in template."

    return fallback_rfq, f"{provider} returned no text ({'; '.join(skipped) or 'no response'}). Using built-in template."

def add_dispatch(req_id: str, supplier: str, link: str) -> bool:
    """Store a WhatsApp dispatch. Re-approving the same request + vendor replaces it
    instead of adding a duplicate. Returns True if it was a new dispatch."""
    links = st.session_state.approved_links
    is_new = not any(d["req_id"] == req_id and d["supplier"] == supplier for d in links)
    links = [d for d in links if not (d["req_id"] == req_id and d["supplier"] == supplier)]
    links.insert(0, {"req_id": req_id, "supplier": supplier, "link": link})
    st.session_state.approved_links = links[:10]  # bounded, newest first
    return is_new

def current_audit(tenant_id: str) -> list[dict]:
    persisted = orbyte_hub.fetch_activity_log(tenant_id, limit=50)
    return persisted if persisted else st.session_state.audit_logs.get(tenant_id, [])

def record_activity(tenant_id: str, entry: dict):
    st.session_state.audit_logs.setdefault(tenant_id, []).insert(0, entry)
    orbyte_hub.log_activity(tenant_id, entry)

# ---------------------------------------------------------------------------
# SIDEBAR: REPLICA OF ORBYTE LEFT NAVIGATION (image_d9613d.jpg)
# ---------------------------------------------------------------------------
def render_sidebar_controls():
    st.markdown(f"""
        <div class="orbyte-logo-row">
            <div class="orbyte-brand">
                <div class="orbyte-logo-icon">{svg_icon("layers", 19)}</div>
                <span>Orbyte</span>
            </div>
            <span style="color:#94A3B8; font-size:0.9rem;" aria-hidden="true">{svg_icon("chevron-down", 16)}</span>
        </div>
    """, unsafe_allow_html=True)

    tenant_id = st.selectbox(
        ":material/apartment: Current organization",
        options=list(orbyte_hub.TENANTS.keys()),
        format_func=lambda k: orbyte_hub.TENANTS[k]["name"],
    )

    if st.session_state.last_tenant != tenant_id:
        per_tenant_keys = ["active_request", "matched_suppliers", "draft_rfq_message", "draft_vendor", "ai_status_msg", "pending_approvals", "approved_links", "req_id"]
        store = st.session_state.tenant_store
        old = st.session_state.last_tenant
        if old is not None:  # save the organization we're leaving
            store[old] = {k: st.session_state[k] for k in per_tenant_keys}
        saved = store.get(tenant_id)
        if saved:  # restore where we left off
            for k in per_tenant_keys:
                st.session_state[k] = saved[k]
        else:  # first visit to this organization: fresh state
            st.session_state.active_request = orbyte_hub.get_inventory_alert(tenant_id)
            st.session_state.matched_suppliers = None
            st.session_state.draft_rfq_message = ""
            st.session_state.ai_status_msg = ""
            st.session_state.pending_approvals = []
            st.session_state.approved_links = []
            st.session_state.req_id = None
            st.session_state.draft_vendor = None
        st.session_state.last_tenant = tenant_id

    # Orbyte Tree Navigation Menu showing how InstaQuote fits into the Hub
    st.markdown(f"""
        <div class="orbyte-nav-tree">
            <div class="orbyte-nav-item"><span>{svg_icon("briefcase", 17)}&nbsp;Workspace</span>{svg_icon("chevron", 15)}</div>
            <div class="orbyte-nav-item"><span>{svg_icon("users", 17)}&nbsp;Talent Hub</span>{svg_icon("chevron", 15)}</div>
            <div class="orbyte-nav-item" style="color:#0F172A; font-weight:600;"><span>{svg_icon("package", 17)}&nbsp;Procurement Hub</span>{svg_icon("chevron-down", 15)}</div>
            <div class="orbyte-nav-active"><span>{svg_icon("bolt", 17)}&nbsp;InstaQuote RFQ</span><span class="orbyte-nav-current" aria-label="Current page"></span></div>
            <div class="orbyte-nav-sub">{svg_icon("clipboard", 16)}&nbsp;Vendor Directory</div>
            <div class="orbyte-nav-sub">{svg_icon("receipt", 16)}&nbsp;Purchase Orders</div>
            <div class="orbyte-nav-item"><span>{svg_icon("chart", 17)}&nbsp;Reports</span>{svg_icon("chevron", 15)}</div>
            <div class="orbyte-nav-item"><span>{svg_icon("settings", 17)}&nbsp;Settings</span>{svg_icon("chevron", 15)}</div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    role_options = ["Staff (Draft Only)", "SME Owner / Manager (Approver)"]
    current_role = st.selectbox(
        "Active Role (RBAC)",
        options=role_options,
        index=0,  # always start as Staff (Draft Only)
        key=f"role_{tenant_id}",  # resets to Staff whenever you switch organization
    )
    is_approver = "Approver" in current_role

    with st.expander(":material/psychology: AI Co-Pilot Settings", expanded=False):
        provider = st.selectbox("LLM Provider", ["Gemini", "Groq", "OpenRouter"])
        api_key = st.text_input(
            "API Key (Session-Only, Never Saved)",
            type="password",
            placeholder="Optional (uses template)",
            autocomplete="off",
        )

    return tenant_id, is_approver, provider, api_key


with st.sidebar:
    with st.container(key="sidebar-scroll-content"):
        tenant_id, is_approver, provider, api_key = render_sidebar_controls()

    tenant_name = orbyte_hub.TENANTS[tenant_id]["name"]
    role_badge = "Owner (Approver)" if is_approver else "Staff (Drafter)"
    with st.container(key="sidebar-account-footer"):
        st.markdown(f"""
            <div class="orbyte-user-footer">
                <div class="orbyte-avatar">{tenant_name[:2].upper()}</div>
                <div style="line-height:1.3;">
                    <div style="font-size:0.82rem; font-weight:600; color:#0F172A;">{tenant_name[:20]}</div>
                    <div style="font-size:0.72rem; color:#64748B;">{role_badge}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# MAIN ORBYTE DASHBOARD HEADER (Matches image_d9613d.jpg)
# ---------------------------------------------------------------------------
req = st.session_state.active_request
today_str = datetime.now().strftime("%A, %d %B %Y")

st.markdown(f"""
<div style="margin-bottom: 1.25rem;">
    <h1 style="font-size: 1.65rem; font-weight: 700; color: #0F172A; margin: 0; padding: 0;">Dashboard</h1>
    <div style="font-size: 0.84rem; color: #64748B; margin-top: 4px;">{today_str}</div>
    <div style="font-size: 0.92rem; color: #475569; margin-top: 8px;">
        Good day, <strong style="color: #0F172A;">{orbyte_hub.TENANTS[tenant_id]['name']}</strong>. Here's what needs your attention today.
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TOP CARD: ORBYTE TRIGGER BANNER (Replica of "On leave today" Card)
# ---------------------------------------------------------------------------
matched_count = len(st.session_state.matched_suppliers) if st.session_state.matched_suppliers is not None else 0

st.markdown(f"""
<div class="orbyte-card">
    <div style="display:flex; justify-content:space-between; align-items:center; padding-bottom:14px; border-bottom:1px solid #F1F5F9;">
        <div style="display:flex; align-items:center; gap:14px;">
            <div style="background:#EFF6FF; color:#0284C7; width:42px; height:42px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:1.2rem; font-weight:700;">
                {svg_icon("package", 21)}
            </div>
            <div>
                <div style="display:flex; align-items:center;">
                    <span style="font-weight:600; font-size:0.98rem; color:#0F172A;">Low-stock procurement trigger</span>
                    <span class="orbyte-badge-gray">{req.get('trigger_source', 'Inventory Alert')}</span>
                </div>
                <div style="font-size:0.82rem; color:#64748B; margin-top:2px;">
                    Automated supplier matching & WhatsApp RFQ dispatch • Saves ~42 mins per order
                </div>
            </div>
        </div>
    </div>
    <div style="display:flex; align-items:center; gap:14px; padding-top:14px;">
        <div style="background:#ECFDF5; color:#10B981; width:36px; height:36px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.95rem; font-weight:700;">
            ✓
        </div>
        <div>
            <div style="font-weight:600; font-size:0.86rem; color:#0F172A;">
                Active Alert: {req['quantity']} units of {req['item_name']} (Max Budget: RM {req['max_budget_rm']:.2f})
            </div>
            <div style="font-size:0.8rem; color:#64748B;">
                Status: <strong>{req.get('status', 'Triggered')}</strong> • {matched_count} verified Malaysian suppliers evaluated • Max lead time: {req['max_lead_days']} days
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# SECOND CARD: PENDING ACTIONS WORKSPACE (Replica of "Pending Actions" Card)
# ---------------------------------------------------------------------------
pending_count = len(st.session_state.pending_approvals)

# Hide "Matched" entries entirely (also covers ones already saved earlier in the session or DB)
audit_entries = [e for e in current_audit(tenant_id) if e.get("Status") != "Matched"]

# Current state of each (request + vendor). audit_entries are newest-first,
# so the first entry we see for a pair is its latest status.
vendor_latest = {}
for e in audit_entries:
    vendor_latest.setdefault((e.get("ID"), e.get("Item")), e)

filter_items = {
    "All": audit_entries,
    "Pending Approval": [e for e in vendor_latest.values() if e.get("Status") == "Pending Approval"],
    "Completed": [e for e in vendor_latest.values() if e.get("Status") != "Pending Approval"],
}

# Safety: if the saved filter no longer exists (e.g. "Match" from before), fall back to All
if st.session_state.get("action_filter") not in filter_items:
    st.session_state.action_filter = "All"

with st.container(border=True):
    st.markdown('<div style="font-weight:700; font-size:1.02rem; color:#0F172A;">Pending Actions</div>', unsafe_allow_html=True)
    c_search, c_filter, c_role = st.columns([1.4, 2.4, 1.2], vertical_alignment="center")
    with c_search:
        search_q = st.text_input("Search", placeholder="Search procurement requests...",
                                label_visibility="collapsed", key="action_search")
    with c_filter:
        active_filter = st.radio("Filter", list(filter_items), horizontal=True,
                                label_visibility="collapsed", key="action_filter",
                                format_func=lambda f: f"{f} ({len(filter_items[f])})")
    with c_role:
        st.markdown(
            f'<div style="border:1px solid #E2E8F0; border-radius:8px; padding:5px 12px; font-size:0.8rem; color:#475569; font-weight:500; text-align:center;">'
            f'Role: <strong>{"Owner (Approver)" if is_approver else "Staff (Draft Only)"}</strong></div>',
            unsafe_allow_html=True,
        )

# Rows shown in "My Submissions & Activity Log"
visible_entries = filter_items[active_filter]
q = search_q.strip().lower()
if q:
    visible_entries = [e for e in visible_entries if q in " ".join(str(v) for v in e.values()).lower()]
# ---------------------------------------------------------------------------
# STEP 1 & STEP 2: SOURCING FORM & RECOMMENDED SUPPLIERS
# ---------------------------------------------------------------------------
col_left, col_right = st.columns([1, 1.45], gap="medium")

with col_left:
    with st.container(border=True):
        st.markdown("""
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
                <span style="background:#EFF6FF; color:#0284C7; padding:4px 8px; border-radius:6px; font-weight:700; font-size:0.8rem;">1</span>
                <span style="font-weight:600; font-size:0.95rem; color:#0F172A;">Sourcing Requirements</span>
                <span class="orbyte-badge-gray">Connected Inventory</span>
            </div>
        """, unsafe_allow_html=True)

        categories = ["Packaging", "F&B Ingredients", "Store Operations"]
        cat_idx = categories.index(req["category"]) if req["category"] in categories else 0
        category = st.selectbox("Category", categories, index=cat_idx)

        cat_df = suppliers_df[suppliers_df["category"] == category]
        product_options = sorted(cat_df["products"].unique().tolist())

        default_idx = 0
        for idx_opt, prod_name in enumerate(product_options):
            if req["item_name"].lower() in prod_name.lower() or prod_name.lower() in req["item_name"].lower():
                default_idx = idx_opt
                break

        with st.form("trigger_form", border=False):
            item_name = st.selectbox("Item Needed", options=product_options, index=default_idx)
            c1, c2 = st.columns(2)
            with c1:
                quantity = st.number_input("Quantity", 1, 10000, int(req["quantity"]))
                max_lead_days = st.slider("Max Lead Time (Days)", 1, 7, int(req["max_lead_days"]))
            with c2:
                max_budget_rm = st.number_input("Max Budget (RM)", 10.0, 50000.0, float(req["max_budget_rm"]), step=10.0)
                prefer_eco = st.checkbox(":material/eco: Prioritize Eco-Certified", value=req["prefer_eco"])

            run = st.form_submit_button(":material/search: Evaluate & Rank Suppliers", type="primary", use_container_width=True)

        if run:
            st.session_state.req_id = f"REQ-{random.randint(1000, 9999)}"
            st.session_state.active_request.update({
                "category": category, "item_name": item_name, "quantity": quantity,
                "max_budget_rm": max_budget_rm, "max_lead_days": max_lead_days,
                "prefer_eco": prefer_eco, "status": "Matched"
            })
            ranked = evaluate_suppliers(suppliers_df, st.session_state.active_request)
            st.session_state.matched_suppliers = ranked
            st.session_state.draft_rfq_message = ""
            st.session_state.approved_link = None
            st.rerun()

with col_right:
    with st.container(border=True):
        st.markdown(f"""
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="background:#EFF6FF; color:#0284C7; padding:4px 8px; border-radius:6px; font-weight:700; font-size:0.8rem;">2</span>
                    <span style="font-weight:600; font-size:0.95rem; color:#0F172A;">Recommended Suppliers</span>
                    <span class="orbyte-badge-gray">{matched_count} Matches</span>
                </div>
                <span style="font-size:0.78rem; color:#0284C7; font-weight:500;">Explainable Scoring Active</span>
            </div>
        """, unsafe_allow_html=True)

        if st.session_state.matched_suppliers is not None and not st.session_state.matched_suppliers.empty:
            display = st.session_state.matched_suppliers.rename(columns={
                "name": "Supplier",
                "Match_Score": "Score",
                "Why_Matched": "Decision Rationale",
                "est_min_total": "Min (RM)",
                "est_max_total": "Max (RM)",
                "moq": "MOQ",
                "lead_time_days": "Lead (d)",
                "state": "State",
                "eco_certified": "Eco"
            })[["Supplier", "Score", "Decision Rationale", "Min (RM)", "Max (RM)", "MOQ", "Lead (d)", "State", "Eco"]]

            st.dataframe(
                display,
                column_config={
                    "Score": st.column_config.ProgressColumn("Match Score", min_value=0, max_value=100, format="%d"),
                    "Min (RM)": st.column_config.NumberColumn("Min (RM)", format="RM %.2f"),
                    "Max (RM)": st.column_config.NumberColumn("Max (RM)", format="RM %.2f"),
                },
                use_container_width=True,
                hide_index=True,
                height=310,
            )
        else:
            st.info("Click **Evaluate & Rank Suppliers** on the left to run the decision engine against your inventory alert.")

# ---------------------------------------------------------------------------
# STEP 3 & STEP 4: HUMAN APPROVAL & AUDIT LOG (Replica of "My Submissions" List)
# ---------------------------------------------------------------------------
col_approve, col_outcome = st.columns([1, 1.45], gap="medium")

with col_approve:
    with st.container(border=True):
        st.markdown(f"""
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
                <span style="background:#EFF6FF; color:#0284C7; padding:4px 8px; border-radius:6px; font-weight:700; font-size:0.8rem;">3</span>
                <span style="font-weight:600; font-size:0.95rem; color:#0F172A;">RFQ Draft & Human Approval</span>
                <span class="orbyte-badge-gray">{pending_count} Pending</span>
            </div>
        """, unsafe_allow_html=True)

        # OWNER INBOX
        if is_approver and st.session_state.pending_approvals:
            st.warning(f":material/notifications: **{len(st.session_state.pending_approvals)}** staff submission(s) due for your review.")
            pending_options = [
                f"{p['req_id']} — {p['supplier']['name']} ({p['req']['quantity']}x)"
                for p in st.session_state.pending_approvals
            ]
            selected_pending_idx = st.selectbox(
                "Select submission to approve:",
                options=range(len(pending_options)),
                format_func=lambda i: pending_options[i],
                index=len(pending_options) - 1,  # newest submission first
            )
            selected_pending = st.session_state.pending_approvals[selected_pending_idx]

            final_message = st.text_area(
                "WhatsApp RFQ Message:",
                value=selected_pending["message"],
                height=155,
                key=f"owner_edit_{selected_pending['req_id']}_{abs(hash(selected_pending['message']))}",
            )

            c_app, c_rej = st.columns(2)
            with c_app:
                if st.button(":material/check_circle: Approve & Dispatch :material/open_in_new:", type="primary", use_container_width=True):
                    digits = re.sub(r"\D", "", str(selected_pending["supplier"].get("phone", "")))
                    add_dispatch(
                        selected_pending["req_id"],
                        selected_pending["supplier"]["name"],
                        f"https://wa.me/{digits}?text={quote(final_message)}",
                    )
                    record_activity(tenant_id, {
                        "ID": selected_pending["req_id"],
                        "Role": "Owner",
                        "Action": "Approved & Dispatched RFQ",
                        "Item": selected_pending["supplier"]["name"],
                        "Status": "Approved"
                    })
                    st.session_state.pending_approvals.pop(selected_pending_idx)
                    if st.session_state.req_id == selected_pending["req_id"]:
                        st.session_state.active_request["status"] = "Approved"
                    st.rerun()
            with c_rej:
                if st.button(":material/close: Reject", type="secondary", use_container_width=True):
                    record_activity(tenant_id, {
                        "ID": selected_pending["req_id"],
                        "Role": "Owner",
                        "Action": "Rejected Draft",
                        "Item": selected_pending["supplier"]["name"],
                        "Status": "Rejected"
                    })
                    st.session_state.pending_approvals.pop(selected_pending_idx)
                    st.rerun()

        # STAFF / OWNER DIRECT DRAFTING
        elif st.session_state.matched_suppliers is not None and not st.session_state.matched_suppliers.empty:
            records = st.session_state.matched_suppliers.to_dict("records")
            idx = st.selectbox(
                "Select vendor for quotation:",
                options=range(len(records)),
                format_func=lambda i: f"[{records[i]['Match_Score']} pts] {records[i]['name']} (RM {records[i]['est_min_total']:.2f}–{records[i]['est_max_total']:.2f})"
            )
            chosen = records[idx]

            # A draft belongs to the vendor it was written for. Switching vendor clears it.
            if st.session_state.draft_vendor != chosen["name"]:
                st.session_state.draft_rfq_message = ""
                st.session_state.ai_status_msg = ""
                st.session_state.draft_vendor = chosen["name"]

            c_lang, c_tone = st.columns(2)
            with c_lang:
                lang_choice = st.selectbox("Language", ["English + Bahasa Melayu", "English Only", "Bahasa Melayu Only"])
            with c_tone:
                tone_choice = st.select_slider(
                    "Tone",
                    options=[1, 2, 3, 4, 5],
                    value=3,
                    format_func=lambda x: {1: "Formal", 2: "Pro", 3: "Standard", 4: "Friendly", 5: "Casual"}[x],
                )

            if st.button(":material/auto_awesome: Generate RFQ Draft", type="secondary", use_container_width=True):
                with st.spinner("Drafting quotation request..."):
                    text, status_msg = generate_rfq_text(chosen, st.session_state.active_request, lang_choice, tone_choice, provider, api_key, tenant_name)
                    st.session_state.draft_rfq_message = text
                    st.session_state.ai_status_msg = status_msg
                    st.rerun()

            if st.session_state.ai_status_msg:
                st.caption(st.session_state.ai_status_msg)

            edited_rfq = st.text_area("WhatsApp RFQ Message:", value=st.session_state.draft_rfq_message, height=145)
            st.session_state.draft_rfq_message = edited_rfq

            if not is_approver:
                is_pending_here = any(
                    p["req_id"] == st.session_state.req_id and p["supplier"]["name"] == chosen["name"]
                    for p in st.session_state.pending_approvals
                    )
                if is_pending_here:
                    st.warning(":material/schedule: Pending Owner approval.")
                    if st.button("Withdraw Submission", type="secondary", use_container_width=True):
                        st.session_state.pending_approvals = [
                            p for p in st.session_state.pending_approvals
                            if not (p["req_id"] == st.session_state.req_id and p["supplier"]["name"] == chosen["name"])
                            ]
                        st.session_state.active_request["status"] = "Cancelled"
                        record_activity(tenant_id, {
                            "ID": st.session_state.req_id,
                            "Role": "Staff",
                            "Action": "Withdrew Request",
                            "Item": chosen["name"],
                            "Status": "Cancelled"
                        })
                        st.rerun()
                else:
                    if st.button(":material/send: Submit for Owner Approval :material/open_in_new:", type="primary", use_container_width=True):
                        if not edited_rfq.strip():
                            st.error("Click 'Generate RFQ Draft' first.")
                        else:
                            st.session_state.pending_approvals.append({
                                "req_id": st.session_state.req_id,
                                "req": st.session_state.active_request.copy(),
                                "supplier": chosen.copy(),
                                "message": edited_rfq,
                            })
                            st.session_state.active_request["status"] = "Pending Approval"
                            record_activity(tenant_id, {
                                "ID": st.session_state.req_id,
                                "Role": "Staff",
                                "Action": "Submitted RFQ Draft",
                                "Item": chosen["name"],
                                "Status": "Pending Approval"
                            })
                            st.rerun()
            else:
                if st.button(":material/check_circle: Approve & Open WhatsApp :material/open_in_new:", type="primary", use_container_width=True):
                    if not edited_rfq.strip():
                        st.error("Click 'Generate RFQ Draft' first.")
                    else:
                        digits = re.sub(r"\D", "", str(chosen.get("phone", "")))
                        is_new = add_dispatch(
                            st.session_state.req_id,
                            chosen["name"],
                            f"https://wa.me/{digits}?text={quote(edited_rfq)}",
                        )
                        st.session_state.active_request["status"] = "Approved"
                        if is_new:  # only log the first approval, not repeat clicks
                            record_activity(tenant_id, {
                                "ID": st.session_state.req_id,
                                "Role": "Owner",
                                "Action": "Approved & Dispatched RFQ",
                                "Item": chosen["name"],
                                "Status": "Approved"
                            })
                        st.rerun()
        else:
            st.caption("Evaluate suppliers in Step 1 to begin drafting an RFQ.")

with col_outcome:
    with st.container(border=True):
        st.markdown(f"""
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="background:#EFF6FF; color:#0284C7; padding:4px 8px; border-radius:6px; font-weight:700; font-size:0.8rem;">4</span>
                    <span style="font-weight:600; font-size:0.95rem; color:#0F172A;">My Submissions & Activity Log</span>
                    <span class="orbyte-badge-gray">{len(audit_entries)}</span>
                    <span style="font-size:0.8rem; color:#0284C7; font-weight:500;">Due from you</span>
                </div>
                <span style="font-size:0.8rem; color:#64748B;">⌃</span>
            </div>
        """, unsafe_allow_html=True)

        for dispatch in st.session_state.approved_links[:5]:  # newest first
            st.markdown(f"""
            <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:10px; padding:12px 16px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-weight:600; font-size:0.88rem; color:#065F46;">{svg_icon("check-circle", 16)} WhatsApp RFQ Ready for Dispatch</div>
                    <div style="font-size:0.78rem; color:#047857;">{dispatch['req_id'].lower()} • {dispatch['supplier']} • Approved by SME Owner</div>
                </div>
                <a href="{dispatch['link']}" target="_blank" style="background:#059669; color:white; text-decoration:none; padding:7px 14px; border-radius:8px; font-size:0.82rem; font-weight:600;">
                    Open WhatsApp {svg_icon("external", 14)}
                </a>
            </div>
            """, unsafe_allow_html=True)

        # Render Activity Log Rows in the exact style of Orbyte's "My Submissions" table!
        if visible_entries:
            shown = visible_entries[:10]
            for n, item in enumerate(shown):
                is_last = n == len(shown) - 1
                req_id_txt = item.get("ID", "REQ-001")
                role_txt = item.get("Role", "You")
                action_txt = item.get("Action", "Submission")
                vendor_txt = item.get("Item", "Supplier")
                status_txt = item.get("Status", "Pending")
                ts_txt = item.get("Timestamp", "Today, " + datetime.now().strftime("%I:%M %p"))

                badge_class = "orbyte-status-approved" if "Approved" in status_txt or "Sent" in status_txt else "orbyte-status-pending"

                st.markdown(f"""
                <div class="orbyte-activity-row" style="{'border-bottom:none;' if is_last else ''}">
                    <div>
                        <div style="font-weight:600; color:#0F172A;">{action_txt}</div>
                        <div style="font-size:0.76rem; color:#64748B;">{req_id_txt.lower()} • {vendor_txt}</div>
                    </div>
                    <div class="orbyte-activity-role" style="color:#64748B; font-size:0.8rem;">{role_txt}</div>
                    <div>
                        <span class="{badge_class}">{svg_icon("clock", 14)} {status_txt}</span>
                    </div>
                    <div style="color:#334155; font-size:0.8rem;">{ts_txt}</div>
                    <div class="orbyte-activity-logged" style="text-align:right; color:#0284C7; font-weight:600; font-size:0.8rem;">
                        Logged {svg_icon("external", 12)}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        elif audit_entries:
            st.caption("No requests match your search or filter.")
        else:
            st.markdown("""
            <div style="padding:18px 4px; color:#64748B; font-size:0.84rem;">
                No procurement submissions recorded today. Run a supplier match on the left to log your first activity.
            </div>
            """, unsafe_allow_html=True)