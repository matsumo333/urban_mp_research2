# result_collector.py
import csv
import os

CSV_FILE = "output/urban_plan_index.csv"


def save_results(records):
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)

    fieldnames = ["title", "url", "source", "depth"]

    with open(CSV_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
