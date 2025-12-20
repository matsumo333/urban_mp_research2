import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
import os

# =========================================
# 設定
# =========================================
KEYWORDS = ["都市", "マス"]
PDF_DIR = "output/pdfs"


# =========================================
# PDFファイルだけ削除（フォルダは残す）
# =========================================
def clear_pdf_files():
    if not os.path.exists(PDF_DIR):
        return

    for filename in os.listdir(PDF_DIR):
        if filename.lower().endswith(".pdf"):
            try:
                os.remove(os.path.join(PDF_DIR, filename))
            except Exception as e:
                print(f"⚠️ 削除失敗: {filename} ({e})")


# =========================================
# PDF探索・保存メイン関数
# =========================================
def find_pdfs_recursively(start_url, city, max_depth=4):
    # ★ 実行時に過去PDFを全削除（②方式）
    clear_pdf_files()

    visited = set()
    results = []

    os.makedirs(PDF_DIR, exist_ok=True)

    # -------------------------------------
    # PDFダウンロード
    # -------------------------------------
    def download_pdf(pdf_url):
        filename = os.path.basename(urlparse(pdf_url).path)
        filename = unquote(filename) or "document.pdf"

        safe_city = city.replace(" ", "")
        save_name = f"{safe_city}_{filename}"
        save_path = os.path.join(PDF_DIR, save_name)

        if os.path.exists(save_path):
            return save_path, "SKIP_EXISTS"

        try:
            r = requests.get(pdf_url, timeout=30, stream=True)
            r.raise_for_status()

            content_type = r.headers.get("Content-Type", "").lower()
            if "application/pdf" not in content_type:
                return None, "NOT_A_PDF_CONTENT"

            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

            return save_path, "OK"

        except requests.HTTPError:
            return None, f"HTTP_{r.status_code}"
        except Exception as e:
            return None, f"ERROR_{type(e).__name__}"

    # -------------------------------------
    # 再帰クロール
    # -------------------------------------
    def crawl(url, depth):
        if depth > max_depth:
            return
        if url in visited:
            return

        visited.add(url)
        print(f"🔍 探索中 (depth={depth}): {url}")

        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            r.encoding = r.apparent_encoding
        except Exception:
            return

        soup = BeautifulSoup(r.text, "html.parser")

        # ① PDFリンク探索
        for a in soup.select("a[href*='.pdf']"):
            href = a.get("href")
            if not href:
                continue

            title = a.get_text(strip=True)
            pdf_url = urljoin(url, href)

            local_path, status = download_pdf(pdf_url)

            print(f"  {'✅' if status == 'OK' else '⚠️'} {status}: {pdf_url}")

            results.append(
                {
                    "city": city,
                    "title": title if title else "PDF（名称不明）",
                    "type": "PDF",
                    "url": pdf_url,
                    "local_path": local_path or "",
                    "source": url,
                    "depth": depth,
                    "status": status,
                }
            )

        # ② 次のHTMLリンク探索
        for a in soup.select("a[href]"):
            text = a.get_text(separator="", strip=True)
            href = a.get("href")

            if not text or not href:
                continue

            if not any(k in text for k in KEYWORDS):
                continue

            next_url = urljoin(url, href)

            if urlparse(next_url).netloc != urlparse(start_url).netloc:
                continue

            crawl(next_url, depth + 1)

    # 実行
    crawl(start_url, 0)
    return results
