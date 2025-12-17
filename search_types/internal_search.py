# search_types/internal_search.py

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from robot_guard import handle_manual_if_needed

SEARCH_WORD = "都市計画 マスタープラン"


def search(start_url: str, max_pages: int = 5) -> str:
    options = Options()
    options.add_argument("--window-size=1200,900")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    html_parts = []

    try:
        driver.get(start_url)
        time.sleep(2)

        # ★ ロボット検知 → 手動対応
        handle_manual_if_needed(driver)

        search_box = wait.until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        search_box.clear()
        search_box.send_keys(SEARCH_WORD)
        search_box.send_keys(Keys.ENTER)

        time.sleep(2)

        for _ in range(max_pages):
            html = handle_manual_if_needed(driver)
            html_parts.append(html)
            break  # 無理にページ送りしない（安全重視）

    finally:
        driver.quit()

    return "\n".join(html_parts)
