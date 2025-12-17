from selenium import webdriver

def search(url):
    print("⚠ 検索方式不明：トップページのみ保存")

    driver = webdriver.Chrome()
    driver.get(url)
    html = driver.page_source
    driver.quit()
    return html
