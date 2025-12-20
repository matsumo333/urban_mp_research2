import re
import os
import tkinter as tk
from tkinter import Tk, messagebox, Label

from municipality_selector_gui import select_municipality
from municipality_detector import detect_municipality_name
from search_strategy_detector import detect_search_strategy_candidates

from search_types.google_cse import search as google_cse_search
from search_types.internal_search import search as internal_search
from search_types.topical_entry import search as topical_entry_search
from search_types.hierarchical_entry import search as hierarchical_entry_search
from search_types.fallback import search as fallback_search
from search_types.sitemap import search as sitemap
from search_types.google_broad_search import search as google_broad_search

from link_extractor import extract_links, save_links_csv
from deep_pdf_finder import find_pdfs_recursively
from result_collector import save_results
from pdf_selector_gui import show_pdf_selector

# ==========================================
# 設定
# ==========================================
MAX_PAGES = 5
LINKS_CSV = r"C:\Users\matsu\Desktop\python\urban_mp_research\output\links.csv"
PDF_DIR = "output/pdfs"

SEARCH_FUNCS = {
    "hierarchical_entry": hierarchical_entry_search,
    "internal_search": internal_search,
    "google_cse": google_cse_search,
    "sitemap": sitemap,
}

root = None


# ==========================================
# PDF初期化（1自治体につき1回だけ）
# ==========================================
def clear_pdf_files():
    os.makedirs(PDF_DIR, exist_ok=True)
    for f in os.listdir(PDF_DIR):
        if f.lower().endswith(".pdf"):
            try:
                os.remove(os.path.join(PDF_DIR, f))
            except Exception as e:
                print(f"⚠️ 削除失敗: {f} ({e})")


# ==========================================
# 一時メッセージ表示（3秒）
# フォント・位置・サイズ調整可能
# ==========================================
def show_temp_message(parent, text, seconds=3):
    win = tk.Toplevel(parent)
    win.title("お知らせ")
    win.geometry("520x160+840+360")  # ← 位置調整
    win.attributes("-topmost", True)

    frame = tk.Frame(win, bd=2, relief="groove")
    frame.pack(expand=True, fill="both", padx=12, pady=12)

    Label(
        frame,
        text=text,
        font=("MS Gothic", 12),  # ← フォントサイズ変更可
        justify="center",
    ).pack(expand=True)

    win.after(seconds * 1000, win.destroy)
    win.update()


# ==========================================
# Google広域検索（フォールバック専用）
# ==========================================
def run_google_broad(city, loading, status):
    # 一時メッセージ表示
    show_temp_message(
        root,
        "Google検索を実行します。\n"
        "ロボット認証画面が表示された場合は\n"
        "手動で解除してください。",
        seconds=3,
    )

    # 🔑 ここが重要：3秒間 Tk のイベントを回す
    root.update()
    root.after(3000)  # ← 実際に3秒待つ
    root.update()

    status.config(text="Google広域検索中…")
    loading.update()

    records = []
    try:
        results = google_broad_search(city)
        print(f"🌍 Google検索結果: {len(results or [])} 件")

        for title, link in results or []:
            if link.lower().endswith(".pdf"):
                records.append(
                    {
                        "title": title or os.path.basename(link),
                        "url": link,
                        "source": "google_broad_direct",
                        "depth": 0,
                    }
                )
            else:
                records.extend(find_pdfs_recursively(link, city, max_depth=3))

    except Exception as e:
        print(f"❌ Google検索失敗: {e}")

    return records


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
        messagebox.showerror("エラー", "有効なURLではありません")
        return True

    city = municipality or detect_municipality_name(url)

    print("\n==============================")
    print(f"🏙 自治体: {city}")
    print(f"🌐 URL: {url}")

    clear_pdf_files()

    # 検索中ウィンドウ
    loading = tk.Toplevel(root)
    loading.title("検索中")
    loading.geometry("600x220+800+150")
    loading.attributes("-topmost", True)

    Label(
        loading,
        text=f"{city} を検索中",
        font=("MS Gothic", 14, "bold"),
    ).pack(pady=(20, 8))

    status = Label(loading, text="準備中…", font=("MS Gothic", 12))
    status.pack()

    loading.update()

    # ==================================
    # 通常検索（自動）
    # ==================================
    strategies = ["hierarchical_entry", "internal_search", "google_cse", "sitemap"]
    detected = detect_search_strategy_candidates(url)
    for s in detected:
        if s not in strategies and s in SEARCH_FUNCS:
            strategies.append(s)

    final_links = []
    used = None

    for strategy in strategies:
        status.config(text=f"{strategy} で検索中…")
        loading.update()
        print(f"▶ {strategy}")

        func = SEARCH_FUNCS.get(strategy)
        try:
            result = (
                func(start_url=url, max_pages=MAX_PAGES)
                if strategy in ("google_cse", "internal_search")
                else func(start_url=url)
            )

            if not result:
                continue

            links = (
                [(u, u) for u in result]
                if strategy in ("topical_entry", "hierarchical_entry", "sitemap")
                else extract_links(result)
            )

            test = []
            for _, link in links[:3]:
                test.extend(
                    find_pdfs_recursively(
                        start_url=link,
                        city=city,
                        max_depth=1 if link.endswith(".pdf") else 2,
                    )
                )

            if test:
                final_links = links
                used = strategy
                break

        except Exception as e:
            print(f"⚠ {strategy} エラー: {e}")

    # ==================================
    # フォールバック：Google広域検索
    # ==================================
    records = []

    if not used:
        print("⚠ 通常検索失敗 → Google広域検索へ")
        records = run_google_broad(city, loading, status)
    else:
        save_links_csv(final_links, LINKS_CSV)
        status.config(text="PDF探索中…")
        loading.update()

        for _, link in final_links:
            records.extend(find_pdfs_recursively(link, city, max_depth=4))

        if not records:
            records = run_google_broad(city, loading, status)

    loading.destroy()

    if not records:
        messagebox.showwarning("もう一度、右側のgPDFが見つかりませんでした")
        return True

    save_results(records)
    show_pdf_selector()
    return True


# ==========================================
# メイン
# ==========================================
def main():
    global root
    root = Tk()
    root.withdraw()

    while True:
        if not run_once():
            break
        if not messagebox.askyesno("完了", "別の自治体を続けて検索しますか？"):
            break

    root.destroy()


if __name__ == "__main__":
    main()
