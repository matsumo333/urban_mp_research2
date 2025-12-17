from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

SEARCH_WORD = "都市計画 マスタープラン"

def search(start_url: str, max_pages: int):
    """
    京都市トップページの内部検索を Selenium で実行する
    """

    options = Options()
    options.add_argument("--window-size=1200,900")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    # ★ 京都市URLを main.py から受け取る
    driver.get(start_url)

    search_box = wait.until(
        EC.presence_of_element_located((By.NAME, "q"))
    )
    search_box.send_keys(SEARCH_WORD)
    search_box.send_keys(Keys.ENTER)

    html_list = []
    prev_html = ""

    for page in range(1, max_pages + 1):
        print(f"📄 京都市 {page}ページ目取得中...")

        wait.until(lambda d: d.page_source != prev_html)
        html = driver.page_source
        html_list.append(html)
        prev_html = html

        if page < max_pages:
            try:
                time.sleep(1)
                btn = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            f"//div[contains(@class,'gsc-cursor-page') and text()='{page + 1}']"
                        )
                    )
                )
                driver.execute_script("arguments[0].click();", btn)
            except Exception:
                break

    driver.quit()
    return "\n".join(html_list)
