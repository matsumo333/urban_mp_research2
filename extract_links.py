# link_extractor.py

from bs4 import BeautifulSoup
from urllib.parse import urljoin


PDF_HINT_WORDS = [
    "都市計画",
    "マスタープラン",
    "master",
    "plan",
]


def extract_links(html: str, base_url: str = ""):
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(strip=True)

        full_url = urljoin(base_url, href)

        # PDF直リンク
        if full_url.lower().endswith(".pdf"):
            results.append((text or full_url, full_url))
            continue

        # PDFらしいリンク（中間ページ）
        if any(w in (text + full_url).lower() for w in PDF_HINT_WORDS):
            results.append((text or full_url, full_url))

    # 重複除去（順序保持）
    seen = set()
    uniq = []
    for t, u in results:
        if u not in seen:
            uniq.append((t, u))
            seen.add(u)

    return uniq
