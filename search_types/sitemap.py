import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import time
import re

# --- キーワード設定 ---
# 本命：これが見つかれば最優先
PRIMARY_GOAL_KEYWORDS = ["都市計画マスタープラン", "都市マスタープラン", "都市マスタ"]

# 予備：本命が一つもない場合のみ、最終リストに加える
SECONDARY_GOAL_KEYWORDS = ["総合計画", "立地適正化", "まちづくり計画", "施策"]

PARENT_KEYWORDS = ["まちづくり", "都市計画", "景観"]
EXCLUDE_TEXT_KEYWORDS = ["移転し", "移転しました", "閉鎖"]

def search(start_url: str, max_depth: int = 5):
    domain = urlparse(start_url).netloc
    visited = set()
    to_crawl = []  # (url, depth, priority)
    
    primary_found = []    # 本命リスト
    secondary_found = []  # 予備リスト

    start_url = start_url.rstrip("/") + "/"
    to_crawl.append((start_url, 0, 0))

    while to_crawl and (len(primary_found) + len(secondary_found)) < 40:
        to_crawl.sort(key=lambda x: x[2], reverse=True)
        current_url, depth, priority = to_crawl.pop(0)

        if depth > max_depth or current_url in visited:
            continue

        visited.add(current_url)
        print(f"  [探索中] {current_url}")

        try:
            r = requests.get(current_url, timeout=15)
            r.encoding = r.apparent_encoding
            soup = BeautifulSoup(r.text, "html.parser")

            for a in soup.find_all("a", href=True):
                raw_text = a.get_text(strip=True)
                
                # 「移転し」除外
                if any(ex in raw_text for ex in EXCLUDE_TEXT_KEYWORDS):
                    continue

                href = a["href"]
                full_url = urljoin(current_url, href)
                
                # マスタープラン系のアンカー(#)保持
                if any(k in raw_text for k in PRIMARY_GOAL_KEYWORDS) or "#toshimasu" in full_url.lower():
                    pass 
                else:
                    full_url = urldefrag(full_url)[0]

                if urlparse(full_url).netloc != domain:
                    continue

                new_priority = 0
                
                # 1. 本命キーワードの判定
                if any(k in raw_text for k in PRIMARY_GOAL_KEYWORDS):
                    new_priority = 1000
                    if full_url not in [u[0] for u in primary_found]:
                        primary_found.append((full_url, raw_text))
                        print(f"    ⭐ 本命発見: {raw_text}")

                # 2. 予備キーワード（総合計画など）の判定
                elif any(k in raw_text for k in SECONDARY_GOAL_KEYWORDS):
                    new_priority = 100 # クロール優先度は低く設定
                    if full_url not in [u[0] for u in secondary_found]:
                        secondary_found.append((full_url, raw_text))

                # 3. サイトマップ・親カテゴリ（探索用）
                elif "sitemap" in full_url.lower() or "サイトマップ" in raw_text:
                    new_priority = 800
                elif any(k in raw_text for k in PARENT_KEYWORDS):
                    new_priority = 500

                # クロール候補に追加
                if new_priority > 0 and full_url not in visited:
                    if not any(url == full_url for url, d, p in to_crawl):
                        to_crawl.append((full_url, depth + 1, new_priority))

            time.sleep(0.5)
        except:
            continue

    # --- 最終リストの作成ロジック ---
    # 本命が1つでもあれば、本命のみを返す。
    # 本命が0件の場合のみ、予備（総合計画など）を返す。
    if primary_found:
        print("\n✅ 本命（マスタープラン等）が見つかったため、予備は除外しました。")
        results = [u[0] for u in primary_found]
    else:
        print("\nℹ 本命が見つからなかったため、予備（総合計画等）を表示します。")
        results = [u[0] for u in secondary_found]
            
    return results

if __name__ == "__main__":
    target = "https://www.info.city.tsu.mie.jp/www/sitemap/index.html"
    final_urls = search(target)
    
    print("\n--- 最終結果 ---")
    for i, url in enumerate(final_urls, 1):
        print(f"{i}: {url}")