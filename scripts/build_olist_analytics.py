"""
Build analytical outputs for the Olist Delivery Experience project.

This script reads the raw Olist CSV files, creates an order-level analytical mart,
runs SQL-style assumption tests using SQLite, and trains baseline predictive models
for low-review risk.

Expected raw files inside data/:
- olist_orders_dataset.csv
- olist_order_items_dataset.csv
- olist_order_payments_dataset.csv
- olist_order_reviews_dataset.csv
- olist_products_dataset.csv
- olist_customers_dataset.csv
- olist_sellers_dataset.csv
- product_category_name_translation.csv
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
except Exception:  # pragma: no cover
    LogisticRegression = RandomForestClassifier = None

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)


def read_csv(name: str) -> pd.DataFrame:
    path = DATA / name
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return pd.read_csv(path)


def build_order_mart() -> pd.DataFrame:
    orders = read_csv("olist_orders_dataset.csv")
    items = read_csv("olist_order_items_dataset.csv")
    payments = read_csv("olist_order_payments_dataset.csv")
    reviews = read_csv("olist_order_reviews_dataset.csv")
    products = read_csv("olist_products_dataset.csv")
    customers = read_csv("olist_customers_dataset.csv")
    sellers = read_csv("olist_sellers_dataset.csv")
    translation = read_csv("product_category_name_translation.csv")

    category_map = dict(zip(translation.product_category_name, translation.product_category_name_english))
    products["category"] = products["product_category_name"].map(category_map).fillna(products["product_category_name"]).fillna("unknown")

    item_enriched = (
        items.merge(products[["product_id", "category"]], on="product_id", how="left")
        .merge(sellers[["seller_id", "seller_state"]], on="seller_id", how="left")
    )

    item_agg = item_enriched.groupby("order_id").agg(
        price=("price", "sum"),
        freight=("freight_value", "sum"),
        items_count=("order_item_id", "count"),
        sellers_count=("seller_id", "nunique"),
        primary_category=("category", lambda s: s.value_counts().index[0] if len(s.dropna()) else "unknown"),
        seller_state=("seller_state", lambda s: s.dropna().mode().iloc[0] if len(s.dropna()) else "unknown"),
    ).reset_index()

    pay_agg = payments.groupby("order_id").agg(
        payment_value=("payment_value", "sum"),
        installments=("payment_installments", "max"),
        primary_payment_type=("payment_type", lambda s: s.value_counts().index[0] if len(s.dropna()) else "unknown"),
    ).reset_index()

    review_agg = reviews.sort_values("review_creation_date").groupby("order_id").agg(
        review_score=("review_score", "mean"),
        review_count=("review_id", "count"),
    ).reset_index()

    mart = (
        orders.merge(customers[["customer_id", "customer_state"]], on="customer_id", how="left")
        .merge(item_agg, on="order_id", how="left")
        .merge(pay_agg, on="order_id", how="left")
        .merge(review_agg, on="order_id", how="left")
    )

    for col in ["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]:
        mart[col] = pd.to_datetime(mart[col], errors="coerce")

    mart["delivery_days"] = (mart["order_delivered_customer_date"] - mart["order_purchase_timestamp"]).dt.total_seconds() / 86400
    mart["delay_days"] = (mart["order_delivered_customer_date"] - mart["order_estimated_delivery_date"]).dt.total_seconds() / 86400
    mart["promised_days"] = (mart["order_estimated_delivery_date"] - mart["order_purchase_timestamp"]).dt.total_seconds() / 86400
    mart["late"] = mart["delay_days"] > 0
    mart["low_review"] = mart["review_score"] <= 2
    mart["cross_state"] = mart["customer_state"] != mart["seller_state"]
    mart["gmv"] = mart["price"].fillna(0) + mart["freight"].fillna(0)
    mart["delivered"] = mart["order_status"].eq("delivered")

    mart.to_csv(OUT / "order_level_mart.csv", index=False)
    return mart


def sql_outputs(mart: pd.DataFrame) -> None:
    conn = sqlite3.connect(OUT / "olist_analytics.sqlite")
    mart.to_sql("order_mart", conn, if_exists="replace", index=False)

    queries = {
        "delay_review_test": """
            SELECT
                CASE WHEN late = 1 THEN 'late_delivery' ELSE 'on_time_or_early' END AS segment,
                COUNT(*) AS orders,
                AVG(CASE WHEN low_review = 1 THEN 1.0 ELSE 0.0 END) AS low_review_rate,
                AVG(review_score) AS avg_review_score,
                AVG(delivery_days) AS avg_delivery_days
            FROM order_mart
            WHERE delivered = 1 AND review_score IS NOT NULL
            GROUP BY segment
            ORDER BY low_review_rate DESC
        """,
        "category_hotspots": """
            SELECT
                primary_category,
                COUNT(*) AS orders,
                AVG(CASE WHEN low_review = 1 THEN 1.0 ELSE 0.0 END) AS low_review_rate,
                AVG(CASE WHEN late = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate,
                AVG(freight) AS avg_freight,
                AVG(delivery_days) AS avg_delivery_days
            FROM order_mart
            WHERE delivered = 1 AND review_score IS NOT NULL
            GROUP BY primary_category
            HAVING COUNT(*) >= 100
            ORDER BY (low_review_rate * COUNT(*)) DESC
            LIMIT 20
        """,
        "state_route_test": """
            SELECT
                CASE WHEN cross_state = 1 THEN 'cross_state' ELSE 'same_state' END AS route_type,
                COUNT(*) AS orders,
                AVG(delivery_days) AS avg_delivery_days,
                AVG(freight) AS avg_freight,
                AVG(CASE WHEN late = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate,
                AVG(CASE WHEN low_review = 1 THEN 1.0 ELSE 0.0 END) AS low_review_rate
            FROM order_mart
            WHERE delivered = 1 AND review_score IS NOT NULL
            GROUP BY route_type
        """,
    }

    for name, query in queries.items():
        pd.read_sql_query(query, conn).to_csv(OUT / f"{name}.csv", index=False)

    conn.close()


def train_models(mart: pd.DataFrame) -> None:
    if LogisticRegression is None:
        return

    df = mart[mart["delivered"] & mart["review_score"].notna()].copy()
    df = df.dropna(subset=["delivery_days", "delay_days", "freight"])
    df["target"] = df["low_review"].astype(int)

    features = [
        "delivery_days", "delay_days", "promised_days", "freight", "items_count",
        "sellers_count", "cross_state", "primary_category", "customer_state", "primary_payment_type", "installments",
    ]
    X = df[features].copy()
    y = df["target"]

    cat_cols = ["primary_category", "customer_state", "primary_payment_type", "cross_state"]
    num_cols = [c for c in features if c not in cat_cols]

    pre = ColumnTransformer([
        ("num", StandardScaler(), num_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=50), cat_cols),
    ])

    models = {
        "Logistic Regression": LogisticRegression(max_iter=2000, class_weight="balanced"),
        "Random Forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=20, class_weight="balanced", random_state=42),
    }

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.25, stratify=y, random_state=42)
    rows = []
    for name, clf in models.items():
        pipe = Pipeline([("prep", pre), ("model", clf)])
        pipe.fit(X_train, y_train)
        pred = pipe.predict(X_test)
        proba = pipe.predict_proba(X_test)[:, 1]
        rows.append({
            "model": name,
            "accuracy": accuracy_score(y_test, pred),
            "roc_auc": roc_auc_score(y_test, proba),
            "precision": precision_score(y_test, pred, zero_division=0),
            "recall": recall_score(y_test, pred, zero_division=0),
            "f1": f1_score(y_test, pred, zero_division=0),
        })

    pd.DataFrame(rows).to_csv(OUT / "model_metrics.csv", index=False)


def main() -> None:
    mart = build_order_mart()
    sql_outputs(mart)
    train_models(mart)
    print("Analytics outputs created in", OUT)


if __name__ == "__main__":
    main()
