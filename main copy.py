# main.py

from search_strategy_detector import detect_search_strategy
from municipality_detector import detect_municipality_name

from search_types.google_cse import search as google_cse_search
from search_types.internal_search import search as internal_search
from search_types.fallback import search as fallback_search
from search_types.topical_entry import search as topical_entry_search

from link_extractor import extract_links, save_links_csv, load_links_csv
from deep_pdf_finder import find_pdfs_recursively
from result_collector import save_results
from pdf_selector_gui import show_pdf_selector


# ==========================================
# 設定
# ==========================================
MAX_PAGES = 5
LINKS_CSV = r"C:\Users\matsu\Desktop\python\urban_mp_research\output\links.csv"


def main():
    # ==============================
    # ① 自治体トップURL入力
    # ==============================
    url = input("自治体トップページURLを入力してください: ").strip()
    if not url:
        print("❌ URLが入力されていません")
        return

    # ==============================
    # ② 自治体名を自動検出
    # ==============================
    city = detect_municipality_name(url)
    print(f"\n🏙 自動検出された自治体名: {city}")

    # ==============================
    # ③ 検索方式を自動判別
    # ==============================
    strategy = detect_search_strategy(url)
    print(f"🔧 検出された検索方式: {strategy}\n")

    # ==============================
    # ④ 検索実行
    # ==============================
    html = ""
    entry_urls = []

    try:
        if strategy == "google_cse":
            html = google_cse_search(start_url=url, max_pages=MAX_PAGES)

        elif strategy == "internal_search":
            html = internal_search(start_url=url, max_pages=MAX_PAGES)

        elif strategy == "topical_entry":
            # 🔑 神戸市・横浜市タイプ
            print("🔁 トップページ導線型検索を使用します")
            entry_urls = topical_entry_search(start_url=url)

        else:
            html = fallback_search(start_url=url)

    except Exception as e:
        print(f"❌ 検索処理中にエラーが発生しました: {e}")
        return

    # ==============================
    # ⑤ トップページ導線型の場合
    # ==============================
    if strategy == "topical_entry":
        if not entry_urls:
            print("❌ 都市計画・まちづくり導線が見つかりませんでした")
            return

        records = []

        for entry in entry_urls:
            print(f"🔍 導線探索開始: {entry}")
            try:
                found = find_pdfs_recursively(
                    start_url=entry,
                    city=city,
                    max_depth=5
                )
                records.extend(found)
            except Exception as e:
                print(f"⚠️ 探索エラー: {e}")

        if not records:
            print("❌ PDFを取得できませんでした")
            return

        save_results(records)
        show_pdf_selector()
        print("\n🎊 すべての処理が完了しました！")
        return

    # ==============================
    # ⑥ 通常検索：HTML解析
    # ==============================
    if not html:
        print("❌ 検索結果HTMLを取得できませんでした")
        return

    links = extract_links(html, base_url=url)

    if not links:
        print("❌ 関連リンクが見つかりませんでした")
        return

    # 中間CSVは保存のみ（将来復活用）
    save_links_csv(links, LINKS_CSV)

    # ==============================
    # ⑦ 重複除去（URL基準）
    # ==============================
    seen = set()
    unique_links = []
    for title, link in links:
        if link not in seen:
            seen.add(link)
            unique_links.append((title, link))

    print(f"\n✔ 深掘り対象リンク数: {len(unique_links)} 件\n")

    # ==============================
    # ⑧ 深掘り探索（PDF収集）
    # ==============================
    records = []

    for idx, (title, link) in enumerate(unique_links, 1):
        print(f"▶ 処理 {idx}/{len(unique_links)}: {title}")

        try:
            if link.lower().endswith(".pdf"):
                found = find_pdfs_recursively(
                    start_url=link,
                    city=city,
                    max_depth=1
                )
            else:
                found = find_pdfs_recursively(
                    start_url=link,
                    city=city,
                    max_depth=4
                )

            records.extend(found)

        except Exception as e:
            print(f"⚠️ 深掘り中にエラー: {e}")

    if not records:
        print("\n❌ PDFを取得できませんでした")
        return

    # ==============================
    # ⑨ 最終CSV保存
    # ==============================
    save_results(records)

    # ==============================
    # ⑩ PDF選択GUI起動
    # ==============================
    print("\n🖥 PDF選択画面を起動します...")
    try:
        show_pdf_selector()
    except Exception as e:
        print(f"⚠️ GUI起動に失敗しました: {e}")

    print("\n🎊 すべての処理が完了しました！")


if __name__ == "__main__":
    main()
