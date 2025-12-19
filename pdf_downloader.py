import os
import requests
from urllib.parse import urlparse, unquote

OUTPUT_DIR = "output/pdfs"

def clear_previous_downloads():
    """
    output/pdfs/ フォルダ内の前回の個別PDFをすべて削除
    次に新しい自治体を処理するときに必ず呼び出す
    """
    if not os.path.exists(OUTPUT_DIR):
        return

    deleted_count = 0
    for filename in os.listdir(OUTPUT_DIR):
        file_path = os.path.join(OUTPUT_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # ファイルやシンボリックリンクを削除
                deleted_count += 1
        except Exception as e:
            print(f"⚠ 削除失敗: {file_path} ({e})")

    if deleted_count > 0:
        print(f"🗑 前回の個別PDF {deleted_count} ファイルをすべて削除しました")
    else:
        print("🧹 前回の個別PDFはありません（クリーンな状態）")


def download_pdfs(pdf_urls):
    """
    PDFをダウンロードするメイン関数
    呼び出し前に clear_previous_downloads() を実行することを推奨
    """
    # フォルダ作成
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ★ここが重要：最初に前回のファイルをすべて削除★
    clear_previous_downloads()

    downloaded = []

    for url in pdf_urls:
        try:
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path)

            # URLエンコード解除（日本語ファイル名対策）
            filename = unquote(filename)

            if not filename.lower().endswith(".pdf"):
                print(f"⏭ PDFでないためスキップ: {filename}")
                continue

            save_path = os.path.join(OUTPUT_DIR, filename)

            print(f"📥 ダウンロード中: {filename}")

            r = requests.get(url, timeout=30, stream=True)
            r.raise_for_status()

            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print(f"✓ ダウンロード完了: {filename}")
            downloaded.append(save_path)

        except Exception as e:
            print(f"⚠ ダウンロード失敗: {url} ({e})")

    return downloaded