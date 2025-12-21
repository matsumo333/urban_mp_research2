import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


INPUT_CSV = "municipalities.csv"
OUTPUT_CSV = "municipalities_with_search.csv"
TIMEOUT = 10

SEARCH_NAME_CANDIDATES = ["q", "query", "search", "keyword", "s", "wd"]


def detect_by_html(url):
    try:
        r = requests.get(url, timeout=TIMEOUT)
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, "html.parser")

        for form in soup.find_all("form"):
            inputs = form.find_all("input")
            for inp in inputs:
                name = inp.get("name", "").lower()
                itype = inp.get("type", "").lower()
                if itype in ["text", "search"] or name in SEARCH_NAME_CANDIDATES:
                    return {
                        "has_search": True,
                        "form_action": urljoin(url, form.get("action", "")),
                        "form_method": form.get("method", "GET").upper(),
                        "input_name": inp.get("name", ""),
                        "input_id": inp.get("id", ""),
                        "input_type": inp.get("type", ""),
                        "detected_by": "html",
                    }
    except Exception:
        pass

    return None


def detect_by_selenium(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1200,900")

    driver = webdriver.Chrome(options=options)
    result = None

    try:
        driver.get(url)
        time.sleep(3)

        forms = driver.find_elements(By.TAG_NAME, "form")
        for form in forms:
            inputs = form.find_elements(By.TAG_NAME, "input")
            for inp in inputs:
                name = (inp.get_attribute("name") or "").lower()
                itype = (inp.get_attribute("type") or "").lower()

                if itype in ["text", "search"] or name in SEARCH_NAME_CANDIDATES:
                    result = {
                        "has_search": True,
                        "form_action": form.get_attribute("action"),
                        "form_method": (form.get_attribute("method") or "GET").upper(),
                        "input_name": inp.get_attribute("name"),
                        "input_id": inp.get_attribute("id"),
                        "input_type": inp.get_attribute("type"),
                        "detected_by": "selenium",
                    }
                    break
            if result:
                break

    except Exception:
        pass
    finally:
        driver.quit()

    return result


def main():
    with open(INPUT_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    fieldnames = rows[0].keys() | {
        "has_search",
        "form_action",
        "form_method",
        "input_name",
        "input_id",
        "input_type",
        "detected_by",
    }

    results = []

    for row in rows:
        url = row["url"]
        print(f"🔍 {row['municipality']} を解析中")

        data = detect_by_html(url)
        if not data:
            data = detect_by_selenium(url)

        if not data:
            data = {
                "has_search": False,
                "form_action": "",
                "form_method": "",
                "input_name": "",
                "input_id": "",
                "input_type": "",
                "detected_by": "",
            }

        results.append({**row, **data})

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print("✅ 完了:", OUTPUT_CSV)


if __name__ == "__main__":
    main()
