import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import time
import re

# --- キーワード設定 ---
PRIMARY_GOAL_KEYWORDS = ["都市計画マスタープラン", "都市マスタープラン", "都市マスタ"]
SECONDARY_GOAL_KEYWORDS = ["総合計画", "立地適正化", "まちづくり計画", "施策"]
PARENT_KEYWORDS = ["まちづくり", "都市計画", "景観"]
EXCLUDE_TEXT_KEYWORDS = ["移転し", "移転しました", "閉鎖"]

def search(start_url: str, max_depth: int = 5):
    domain = urlparse(start_url).netloc
    visited = set()
    to_crawl = []  # (url, depth, priority)
    
    primary_found = []
    secondary_found = []

    # ★追加：サイトマップで「都市計画」が見つかったかどうかのフラグ
    urban_planning_in_sitemap = False

    start_url = start_url.rstrip("/") + "/"
    to_crawl.append((start_url, 0, 0))

    while to_crawl and (len(primary_found) + len(secondary_found)) < 40:
        to_crawl.sort(key=lambda x: x[2], reverse=True)
        current_url, depth, priority = to_crawl.pop(0)

        if depth > max_depth or current_url in visited:
            continue

        visited.add(current_url)
        print(f"  [探索中] {current_url}")

        # ★追加：現在処理中のページがサイトマップかどうかを判定
        is_sitemap_page = ("sitemap" in current_url.lower()) or ("サイトマップ" in current_url)

        try:
            r = requests.get(current_url, timeout=15)
            r.encoding = r.apparent_encoding
            soup = BeautifulSoup(r.text, "html.parser")

            for a in soup.find_all("a", href=True):
                raw_text = a.get_text(strip=True)
                
                if any(ex in raw_text for ex in EXCLUDE_TEXT_KEYWORDS):
                    continue

                href = a["href"]
                full_url = urljoin(current_url, href)
                
                if any(k in raw_text for k in PRIMARY_GOAL_KEYWORDS) or "#toshimasu" in full_url.lower():
                    pass 
                else:
                    full_url = urldefrag(full_url)[0]

                if urlparse(full_url).netloc != domain:
                    continue

                new_priority = 0

                # 1. 本命キーワード
                if any(k in raw_text for k in PRIMARY_GOAL_KEYWORDS):
                    new_priority = 1000
                    if full_url not in [u[0] for u in primary_found]:
                        primary_found.append((full_url, raw_text))
                        print(f"    ⭐ 本命発見: {raw_text}")

                # 2. 予備キーワード（総合計画など）
                elif any(k in raw_text for k in SECONDARY_GOAL_KEYWORDS):
                    # ★追加：サイトマップで「都市計画」が見つかっていたら予備を完全に無視
                    if urban_planning_in_sitemap:
                        continue  # クロール候補にも入れない
                    new_priority = 100
                    if full_url not in [u[0] for u in secondary_found]:
                        secondary_found.append((full_url, raw_text))

                # 3. サイトマップ・親カテゴリ
                elif "sitemap" in full_url.lower() or "サイトマップ" in raw_text:
                    new_priority = 800
                elif any(k in raw_text for k in PARENT_KEYWORDS):
                    new_priority = 500

                    # ★追加：サイトマップページ内で「都市計画」があったらフラグを立てる
                    if is_sitemap_page and "都市計画" in raw_text:
                        urban_planning_in_sitemap = True
                        print("    🚩 サイトマップ内で「都市計画」発見 → 予備キーワードの探索を抑制します")

                # クロール候補に追加
                if new_priority > 0 and full_url not in visited:
                    if not any(url == full_url for url, d, p in to_crawl):
                        to_crawl.append((full_url, depth + 1, new_priority))

            time.sleep(0.5)
        except Exception as e:
            print(f"    エラー: {e}")
            continue

    # 最終リスト（従来通り）
    if primary_found:
        print("\n✅ 本命（マスタープラン等）が見つかったため、予備は除外しました。")
        results = [u[0] for u in primary_found]
    else:
        print("\nℹ 本命が見つからなかったため、予備（総合計画等）を表示します。")
        results = [u[0] for u in secondary_found]
            
    return results

if __name__ == "__main__":
    target = "https://www.info.city.tsu.mie.jp/www/sitemap/index.html"  # 例: サイトマップからスタートする場合
    # target = "https://www.city.example.jp/"  # トップページからスタートする場合も可
    final_urls = search(target)
    
    print("\n--- 最終結果 ---")
    for i, url in enumerate(final_urls, 1):
        print(f"{i}: {url}")