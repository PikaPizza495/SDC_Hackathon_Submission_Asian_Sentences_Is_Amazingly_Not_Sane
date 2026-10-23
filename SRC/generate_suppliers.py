"""
generate_suppliers.py
Generates a synthetic Malaysian supplier dataset for the Orbyte InstaQuote prototype.

Usage:
    python generate_suppliers.py

Outputs:
    suppliers.csv   -> import into PostgreSQL with seed_suppliers.py
    suppliers.json  -> same data, handy for API mocks / frontend testing

All companies, phone numbers, and emails are FICTIONAL.
Emails use the reserved example.com domain.
"""
import csv
import json
import random
import re

random.seed(42)

SUPPLIERS = [
    # (name, category, products, unit, price_min_rm, price_max_rm, moq,
    #  state, lead_time_days, reliability_rating, eco_certified)
    # ---------------- Packaging ----------------
    ("Selangor EcoPack Sdn Bhd", "Packaging", "Kraft Paper Bowls (500ml/750ml) & Eco Containers", "per piece", 0.38, 0.65, 300, "Selangor", 2, 4.8, True),
    ("KL Metro Box Trading", "Packaging", "Kraft Paper Bowls & Takeaway Boxes", "per piece", 0.30, 0.52, 500, "Kuala Lumpur", 3, 4.1, False),
    ("GreenLeaf Bio Supplies Sdn Bhd", "Packaging", "Biodegradable Bagasse Bowls & Cutlery", "per piece", 0.45, 0.80, 200, "Selangor", 1, 4.6, True),
    ("Southern Bulk Pack Enterprise", "Packaging", "Plastic & Paper Food Containers", "per piece", 0.22, 0.40, 1000, "Johor", 5, 3.4, False),
    ("Petaling Pulp & Paper Sdn Bhd", "Packaging", "PLA-Lined Paper Bowls (Compostable)", "per piece", 0.55, 0.95, 100, "Selangor", 2, 4.9, True),
    ("Penang Green Wrap Trading", "Packaging", "Compostable Paper Cups & Lids", "per piece", 0.18, 0.35, 500, "Penang", 4, 4.3, True),
    ("Johor Cup & Carton Industries", "Packaging", "Double-Wall Paper Coffee Cups", "per piece", 0.15, 0.28, 2000, "Johor", 6, 3.8, False),
    ("Klang Valley Takeaway Supplies", "Packaging", "Paper Bags & Food Wrap", "per piece", 0.12, 0.30, 500, "Selangor", 2, 3.9, False),
    ("Cheras PackMart", "Packaging", "Budget Kraft Paper Bowls with Lids", "per piece", 0.28, 0.45, 1000, "Kuala Lumpur", 3, 3.2, False),
    ("BioBowl Malaysia Sdn Bhd", "Packaging", "Wheat-Straw & Bagasse Bowls (Premium)", "per piece", 0.70, 1.20, 100, "Kuala Lumpur", 2, 4.7, True),
    ("Shah Alam Carton Works", "Packaging", "Corrugated Shipping Cartons", "per piece", 0.90, 1.60, 200, "Selangor", 3, 4.4, False),
    ("Northern Logistics & Pack", "Packaging", "Heavy-Duty Recycled Corrugated Cartons", "per piece", 1.10, 1.80, 200, "Penang", 4, 4.0, True),
    ("Perak Bamboo Ware Enterprise", "Packaging", "Bamboo Fibre Cutlery & Straws", "per piece", 0.10, 0.25, 500, "Perak", 4, 4.2, True),
    ("Subang Compost Pack Sdn Bhd", "Packaging", "Compostable Cutlery Sets (Fork, Spoon, Napkin)", "per set", 0.15, 0.30, 300, "Selangor", 1, 4.5, True),
    ("Johor Kraft Direct", "Packaging", "Kraft Paper Bowls 500ml (Bulk Pricing)", "per piece", 0.25, 0.38, 2000, "Johor", 5, 3.6, False),
    # ---------------- F&B Ingredients ----------------
    ("Nusantara Coffee Roasters Sdn Bhd", "F&B Ingredients", "Arabica & Liberica Coffee Beans", "per kg", 38.00, 55.00, 10, "Selangor", 2, 4.9, True),
    ("Borneo Aroma Wholesale", "F&B Ingredients", "House Blend Coffee Beans", "per kg", 32.00, 44.00, 15, "Kuala Lumpur", 3, 4.1, False),
    ("Penang Heritage Bean Co", "F&B Ingredients", "Specialty Single-Origin Arabica Beans", "per kg", 42.00, 62.00, 5, "Penang", 4, 4.7, True),
    ("AgroFresh Klang Valley", "F&B Ingredients", "Fresh Dairy Milk Cartons", "per litre", 5.50, 8.20, 48, "Selangor", 1, 4.8, True),
    ("Highlands Tea Merchants", "F&B Ingredients", "Cameron Highlands Loose-Leaf Tea", "per kg", 28.00, 70.00, 5, "Perak", 3, 4.6, True),
    ("Johor Sugar & Syrup Sdn Bhd", "F&B Ingredients", "Flavoured Syrups & Sweeteners", "per bottle", 12.00, 22.00, 24, "Johor", 4, 3.5, False),
    ("Bangsar Bakery Supply", "F&B Ingredients", "Butter, Flour & Pastry Ingredients", "per kg", 6.00, 18.00, 20, "Kuala Lumpur", 2, 4.3, False),
    ("Serdang Fresh Produce Hub", "F&B Ingredients", "Fresh Fruits & Vegetables", "per kg", 3.00, 12.00, 20, "Selangor", 1, 3.7, False),
    ("Oat & Plant Co Malaysia", "F&B Ingredients", "Oat Milk & Plant-Based Milk Cartons", "per litre", 6.50, 9.50, 24, "Kuala Lumpur", 3, 4.4, True),
    ("Penang Cocoa House", "F&B Ingredients", "Cocoa & Chocolate Powder", "per kg", 22.00, 40.00, 10, "Penang", 5, 4.2, False),
    ("Kuala Selangor Honey Farm", "F&B Ingredients", "Raw Honey & Natural Sweeteners", "per bottle", 18.00, 35.00, 12, "Selangor", 3, 4.5, True),
    ("Ampang Frozen Foods", "F&B Ingredients", "Frozen Pastries & Dough", "per kg", 10.00, 25.00, 30, "Selangor", 2, 3.3, False),
    # ---------------- Store Operations ----------------
    ("SmartPOS Thermal Malaysia", "Store Operations", "80mm Thermal Receipt Rolls (Box of 50)", "per box", 60.00, 70.00, 2, "Kuala Lumpur", 1, 4.6, False),
    ("EcoPrint Paper Supplies", "Store Operations", "BPA-Free Thermal Receipt Rolls (Box of 50)", "per box", 64.00, 76.00, 2, "Selangor", 2, 4.8, True),
    ("PrimeClean Hygiene Hub", "Store Operations", "Food-Grade Sanitizer & Dish Soap (5L)", "per 5L", 20.00, 28.00, 10, "Selangor", 2, 4.6, True),
    ("Johor Janitorial Supplies", "Store Operations", "Cleaning Chemicals, Mops & Cloths", "per set", 15.00, 40.00, 10, "Johor", 4, 3.6, False),
    ("KL Uniform & Apron House", "Store Operations", "Cafe Aprons & Staff Uniforms", "per piece", 25.00, 60.00, 20, "Kuala Lumpur", 7, 4.0, False),
    ("Penang Coffee Machine Care", "Store Operations", "Espresso Machine Servicing & Descaler", "per service", 120.00, 350.00, 1, "Penang", 3, 4.5, False),
    ("Selangor Grease & Waste Services", "Store Operations", "Used Cooking Oil & Food Waste Collection", "per month", 80.00, 200.00, 1, "Selangor", 3, 4.1, True),
    ("Damansara Signage & Print", "Store Operations", "Menu Boards, Stickers & Labels", "per set", 45.00, 180.00, 10, "Selangor", 5, 3.9, False),
    ("QuickFix Cafe Equipment", "Store Operations", "Grinders, Blenders & Small Appliances", "per unit", 350.00, 2800.00, 1, "Kuala Lumpur", 6, 3.4, False),
]

FIELDS = [
    "supplier_code", "name", "category", "products", "unit",
    "price_min_rm", "price_max_rm", "moq", "state", "lead_time_days",
    "reliability_rating", "eco_certified", "phone", "email", "tags",
]

STOPWORDS = {"and", "with", "the", "of", "for", "per", "box", "set", "boxed"}


def slugify(name: str) -> str:
    name = re.sub(r"\b(sdn|bhd|enterprise|trading)\b", "", name, flags=re.I)
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def fake_phone() -> str:
    prefix = random.choice(["12", "16", "17", "19"])
    return f"+60{prefix}{random.randint(1000000, 9999999)}"


def derive_tags(products: str) -> str:
    """'Kraft Paper Bowls (500ml/750ml)' -> 'bowls,containers,eco,kraft,paper'"""
    words = re.findall(r"[a-zA-Z]+", products.lower())
    keep = {w for w in words if len(w) > 2 and w not in STOPWORDS}
    return ",".join(sorted(keep))


def build_rows():
    rows = []
    for i, s in enumerate(SUPPLIERS, start=1):
        (name, cat, products, unit, pmin, pmax, moq,
         state, lead, rating, eco) = s
        rows.append({
            "supplier_code": f"SUP-{i:03d}",
            "name": name,
            "category": cat,
            "products": products,
            "unit": unit,
            "price_min_rm": f"{pmin:.2f}",
            "price_max_rm": f"{pmax:.2f}",
            "moq": moq,
            "state": state,
            "lead_time_days": lead,
            "reliability_rating": f"{rating:.1f}",
            "eco_certified": str(eco).lower(),
            "phone": fake_phone(),
            "email": f"sales@{slugify(name)}.example.com",
            "tags": derive_tags(products),
        })
    return rows


def main():
    rows = build_rows()
    with open("suppliers.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)
    with open("suppliers.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(rows)} suppliers to suppliers.csv and suppliers.json")


if __name__ == "__main__":
    main()