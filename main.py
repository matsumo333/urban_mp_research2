import re
import tkinter as tk
from tkinter import Tk, messagebox, Label
import os

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

SEARCH_FUNCS = {
    "google_cse": google_cse_search,
    "internal_search": internal_search,
    "topical_entry": topical_entry_search,
    "hierarchical_entry": hierarchical_entry_search,
    "fallback": fallback_search,
    "sitemap": sitemap,
    "google_broad": google_broad_search,
}

root = None  # Tkインスタンス


# ==========================================
# ロボット判定時の手動待機
# ==========================================
def wait_for_manual_robot_action(strategy: str):
    pass
    # 必要なら messagebox を復活可能


# ==========================================
# 1自治体分の処理
# ==========================================
def run_once():
    global root

    selection = select_municipality(root)
    if selection is None:
        print("❌ キャンセルされました")
        return False

    url = selection.get("url")
    municipality = selection.get("municipality")

    if not url:
        messagebox.showerror("エラー", "URLが取得できませんでした")
        return False

    url = url.strip()
    if not re.match(r"^https?://", url, re.IGNORECASE):
        messagebox.showerror("エラー", "有効なURLではありません")
        return False

    city = municipality or detect_municipality_name(url)
    print(f"\n🏙 自治体: {city}")
    print(f"🌐 URL: {url}")

    # ----------------------------------
    # 検索中ウィンドウ
    # ----------------------------------
    loading_win = tk.Toplevel(root)
    loading_win.title("実行中")
    loading_win.geometry("600x180+800+150")
    loading_win.attributes("-topmost", True)

    Label(loading_win, text=f"{city}を検索", font=("MS Gothic", 14, "bold")).pack(
        pady=(20, 5)
    )
    status_label = Label(loading_win, text="検索中…", font=("MS Gothic", 13))
    status_label.pack(pady=10)
    loading_win.update()

    # ----------------------------------
    # 検索方式の決定
    # ----------------------------------
    strategies = ["hierarchical_entry", "internal_search", "google_cse", "sitemap"]
    detected = detect_search_strategy_candidates(url)
    for s in detected:
        if s not in strategies and s in SEARCH_FUNCS:
            strategies.append(s)

    final_links = []
    used_strategy = None

    # ----------------------------------
    # 検索方式ループ
    # ----------------------------------
    for strategy in strategies:
        if strategy == "google_broad":
            continue

        print(f"▶ 検索方式: {strategy}")
        status_label.config(text=f"{strategy} で検索中…")
        loading_win.update()

        func = SEARCH_FUNCS.get(strategy)
        if not func:
            continue

        try:
            if strategy in ("google_cse", "internal_search"):
                result = func(start_url=url, max_pages=MAX_PAGES)
            else:
                result = func(start_url=url)

            if not result:
                print(f"⚠ {strategy} 結果なし → 次へ")
                continue

            # --- リンク抽出 ---
            if strategy in ("topical_entry", "hierarchical_entry", "sitemap"):
                current_links = [(u, u) for u in result]
            else:
                current_links = extract_links(result)

            if not current_links:
                print(f"⚠ {strategy} リンク0件 → 次へ")
                continue

            # --- PDFが実在するか軽く確認 ---
            test_records = []
            for _, test_link in current_links[:3]:
                try:
                    depth = 1 if test_link.lower().endswith(".pdf") else 2
                    found = find_pdfs_recursively(
                        start_url=test_link, city=city, max_depth=depth
                    )
                    test_records.extend(found)
                except Exception:
                    pass

            if test_records:
                final_links = current_links
                used_strategy = strategy
                print(f"✅ {strategy} でPDF確認")
                break
            else:
                print(f"⚠ {strategy} PDF 0件 → 次の検索方式へ")

        except Exception as e:
            print(f"⚠ {strategy} エラー: {e}")
            wait_for_manual_robot_action(strategy)

    # ----------------------------------
    # 検索失敗
    # ----------------------------------
    if not used_strategy:
        loading_win.destroy()
        messagebox.showerror("エラー", "有効な検索方式が見つかりませんでした")
        return True

    # ----------------------------------
    # リンク保存
    # ----------------------------------
    save_links_csv(final_links, LINKS_CSV)

    # ----------------------------------
    # 本格PDF探索
    # ----------------------------------
    records = []
    for title, link in final_links:
        try:
            depth = 1 if link.lower().endswith(".pdf") else 4
            records.extend(find_pdfs_recursively(link, city, max_depth=depth))
        except Exception:
            pass

    # ----------------------------------
    # PDF 0件 → Google広域検索
    # ----------------------------------
    if not records:
        try:
            broad_results = google_broad_search(city)
            for title, link in broad_results or []:
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
            print(f"⚠ Google広域検索エラー: {e}")

    loading_win.destroy()

    if not records:
        messagebox.showwarning(
            "警告",
            "関連するPDFが見つかりませんでした。\n"
            "（自治体未公開・構造差異の可能性）",
        )
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
