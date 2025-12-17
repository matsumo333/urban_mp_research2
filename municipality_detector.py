import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# 自治体名の正規表現（必要に応じて拡張可）
MUNICIPALITY_PATTERN = re.compile(
    r"(?:[一-龥]{1,10})(市|町|村|区)"
)


def detect_municipality_name(url: str) -> str:
    """
    自治体トップページURLから自治体名を自動抽出する
    """
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
    except Exception:
        return "不明自治体"

    soup = BeautifulSoup(r.text, "html.parser")

    # ----------------------------------
    # ① title タグ
    # ----------------------------------
    if soup.title and soup.title.string:
        m = MUNICIPALITY_PATTERN.search(soup.title.string)
        if m:
            return m.group(0)

    # ----------------------------------
    # ② h1 タグ
    # ----------------------------------
    h1 = soup.find("h1")
    if h1:
        m = MUNICIPALITY_PATTERN.search(h1.get_text())
        if m:
            return m.group(0)

    # ----------------------------------
    # ③ og:site_name
    # ----------------------------------
    og = soup.find("meta", property="og:site_name")
    if og and og.get("content"):
        m = MUNICIPALITY_PATTERN.search(og["content"])
        if m:
            return m.group(0)

    # ----------------------------------
    # ④ URL から推測
    # ----------------------------------
    host = urlparse(url).netloc
    host = host.replace("www.", "")

    if host.startswith("city."):
        name = host.split(".")[1]
        return f"{name}市"

    return "不明自治体"
