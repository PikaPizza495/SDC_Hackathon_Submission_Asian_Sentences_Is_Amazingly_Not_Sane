"""
Orbyte InstaQuote: Smart SME Supplier Match & WhatsApp RFQ Automation
SDC Hackathon 2026 — Domain 2 (Orbyte Smart SME Challenge)
"""
import os
import re
import random
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
    page_title="Orbyte InstaQuote | Smart SME Supplier Hub",
    page_icon="📦",
    layout="wide",
)

# --- Custom B2B SaaS CSS (Stripe / Linear Aesthetic) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* 3. Light Grey App Background */
    .stApp {
        background-color: #F8FAFC;
        color: #0F172A;
    }

    /* 4. Sleek Navigation Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }
    section[data-testid="stSidebar"] h2 {
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        letter-spacing: -0.02em;
    }
    section[data-testid="stSidebar"] label {
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #475569 !important;
    }

    /* 1. Professional Deep Blue Primary Buttons */
    div.stButton > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(180deg, #1E40AF 0%, #1E3A8A 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #1E3A8A !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.55rem 1rem !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
        transition: all 0.15s ease-in-out !important;
    }
    div.stButton > button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        background: linear-gradient(180deg, #1D4ED8 0%, #1E40AF 100%) !important;
        box-shadow: 0 4px 12px rgba(30, 64, 175, 0.25) !important;
        transform: translateY(-1px);
    }

    /* Secondary Buttons */
    div.stButton > button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
        transition: all 0.15s ease-in-out !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #F8FAFC !important;
        border-color: #94A3B8 !important;
    }

    /* 2. Crisp White Cards around st.metric, st.dataframe, and Forms */
    div[data-testid="stMetric"],
    div[data-testid="stDataFrame"],
    div[data-testid="stForm"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 1.25rem !important;
        box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 1px 2px -1px rgba(15, 23, 42, 0.02) !important;
    }

    div[data-testid="stDataFrame"] {
        padding: 0.5rem !important;
        overflow: hidden;
    }

    h1, h2, h3 {
        color: #0F172A !important;
        letter-spacing: -0.025em;
        font-weight: 700 !important;
    }
    hr {
        border-color: #E2E8F0 !important;
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

        # 1. Product / Keyword Relevance Check
        prod_words = set(re.findall(r"[a-zA-Z]+", f"{row['products']} {row['tags']}".lower()))
        has_keyword_match = bool(req_words & prod_words) if req_words else True
        item_matches.append(has_keyword_match)

        if has_keyword_match:
            score += 20
            why.append("🎯 Exact Item")
        else:
            score -= 30
            why.append("⚠️ Diff Item")

        # 2. MOQ Check
        if row["Meets_MOQ"]:
            score += 15
            why.append("✅ MOQ OK")
        else:
            score -= 25
            why.append(f"❌ MOQ ({row['moq']})")

        # 3. Budget Check
        if row["Within_Budget"]:
            score += 15
            why.append("✅ In Budget")
        else:
            score -= 20
            why.append("❌ Over Budget")

        # 4. Lead Time Check
        if row["Meets_Lead_Time"]:
            score += 10
            why.append(f"🚚 {row['lead_time_days']}d Lead")
        else:
            score -= 10
            why.append(f"⏳ {row['lead_time_days']}d Lead")

        # 5. Reliability & Eco Bonus
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
        return fallback_rfq, "⚠️ Using built-in template (No API Key)."
        
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
            return fallback_rfq, "❌ Gemini Error (all models busy). Using fallback template."

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
            return fallback_rfq, "⚠️ Groq cut off the message. Using template instead."

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
            return fallback_rfq, "⚠️ OpenRouter cut off the message. Using template."

    except Exception as e:
        return fallback_rfq, f"❌ {provider} Error: {str(e)}"

    return fallback_rfq, "⚠️ Provider SDK not installed or available."

def current_audit(tenant_id: str) -> list[dict]:
    persisted = orbyte_hub.fetch_activity_log(tenant_id, limit=50)
    return persisted if persisted else st.session_state.audit_logs.get(tenant_id, [])

def record_activity(tenant_id: str, entry: dict):
    st.session_state.audit_logs.setdefault(tenant_id, []).insert(0, entry)
    orbyte_hub.log_activity(tenant_id, entry)

# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🏢 Orbyte Hub")
    st.caption("Smart SME Procurement")
    st.divider()

    tenant_id = st.selectbox(
        "Business Profile",
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

    st.divider()
    role_options = ["Staff (Draft Only)", "SME Owner / Manager (Approver)"]
    role_default = orbyte_hub.get_role(tenant_id)
    role_index = 1 if "Owner" in role_default else 0
    current_role = st.selectbox("Role", options=role_options, index=role_index)
    is_approver = "Approver" in current_role
    
    if is_approver:
        st.success("✅ Owner Mode Active")
    else:
        st.info("🔒 Staff Mode (Draft Only)")

    st.divider()
    st.markdown("### 🤖 AI Provider")
    provider = st.selectbox("Choose API", ["Gemini", "Groq", "OpenRouter"])
    api_key = st.text_input("API Key", type="password", placeholder="Optional (uses template if blank)")

# ---------------------------------------------------------------------------
# MAIN UI & METRIC CARDS
# ---------------------------------------------------------------------------
st.title("📦 InstaQuote: Smart Supplier Match & RFQ")

req = st.session_state.active_request

# Top SaaS Metric Bar (Demonstrates Trigger, Control, and Measurable Benefit)
m1, m2, m3, m4 = st.columns(4)
m1.metric("⚡ Hub Trigger", req.get("trigger_source", "Inventory Alert"), "Connected Data")
m2.metric("🔔 Pending Approvals", str(len(st.session_state.pending_approvals)), "Owner Inbox")
m3.metric("⏱️ Est. Time Saved", "42 mins / RFQ", "vs Manual Sourcing")
m4.metric("🌱 Sustainability Fit", "SDG 8 & SDG 12", "Eco-Supplier Priority")

st.write("")

col_left, col_right = st.columns([1, 1.3], gap="large")

with col_left:
    st.subheader("1. What do you need?")
    
    categories = ["Packaging", "F&B Ingredients", "Store Operations"]
    cat_idx = categories.index(req["category"]) if req["category"] in categories else 0
    category = st.selectbox("Category", categories, index=cat_idx)
    
    cat_df = suppliers_df[suppliers_df["category"] == category]
    product_options = sorted(cat_df["products"].unique().tolist())
    
    # Smart fallback matching if preset name is a substring of the full product name
    default_idx = 0
    for idx_opt, prod_name in enumerate(product_options):
        if req["item_name"].lower() in prod_name.lower() or prod_name.lower() in req["item_name"].lower():
            default_idx = idx_opt
            break
        
    with st.form("trigger_form"):
        item_name = st.selectbox("Item Needed", options=product_options, index=default_idx)
        c1, c2 = st.columns(2)
        with c1:
            quantity = st.number_input("Quantity", 1, 10000, int(req["quantity"]))
            max_lead_days = st.slider("Max Delivery Days", 1, 7, int(req["max_lead_days"]))
        with c2:
            max_budget_rm = st.number_input("Max Budget (RM)", 10.0, 50000.0, float(req["max_budget_rm"]), step=10.0)
            prefer_eco = st.checkbox("Prioritize Eco-Friendly", value=req["prefer_eco"])
            
        run = st.form_submit_button("🔍 Find Suppliers", type="primary", use_container_width=True)

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
            "Action": f"Matched {len(ranked)} suppliers",
            "Item": f"{quantity}x {item_name}",
            "Status": "🔍 Matched"
        })
        st.rerun()

with col_right:
    st.subheader("2. Recommended Suppliers")
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
                "Score": st.column_config.ProgressColumn("Match Score", min_value=0, max_value=100, format="%d/100"),
                "Min (RM)": st.column_config.NumberColumn("Min (RM)", format="RM %.2f"),
                "Max (RM)": st.column_config.NumberColumn("Max (RM)", format="RM %.2f"),
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Click **Find Suppliers** on the left to evaluate and rank verified Malaysian vendors.")

st.divider()

# ---------------------------------------------------------------------------
# APPROVAL & OUTCOME
# ---------------------------------------------------------------------------
col_approve, col_outcome = st.columns([1, 1.3], gap="large")

with col_approve:
    st.subheader("3. Review & Send")
    
    # ---------------------------------------------------------
    # OWNER INBOX (Shows if there are pending approvals)
    # ---------------------------------------------------------
    if is_approver and st.session_state.pending_approvals:
        st.warning(f"🔔 You have **{len(st.session_state.pending_approvals)}** staff draft(s) waiting for approval.")
        
        pending_options = [
            f"{p['req_id']} | {p['supplier']['name']} ({p['req']['quantity']}x {p['req']['item_name']})"
            for p in st.session_state.pending_approvals
        ]
        selected_pending_idx = st.selectbox(
            "Select draft to review:",
            options=range(len(pending_options)),
            format_func=lambda i: pending_options[i],
        )
        
        selected_pending = st.session_state.pending_approvals[selected_pending_idx]
        
        st.markdown("---")
        st.write(f"**Supplier:** {selected_pending['supplier']['name']} ({selected_pending['supplier']['state']})")
        st.caption(f"Rationale: {selected_pending['supplier'].get('Why_Matched', 'Verified Supplier')}")
        
        final_message = st.text_area("Review message before dispatch:", value=selected_pending["message"], height=180, key="owner_edit")
        
        c_app, c_rej = st.columns(2)
        with c_app:
            if st.button("✅ Approve & Open WhatsApp", type="primary", use_container_width=True):
                digits = re.sub(r"\D", "", str(selected_pending["supplier"].get("phone", "")))
                st.session_state.approved_link = f"https://wa.me/{digits}?text={quote(final_message)}"
                
                record_activity(tenant_id, {
                    "ID": selected_pending["req_id"],
                    "Role": "Owner",
                    "Action": "Approved & Dispatched RFQ",
                    "Item": selected_pending["supplier"]["name"],
                    "Status": "✅ Sent"
                })
                
                st.session_state.pending_approvals.pop(selected_pending_idx)
                if st.session_state.req_id == selected_pending["req_id"]:
                    st.session_state.active_request["status"] = "Approved"
                st.rerun()
        with c_rej:
            if st.button("❌ Reject Draft", type="secondary", use_container_width=True):
                record_activity(tenant_id, {
                    "ID": selected_pending["req_id"],
                    "Role": "Owner",
                    "Action": "Rejected Draft",
                    "Item": selected_pending["supplier"]["name"],
                    "Status": "❌ Rejected"
                })
                st.session_state.pending_approvals.pop(selected_pending_idx)
                st.rerun()

    # ---------------------------------------------------------
    # DRAFTING VIEW (Staff or Owner Direct Drafting)
    # ---------------------------------------------------------
    elif st.session_state.matched_suppliers is not None and not st.session_state.matched_suppliers.empty:
        records = st.session_state.matched_suppliers.to_dict("records")
        idx = st.selectbox(
            "Choose a supplier",
            options=range(len(records)),
            format_func=lambda i: f"[{records[i]['Match_Score']}/100] {records[i]['name']} — RM {records[i]['est_min_total']:.2f}–{records[i]['est_max_total']:.2f}"
        )
        chosen = records[idx]
        st.session_state.chosen_supplier = chosen
        
        st.markdown("---")
        c_lang, c_tone = st.columns([1, 1])
        with c_lang:
            lang_choice = st.selectbox("Language", ["English + Bahasa Melayu", "English Only", "Bahasa Melayu Only"])
        with c_tone:
            tone_choice = st.select_slider(
                "Tone",
                options=[1, 2, 3, 4, 5],
                value=3,
                format_func=lambda x: {1: "Formal", 2: "Professional", 3: "Standard", 4: "Friendly", 5: "Casual"}[x]
            )
            
        if st.button("✨ Generate Draft Message", type="secondary", use_container_width=True):
            with st.spinner("Drafting RFQ..."):
                text, status_msg = generate_rfq_text(chosen, st.session_state.active_request, lang_choice, tone_choice, provider, api_key)
                st.session_state.draft_rfq_message = text
                st.session_state.ai_status_msg = status_msg
                st.rerun()

        if st.session_state.ai_status_msg:
            if "Error" in st.session_state.ai_status_msg:
                st.error(st.session_state.ai_status_msg)
            elif "⚠️" in st.session_state.ai_status_msg:
                st.warning(st.session_state.ai_status_msg)
            else:
                st.success(st.session_state.ai_status_msg)

        edited_rfq = st.text_area("Message to send:", value=st.session_state.draft_rfq_message, height=180)
        st.session_state.draft_rfq_message = edited_rfq

        # ROLE-BASED ACTION CONTROLS
        if not is_approver:
            if st.session_state.active_request.get("status") == "Pending Approval":
                st.warning("⏳ This request is waiting for Owner approval.")
                if st.button("❌ Withdraw Request", type="secondary", use_container_width=True):
                    st.session_state.pending_approvals = [
                        p for p in st.session_state.pending_approvals if p["req_id"] != st.session_state.req_id
                    ]
                    st.session_state.active_request["status"] = "Cancelled"
                    record_activity(tenant_id, {
                        "ID": st.session_state.req_id,
                        "Role": "Staff",
                        "Action": "Withdrew Request",
                        "Item": chosen["name"],
                        "Status": "❌ Cancelled"
                    })
                    st.rerun()
            elif st.session_state.active_request.get("status") == "Approved":
                st.success("✅ This request was approved by the Owner.")
            else:
                if st.button("📨 Submit to Owner for Approval", type="primary", use_container_width=True):
                    if not edited_rfq.strip():
                        st.error("Please click 'Generate Draft Message' first.")
                    else:
                        request_obj = {
                            "req_id": st.session_state.req_id,
                            "req": st.session_state.active_request.copy(),
                            "supplier": chosen.copy(),
                            "message": edited_rfq
                        }
                        st.session_state.pending_approvals.append(request_obj)
                        st.session_state.active_request["status"] = "Pending Approval"
                        record_activity(tenant_id, {
                            "ID": st.session_state.req_id,
                            "Role": "Staff",
                            "Action": "Submitted for approval",
                            "Item": chosen["name"],
                            "Status": "⏳ Pending"
                        })
                        st.rerun()
        else:
            # Allow Owner to also approve & send directly without switching to Staff first!
            if st.button("✅ Approve & Open WhatsApp Directly (Owner Override)", type="primary", use_container_width=True):
                if not edited_rfq.strip():
                    st.error("Please click 'Generate Draft Message' first.")
                else:
                    digits = re.sub(r"\D", "", str(chosen.get("phone", "")))
                    st.session_state.approved_link = f"https://wa.me/{digits}?text={quote(edited_rfq)}"
                    st.session_state.active_request["status"] = "Approved"
                    record_activity(tenant_id, {
                        "ID": st.session_state.req_id,
                        "Role": "Owner",
                        "Action": "Direct Approved & Sent",
                        "Item": chosen["name"],
                        "Status": "✅ Sent"
                    })
                    st.rerun()
    else:
        st.info("Match suppliers in Step 1 to draft and route an RFQ.")

with col_outcome:
    st.subheader("4. Outcome & Audit Log")
    
    if st.session_state.approved_link:
        st.success("✅ RFQ Approved! Click the link below to launch WhatsApp with the pre-filled quote request.")
        st.markdown(f"### [👉 Click here to open WhatsApp]({st.session_state.approved_link})")
    else:
        st.info("Once an Owner approves a request, the pre-filled WhatsApp dispatch link appears here.")

    st.markdown("#### Persistent Tenant Activity Log")
    entries = current_audit(tenant_id)
    if entries:
        log_df = pd.DataFrame(entries)
        cols = [c for c in ["Timestamp", "ID", "Role", "Action", "Item", "Status"] if c in log_df.columns]
        st.dataframe(log_df[cols] if cols else log_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No activity recorded for this tenant yet.")

st.divider()
with st.expander("🛡️ Orbyte Hub Architecture, RBAC Governance & Malaysia PDPA Compliance"):
    st.markdown("""
    * **Connected Hub Architecture:** Supplier catalog (`suppliers` table) is shared across the Orbyte ecosystem, while inventory triggers, budgets, and audit logs (`audit_log` table) are strictly isolated per `tenant_id`.
    * **Human-in-the-Loop Governance:** Staff accounts (`Draft Only`) can evaluate suppliers and draft RFQs, but consequential external communications require explicit `SME Owner / Manager` approval.
    * **Malaysia PDPA Compliance:** All demo records use synthetic business contact data (`@example.com`). In production, vendor representatives' personal data is processed under commercial contract necessity, encrypted at rest in PostgreSQL, and never used to train external AI models.
    """)