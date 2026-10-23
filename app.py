"""
Orbyte InstaQuote: Smart SME Supplier Match & WhatsApp RFQ Automation
SDC Hackathon 2026 — Domain 2 (Orbyte Smart SME Challenge)

Runs locally on CSV; on Replit it reads suppliers from PostgreSQL via DATABASE_URL.
Audit entries persist to the audit_log table when DATABASE_URL is set,
otherwise they stay in session state.
"""
import os
import re
from datetime import datetime
from urllib.parse import quote

import pandas as pd
import streamlit as st

import orbyte_hub

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


st.set_page_config(
    page_title="Orbyte InstaQuote | Smart SME Supplier Hub",
    page_icon="📦",
    layout="wide",
)

FALLBACK_SUPPLIERS = [
    {"supplier_code": "SUP-001", "name": "Selangor EcoPack Sdn Bhd", "category": "Packaging",
     "products": "Kraft Paper Bowls (500ml/750ml) & Eco Containers", "unit": "per piece",
     "price_min_rm": 0.38, "price_max_rm": 0.65, "moq": 300, "state": "Selangor",
     "lead_time_days": 2, "reliability_rating": 4.8, "eco_certified": True,
     "phone": "+60121419610", "email": "sales@selangor-ecopack.example.com",
     "tags": "bowls,containers,eco,kraft,paper"},
    {"supplier_code": "SUP-002", "name": "KL Metro Box Trading", "category": "Packaging",
     "products": "Kraft Paper Bowls & Takeaway Boxes", "unit": "per piece",
     "price_min_rm": 0.30, "price_max_rm": 0.52, "moq": 500, "state": "Kuala Lumpur",
     "lead_time_days": 3, "reliability_rating": 4.1, "eco_certified": False,
     "phone": "+60175108603", "email": "sales@kl-metro-box.example.com",
     "tags": "bowls,boxes,kraft,paper,takeaway"},
    {"supplier_code": "SUP-016", "name": "Nusantara Coffee Roasters Sdn Bhd", "category": "F&B Ingredients",
     "products": "Arabica & Liberica Coffee Beans", "unit": "per kg",
     "price_min_rm": 38.00, "price_max_rm": 55.00, "moq": 10, "state": "Selangor",
     "lead_time_days": 2, "reliability_rating": 4.9, "eco_certified": True,
     "phone": "+60192622631", "email": "sales@nusantara-coffee-roasters.example.com",
     "tags": "arabica,beans,coffee,liberica"},
    {"supplier_code": "SUP-028", "name": "SmartPOS Thermal Malaysia", "category": "Store Operations",
     "products": "80mm Thermal Receipt Rolls (Box of 50)", "unit": "per box",
     "price_min_rm": 60.00, "price_max_rm": 70.00, "moq": 2, "state": "Kuala Lumpur",
     "lead_time_days": 1, "reliability_rating": 4.6, "eco_certified": False,
     "phone": "+60173728882", "email": "sales@smartpos-thermal-malaysia.example.com",
     "tags": "receipt,rolls,thermal"},
]


@st.cache_data(ttl=30)
def load_supplier_data() -> pd.DataFrame:
    db_url = os.environ.get("DATABASE_URL")
    df = None
    if db_url:
        try:
            import psycopg2
            with psycopg2.connect(db_url) as conn:
                df = pd.read_sql("SELECT * FROM suppliers", conn)
        except Exception as e:
            st.warning(f"DB read failed ({type(e).__name__}); falling back to CSV.")

    if df is None:
        csv_path = os.path.join(os.path.dirname(__file__), "suppliers.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
        else:
            df = pd.DataFrame(FALLBACK_SUPPLIERS)

    df["eco_certified"] = df["eco_certified"].map(
        lambda v: str(v).strip().lower() in ("true", "t", "yes", "y", "1")
    )
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
        "ai_explanation": "",
        "selected_supplier_row": None,
        "last_tenant": None,
        "active_request": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()
suppliers_df = load_supplier_data()


def _request_terms(item_name: str) -> list[str]:
    words = re.findall(r"[a-zA-Z]+", item_name.lower())
    return [w for w in words if len(w) > 2]


def _tag_overlap(tags: str, terms: list[str]) -> int:
    row = {t.strip() for t in str(tags).split(",") if t.strip()}
    return len(row & set(terms))


def evaluate_suppliers(df: pd.DataFrame, req: dict) -> pd.DataFrame:
    terms = _request_terms(req["item_name"])
    cat_df = df[df["category"] == req["category"]].copy()
    cat_df["tag_overlap"] = cat_df["tags"].apply(lambda t: _tag_overlap(t, terms))

    overlap_df = cat_df[cat_df["tag_overlap"] > 0]
    sub = overlap_df if not overlap_df.empty else cat_df
    if sub.empty:
        sub = df.copy()
        sub["tag_overlap"] = 0

    qty = req["quantity"]
    sub["est_min_total"] = (sub["price_min_rm"] * qty).round(2)
    sub["est_max_total"] = (sub["price_max_rm"] * qty).round(2)
    sub["Meets_MOQ"] = sub["moq"] <= qty
    sub["Within_Budget"] = sub["est_max_total"] <= req["max_budget_rm"]
    sub["Meets_Lead_Time"] = sub["lead_time_days"] <= req["max_lead_days"]

    scores, notes = [], []
    for _, row in sub.iterrows():
        score, reasons = 50, []
        if row["Meets_MOQ"]:
            score += 15
            reasons.append(f"MOQ OK ({row['moq']} ≤ {qty})")
        else:
            score -= 25
            reasons.append(f"MOQ too high ({row['moq']} > {qty})")

        if row["Within_Budget"]:
            score += 15
            savings = req["max_budget_rm"] - row["est_max_total"]
            reasons.append(f"Fits budget (≤ RM {row['est_max_total']:.2f})")
        else:
            score -= 20
            reasons.append(f"Over budget at worst case (RM {row['est_max_total']:.2f})")

        if row["Meets_Lead_Time"]:
            score += 10
            reasons.append(f"{int(row['lead_time_days'])}d lead time")
        else:
            score -= 10
            reasons.append(f"Slow ({int(row['lead_time_days'])}d)")

        score += int((row["reliability_rating"] - 4.0) * 10)
        if req["prefer_eco"] and bool(row["eco_certified"]):
            score += 5
            reasons.append("Eco-certified (SDG 12)")

        if row["tag_overlap"] > 0:
            bonus = min(15, int(row["tag_overlap"]) * 4)
            score += bonus
            reasons.append(f"Product match ×{int(row['tag_overlap'])}")

        scores.append(max(0, min(100, score)))
        notes.append(" | ".join(reasons))

    sub["Match_Score"] = scores
    sub["Rule_Evaluation"] = notes
    return sub.sort_values(
        by=["Within_Budget", "Meets_MOQ", "Meets_Lead_Time", "Match_Score"],
        ascending=[False, False, False, False],
    )


def generate_ai_rfq_and_explanation(top: dict, req: dict, api_key: str) -> tuple[str, str]:
    mins, maxs = top["est_min_total"], top["est_max_total"]
    savings = req["max_budget_rm"] - maxs
    fallback_explanation = (
        f"**Top match:** `{top['name']}` scored **{top['Match_Score']}/100**. "
        f"MOQ {top['moq']} ≤ {req['quantity']}, delivers in "
        f"{int(top['lead_time_days'])} day(s) to {top['state']}, "
        f"estimated **RM {mins:.2f} – {maxs:.2f}** (max-case savings "
        f"RM {savings:.2f} under budget)."
    )
    fallback_rfq = (
        f"Salam / Hi {top['name']} Team,\n\n"
        f"We are reaching out via the Orbyte Smart SME Hub with a quotation request:\n"
        f"• Item: {req['item_name']}\n"
        f"• Quantity: {req['quantity']} × {top.get('unit', 'unit')}\n"
        f"• Indicative price range seen: RM {mins:.2f} – {maxs:.2f}\n"
        f"• Required delivery: within {req['max_lead_days']} days to the Klang Valley\n\n"
        f"Boleh sahkan stok sedia ada dan tarikh penghantaran terdekat? / "
        f"Could you confirm stock availability and send an official quotation?\n\n"
        f"Thank you,\nProcurement (via Orbyte Hub)"
    )
    if not api_key or not GEMINI_AVAILABLE:
        return fallback_explanation, fallback_rfq
    try:
        client = genai.Client(api_key=api_key)
        prompt = (
            f"You are an SME procurement assistant inside the Malaysian Orbyte Business Hub.\n"
            f"Request: {req['quantity']} × {req['item_name']}, budget RM {req['max_budget_rm']:.2f}, "
            f"max lead {req['max_lead_days']} days.\n"
            f"Top supplier: {top['name']} ({top['state']}), price range RM {mins:.2f} – {maxs:.2f}, "
            f"MOQ {top['moq']}, lead {int(top['lead_time_days'])} days, eco: {top['eco_certified']}.\n\n"
            f"Write a short, polite WhatsApp RFQ ({req['language']}) under 110 words."
        )
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        if resp and resp.text:
            return fallback_explanation + " *(drafted with Gemini)*", resp.text.strip()
    except Exception as e:
        return fallback_explanation + f" *(Gemini unavailable: {type(e).__name__})*", fallback_rfq
    return fallback_explanation, fallback_rfq


def current_audit(tenant_id: str) -> list[dict]:
    persisted = orbyte_hub.fetch_activity_log(tenant_id, limit=50)
    if persisted:
        return persisted
    return st.session_state.audit_logs.get(tenant_id, [])


def record_activity(tenant_id: str, entry: dict):
    st.session_state.audit_logs.setdefault(tenant_id, []).insert(0, entry)
    orbyte_hub.log_activity(tenant_id, entry)


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🏢 Orbyte Business Hub")
    st.caption("Domain 2: Less Busywork, Better Business")
    st.divider()

    st.markdown("### 🏬 Tenant (Simulated Hub Login)")
    tenant_id = st.selectbox(
        "Active SME",
        options=list(orbyte_hub.TENANTS.keys()),
        format_func=lambda k: orbyte_hub.TENANTS[k]["name"],
    )
    st.caption("Same matching engine, same shared supplier directory, different tenant context.")

    if st.session_state.last_tenant != tenant_id:
        st.session_state.last_tenant = tenant_id
        st.session_state.active_request = orbyte_hub.get_inventory_alert(tenant_id)
        st.session_state.matched_suppliers = None
        st.session_state.draft_rfq_message = ""
        st.session_state.ai_explanation = ""
        st.session_state.selected_supplier_row = None

    st.divider()
    st.markdown("### 🔐 Role & Permissions (RBAC)")
    role_options = [
        "Staff (Junior Purchaser — Draft Only)",
        "SME Owner / Manager (Approver)",
    ]
    role_default = orbyte_hub.get_role(tenant_id)
    current_role = st.selectbox(
        "Active Orbyte User Role",
        options=role_options,
        index=role_options.index(role_default) if role_default in role_options else 0,
    )
    is_approver = "Owner" in current_role
    st.success("✅ Approver mode active." if is_approver else "🔒 Staff mode: Owner approval required.")

    st.divider()
    st.markdown("### 🤖 Gemini API Key (Optional)")
    gemini_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        placeholder="Leave blank for built-in template",
    )

    st.divider()
    st.markdown("### 📊 SDG Fit")
    st.markdown(
        "- **SDG 8 (8.2, 8.3):** SME productivity\n"
        "- **SDG 12:** Eco-supplier prioritization\n"
        "- **PDPA:** 100% synthetic data"
    )


# ---------------------------------------------------------------------------
# MAIN HEADER + 5-STEP BANNER
# ---------------------------------------------------------------------------
st.title("📦 Orbyte InstaQuote — Smart SME Supplier Match & RFQ Automation")
st.markdown(
    "Matches micro-enterprises with local suppliers, checks MOQ + budget + lead time, "
    "drafts a bilingual WhatsApp RFQ, and enforces owner approval before dispatch."
)

cols = st.columns(5)
for col, (title, desc) in zip(cols, [
    ("1️⃣ Trigger", "Inventory alert or staff request"),
    ("2️⃣ Connected Data", "SME constraints + shared supplier directory"),
    ("3️⃣ Decision Logic", "Rules filter + AI draft"),
    ("4️⃣ Human Approval", "Owner RBAC sign-off"),
    ("5️⃣ Visible Outcome", "WhatsApp dispatch + audit log"),
]):
    with col:
        st.info(f"**{title}**\n\n{desc}")

st.divider()

# ---------------------------------------------------------------------------
# STEPS 1-3
# ---------------------------------------------------------------------------
col_left, col_right = st.columns([1.05, 1.25], gap="large")

with col_left:
    st.subheader("1️⃣ Step 1: Trigger")
    st.caption(f"Source: `{st.session_state.active_request['trigger_source']}`")

    if st.button("⚡ Reload Tenant Preset Alert", use_container_width=True):
        st.session_state.active_request = orbyte_hub.get_inventory_alert(tenant_id)
        st.session_state.matched_suppliers = None
        st.rerun()

    req = st.session_state.active_request
    with st.form("trigger_form"):
        category = st.selectbox(
            "Category",
            ["Packaging", "F&B Ingredients", "Store Operations"],
            index=["Packaging", "F&B Ingredients", "Store Operations"].index(req["category"]),
        )
        item_name = st.text_input("Item Needed", value=req["item_name"])
        c1, c2 = st.columns(2)
        with c1:
            quantity = st.number_input("Quantity", 1, 10000, int(req["quantity"]))
            max_lead_days = st.slider("Max Lead Time (Days)", 1, 7, int(req["max_lead_days"]))
        with c2:
            max_budget_rm = st.number_input("Max Budget (RM)", 10.0, 50000.0,
                                            float(req["max_budget_rm"]), step=10.0)
            prefer_eco = st.checkbox("Prioritize Eco-Certified (SDG 12)", value=req["prefer_eco"])
        language = st.selectbox(
            "RFQ Language",
            ["English + Bahasa Melayu", "English Only", "Bahasa Melayu Only"],
            index=["English + Bahasa Melayu", "English Only", "Bahasa Melayu Only"].index(req["language"]),
        )
        run = st.form_submit_button("🔍 Run Match & Draft", type="primary", use_container_width=True)

    if run:
        st.session_state.active_request = {
            "trigger_source": req["trigger_source"],
            "category": category,
            "item_name": item_name,
            "quantity": quantity,
            "max_budget_rm": max_budget_rm,
            "max_lead_days": max_lead_days,
            "prefer_eco": prefer_eco,
            "language": language,
            "status": "Matched — Pending Approval",
        }
        ranked = evaluate_suppliers(suppliers_df, st.session_state.active_request)
        st.session_state.matched_suppliers = ranked
        top = ranked.iloc[0].to_dict()
        st.session_state.selected_supplier_row = top
        expl, rfq = generate_ai_rfq_and_explanation(top, st.session_state.active_request, gemini_key)
        st.session_state.ai_explanation, st.session_state.draft_rfq_message = expl, rfq
        record_activity(tenant_id, {
            "User_Role": current_role,
            "Action": "Matched suppliers & drafted RFQ",
            "Item_Request": f"{item_name} × {quantity} (RM {max_budget_rm:.2f})",
            "Supplier_Selected": top["name"],
            "Total_Est_RM": f"{top['est_min_total']:.2f} – {top['est_max_total']:.2f}",
            "Status": "Awaiting Approval",
        })

with col_right:
    st.subheader("2️⃣–3️⃣ Connected Data & Decision Logic")

    if st.session_state.matched_suppliers is None:
        ranked = evaluate_suppliers(suppliers_df, st.session_state.active_request)
        st.session_state.matched_suppliers = ranked
        top = ranked.iloc[0].to_dict()
        st.session_state.selected_supplier_row = top
        expl, rfq = generate_ai_rfq_and_explanation(top, st.session_state.active_request, gemini_key)
        st.session_state.ai_explanation, st.session_state.draft_rfq_message = expl, rfq

    matched_df = st.session_state.matched_suppliers
    st.markdown(st.session_state.ai_explanation)

    display = matched_df.rename(columns={
        "name": "Supplier", "Match_Score": "Score", "est_min_total": "Est Min (RM)",
        "est_max_total": "Est Max (RM)", "moq": "MOQ", "lead_time_days": "Lead (d)",
        "state": "State", "eco_certified": "Eco", "Rule_Evaluation": "Why",
    })[["Supplier", "Score", "Est Min (RM)", "Est Max (RM)", "MOQ", "Lead (d)", "State", "Eco", "Why"]]
    st.dataframe(display, use_container_width=True, hide_index=True)

    with st.expander(f"📂 View full shared supplier directory ({len(suppliers_df)} suppliers)"):
        st.dataframe(
            suppliers_df.rename(columns={
                "supplier_code": "Code", "name": "Supplier", "category": "Category",
                "products": "Products", "unit": "Unit", "price_min_rm": "Min (RM)",
                "price_max_rm": "Max (RM)", "moq": "MOQ", "state": "State",
                "lead_time_days": "Lead (d)", "reliability_rating": "Rating",
                "eco_certified": "Eco", "phone": "Phone", "email": "Email",
            })[["Code", "Supplier", "Category", "Products", "Min (RM)", "Max (RM)",
                "MOQ", "State", "Lead (d)", "Rating", "Eco"]],
            use_container_width=True, hide_index=True,
        )

st.divider()

# ---------------------------------------------------------------------------
# STEPS 4-5
# ---------------------------------------------------------------------------
col_approve, col_outcome = st.columns([1.05, 1.25], gap="large")

with col_approve:
    st.subheader("4️⃣ Human Approval")
    st.caption("Review or edit the draft before any external outreach.")

    records = st.session_state.matched_suppliers.to_dict("records")
    idx = st.selectbox(
        "Select supplier to contact",
        options=range(len(records)),
        format_func=lambda i: f"{records[i]['name']} — RM {records[i]['est_min_total']:.2f}–{records[i]['est_max_total']:.2f} (Score {records[i]['Match_Score']})",
    )
    chosen = records[idx]

    edited_rfq = st.text_area("Editable RFQ message", value=st.session_state.draft_rfq_message, height=210)

    if not is_approver:
        st.warning("🔒 **Approval locked (Staff role).** Switch to Owner/Manager in the sidebar to approve.")
        if st.button("📨 Submit draft to Owner", use_container_width=True):
            record_activity(tenant_id, {
                "User_Role": current_role,
                "Action": "Submitted draft for Owner approval",
                "Item_Request": f"{st.session_state.active_request['item_name']} × {st.session_state.active_request['quantity']}",
                "Supplier_Selected": chosen["name"],
                "Total_Est_RM": f"{chosen['est_min_total']:.2f} – {chosen['est_max_total']:.2f}",
                "Status": "Pending Owner Sign-Off",
            })
            st.toast("Draft routed to Owner.", icon="📩")
    else:
        b1, b2 = st.columns(2)
        with b1:
            do_approve = st.button("✅ Approve & Dispatch", type="primary", use_container_width=True)
        with b2:
            do_reject = st.button("❌ Reject / Revise", use_container_width=True)

        if do_approve:
            st.session_state.active_request["status"] = "Approved & Dispatched"
            st.session_state.selected_supplier_row = chosen
            st.session_state.draft_rfq_message = edited_rfq
            record_activity(tenant_id, {
                "User_Role": current_role,
                "Action": "APPROVED & sent WhatsApp RFQ",
                "Item_Request": f"{st.session_state.active_request['item_name']} × {st.session_state.active_request['quantity']}",
                "Supplier_Selected": chosen["name"],
                "Total_Est_RM": f"{chosen['est_min_total']:.2f} – {chosen['est_max_total']:.2f}",
                "Status": "✅ Approved & Sent",
            })
            st.success("RFQ approved and logged.")

        if do_reject:
            st.session_state.active_request["status"] = "Rejected — Returned to Staff"
            record_activity(tenant_id, {
                "User_Role": current_role,
                "Action": "REJECTED RFQ draft",
                "Item_Request": f"{st.session_state.active_request['item_name']} × {st.session_state.active_request['quantity']}",
                "Supplier_Selected": chosen["name"],
                "Total_Est_RM": f"{chosen['est_min_total']:.2f} – {chosen['est_max_total']:.2f}",
                "Status": "❌ Revision Requested",
            })
            st.error("Draft marked for revision.")

with col_outcome:
    st.subheader("5️⃣ Outcome & Audit Log")
    st.metric(
        "Workflow status",
        st.session_state.active_request["status"],
        delta=f"{chosen['name']} (RM {chosen['est_min_total']:.2f}–{chosen['est_max_total']:.2f})",
    )

    if st.session_state.active_request["status"] == "Approved & Dispatched":
        digits = re.sub(r"\D", "", str(chosen.get("phone", "")))
        wa_url = f"https://wa.me/{digits}?text={quote(st.session_state.draft_rfq_message)}"
        st.success(f"📲 [Open pre-filled WhatsApp RFQ to **{chosen['name']}**]({wa_url})  \nNumber: `+{digits}`")

    entries = current_audit(tenant_id)
    if entries:
        st.dataframe(pd.DataFrame(entries), use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Export audit log (CSV)",
            data=pd.DataFrame(entries).to_csv(index=False).encode("utf-8"),
            file_name=f"orbyte_audit_{tenant_id}.csv",
            mime="text/csv",
        )
    else:
        st.info("No activity yet for this tenant.")

st.divider()
st.caption(
    "🔒 **PDPA notice:** All supplier names, prices, and phone numbers are synthetic. "
    "On production Orbyte, supplier credentials are governed by tenant-level RBAC and encrypted at rest."
)