import os
import requests
from pypdf import PdfReader, PdfWriter
from urllib.parse import urlparse
from tkinter import filedialog, messagebox

TEMP_DIR = "output/tmp"


def get_unique_filename(dir_path: str, base_name: str) -> str:
    """
    同名ファイルが存在する場合、
    file.pdf → file (2).pdf → file (3).pdf … を返す
    """
    name, ext = os.path.splitext(base_name)
    candidate = base_name
    counter = 2

    while os.path.exists(os.path.join(dir_path, candidate)):
        candidate = f"{name} ({counter}){ext}"
        counter += 1

    return candidate


def merge_selected_pdfs(records, city):
    # -----------------------
    # 保存先フォルダを選択
    # -----------------------
    output_dir = filedialog.askdirectory(title="結合PDFの保存先を選択してください")

    if not output_dir:
        messagebox.showinfo("キャンセル", "保存先が選択されなかったため中止しました")
        return None

    os.makedirs(TEMP_DIR, exist_ok=True)

    writer = PdfWriter()

    # -----------------------
    # PDF収集・結合
    # -----------------------
    for r in records:
        url = r.get("url")
        if not url:
            continue

        filename = os.path.basename(urlparse(url).path)
        if not filename.lower().endswith(".pdf"):
            continue

        temp_path = os.path.join(TEMP_DIR, filename)

        # --- PDFダウンロード ---
        if not os.path.exists(temp_path):
            try:
                print(f"📥 取得中: {url}")
                res = requests.get(url, timeout=20)

                if res.status_code != 200:
                    print(f"⏭ スキップ（取得不可 {res.status_code}）: {url}")
                    continue

                with open(temp_path, "wb") as f:
                    f.write(res.content)

            except Exception as e:
                print(f"⚠ 取得失敗（スキップ）: {url}")
                continue

        # --- PDF結合 ---
        try:
            reader = PdfReader(temp_path)
            for page in reader.pages:
                writer.add_page(page)
        except Exception:
            print(f"⚠ PDF追加失敗（スキップ）: {filename}")
            continue

    if len(writer.pages) == 0:
        messagebox.showwarning("警告", "結合できるPDFがありませんでした")
        return None

    # -----------------------
    # 出力ファイル名決定
    # -----------------------
    base_filename = f"{city}_都市計画マスタープラン.pdf"
    unique_filename = get_unique_filename(output_dir, base_filename)

    output_file = os.path.join(output_dir, unique_filename)

    # -----------------------
    # 保存
    # -----------------------
    with open(output_file, "wb") as f:
        writer.write(f)

    print(f"✅ 結合PDF作成: {output_file}")
    messagebox.showinfo("完了", f"結合PDFを作成しました:\n{output_file}")

    return output_file
