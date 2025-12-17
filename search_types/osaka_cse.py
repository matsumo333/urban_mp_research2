# search_types/osaka_cse.py

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

# ==========================================
# 設定
# ==========================================
SEARCH_WORD = "都市計画 マスタープラン"
SEARCH_URL = "https://sc.city.osaka.lg.jp/search/index.html"


def search(start_url: str = None, max_pages: int = 2) -> str:
    """
    大阪市 Googleカスタム検索を巡回し、
    各ページの HTML を結合して返す。

    start_url : 互換用（未使用）
    max_pages : 最大巡回ページ数
    戻り値    : HTML文字列
    """

    options = Options()
    options.add_argument("--window-size=1200,900")
    # 安定させたい場合は有効化
    # options.add_argument("--headless")
    # options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    html_parts = []
    prev_html = ""

    try:
        # ----------------------------------
        # 検索ページを開く
        # ----------------------------------
        driver.get(SEARCH_URL)

        search_box = wait.until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        search_box.clear()
        search_box.send_keys(SEARCH_WORD)
        search_box.send_keys(Keys.ENTER)

        time.sleep(2)

        # ----------------------------------
        # ページ巡回
        # ----------------------------------
        for page in range(1, max_pages + 1):
            print(f"📄 大阪市検索 {page}ページ目 取得中...")

            # ✅ HTMLが更新されたことを保証
            wait.until(lambda d: d.page_source != prev_html)

            html = driver.page_source
            html_parts.append(html)
            prev_html = html

            # 最終ページなら終了
            if page >= max_pages:
                break

            # 次ページボタン
            try:
                next_btn = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            f"//div[contains(@class,'gsc-cursor-page') and text()='{page + 1}']"
                        )
                    )
                )

                # ✅ スクロール必須（これが重要）
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});",
                    next_btn
                )
                time.sleep(0.5)

                driver.execute_script("arguments[0].click();", next_btn)

            except Exception:
                print("次ページが見つからないため終了します")
                break

    finally:
        driver.quit()

    return "\n".join(html_parts)
