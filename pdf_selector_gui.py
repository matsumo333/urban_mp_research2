import csv
import tkinter as tk
from tkinter import messagebox
import webbrowser
import os

from pdf_merger import merge_selected_pdfs
from utils.normalize_url import normalize_url

# 実際に姫路市のデータが書き込まれているファイル名に合わせてください
CSV_FILE = "output/urban_plan_index.csv"


def show_pdf_selector():
    # DPI認識オフで安定表示
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(0)
    except Exception:
        pass

    root = tk.Tk()
    root.title("都市計画マスタープラン PDF選択")
    root.geometry("1400x800")

    def on_close():
        root.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.bind("<Escape>", lambda e: on_close())

    # ==================================================
    # CSV 読み込み（修正箇所：重複排除とステータス無視）
    # ==================================================
    records = []
    seen_urls = set()  # 重複チェック用

    if not os.path.exists(CSV_FILE):
        messagebox.showerror("エラー", f"CSVファイルが見つかりません:\n{CSV_FILE}")
        root.destroy()
        return

    with open(CSV_FILE, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # PDFであり、かつURLがまだ登録されていないものだけを採用
            url = normalize_url(row.get("url", ""))
            if row.get("type") == "PDF" and url and url not in seen_urls:
                row["url"] = url
                # 市町村名やタイトルが空の場合の補完
                if not row.get("city"):
                    row["city"] = "不明"
                if not row.get("title"):
                    row["title"] = "無題のPDF"

                records.append(row)
                seen_urls.add(url)

    if not records:
        messagebox.showwarning("通知", "表示できるPDFデータがCSV内にありませんでした。")
        root.destroy()
        return

    # ==================================================
    # UI設定（フォント・スクロール等）
    # ==================================================
    normal_font = ("Meiryo UI", 13)
    bold_font = ("Meiryo UI", 13, "bold")
    check_font = ("Meiryo UI", 15)

    canvas = tk.Canvas(root, bg="white")
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    inner_frame = tk.Frame(canvas, bg="white")
    canvas.create_window((0, 0), window=inner_frame, anchor="nw")

    # ヘッダー
    header_frame = tk.Frame(inner_frame, bg="#e8e8e8", pady=4)
    header_frame.pack(fill="x", padx=15)
    tk.Label(header_frame, text="✓", font=check_font, width=2, bg="#e8e8e8").pack(
        side="left"
    )
    tk.Label(header_frame, text="市町村", font=bold_font, width=13, bg="#e8e8e8").pack(
        side="left"
    )
    tk.Label(
        header_frame,
        text="タイトル (クリックで開く)",
        font=bold_font,
        anchor="w",
        bg="#e8e8e8",
    ).pack(side="left", expand=True, fill="x")

    tk.Frame(inner_frame, height=2, bg="gray").pack(fill="x")

    # 各行の生成
    checked = {}
    for i, r in enumerate(records):
        row_frame = tk.Frame(inner_frame, pady=2, bg="white")
        row_frame.pack(fill="x", padx=15)

        var = tk.BooleanVar(value=False)
        checked[i] = var

        # チェックボックス（カスタム）
        check_label = tk.Label(
            row_frame,
            text="□",
            font=check_font,
            fg="gray30",
            bg="white",
            width=2,
            cursor="hand2",
        )
        check_label.pack(side="left")

        def make_toggle(lbl, v):
            def toggle(event):
                v.set(not v.get())
                lbl.config(
                    text="✓" if v.get() else "□", fg="green" if v.get() else "gray30"
                )

            return toggle

        check_label.bind("<Button-1>", make_toggle(check_label, var))

        # 市町村名
        tk.Label(
            row_frame,
            text=r["city"],
            font=normal_font,
            width=13,
            anchor="center",
            bg="white",
        ).pack(side="left")

        # タイトル（リンク）
        title_label = tk.Label(
            row_frame,
            text=r["title"],
            font=normal_font,
            anchor="w",
            fg="blue",
            cursor="hand2",
            bg="white",
        )
        title_label.pack(side="left", expand=True, fill="x", padx=(10, 0))
        title_label.bind(
            "<Button-1>", lambda e, url=r["url"]: webbrowser.open(url, new=0)
        )

        # 区切り線
        tk.Frame(inner_frame, height=1, bg="#f0f0f0").pack(fill="x")

    inner_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    # 結合ボタン
    def on_execute():
        selected = [records[i] for i, var in checked.items() if var.get()]
        if not selected:
            messagebox.showwarning("未選択", "PDFを選択してください")
            return
        city = selected[0]["city"]
        merge_selected_pdfs(selected, city)
        messagebox.showinfo("完了", f"{city} のPDF結合が完了しました")

    btn = tk.Button(
        root,
        text="選択したPDFを結合する",
        font=("Meiryo UI", 16, "bold"),
        bg="#0078d7",
        fg="white",
        command=on_execute,
        pady=10,
    )
    btn.pack(side="bottom", fill="x", padx=50, pady=20)

    root.mainloop()


if __name__ == "__main__":
    show_pdf_selector()
