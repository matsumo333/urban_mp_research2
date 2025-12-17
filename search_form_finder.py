import re
import requests
from bs4 import BeautifulSoup


def get_soup(url: str) -> BeautifulSoup:
    res = requests.get(url, timeout=10)
    res.encoding = res.apparent_encoding
    return BeautifulSoup(res.text, "html.parser")


def find_search_inputs(soup: BeautifulSoup):
    """
    「検索」という文字の前後から input を探索
    """
    candidates = []

    # 「検索」を含むテキストノード
    texts = soup.find_all(string=re.compile("検索"))

    for text in texts:
        parent = text.parent

        # 近傍の探索範囲を広めに取る
        scope = parent.find_parent(
            ["form", "div", "nav", "header"]
        ) or parent

        inputs = scope.find_all("input")
        for inp in inputs:
            t = inp.get("type", "").lower()
            if t in ["text", "search", ""]:
                candidates.append(inp)

    return candidates


def find_search_form(soup: BeautifulSoup):
    """
    input を含む form を返す
    """
    inputs = find_search_inputs(soup)

    for inp in inputs:
        form = inp.find_parent("form")
        if form:
            return form, inp

    return None, None
