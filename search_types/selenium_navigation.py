import time
from selenium.webdriver.common.by import By

NAV_KEYWORDS = [
    "まちづくり",
    "都市計画",
    "マスタープラン",
    "計画",
]

def click_navigation_buttons(driver, wait=2):
    """
    画面内の a / button / img を対象に、
    日本語キーワードを含む要素を自動クリックする
    """
    clicked = set()

    elements = driver.find_elements(
        By.XPATH,
        "//a | //button | //img"
    )

    for el in elements:
        try:
            text = (el.text or "").strip()
            alt = el.get_attribute("alt") or ""
            aria = el.get_attribute("aria-label") or ""

            combined = text + alt + aria

            if not any(k in combined for k in NAV_KEYWORDS):
                continue

            key = combined + str(el.location)
            if key in clicked:
                continue

            print(f"🧭 ナビクリック: {combined}")

            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", el
            )
            time.sleep(0.5)

            try:
                el.click()
            except Exception:
                driver.execute_script("arguments[0].click();", el)

            clicked.add(key)
            time.sleep(wait)

        except Exception:
            continue
