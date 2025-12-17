# link_extractor.py

import csv
import os
from bs4 import BeautifulSoup


def extract_links(html: str):
    soup = BeautifulSoup(html, "html.parser")
    links = []

    for a in soup.select("a"):
        title = a.get_text(strip=True)
        url = a.get("href")
        if not title or not url:
            continue
        if "都市計画" in title or "マスタープラン" in title:
            links.append((title, url))
    return links


def save_links_csv(links, csv_path):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "url"])
        writer.writerows(links)
    print(f"💾 中間CSV保存: {csv_path}")


def load_links_csv(csv_path):
    with open(csv_path, encoding="utf-8-sig") as f:
        return [(r["title"], r["url"]) for r in csv.DictReader(f)]








