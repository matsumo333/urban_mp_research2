import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# 表示用
STRATEGY_LABELS = {
    "google_cse": "Google検索型",
    "internal_search": "内部検索型",
    "topical_entry": "トップページ導線型",
    "hierarchical_entry": "階層導線型（神戸市タイプ）",
    "fallback": "フォールバック",
}

TOPICAL_KEYWORDS = [
    "都市計画",
    "まちづくり",
    "都市づくり",
    "都市整備",
    "都市政策",
]

HIERARCHICAL_PATH_KEYWORDS = [
    "/shise/",
    "/machizukuri/",
    "/keikaku/",
    "/toshikeikaku/",
]


def detect_search_strategy_candidates(url: str) -> list[str]:
    """
    自治体トップページから
    使えそうな検索方式を「優先順」で返す
    """
    candidates = []

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
    except Exception:
        return ["fallback"]

    soup = BeautifulSoup(r.text, "html.parser")

    # ① Google CSE
    if soup.select_one("div.gsc-control-cse"):
        candidates.append("google_cse")

    # ② 内部検索
    if soup.select_one("input[name='q']"):
        candidates.append("internal_search")

    # ③ トップページ導線（京都など）
    for a in soup.select("a"):
        text = a.get_text(strip=True)
        if any(k in text for k in TOPICAL_KEYWORDS):
            candidates.append("topical_entry")
            break

    # ④ 階層導線（神戸市タイプ）
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        if any(k in href for k in HIERARCHICAL_PATH_KEYWORDS):
            candidates.append("hierarchical_entry")
            break

    if not candidates:
        candidates.append("fallback")

    # 重複除去（順序保持）
    return list(dict.fromkeys(candidates))
