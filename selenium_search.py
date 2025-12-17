from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

SEARCH_WORD = "都市計画 マスタープラン"

def selenium_site_search(_unused=None, max_pages=3):
    max_pages = int(max_pages)  # 保険

    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1200,900")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    # 京都市 Google CSE
    driver.get("https://cse.google.com/cse?cx=d65aa2c189dd8476b")

    # 検索入力
    search_box = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input.gsc-input"))
    )
    search_box.clear()
    search_box.send_keys(SEARCH_WORD)
    search_box.send_keys(Keys.ENTER)

    all_html = []  # ← ★ ここがポイント

    for page in range(1, max_pages + 1):
        print(f"\n📄 {page}ページ目を表示・保存中...")

        # 現在ページ番号を確認（非同期対策）
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH,
                 f"//div[contains(@class,'gsc-cursor-current-page') and text()='{page}']")
            )
        )

        # 検索結果が描画されるまで待つ
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".gsc-webResult"))
        )

        # ★ 今表示されているページのHTMLを保存
        page_html = driver.page_source
        all_html.append(
            f"\n\n<!-- ===== page {page} start ===== -->\n"
            + page_html +
            f"\n<!-- ===== page {page} end ===== -->\n"
        )

        # 次ページへ
        if page < max_pages:
            try:
                next_page = wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH,
                         f"//div[@class='gsc-cursor-page' and text()='{page + 1}']")
                    )
                )
                driver.execute_script("arguments[0].click();", next_page)
            except Exception as e:
                print("⚠ 次ページに進めませんでした", e)
                break

    driver.quit()

    # ★ 全ページ分を1つのHTML文字列として返す
    return "\n".join(all_html)
