# main.py

import re
from tkinter import Tk, messagebox

from municipality_selector_gui import select_municipality

from municipality_detector import detect_municipality_name
from search_strategy_detector import detect_search_strategy_candidates

from search_types.google_cse import search as google_cse_search
from search_types.internal_search import search as internal_search
from search_types.topical_entry import search as topical_entry_search
from search_types.hierarchical_entry import search as hierarchical_entry_search
from search_types.fallback import search as fallback_search

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
}

root = None  # Tkインスタンス

# ==========================================
# ロボット判定時の手動待機（ポップアップ）
# ==========================================
def wait_for_manual_robot_action(strategy: str):
    messagebox.showinfo(
        "手動操作が必要です",
        f"検索方式「{strategy}」でロボット判定が出た可能性があります。\n\n"
        "・ブラウザ画面を確認してください\n"
        "・「私はロボットではありません」等を手動で操作してください\n\n"
        "完了したら OK を押すと検索を再開します。"
    )


# ==========================================
# 1自治体分の処理
# ==========================================
def run_once():
    global root

    # ----------------------------------
    # 自治体選択（CSV + GUI）
    # ----------------------------------
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

    # URL形式チェック
    if not re.match(r"^https?://", url, re.IGNORECASE):
        messagebox.showerror(
            "エラー",
            "有効なURLではありません\n（http:// または https://）"
        )
        return False

    print(f"\n🏙 選択された自治体: {municipality}")
    print(f"🌐 自治体トップURL: {url}")

    # ----------------------------------
    # 自治体名の確定
    # （GUI選択を最優先）
    # ----------------------------------
    city = municipality or detect_municipality_name(url)
    print(f"✅ 使用する自治体名: {city}")

    # ----------------------------------
    # 検索方式の決定
    # ----------------------------------
    strategies = detect_search_strategy_candidates(url)
    print(f"🔍 検索方式候補: {strategies}")

    result = None
    used_strategy = None

    # ==============================
    # 検索方式を順番に試行
    # ==============================
    for strategy in strategies:
        print(f"▶ 検索方式を試行中: {strategy}")

        func = SEARCH_FUNCS[strategy]

        try:
            if strategy in ("google_cse", "internal_search"):
                result = func(start_url=url, max_pages=MAX_PAGES)
            else:
                result = func(start_url=url)

            if result:
                used_strategy = strategy
                break

        except Exception as e:
            print(f"⚠ {strategy} でエラー発生: {e}")

            # ★ ロボット判定時は手動対応ポップアップ
            wait_for_manual_robot_action(strategy)

            try:
                print("🔁 手動操作後に再試行します")
                if strategy in ("google_cse", "internal_search"):
                    result = func(start_url=url, max_pages=MAX_PAGES)
                else:
                    result = func(start_url=url)

                if result:
                    used_strategy = strategy
                    break

            except Exception as e2:
                print(f"❌ 再試行失敗: {e2}")

    if not used_strategy:
        messagebox.showerror(
            "エラー",
            "有効な検索方式が見つかりませんでした"
        )
        return True

    print(f"✅ 使用した検索方式: {used_strategy}")

    # ----------------------------------
    # リンク抽出
    # ----------------------------------
    if used_strategy in ("topical_entry", "hierarchical_entry"):
        links = [(u, u) for u in result]
    else:
        links = extract_links(result)

    if not links:
        messagebox.showwarning(
            "警告",
            "関連リンクが見つかりませんでした"
        )
        return True

    save_links_csv(links, LINKS_CSV)

    # ----------------------------------
    # PDF探索
    # ----------------------------------
    records = []

    for title, link in links:
        try:
            depth = 1 if link.lower().endswith(".pdf") else 4
            found = find_pdfs_recursively(
                start_url=link,
                city=city,
                max_depth=depth
            )
            records.extend(found)

        except Exception as e:
            print(f"⚠ PDF探索エラー ({link}): {e}")

    if not records:
        messagebox.showwarning(
            "警告",
            "関連するPDFが見つかりませんでした"
        )
        return True

    save_results(records)

    # ----------------------------------
    # PDF選択・結合
    # ----------------------------------
    show_pdf_selector()

    return True


# ==============================
# メインループ
# ==============================
def main():
    global root

    root = Tk()
    root.withdraw()  # メインウィンドウは非表示

    while True:
        cont = run_once()

        if not cont:
            break

        answer = messagebox.askyesno(
            "完了",
            "PDFの処理が完了しました。\n\n"
            "別の自治体を続けて検索しますか？"
        )

        if not answer:
            break

    print("\n👋 アプリを終了します")
    root.destroy()


if __name__ == "__main__":
    main()
