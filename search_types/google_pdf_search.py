import time
import urllib.parse
import re
import csv
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

SEARCH_WORD = "都市計画 マスタープラン"

# ★ 保存先CSVファイルパス（必要に応じて変更）
LINKS_CSV_PATH = "output/links.csv"  # 既存のアプリと合わせる場合
# または "links_from_google.csv" など専用名でもOK

def clean_title(raw_text: str) -> str:
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    cleaned = []
    for line in lines:
        if re.search(r"https?://|www\.|›", line):
            continue
        cleaned.append(line)
    return cleaned[0] if cleaned else "名称不明"


def save_links_to_csv(links, csv_path=LINKS_CSV_PATH):
    """
    リンクリストをCSVに保存
    links: [("title1", "url1"), ("title2", "url2"), ...]
    """
    os.makedirs(os.path.dirname(csv_path), exist_ok=True) if os.path.dirname(csv_path) else None

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "url"])  # ヘッダー
        for title, url in links:
            writer.writerow([title, url])

    print(f"💾 リンクをCSVに保存しました: {csv_path}（{len(links)}件）")


def search(city_name: str, max_pages: int = 1):
    """
    Googleで広く関連ページを検索 → 結果をCSVに保存して返す
    """
    options = Options()
    options.add_argument("--window-size=1200,900")

    driver = webdriver.Chrome(options=options)
    results = []  # (title, url) のリスト

    try:
        # filetype:pdf を外して広く検索
        query = f'{city_name} {SEARCH_WORD} site:.go.jp OR site:.lg.jp'
        encoded = urllib.parse.quote(query)
        search_url = f"https://www.google.com/search?q={encoded}&num=30"

        print(f"🔍 Google広域検索中: {query}")
        print("   （ロボット認証が出たら手動で解除 → 30秒待機）")

        driver.get(search_url)
        time.sleep(30)  # 手動対応時間

        for a in driver.find_elements(By.CSS_SELECTOR, "a"):
            href = a.get_attribute("href")
            if not href or href.startswith(("javascript:", "/")) or "google" in href:
                continue

            raw_title = a.text.strip()
            title = clean_title(raw_title)
            if not title or title == "名称不明":
                try:
                    h3 = a.find_element(By.XPATH, ".//h3")
                    title = h3.text.strip()
                except:
                    pass
                if not title:
                    continue

            results.append((title, href))

        # 重複除去
        seen = set()
        unique = []
        for item in results:
            if item[1] not in seen:
                unique.append(item)
                seen.add(item[1])

        # ★★★ CSVに保存 ★★★
        save_links_to_csv(unique)

        print(f"✅ 検索完了！発見リンク数: {len(unique)}件")
        return unique

    except Exception as e:
        print(f"⚠ 検索エラー: {e}")
        return []
    finally:
        driver.quit()


# テスト用（直接実行時）
if __name__ == "__main__":
    city = input("市町村名を入力（例: 横浜市）: ").strip()
    if city:
        search(city)