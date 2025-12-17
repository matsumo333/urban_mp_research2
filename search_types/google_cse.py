# search_types/google_cse.py

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

from robot_guard import handle_manual_if_needed

SEARCH_WORD = "都市計画 マスタープラン"


def search(start_url: str, max_pages: int = 3) -> str:
    options = Options()
    options.add_argument("--window-size=1200,900")

    driver = webdriver.Chrome(options=options)
    html_parts = []

    try:
        driver.get(start_url)
        time.sleep(2)

        # ★ ロボット検知対応
        html = handle_manual_if_needed(driver)
        html_parts.append(html)

    finally:
        driver.quit()

    return "\n".join(html_parts)
# search_types/google_cse.py

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

from robot_guard import handle_manual_if_needed

SEARCH_WORD = "都市計画 マスタープラン"


def search(start_url: str, max_pages: int = 3) -> str:
    options = Options()
    options.add_argument("--window-size=1200,900")

    driver = webdriver.Chrome(options=options)
    html_parts = []

    try:
        driver.get(start_url)
        time.sleep(2)

        # ★ ロボット検知対応
        html = handle_manual_if_needed(driver)
        html_parts.append(html)

    finally:
        driver.quit()

    return "\n".join(html_parts)
