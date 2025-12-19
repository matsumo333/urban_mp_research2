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
from search_types.google_broad_search import search as google_broad_search  # 追加

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
# ロボット判定時の手動待機（ポップアップ）
# ==========================================
def wait_for_manual_robot_action(strategy: str):
    # messagebox.showinfo(
    #     "手動操作が必要です",
    #     f"検索方式「{strategy}」でロボット判定が出た可能性があります。\n\n"
    #     "・ブラウザ画面を確認してください\n"
    #     "・「私はロボットではありません」等を手動で操作してください\n\n"
    #     "完了したら OK を押すと検索を再開します。"
    # )


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
    # ----------------------------------
    city = municipality or detect_municipality_name(url)
    print(f"✅ 使用する自治体名: {city}")

    # ----------------------------------
    # ★ 「検索中」画面の表示
    # ----------------------------------
    loading_win = tk.Toplevel(root)
    loading_win.title("実行中")
    loading_win.geometry("600x180+500+350")
    loading_win.attributes("-topmost", True)
    loading_win.configure(bg="#f0f0f0")

    Label(loading_win, text=f"{city}を検索", font=("MS Gothic", 14, "bold"), bg="#f0f0f0").pack(pady=(20, 5))
    status_label = Label(loading_win, text="データ検索中\n１０分くらいかかる場合があります。", font=("MS Gothic", 13), bg="#f0f0f0")
    status_label.pack(pady=10)

    loading_win.update()

    # ----------------------------------
    # 検索方式の決定（優先順位固定）
    # ----------------------------------
    strategies = ["hierarchical_entry", "internal_search", "google_cse", "sitemap"]
    
    base_detected = detect_search_strategy_candidates(url)
    for strat in base_detected:
        if strat not in strategies and strat in SEARCH_FUNCS:
            strategies.append(strat)

    final_links = []
    used_strategy = None

    # ==============================
    # 検索方式を順番に試行
    # ==============================
    for strategy in strategies:
        if strategy == "google_broad":
            continue

        print(f"▶ 検索方式を試行中: {strategy}")
        
        status_label.config(text=f"「{strategy}」で検索中...\nしばらくお待ちください\n５分くらいかかる場合があります。")
        loading_win.update()

        func = SEARCH_FUNCS.get(strategy)
        if not func:
            continue

        try:
            if strategy in ("google_cse", "internal_search"):
                result = func(start_url=url, max_pages=MAX_PAGES)
            else:
                result = func(start_url=url)

            if result:
                if strategy in ("topical_entry", "hierarchical_entry", "sitemap"):
                    current_links = [(u, u) for u in result]
                else:
                    current_links = extract_links(result)
                
                if current_links:
                    final_links = current_links
                    used_strategy = strategy
                    print(f"  ✅ {strategy} でリンク発見")
                    break
        
        except Exception as e:
            print(f"⚠ {strategy} でエラー発生: {e}")
            loading_win.attributes("-topmost", False)
            wait_for_manual_robot_action(strategy)
            loading_win.attributes("-topmost", True)

            try:
                print("🔁 手動操作後に再試行します")
                loading_win.update()
                if strategy in ("google_cse", "internal_search"):
                    result = func(start_url=url, max_pages=MAX_PAGES)
                else:
                    result = func(start_url=url)

                if result:
                    if strategy in ("topical_entry", "hierarchical_entry", "sitemap"):
                        current_links = [(u, u) for u in result]
                    else:
                        current_links = extract_links(result)
                    
                    if current_links:
                        final_links = current_links
                        used_strategy = strategy
                        break
            except Exception as e2:
                print(f"❌ 再試行失敗: {e2}")

    if not used_strategy:
        loading_win.destroy()
        messagebox.showerror("エラー", "有効な検索方式が見つかりませんでした")
        return True

    # ----------------------------------
    # リンク保存
    # ----------------------------------
    save_links_csv(final_links, LINKS_CSV)

    # ----------------------------------
    # PDF探索（深く再帰検索）
    # ----------------------------------
    records = []
    total = len(final_links)
    for i, (title, link) in enumerate(final_links):
        status_label.config(text=f"PDFを探索中 ({i+1}/{total})\n解析中: {link[:40]}...")
        loading_win.update()

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

    # ----------------------------------
    # ★ PDFが0件 → Google広域検索実行
    # ----------------------------------
    if not records:
        print(f"\n🔍 既存方式でPDFが見つかりませんでした。Google広域検索を追加実行します: {city}")

        # status_label.config(
        #     text=f"Google広域検索を実行中...\n"
        #          f"{city} の「都市計画 マスタープラン」を検索中\n"
        #          f"ブラウザが開きます。ロボット認証が出たら手動で対応してください（30秒待機）"
        # )
        loading_win.update()

        additional_records = []

        try:
            broad_results = google_broad_search(city)

            if broad_results:
                print(f"✅ Google広域検索で {len(broad_results)}件の関連ページを発見")

                status_label.config(text="Googleで見つかったページからPDFを探索中...\n（少し時間がかかる場合があります）")
                loading_win.update()

                for idx, (b_title, b_link) in enumerate(broad_results):
                    status_label.config(
                        text=f"Google結果を解析中 ({idx+1}/{len(broad_results)})\n"
                             f"{b_title[:50]}..."
                    )
                    loading_win.update()

                    try:
                        if b_link.lower().endswith(".pdf"):
                            additional_records.append({
                                "title": b_title or os.path.basename(b_link),
                                "url": b_link,
                                "source": "google_broad_direct",
                                "depth": 0
                            })
                        else:
                            found = find_pdfs_recursively(
                                start_url=b_link,
                                city=city,
                                max_depth=3
                            )
                            additional_records.extend(found)
                    except Exception as e:
                        print(f"⚠ Google結果の個別探索エラー ({b_link}): {e}")

                records.extend(additional_records)
                print(f"✅ Google広域検索経由で追加 {len(additional_records)}件発見")

        except Exception as e:
            print(f"⚠ Google広域検索実行中にエラー: {e}")

        finally:
            if records:
                status_label.config(text="PDF発見完了！結果を保存中...")
            else:
                status_label.config(text="すべての検索を試しましたが、PDFが見つかりませんでした")
            loading_win.update()

    # ----------------------------------
    # 最終完了処理
    # ----------------------------------
    loading_win.destroy()

    if not records:
        messagebox.showwarning(
            "警告",
            "関連するPDFが見つかりませんでした。\n\n"
            "・自治体サイトの構造が特殊である\n"
            "・都市計画マスタープランが未公開である\n"
            "・検索キーワードに該当しない\n"
            "などの可能性があります。"
        )
        return True

    save_results(records)
    show_pdf_selector()

    return True


# ==============================
# メインループ
# ==============================
def main():
    global root
    root = Tk()
    root.withdraw()

    while True:
        cont = run_once()
        if not cont:
            break

        answer = messagebox.askyesno(
            "完了",
            "PDFの処理が完了しました。\n\n別の自治体を続けて検索しますか？"
        )
        if not answer:
            break

    print("\n👋 アプリを終了します")
    root.destroy()


if __name__ == "__main__":
    main()