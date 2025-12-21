import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
import os
import sys


# =========================================
# 実行ディレクトリ取得（exe / py 両対応）
# =========================================
def get_base_dir():
    if getattr(sys, "frozen", False):
        # exe のある場所
        return os.path.dirname(sys.executable)
    else:
        # python 実行時のファイル位置
        return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()
PDF_DIR = os.path.join(BASE_DIR, "output", "pdfs")

KEYWORDS = ["都市", "マス"]


# =========================================
# PDF探索・保存メイン関数
# =========================================
def find_pdfs_recursively(start_url, city, max_depth=4):
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

            if "application/pdf" not in r.headers.get("Content-Type", "").lower():
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
        if depth > max_depth or url in visited:
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

        # PDF探索
        for a in soup.select("a[href*='.pdf']"):
            pdf_url = urljoin(url, a.get("href"))
            title = a.get_text(strip=True)

            local_path, status = download_pdf(pdf_url)
            print(f"  {'✅' if status == 'OK' else '⚠️'} {status}: {pdf_url}")

            results.append(
                {
                    "city": city,
                    "title": title or "PDF（名称不明）",
                    "type": "PDF",
                    "url": pdf_url,
                    "local_path": local_path or "",
                    "source": url,
                    "depth": depth,
                    "status": status,
                }
            )

        # 次のHTML探索
        for a in soup.select("a[href]"):
            text = a.get_text(strip=True)
            href = a.get("href")

            if not text or not href:
                continue
            if not any(k in text for k in KEYWORDS):
                continue

            next_url = urljoin(url, href)
            if urlparse(next_url).netloc != urlparse(start_url).netloc:
                continue

            crawl(next_url, depth + 1)

    crawl(start_url, 0)
    return results
