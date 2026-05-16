"""Download Olist raw CSV files from Kaggle using kagglehub.

Run locally:
    pip install kagglehub pandas
    python scripts/download_olist_raw_kagglehub.py

The raw files are downloaded into data/raw/.
They are intentionally not required for GitHub Pages. The dashboard can use derived CSVs.
"""

from pathlib import Path
import shutil

import kagglehub

DATASET = "olistbr/brazilian-ecommerce"
RAW_DIR = Path("data/raw")

EXPECTED_FILES = [
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    dataset_path = Path(kagglehub.dataset_download(DATASET))
    print(f"Downloaded Kaggle dataset to: {dataset_path}")

    copied = 0
    for filename in EXPECTED_FILES:
        matches = list(dataset_path.rglob(filename))
        if not matches:
            print(f"Missing expected file: {filename}")
            continue

        source = matches[0]
        destination = RAW_DIR / filename
        shutil.copy2(source, destination)
        copied += 1
        print(f"Copied {filename} -> {destination}")

    print(f"Done. {copied}/{len(EXPECTED_FILES)} files copied to {RAW_DIR}")


if __name__ == "__main__":
    main()
