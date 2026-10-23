"""
seed_suppliers.py
Creates the `suppliers` and `audit_log` tables (if missing) and loads
suppliers.csv into Replit's PostgreSQL via DATABASE_URL.

Usage (in the Replit Shell):
    pip install -r requirements.txt
    python generate_suppliers.py    # creates suppliers.csv
    python seed_suppliers.py

Safe to re-run: rows are matched on supplier_code and updated, not duplicated.
"""
import csv
import os

import psycopg2

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS suppliers (
    id                 SERIAL PRIMARY KEY,
    supplier_code      TEXT UNIQUE NOT NULL,
    name               TEXT NOT NULL,
    category           TEXT NOT NULL,
    products           TEXT NOT NULL,
    unit               TEXT NOT NULL,
    price_min_rm       NUMERIC(10,2) NOT NULL,
    price_max_rm       NUMERIC(10,2) NOT NULL,
    moq                INTEGER NOT NULL,
    state              TEXT NOT NULL,
    lead_time_days     INTEGER NOT NULL,
    reliability_rating NUMERIC(2,1) CHECK (reliability_rating BETWEEN 1 AND 5),
    eco_certified      BOOLEAN NOT NULL DEFAULT FALSE,
    phone              TEXT,
    email              TEXT,
    tags               TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id        BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    ts        TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload   JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_log_tenant_ts
    ON audit_log (tenant_id, ts DESC);
"""

UPSERT = """
INSERT INTO suppliers
    (supplier_code, name, category, products, unit, price_min_rm, price_max_rm,
     moq, state, lead_time_days, reliability_rating, eco_certified, phone,
     email, tags)
VALUES
    (%(supplier_code)s, %(name)s, %(category)s, %(products)s, %(unit)s,
     %(price_min_rm)s, %(price_max_rm)s, %(moq)s, %(state)s, %(lead_time_days)s,
     %(reliability_rating)s, %(eco_certified)s, %(phone)s, %(email)s,
     %(tags)s)
ON CONFLICT (supplier_code) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    products = EXCLUDED.products,
    unit = EXCLUDED.unit,
    price_min_rm = EXCLUDED.price_min_rm,
    price_max_rm = EXCLUDED.price_max_rm,
    moq = EXCLUDED.moq,
    state = EXCLUDED.state,
    lead_time_days = EXCLUDED.lead_time_days,
    reliability_rating = EXCLUDED.reliability_rating,
    eco_certified = EXCLUDED.eco_certified,
    phone = EXCLUDED.phone,
    email = EXCLUDED.email,
    tags = EXCLUDED.tags;
"""


def to_bool(value) -> bool:
    return str(value).strip().lower() in ("true", "t", "yes", "y", "1")


def main():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise SystemExit(
            "DATABASE_URL is not set. In Replit, open the Database tool and "
            "create a PostgreSQL database first."
        )

    with open("suppliers.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        r["price_min_rm"] = float(r["price_min_rm"])
        r["price_max_rm"] = float(r["price_max_rm"])
        r["moq"] = int(r["moq"])
        r["lead_time_days"] = int(r["lead_time_days"])
        r["reliability_rating"] = float(r["reliability_rating"])
        r["eco_certified"] = to_bool(r["eco_certified"])

    conn = psycopg2.connect(db_url)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(CREATE_TABLE)
            cur.executemany(UPSERT, rows)
            cur.execute("SELECT COUNT(*) FROM suppliers;")
            total = cur.fetchone()[0]
        print(f"Seeded {len(rows)} rows. suppliers table now has {total} rows.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()