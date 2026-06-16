#!/usr/bin/env python3
"""Validate Olist CSV tables before analysis. Exit 0 if OK, 1 with errors."""
import sys
from pathlib import Path

import pandas as pd

REQUIRED = {
    "orders": ["order_id", "order_status", "order_purchase_timestamp"],
    "order_items": ["order_id", "product_id", "seller_id", "price"],
    "payments": ["order_id", "payment_value"],
    "reviews": ["order_id", "review_score"],
    "products": ["product_id", "product_category_name"],
    "sellers": ["seller_id"],
}

ALIASES = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
}


def resolve(path: Path) -> Path | None:
    if path.exists():
        return path
    stem = path.stem.replace("olist_", "").replace("_dataset", "")
    for p in path.parent.glob("*.csv"):
        if stem in p.name.lower() or path.stem.lower() in p.name.lower():
            return p
    return None


def main(data_dir: str) -> int:
    base = Path(data_dir)
    errors = []
    for name, cols in REQUIRED.items():
        candidates = list(base.glob(f"*{name}*")) + list(base.glob(f"*orders*"))[:1]
        found = None
        for c in base.glob("*.csv"):
            key = name.replace("_", "")
            if key in c.name.lower().replace("_", ""):
                found = c
                break
        if not found:
            errors.append(f"Missing table for: {name}")
            continue
        try:
            df = pd.read_csv(found, nrows=5)
        except Exception as e:
            errors.append(f"Cannot read {found}: {e}")
            continue
        missing = [c for c in cols if c not in df.columns]
        if missing:
            errors.append(f"{found.name} missing columns: {missing}")
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
