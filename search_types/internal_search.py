import os
import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

SEARCH_WORD = "都市計画 マスタープラン"

# ==========================
# 設定
# ==========================
MAX_DEPTH = 5  # ← ★ 5層まで探索
MAX_LINKS_PER_PAGE = 5  # ← 各ページで辿るリンク数制限

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CSV_PATH = os.path.join(BASE_DIR, "output", "link.csv")


# ==========================
# CSV保存（ログ用）
# ==========================
def save_to_csv(links):
    if not links:
        return

    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    file_exists = os.path.isfile(CSV_PATH)

    with open(CSV_PATH, "a", newline="", encoding="utf_8_sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["title", "url"])
        for link in links:
            writer.writerow([link["title"], link["url"]])


# ==========================
# PDFリンク抽出
# ==========================
def extract_pdf_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    pdf_links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.lower().endswith(".pdf"):
            continue

        full_url = urljoin(base_url, href)
        text = a.get_text(strip=True)

        prev_h = a.find_previous(["h1", "h2", "h3", "h4", "h5"])
        prefix = prev_h.get_text(strip=True) if prev_h else ""

        title = f"{prefix} {text}".strip()

        pdf_links.append({"title": title, "url": full_url})

    return pdf_links


# ==========================
# 内部リンク抽出（深掘り用）
# ==========================
def extract_internal_links(html, base_url, domain):
    soup = BeautifulSoup(html, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])

        if domain not in href:
            continue
        if href.lower().endswith(".pdf"):
            continue
        if "#" in href:
            continue

        links.append(href)

    return list(dict.fromkeys(links))  # 重複除去・順序保持


# ==========================
# internal_search 本体（5層）
# ==========================
def search(start_url: str, max_pages=None):
    options = Options()
    options.add_argument("--window-size=1200,900")
    # options.add_argument("--headless")  # 必要なら有効化

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    try:
        print(f"[internal_search] start: {start_url}")
        driver.get(start_url)

        # --------------------------
        # 検索窓検出
        # --------------------------
        search_box = None
        selectors = [
            (By.ID, "gsc-i-id2"),
            (By.ID, "gsc-i-id1"),
            (By.NAME, "q"),
            (By.NAME, "search"),
        ]

        for sel in selectors:
            try:
                el = wait.until(EC.element_to_be_clickable(sel))
                if el.is_displayed():
                    search_box = el
                    break
            except:
                pass

        if not search_box:
            print("[internal_search] search box not found")
            return None

        # --------------------------
        # 検索実行
        # --------------------------
        search_box.clear()
        search_box.send_keys(SEARCH_WORD)
        search_box.send_keys(Keys.ENTER)
        time.sleep(6)

        # --------------------------
        # 検索結果から最初の同一ドメインURL取得
        # --------------------------
        domain = urlparse(start_url).netloc
        results = driver.find_elements(By.CSS_SELECTOR, "a.gs-title")

        entry_url = None
        for a in results:
            href = a.get_attribute("href")
            if href and domain in href:
                entry_url = href
                break

        if not entry_url:
            print("[internal_search] no internal result")
            return None

        # --------------------------
        # 深掘り探索（DFS）
        # --------------------------
        visited = set()
        stack = [(entry_url, 0)]

        while stack:
            url, depth = stack.pop()

            if url in visited or depth > MAX_DEPTH:
                continue

            visited.add(url)

            print(f"[internal_search] depth={depth} visit: {url}")
            driver.get(url)
            time.sleep(3)

            # PDF抽出
            pdfs = extract_pdf_links(driver.page_source, driver.current_url)
            if pdfs:
                save_to_csv(pdfs)
                print(f"[internal_search] PDF found at depth {depth}")
                return driver.page_source

            # 次の階層へ
            if depth < MAX_DEPTH:
                links = extract_internal_links(
                    driver.page_source, driver.current_url, domain
                )
                for l in links[:MAX_LINKS_PER_PAGE]:
                    stack.append((l, depth + 1))

        print("[internal_search] PDF not found")
        return None

    finally:
        driver.quit()


# ==========================
# 単体テスト
# ==========================
if __name__ == "__main__":
    search("https://www.city.kyoto.lg.jp/")
