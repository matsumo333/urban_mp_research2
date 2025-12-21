# utils/normalize.py


def normalize_url(url: str) -> str:
    """
    京都市などで発生する /page/ を除去
    """
    if not url:
        return url

    if "/page/" in url:
        url = url.replace("/page/", "/")

    return url
