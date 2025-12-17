from search_types.kyoto import search as kyoto_search
from search_types.osaka import search as osaka_search

def run_search(url, max_pages=3):
    if "kyoto" in url:
        return kyoto_search(max_pages)
    elif "osaka" in url:
        return osaka_search(max_pages)
    else:
        raise ValueError("未対応の自治体です")
