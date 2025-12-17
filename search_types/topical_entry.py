import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

TOPIC_KEYWORDS = [
    "都市計画",
    "まちづくり",
    "都市づくり",
    "都市整備",
    "都市政策",
]

def search(start_url: str, max_pages: int = 0):
    """
    トップページの文言から導線URLを拾う
    （京都市など）
    """
    try:
        r = requests.get(start_url, timeout=10)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
    except Exception as e:
        print(f"⚠ トップページ取得失敗: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    urls = set()

    for a in soup.select("a[href]"):
        text = a.get_text(strip=True)
        if not text:
            continue

        if any(k in text for k in TOPIC_KEYWORDS):
            urls.add(urljoin(start_url, a["href"]))

    return list(urls)
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

TOPIC_KEYWORDS = [
    "都市計画",
    "まちづくり",
    "都市づくり",
    "都市整備",
    "都市政策",
]

def search(start_url: str, max_pages: int = 0):
    """
    トップページの文言から導線URLを拾う
    （京都市など）
    """
    try:
        r = requests.get(start_url, timeout=10)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
    except Exception as e:
        print(f"⚠ トップページ取得失敗: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    urls = set()

    for a in soup.select("a[href]"):
        text = a.get_text(strip=True)
        if not text:
            continue

        if any(k in text for k in TOPIC_KEYWORDS):
            urls.add(urljoin(start_url, a["href"]))

    return list(urls)
