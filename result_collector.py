# result_collector.py

import csv
import os

OUTPUT_FILE = "output/urban_plan_index.csv"


def save_results(records):
    os.makedirs("output", exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "city", "title", "type",
                "url", "local_path",
                "source", "depth", "status"
            ]
        )
        writer.writeheader()
        writer.writerows(records)

    print(f"📄 最終CSV保存: {OUTPUT_FILE}")
    