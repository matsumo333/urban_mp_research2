# main.py
from datetime import datetime
import sys
import os
import re
import tkinter as tk
from tkinter import Tk, Label, messagebox

EXPIRE_DATE = "2026-01-31"


def check_expire():
    today = datetime.now().date()
    expire = datetime.strptime(EXPIRE_DATE, "%Y-%m-%d").date()
    if today > expire:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("利用期限切れ", f"利用期限は {EXPIRE_DATE} までです。")
        root.destroy()
        sys.exit(0)


check_expire()

# ==========================================
# インポート
# ==========================================
from municipality_selector_gui import select_municipality
from municipality_detector import detect_municipality_name
from search_types.google_cse import search as google_cse_search
from search_types.internal_search import search as internal_search
from search_types.hierarchical_entry import search as hierarchical_entry_search
from search_types.sitemap import search as sitemap
from search_types.google_broad_search import search as google_broad_search
from link_extractor import extract_links
from deep_pdf_finder import find_pdfs_recursively
from result_collector import save_results
from pdf_selector_gui import show_pdf_selector
from detect_search_profile import detect_search_profile

# ==========================================
# 設定
# ==========================================
MAX_PAGES = 3
PDF_DIR = "output/pdfs"
root = None

SEARCH_FUNCS = {
    "google_cse": google_cse_search,
    "internal_search": internal_search,
    "hierarchical_entry": hierarchical_entry_search,
    "sitemap": sitemap,
}


# ==========================================
# PDF初期化
# ==========================================
def clear_pdf_files():
    os.makedirs(PDF_DIR, exist_ok=True)
    for f in os.listdir(PDF_DIR):
        if f.lower().endswith(".pdf"):
            try:
                os.remove(os.path.join(PDF_DIR, f))
            except Exception:
                pass


# ==========================================
# 1自治体分の処理
# ==========================================
def run_once():
    global root

    selection = select_municipality(root)
    if selection is None:
        return False

    url = selection.get("url")
    municipality = selection.get("municipality")

    if not url or not re.match(r"^https?://", url):
        return True

    city = municipality or detect_municipality_name(url)
    clear_pdf_files()

    # 検索中ポップアップ
    loading = tk.Toplevel(root)
    loading.title("検索中")
    loading.geometry("600x220+800+150")
    loading.attributes("-topmost", True)

    Label(loading, text=f"{city} を検索中", font=("MS Gothic", 14, "bold")).pack(
        pady=(20, 8)
    )
    status = Label(loading, text="準備中…", font=("MS Gothic", 12))
    status.pack()

    loading.update()
    root.update()

    # 検索仕様解析
    status.config(text="検索仕様を解析中…")
    loading.update()

    profile = detect_search_profile(url)
    engine = profile.get("engine")
    input_id = profile.get("input_id")

    if engine == "google_cse":
        strategies = ["google_cse", "hierarchical_entry", "sitemap"]
    elif engine == "internal":
        strategies = ["internal_search", "hierarchical_entry", "sitemap"]
    else:
        strategies = ["hierarchical_entry", "sitemap"]

    records = []

    for strategy in strategies:
        status.config(text=f"{strategy} で検索中…")
        loading.update()
        root.update()

        func = SEARCH_FUNCS[strategy]
        try:
            if strategy == "google_cse":
                html = func(start_url=url, max_pages=MAX_PAGES, input_id=input_id)
            elif strategy == "internal_search":
                html = func(start_url=url, max_pages=MAX_PAGES)
            else:
                html = func(start_url=url)

            if not html:
                continue

            links = extract_links(html, url)
            for _, link in links:
                records.extend(find_pdfs_recursively(link, city, max_depth=3))
                if records:
                    break

            if records:
                break

        except Exception as e:
            print(f"⚠ {strategy} エラー: {e}")

    # 最後の砦：Google広域検索（＋手動確認）
    if not records:
        records = google_broad_search(city)

    loading.destroy()

    if records:
        save_results(records)
        show_pdf_selector()
    else:
        messagebox.showwarning("警告", "PDFが見つかりませんでした")

    return True


def main():
    global root
    root = Tk()
    root.withdraw()

    while True:
        if not run_once():
            break
        if not messagebox.askyesno("完了", "別の自治体を検索しますか？"):
            break

    root.destroy()


if __name__ == "__main__":
    main()
