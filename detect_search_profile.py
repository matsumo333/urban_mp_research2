import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def detect_search_profile(top_url: str) -> dict:
    try:
        res = requests.get(top_url, timeout=15)
        res.raise_for_status()
    except Exception:
        return {"engine": "unknown"}

    soup = BeautifulSoup(res.text, "html.parser")

    for form in soup.find_all("form"):
        action = urljoin(top_url, form.get("action", ""))
        method = (form.get("method") or "GET").upper()

        for inp in form.find_all("input"):
            itype = (inp.get("type") or "").lower()
            if itype not in ("text", "search"):
                continue

            profile = {
                "has_search": True,
                "form_action": action,
                "form_method": method,
                "input_id": inp.get("id"),
                "input_name": inp.get("name"),
            }

            if "google.com/cse" in action:
                profile["engine"] = "google_cse"
            else:
                profile["engine"] = "internal"

            return profile

    return {"has_search": False, "engine": "none"}
