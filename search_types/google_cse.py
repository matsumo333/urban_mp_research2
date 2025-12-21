# search_types/google_cse.py

import time
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

SEARCH_WORD = "都市計画 マスタープラン"


def search(start_url: str, max_pages=None, input_id: str = None):
    """
    Google CSE を使い、
    ・検索を実行
    ・「都市計画マスタープラン」っぽい HTML ページURLを1つ返す
    戻り値: str | None
    """

    print("[google_cse] ===============================")
    print(f"[google_cse] start_url = {start_url}")
    print(f"[google_cse] input_id  = {input_id}")

    options = Options()
    options.add_argument("--window-size=1200,900")
    # options.add_argument("--headless")  # 必要なら有効化

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    try:
        # --------------------------
        # 1. トップページを開く
        # --------------------------
        driver.get(start_url)
        domain = urlparse(start_url).netloc
        print(f"[google_cse] domain = {domain}")

        # --------------------------
        # 2. 検索窓を特定
        # --------------------------
        search_box = None

        # ① CSV / detect_search_profile 由来の input_id を最優先
        if input_id:
            try:
                el = wait.until(EC.element_to_be_clickable((By.ID, input_id)))
                if el.is_displayed():
                    search_box = el
                    print(f"[google_cse] search box found by input_id={input_id}")
            except:
                pass

        # ② フォールバック
        if not search_box:
            for sel in [
                (By.NAME, "q"),
                (By.NAME, "search"),
                (By.ID, "gsc-i-id1"),
                (By.ID, "gsc-i-id2"),
            ]:
                try:
                    el = wait.until(EC.element_to_be_clickable(sel))
                    if el.is_displayed():
                        search_box = el
                        print(f"[google_cse] search box found by {sel}")
                        break
                except:
                    pass

        if not search_box:
            print("[google_cse] ❌ search box not found")
            return None

        # --------------------------
        # 3. 検索実行
        # --------------------------
        search_box.clear()
        search_box.send_keys(SEARCH_WORD)
        search_box.send_keys(Keys.ENTER)
        print(f"[google_cse] search executed: {SEARCH_WORD}")

        time.sleep(6)

        # --------------------------
        # 4. 検索結果から「本命ページ」を1つ選ぶ
        # --------------------------
        results = driver.find_elements(By.CSS_SELECTOR, "a.gs-title")

        print(f"[google_cse] result links = {len(results)}")

        for a in results:
            href = a.get_attribute("href")
            title = (a.text or "").strip()

            if not href:
                continue

            # PDFはここでは扱わない
            if href.lower().endswith(".pdf"):
                continue

            # 同一ドメインのみ
            if domain not in href:
                continue

            # タイトル条件（超重要）
            if "都市計画" not in title:
                continue

            print("[google_cse] ✔ candidate found")
            print(f"  title = {title}")
            print(f"  url   = {href}")

            # ★ 本命HTMLページURLを返す
            return href

        print("[google_cse] ❌ no suitable entry page found")
        return None

    finally:
        driver.quit()
        print("[google_cse] browser closed")
        print("[google_cse] ===============================")
