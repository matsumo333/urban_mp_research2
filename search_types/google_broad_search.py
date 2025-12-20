import time
import urllib.parse
import re
import csv
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

SEARCH_WORD = "都市計画 マスタープラン"
LINKS_CSV_PATH = "../output/links.csv"  # 相対パス（1つ上のoutputフォルダ）


def clean_title(raw_text: str) -> str:
    """タイトルから余計なURLや記号を除去"""
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    cleaned = []
    for line in lines:
        if re.search(r"https?://|www\.|›", line):
            continue
        cleaned.append(line)
    return cleaned[0] if cleaned else "（タイトルなし）"


def save_links_to_csv(links):
    """CSVに完全URLで保存"""
    output_dir = os.path.dirname(LINKS_CSV_PATH)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(LINKS_CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "url"])  # ヘッダー
        for title, url in links:
            writer.writerow([title, url])
    print(f"💾 完全URLでリンク保存完了: {LINKS_CSV_PATH}（{len(links)}件）")


def search(city_name: str) -> list[tuple[str, str]]:
    """
    人間らしいGoogle広域検索
    - city_name: 自治体名（例: "横浜市", "東京都中央区"）
    - 戻り値: [(title, url), ...] のリスト
    """
    if not city_name:
        print("⚠ 自治体名が指定されていません")
        return []

    options = Options()
    options.add_argument("--window-size=1200,900")
    # options.add_argument("--headless")  # 必要に応じて

    driver = webdriver.Chrome(options=options)
    results = []

    try:
        # 公式サイト限定検索
        query = f'"{city_name}" {SEARCH_WORD} site:.go.jp OR site:.lg.jp'
        encoded = urllib.parse.quote(query)
        search_url = f"https://www.google.com/search?q={encoded}&num=30"

        print(f"\n🔍 検索開始: {city_name}")
        print("   Googleが開きます。ロボット認証が出たら手動で解除してください")
        print("   30秒後に自動で結果を収集します...\n")

        driver.get(search_url)
        time.sleep(30)  # 手動対応用待機

        print("🔄 検索結果を解析中...")

        for a in driver.find_elements(By.CSS_SELECTOR, "a"):
            href = a.get_attribute("href")
            if not href:
                continue
            if any(
                x in href
                for x in ["google.com", "youtube.com", "policies", "preferences"]
            ):
                continue
            if href.startswith(("javascript:", "data:")):
                continue
            if not re.search(r"\.(go\.jp|lg\.jp)/", href):
                continue

            raw_title = a.text.strip()
            title = clean_title(raw_title)
            if not title or title == "（タイトルなし）":
                try:
                    h3 = a.find_element(By.XPATH, ".//h3")
                    title = h3.text.strip()
                except:
                    title = "（タイトルなし）"

            results.append((title, href))

        # 重複除去
        seen = set()
        unique = []
        for t, u in results:
            if u not in seen:
                unique.append((t, u))
                seen.add(u)

        save_links_to_csv(unique)
        print(f"✅ 検索完了！公式関連ページ {len(unique)}件を発見・保存しました")
        return unique

    except Exception as e:
        print(f"⚠ 検索中にエラーが発生しました: {e}")
        return []
    finally:
        driver.quit()


# ================================
# 単独実行時の入力対応（他のスクリプトからimportされても邪魔にならない）
# ================================
if __name__ == "__main__":
    print("=== Google広域検索ツール ===\n")
    city = input(
        "自治体名を入力してください（例: 四日市市、横浜市、東京都中央区）: "
    ).strip()
    if city:
        links = search(city)
        if links:
            print("\n=== 保存された主なページ（上位10件） ===")
            for i, (title, url) in enumerate(links[:10], 1):
                print(f"{i}. {title}")
                print(f"   {url}\n")
    else:
        print("入力がありませんでした。")
