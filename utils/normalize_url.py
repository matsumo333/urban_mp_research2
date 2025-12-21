# utils/normalize_url.py
def normalize_url(url: str) -> str:
    if not url:
        return url

    if "/page/" in url:
        url = url.replace("/page/", "/")

    return url
