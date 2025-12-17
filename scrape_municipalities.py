# scrape_municipalities.py
import csv
import requests
from bs4 import BeautifulSoup, NavigableString

URL = "https://uub.jp/opm/ml_homepage.html"

def main():
    res = requests.get(URL, timeout=30)
    res.raise_for_status()

    soup = BeautifulSoup(res.content, "html.parser")

    rows = []
    current_pref = None
    last_text = None

    for node in soup.body.descendants:
        # テキストノードを常に記憶
        if isinstance(node, NavigableString):
            text = node.strip()
            if text:
                last_text = text

                # 都道府県
                if text.endswith(("都", "道", "府", "県")) and len(text) <= 5:
                    current_pref = text

        # aタグが来たら「直前テキスト＝市町村名」
        elif node.name == "a" and current_pref:
            url = node.get("href", "").strip()
            if not url.startswith("http"):
                continue

            municipality = last_text
            rows.append((current_pref, municipality, url))

    with open("municipalities.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["prefecture", "municipality", "url"])
        w.writerows(rows)

    print(f"✅ CSV生成完了: {len(rows)} 行")

if __name__ == "__main__":
    main()
