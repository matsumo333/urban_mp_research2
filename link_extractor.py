import csv
import os
from bs4 import BeautifulSoup


def extract_links(html: str):
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for a in soup.select("a"):
        title = a.get_text(strip=True)
        url = a.get("href")

        if not title or not url:
            continue

        if "都市計画" in title or "マスタープラン" in title:
            results.append((title, url))

    return results


def save_links_csv(links, csv_path):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "url"])
        writer.writerows(links)
    print(f"💾 中間CSV保存: {csv_path}")


def load_links_csv(csv_path):
    links = []
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            links.append((row["title"], row["url"]))
    return links
