import os
import requests
from urllib.parse import urlparse, unquote

OUTPUT_DIR = "output/pdfs"

def download_pdfs(pdf_urls):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    downloaded = []

    for url in pdf_urls:
        try:
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path)

            # URLエンコード解除（日本語ファイル名対策）
            filename = unquote(filename)

            if not filename.lower().endswith(".pdf"):
                continue

            save_path = os.path.join(OUTPUT_DIR, filename)

            # 既に存在する場合はスキップ
            if os.path.exists(save_path):
                print(f"⏭ 既に存在: {filename}")
                continue

            print(f"📥 ダウンロード中: {filename}")

            r = requests.get(url, timeout=20, stream=True)
            r.raise_for_status()

            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            downloaded.append(save_path)

        except Exception as e:
            print(f"⚠ ダウンロード失敗: {url} ({e})")

    return downloaded
