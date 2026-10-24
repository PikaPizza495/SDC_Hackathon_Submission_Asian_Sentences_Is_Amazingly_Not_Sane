"""
orbyte_hub.py
Thin mock of the Orbyte connected-hub interface.
"""
import json
import os

TENANTS = {
    "cafe-selangor": {
        "name": "Kopi & Co Café, Selangor",
        "role": "SME Owner / Manager (Approver)",
        "preset": {
            "trigger_source": "Orbyte Inventory Low-Stock Alert",
            "category": "Packaging",
            "item_name": "Kraft Paper Bowls (500ml/750ml) & Eco Containers",
            "quantity": 400,
            "max_budget_rm": 180.0,
            "max_lead_days": 3,
            "prefer_eco": True,
            "status": "Triggered",
        },
    },
    "bakery-penang": {
        "name": "Penang Sourdough Bakery",
        "role": "SME Owner / Manager (Approver)",
        "preset": {
            "trigger_source": "Staff New Product Sourcing Request",
            "category": "F&B Ingredients",
            "item_name": "Arabica & Liberica Coffee Beans",
            "quantity": 10,
            "max_budget_rm": 450.0,
            "max_lead_days": 4,
            "prefer_eco": True,
            "status": "Triggered",
        },
    },
    "kiosk-kl": {
        "name": "KL Juice Kiosk",
        "role": "Staff (Junior Purchaser — Draft Only)",
        "preset": {
            "trigger_source": "POS Counter Consumables Alert",
            "category": "Store Operations",
            "item_name": "80mm Thermal Receipt Rolls (Box of 50)",
            "quantity": 3,
            "max_budget_rm": 210.0,
            "max_lead_days": 2,
            "prefer_eco": False,
            "status": "Triggered",
        },
    },
}


def get_inventory_alert(tenant_id: str) -> dict:
    return dict(TENANTS[tenant_id]["preset"])


def get_role(tenant_id: str) -> str:
    return TENANTS[tenant_id]["role"]


def _db():
    url = os.environ.get("DATABASE_URL")
    if not url:
        return None
    try:
        import psycopg2
        return psycopg2.connect(url)
    except Exception:
        return None


def log_activity(tenant_id: str, entry: dict) -> bool:
    conn = _db()
    if conn is None:
        return False
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO audit_log (tenant_id, payload) VALUES (%s, %s)",
                (tenant_id, json.dumps(entry)),
            )
        return True
    except Exception:
        return False
    finally:
        conn.close()


def fetch_activity_log(tenant_id: str, limit: int = 50) -> list[dict]:
    conn = _db()
    if conn is None:
        return []
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "SELECT ts, payload FROM audit_log "
                "WHERE tenant_id = %s ORDER BY ts DESC LIMIT %s",
                (tenant_id, limit),
            )
            rows = cur.fetchall()
        return [{"Timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"), **payload} for ts, payload in rows]
    except Exception:
        return []
    finally:
        conn.close()