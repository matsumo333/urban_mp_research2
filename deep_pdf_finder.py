import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
import os

KEYWORDS = ["都市計画", "マスタープラン"]
PDF_DIR = "output/pdfs"


def find_pdfs_recursively(start_url, city, max_depth=4):
    visited = set()
    results = []

    os.makedirs(PDF_DIR, exist_ok=True)

    def download_pdf(pdf_url):
        filename = os.path.basename(urlparse(pdf_url).path)
        filename = unquote(filename) or "document.pdf"

        safe_city = city.replace(" ", "")
        save_name = f"{safe_city}_{filename}"
        save_path = os.path.join(PDF_DIR, save_name)

        if os.path.exists(save_path):
            return save_path, "SKIP_EXISTS"

        try:
            r = requests.get(pdf_url, timeout=30)
            r.raise_for_status()
        except requests.HTTPError as e:
            return None, f"HTTP_{r.status_code}"
        except Exception as e:
            return None, "DOWNLOAD_ERROR"

        with open(save_path, "wb") as f:
            f.write(r.content)

        return save_path, "OK"

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

        # ① PDFリンク
        for a in soup.select("a[href*='.pdf']"):
            href = a.get("href")
            if not href:
                continue

            title = a.get_text(strip=True)

            if href.startswith("/"):
                parsed = urlparse(url)
                pdf_url = f"{parsed.scheme}://{parsed.netloc}{href}"
            else:
                pdf_url = urljoin(url, href)

            local_path, status = download_pdf(pdf_url)

            results.append({
                "city": city,
                "title": title if title else "PDF（名称不明）",
                "type": "PDF",
                "url": pdf_url,
                "local_path": local_path or "",
                "source": url,
                "depth": depth,
                "status": status
            })

        # ② 次のHTMLリンク
        for a in soup.select("a[href]"):
            text = a.get_text(separator="", strip=True)
            href = a.get("href")

            if not text or not href:
                continue

            if not all(k in text for k in KEYWORDS):
                continue

            next_url = urljoin(url, href)

            if urlparse(next_url).netloc != urlparse(start_url).netloc:
                continue

            crawl(next_url, depth + 1)

    crawl(start_url, 0)
    return results
