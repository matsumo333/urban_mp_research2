import requests
from urllib.parse import urljoin

SEARCH_WORDS = "都市計画 マスタープラン"


def is_google_search(action_url: str) -> bool:
    return any(x in action_url for x in [
        "google.com",
        "cse",
        "customsearch"
    ])


def submit_search(form, input_tag, base_url: str):
    method = form.get("method", "get").lower()
    action = form.get("action", "")
    action_url = urljoin(base_url, action)

    if is_google_search(action_url):
        return None, "selenium"

    name = input_tag.get("name")
    if not name:
        return None, "selenium"

    params = {name: SEARCH_WORDS}

    if method == "get":
        return requests.get(action_url, params=params), "requests"
    else:
        return requests.post(action_url, data=params), "requests"
