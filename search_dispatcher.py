from search_types import osaka_cse, kyoto_internal, unknown_fallback
from config.constants import MAX_PAGES

def detect_search_type(url):
    if "city.osaka.lg.jp" in url:
        return "osaka"
    if "city.kyoto.lg.jp" in url:
        return "kyoto"
    return "unknown"

def run_search(url):
    search_type = detect_search_type(url)

    if search_type == "osaka":
        return osaka_cse.search(MAX_PAGES)

    if search_type == "kyoto":
        return kyoto_internal.search(MAX_PAGES)

    return unknown_fallback.search(url)
