# search_types/google_broad_search.py
import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from utils.manual_check_ui import show_manual_check_popup

SEARCH_WORD = "都市計画 マスタープラン"


def search(city_name: str):
    print(f"[google_broad] 🔍 Google広域検索開始: {city_name}")

    options = Options()
    options.add_argument("--window-size=1200,900")

    driver = webdriver.Chrome(options=options)
    results = []

    try:
        query = f'"{city_name}" {SEARCH_WORD}'
        encoded = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded}&num=20"

        driver.get(url)

        print("[google_broad] ⏳ ロボットチェックが出たら解除してください（45秒待機）")
        time.sleep(45)

        for a in driver.find_elements(By.CSS_SELECTOR, "a"):
            href = a.get_attribute("href")
            if not href or not href.lower().endswith(".pdf"):
                continue

            title = a.text.strip() or "都市計画マスタープラン"

            results.append(
                {
                    "title": title,
                    "url": href,
                    "source": "google_broad",
                    "depth": 0,
                }
            )

        if results:
            print(f"[google_broad] PDF直接取得: {len(results)}件")
            return results

        # ここが重要：人間に委ねる
        print("[google_broad] ❌ 自動取得失敗 → 手動確認モード")
        show_manual_check_popup(city_name)
        print("[google_broad] 手動確認モード終了")
        return []

    finally:
        driver.quit()
