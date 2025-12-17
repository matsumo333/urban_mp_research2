import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

TARGET_PATH_KEYWORDS = [
    "/shise/",
    "/machizukuri/",
    "/keikaku/",
    "/toshikeikaku/",
]

def search(start_url: str, max_pages: int = 0):
    """
    URL階層から意味のある入口ページを抽出
    （神戸市・横浜市など）
    """
    try:
        r = requests.get(start_url, timeout=10)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
    except Exception as e:
        print(f"⚠ トップページ取得失敗: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    base_domain = urlparse(start_url).netloc

    urls = set()

    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href:
            continue

        if any(k in href for k in TARGET_PATH_KEYWORDS):
            full_url = urljoin(start_url, href)
            if urlparse(full_url).netloc == base_domain:
                urls.add(full_url)

    return list(urls)
