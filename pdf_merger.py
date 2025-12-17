import os
import requests
from pypdf import PdfReader, PdfWriter
from urllib.parse import urlparse

OUTPUT_DIR = "output/merged"
TEMP_DIR = "output/tmp"


def merge_selected_pdfs(records, city):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    writer = PdfWriter()

    for r in records:
        url = r["url"]
        filename = os.path.basename(urlparse(url).path)
        temp_path = os.path.join(TEMP_DIR, filename)

        # -----------------------
        # PDFダウンロード（安全版）
        # -----------------------
        if not os.path.exists(temp_path):
            try:
                print(f"📥 取得中: {url}")
                res = requests.get(url, timeout=20)

                if res.status_code != 200:
                    print(f"⏭ スキップ（取得不可 {res.status_code}）: {url}")
                    continue

                with open(temp_path, "wb") as f:
                    f.write(res.content)

            except Exception:
                print(f"⚠ 取得失敗（スキップ）: {url}")
                continue

        # -----------------------
        # PDF結合
        # -----------------------
        try:
            reader = PdfReader(temp_path)
            for page in reader.pages:
                writer.add_page(page)
        except Exception as e:
            print(f"⚠ PDF追加失敗（スキップ）: {filename}")
            continue

    output_file = os.path.join(
        OUTPUT_DIR,
        f"{city}_都市計画マスタープラン.pdf"
    )

    with open(output_file, "wb") as f:
        writer.write(f)

    print(f"✅ 結合PDF作成: {output_file}")
    return output_file
