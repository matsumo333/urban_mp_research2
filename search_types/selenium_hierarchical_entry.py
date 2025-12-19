import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from search_types.selenium_navigation import click_navigation_buttons

LINK_TEXT_KEYWORDS = [
    "都市計画",
    "マスタープラン",
    "都市計画マスタープラン",
]

def search(start_url: str, max_pages: int = 0):
    options = Options()
    options.add_argument("--window-size=1200,900")
    # options.add_argument("--headless")  # ← デバッグ中は使わない

    driver = webdriver.Chrome(options=options)
    results = set()

    try:
        print("🧭 Selenium hierarchical search 開始")
        driver.get(start_url)
        time.sleep(3)

        # ★ 汎用ナビクリック
        click_navigation_buttons(driver)

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        base_domain = urlparse(start_url).netloc

        for a in soup.select("a[href]"):
            text = a.get_text(strip=True)
            href = a.get("href")

            if not text or not href:
                continue

            if not any(k in text for k in LINK_TEXT_KEYWORDS):
                continue

            full_url = urljoin(start_url, href)

            if urlparse(full_url).netloc != base_domain:
                continue

            results.add(full_url)

        print(f"✅ Selenium hierarchical 抽出数: {len(results)}")

        return list(results)

    finally:
        driver.quit()
