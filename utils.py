def normalize_url(url: str) -> str:
    """
    京都市などで発生する /page/ を除去する
    """
    if not url:
        return url

    # 京都市対策
    if "/page/" in url:
        url = url.replace("/page/", "/")

    return url
