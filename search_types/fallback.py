import requests


def search(start_url: str, max_pages: int = None) -> str:
    try:
        r = requests.get(start_url, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception:
        return ""
