"""
Orbyte InstaQuote: Smart SME Supplier Match & WhatsApp RFQ Automation
SDC Hackathon 2026 — Domain 2 (Orbyte Smart SME Challenge)
"""
import os
import re
import random
from datetime import datetime
from urllib.parse import quote

import pandas as pd
import streamlit as st

import orbyte_hub

# --- Provider SDKs ---
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from openai import OpenAI
    OPENROUTER_AVAILABLE = True
except ImportError:
    OPENROUTER_AVAILABLE = False

st.set_page_config(
    page_title="Orbyte | Smart SME Procurement Hub",
    page_icon="💠",
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

    /* Orbyte Outlined Secondary Button (Like "View leave calendar ↗" in screenshot) */
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
        padding-left: 24px;
        font-size: 0.83rem;
        color: #64748B;
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
    }
    .orbyte-status-approved {
        background: #DCFCE7;
        color: #15803D;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.76rem;
        font-weight: 600;
        display: inline-block;
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
</style>
""", unsafe_allow_html=True)

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
        "chosen_supplier": None,
        "pending_approvals": [],
        "approved_link": None,
        "req_id": None,
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

    scores = []
    reasons = []
    item_matches = []

    for _, row in cat_df.iterrows():
        score = 50
        why = []

        prod_words = set(re.findall(r"[a-zA-Z]+", f"{row['products']} {row['tags']}".lower()))
        has_keyword_match = bool(req_words & prod_words) if req_words else True
        item_matches.append(has_keyword_match)

        if has_keyword_match:
            score += 20
            why.append("🎯 Exact Item")
        else:
            score -= 30
            why.append("⚠️ Diff Item")

        if row["Meets_MOQ"]:
            score += 15
            why.append("✅ MOQ OK")
        else:
            score -= 25
            why.append(f"❌ MOQ ({row['moq']})")

        if row["Within_Budget"]:
            score += 15
            why.append("✅ In Budget")
        else:
            score -= 20
            why.append("❌ Over Budget")

        if row["Meets_Lead_Time"]:
            score += 10
            why.append(f"🚚 {row['lead_time_days']}d Lead")
        else:
            score -= 10
            why.append(f"⏳ {row['lead_time_days']}d Lead")

        score += int((row["reliability_rating"] - 4.0) * 10)
        if req["prefer_eco"] and bool(row["eco_certified"]):
            score += 5
            why.append("🌱 Eco")

        scores.append(max(0, min(100, score)))
        reasons.append(" • ".join(why))

    cat_df["Item_Match"] = item_matches
    cat_df["Match_Score"] = scores
    cat_df["Why_Matched"] = reasons
    return cat_df.sort_values(
        by=["Item_Match", "Within_Budget", "Meets_MOQ", "Meets_Lead_Time", "Match_Score"],
        ascending=[False, False, False, False, False],
    )

def generate_rfq_text(top: dict, req: dict, lang: str, tone: int, provider: str, api_key: str):
    mins, maxs = top["est_min_total"], top["est_max_total"]
    
    if "Bahasa Melayu Only" in lang:
        fallback_rfq = f"Hi {top['name']},\n\nKami dari Orbyte Hub ingin meminta sebut harga:\n• Item: {req['item_name']}\n• Kuantiti: {req['quantity']}\n• Bajet: RM {mins:.2f} – {maxs:.2f}\nBoleh sahkan stok dan penghantaran dalam {req['max_lead_days']} hari?\n\nTerima kasih."
    elif "English Only" in lang:
        fallback_rfq = f"Hi {top['name']} Team,\n\nWe found you via Orbyte Hub and would like a quote:\n• Item: {req['item_name']}\n• Quantity: {req['quantity']}\n• Budget: RM {mins:.2f} – {maxs:.2f}\nCan you confirm stock and delivery within {req['max_lead_days']} days?\n\nThank you."
    else:
        fallback_rfq = f"Salam / Hi {top['name']} Team,\n\nKami ingin meminta sebut harga:\n• Item: {req['item_name']}\n• Quantity: {req['quantity']}\n• Budget: RM {mins:.2f} – {maxs:.2f}\nBoleh sahkan stok dan penghantaran dalam {req['max_lead_days']} hari? / Can you confirm stock and delivery?\n\nThank you / Terima kasih."

    if not api_key:
        return fallback_rfq, "⚠️ Using built-in Orbyte template (No API Key provided)."
        
    tone_instruction = "formal and professional" if tone <= 2 else ("friendly and casual" if tone >= 4 else "standard business")
    
    prompt = (
        f"You are an SME procurement assistant. Write a short WhatsApp Request for Quotation (RFQ).\n"
        f"Language: {lang}\n"
        f"Tone: {tone_instruction}\n"
        f"Supplier: {top['name']}\n"
        f"Item: {req['quantity']} x {req['item_name']}\n"
        f"Budget: RM {mins:.2f} to {maxs:.2f}\n"
        f"Delivery constraint: {req['max_lead_days']} days\n\n"
        f"CRITICAL INSTRUCTIONS:\n"
        f"- You MUST include the item, quantity, budget, and delivery constraint.\n"
        f"- Use the word 'and' instead of '&'.\n"
        f"- DO NOT use placeholders like [Your Name] or [Company]. Sign off as 'Orbyte Procurement'.\n"
        f"- Output ONLY the message text, no markdown."
    )

    try:
        if provider == "Gemini" and GEMINI_AVAILABLE:
            client = genai.Client(api_key=api_key)
            for model_name in ["gemini-2.5-flash", "gemini-2.0-flash"]:
                try:
                    response = client.models.generate_content(model=model_name, contents=prompt)
                    if response and response.text:
                        text = response.text.strip()
                        if len(text.split()) > 15:
                            return text, f"✅ Drafted with Gemini ({model_name})."
                except Exception:
                    continue
            return fallback_rfq, "❌ Gemini busy. Using template."

        elif provider == "Groq" and GROQ_AVAILABLE:
            client = Groq(api_key=api_key)
            chat_completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=600,
            )
            text = chat_completion.choices[0].message.content
            if text and len(text.split()) > 15:
                return text.strip(), "✅ Drafted with Groq (Llama 3.3 70B)."
            return fallback_rfq, "⚠️ Groq cut off message. Using template."

        elif provider == "OpenRouter" and OPENROUTER_AVAILABLE:
            client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
            response = client.chat.completions.create(
                model="deepseek/deepseek-chat:free",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=600,
            )
            text = response.choices[0].message.content
            if text and len(text.split()) > 15:
                return text.strip(), "✅ Drafted with OpenRouter (DeepSeek)."
            return fallback_rfq, "⚠️ OpenRouter cut off message. Using template."

    except Exception as e:
        return fallback_rfq, f"❌ {provider} Error: {str(e)}"

    return fallback_rfq, "⚠️ Provider SDK not available."

def current_audit(tenant_id: str) -> list[dict]:
    persisted = orbyte_hub.fetch_activity_log(tenant_id, limit=50)
    return persisted if persisted else st.session_state.audit_logs.get(tenant_id, [])

def record_activity(tenant_id: str, entry: dict):
    st.session_state.audit_logs.setdefault(tenant_id, []).insert(0, entry)
    orbyte_hub.log_activity(tenant_id, entry)

# ---------------------------------------------------------------------------
# SIDEBAR: REPLICA OF ORBYTE LEFT NAVIGATION (image_d9613d.jpg)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
        <div class="orbyte-logo-row">
            <div class="orbyte-brand">
                <div class="orbyte-logo-icon">O</div>
                <span>Orbyte</span>
            </div>
            <span style="color:#94A3B8; font-size:0.9rem;">◧</span>
        </div>
    """, unsafe_allow_html=True)

    tenant_id = st.selectbox(
        "🏢 Current organization",
        options=list(orbyte_hub.TENANTS.keys()),
        format_func=lambda k: orbyte_hub.TENANTS[k]["name"],
    )

    if st.session_state.last_tenant != tenant_id:
        st.session_state.last_tenant = tenant_id
        st.session_state.active_request = orbyte_hub.get_inventory_alert(tenant_id)
        st.session_state.matched_suppliers = None
        st.session_state.draft_rfq_message = ""
        st.session_state.ai_status_msg = ""
        st.session_state.pending_approvals = []
        st.session_state.approved_link = None
        st.session_state.req_id = None

    # Orbyte Tree Navigation Menu showing how InstaQuote fits into the Hub
    st.markdown("""
        <div class="orbyte-nav-tree">
            <div class="orbyte-nav-item"><span>🧰 &nbsp;Workspace</span><span>›</span></div>
            <div class="orbyte-nav-item"><span>👥 &nbsp;Talent Hub</span><span>›</span></div>
            <div class="orbyte-nav-item" style="color:#0F172A; font-weight:600;"><span>📦 &nbsp;Procurement Hub</span><span>⌄</span></div>
            <div class="orbyte-nav-active"><span>⚡ InstaQuote RFQ</span><span>●</span></div>
            <div class="orbyte-nav-sub">📋 &nbsp;Vendor Directory</div>
            <div class="orbyte-nav-sub">🧾 &nbsp;Purchase Orders</div>
            <div class="orbyte-nav-item"><span>📊 &nbsp;Reports</span><span>›</span></div>
            <div class="orbyte-nav-item"><span>⚙️ &nbsp;Settings</span><span>›</span></div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    role_options = ["Staff (Draft Only)", "SME Owner / Manager (Approver)"]
    role_default = orbyte_hub.get_role(tenant_id)
    role_index = 1 if "Owner" in role_default else 0
    current_role = st.selectbox("Active Role (RBAC)", options=role_options, index=role_index)
    is_approver = "Approver" in current_role

    with st.expander("🤖 AI Co-Pilot Settings", expanded=False):
        provider = st.selectbox("LLM Provider", ["Gemini", "Groq", "OpenRouter"])
        api_key = st.text_input("API Key", type="password", placeholder="Optional (uses template)")

    tenant_name = orbyte_hub.TENANTS[tenant_id]["name"]
    role_badge = "Owner (Approver)" if is_approver else "Staff (Drafter)"
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
                📦
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
        <div style="border:1px solid #CBD5E1; border-radius:8px; padding:6px 14px; font-size:0.82rem; font-weight:600; color:#0284C7; background:#FFFFFF;">
            SDG 8 & 12 Aligned ↗
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
audit_entries = current_audit(tenant_id)
total_actions = pending_count + (1 if matched_count > 0 else 0)

st.markdown(f"""
<div class="orbyte-card" style="margin-bottom: 12px; padding-bottom: 14px;">
    <div style="font-weight:700; font-size:1.02rem; color:#0F172A; margin-bottom:14px;">Pending Actions</div>
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
        <div style="display:flex; align-items:center; gap:8px; flex:1;">
            <div style="border:1px solid #E2E8F0; border-radius:8px; padding:6px 14px; color:#94A3B8; font-size:0.83rem; width:260px; background:#F8FAFC;">
                🔍 Search procurement requests...
            </div>
            <span class="orbyte-pill-active">All ({total_actions})</span>
            <span class="orbyte-pill-inactive">Match ({matched_count})</span>
            <span class="orbyte-pill-inactive">Pending Approval ({pending_count})</span>
            <span class="orbyte-pill-inactive">Completed ({len(audit_entries)})</span>
        </div>
        <div style="border:1px solid #E2E8F0; border-radius:8px; padding:5px 12px; font-size:0.8rem; color:#475569; font-weight:500;">
            Role: <strong>{"Owner (Approver)" if is_approver else "Staff (Draft Only)"}</strong>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

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
                prefer_eco = st.checkbox("🌱 Prioritize Eco-Certified", value=req["prefer_eco"])

            run = st.form_submit_button("🔍 Evaluate & Rank Suppliers", type="primary", use_container_width=True)

        if run:
            st.session_state.req_id = f"REQ-{random.randint(1000, 9999)}"
            st.session_state.active_request.update({
                "category": category, "item_name": item_name, "quantity": quantity,
                "max_budget_rm": max_budget_rm, "max_lead_days": max_lead_days,
                "prefer_eco": prefer_eco, "status": "Matched"
            })
            ranked = evaluate_suppliers(suppliers_df, st.session_state.active_request)
            st.session_state.matched_suppliers = ranked
            st.session_state.chosen_supplier = None
            st.session_state.draft_rfq_message = ""
            st.session_state.approved_link = None
            record_activity(tenant_id, {
                "ID": st.session_state.req_id,
                "Role": "System",
                "Action": f"Matched {len(ranked)} vendors",
                "Item": f"{quantity}x {item_name[:22]}",
                "Status": "Matched"
            })
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
            st.warning(f"🔔 **{len(st.session_state.pending_approvals)}** staff submission(s) due for your review.")
            pending_options = [
                f"{p['req_id']} — {p['supplier']['name']} ({p['req']['quantity']}x)"
                for p in st.session_state.pending_approvals
            ]
            selected_pending_idx = st.selectbox(
                "Select submission to approve:",
                options=range(len(pending_options)),
                format_func=lambda i: pending_options[i],
            )
            selected_pending = st.session_state.pending_approvals[selected_pending_idx]

            final_message = st.text_area(
                "WhatsApp RFQ Message:",
                value=selected_pending["message"],
                height=155,
                key="owner_edit",
            )

            c_app, c_rej = st.columns(2)
            with c_app:
                if st.button("✅ Approve & Dispatch ↗", type="primary", use_container_width=True):
                    digits = re.sub(r"\D", "", str(selected_pending["supplier"].get("phone", "")))
                    st.session_state.approved_link = f"https://wa.me/{digits}?text={quote(final_message)}"
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
                if st.button("❌ Reject", type="secondary", use_container_width=True):
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
            st.session_state.chosen_supplier = chosen

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

            if st.button("✨ Generate RFQ Draft", type="secondary", use_container_width=True):
                with st.spinner("Drafting quotation request..."):
                    text, status_msg = generate_rfq_text(chosen, st.session_state.active_request, lang_choice, tone_choice, provider, api_key)
                    st.session_state.draft_rfq_message = text
                    st.session_state.ai_status_msg = status_msg
                    st.rerun()

            if st.session_state.ai_status_msg:
                st.caption(st.session_state.ai_status_msg)

            edited_rfq = st.text_area("WhatsApp RFQ Message:", value=st.session_state.draft_rfq_message, height=145)
            st.session_state.draft_rfq_message = edited_rfq

            if not is_approver:
                if st.session_state.active_request.get("status") == "Pending Approval":
                    st.warning("⏳ Pending Owner approval.")
                    if st.button("Withdraw Submission", type="secondary", use_container_width=True):
                        st.session_state.pending_approvals = [
                            p for p in st.session_state.pending_approvals if p["req_id"] != st.session_state.req_id
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
                    if st.button("📨 Submit for Owner Approval ↗", type="primary", use_container_width=True):
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
                if st.button("✅ Approve & Open WhatsApp ↗", type="primary", use_container_width=True):
                    if not edited_rfq.strip():
                        st.error("Click 'Generate RFQ Draft' first.")
                    else:
                        digits = re.sub(r"\D", "", str(chosen.get("phone", "")))
                        st.session_state.approved_link = f"https://wa.me/{digits}?text={quote(edited_rfq)}"
                        st.session_state.active_request["status"] = "Approved"
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

        if st.session_state.approved_link:
            st.markdown(f"""
            <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:10px; padding:12px 16px; margin-bottom:14px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-weight:600; font-size:0.88rem; color:#065F46;">✅ WhatsApp RFQ Ready for Dispatch</div>
                    <div style="font-size:0.78rem; color:#047857;">Approved by SME Owner • Pre-filled quotation link generated</div>
                </div>
                <a href="{st.session_state.approved_link}" target="_blank" style="background:#059669; color:white; text-decoration:none; padding:7px 14px; border-radius:8px; font-size:0.82rem; font-weight:600;">
                    Open WhatsApp ↗
                </a>
            </div>
            """, unsafe_allow_html=True)

        # Render Activity Log Rows in the exact style of Orbyte's "My Submissions" table!
        if audit_entries:
            for item in audit_entries[:6]:
                req_id_txt = item.get("ID", "REQ-001")
                role_txt = item.get("Role", "You")
                action_txt = item.get("Action", "Submission")
                vendor_txt = item.get("Item", "Supplier")
                status_txt = item.get("Status", "Pending")
                ts_txt = item.get("Timestamp", "Today, " + datetime.now().strftime("%I:%M %p"))

                badge_class = "orbyte-status-approved" if "Approved" in status_txt or "Sent" in status_txt else "orbyte-status-pending"

                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; padding:11px 4px; border-bottom:1px solid #F1F5F9; font-size:0.84rem;">
                    <div style="flex:1.6;">
                        <div style="font-weight:600; color:#0F172A;">{action_txt}</div>
                        <div style="font-size:0.76rem; color:#64748B;">{req_id_txt.lower()} • {vendor_txt}</div>
                    </div>
                    <div style="flex:0.6; color:#64748B; font-size:0.8rem;">{role_txt}</div>
                    <div style="flex:0.9;">
                        <span class="{badge_class}">⏱ {status_txt}</span>
                    </div>
                    <div style="flex:0.9; color:#334155; font-size:0.8rem;">{ts_txt}</div>
                    <div style="flex:0.7; text-align:right; color:#0284C7; font-weight:600; font-size:0.8rem;">
                        Logged ↗
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="padding:18px 4px; color:#64748B; font-size:0.84rem;">
                No procurement submissions recorded today. Run a supplier match on the left to log your first activity.
            </div>
            """, unsafe_allow_html=True)