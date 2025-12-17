import csv
import tkinter as tk
from tkinter import messagebox
import webbrowser

from pdf_merger import merge_selected_pdfs
from utils import normalize_url

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

    # ==================================================
    # 終了処理（Ctrl+C、Escape、×ボタン対応）
    # ==================================================
    def on_close():
        root.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.bind("<Escape>", lambda e: on_close())
    root.bind("<Control-c>", lambda e: on_close())
    root.bind("<Control-q>", lambda e: on_close())

    # ==================================================
    # CSV 読み込み
    # ==================================================
    records = []
    with open(CSV_FILE, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("type") == "PDF":
                row["url"] = normalize_url(row.get("url"))
                records.append(row)

    if not records:
        messagebox.showerror("エラー", "PDFデータがありません")
        root.destroy()
        return

    # ==================================================
    # フォント設定
    # ==================================================
    normal_font = ("Meiryo UI", 13)
    bold_font = ("Meiryo UI", 13, "bold")
    check_font = ("Meiryo UI", 15)

    # ==================================================
    # スクロール可能なCanvas
    # ==================================================
    canvas = tk.Canvas(root, bg="white")
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    inner_frame = tk.Frame(canvas, bg="white")
    canvas.create_window((0, 0), window=inner_frame, anchor="nw")

    # ==================================================
    # ヘッダー行
    # ==================================================
    header_frame = tk.Frame(inner_frame, bg="#e8e8e8", pady=4)
    header_frame.pack(fill="x", padx=15)

    tk.Label(header_frame, text="✓", font=check_font, width=2, anchor="center", bg="#e8e8e8").pack(side="left")
    tk.Label(header_frame, text="市町村", font=bold_font, width=13, anchor="center", bg="#e8e8e8").pack(side="left")
    tk.Label(header_frame, text="タイトル", font=bold_font, anchor="w", bg="#e8e8e8").pack(side="left", expand=True, fill="x")

    tk.Frame(inner_frame, height=2, bg="gray").pack(fill="x")

    # ==================================================
    # 各行を作成
    # ==================================================
    checked = {}

    for i, r in enumerate(records):
        row_frame = tk.Frame(inner_frame, pady=0, bg="white")
        row_frame.pack(fill="x", padx=15)

        var = tk.BooleanVar(value=False)
        checked[i] = var

        # チェックボックス
        check_frame = tk.Frame(row_frame, bg="white", cursor="hand2", width=40, height=30)
        check_frame.pack(side="left", padx=(0, 5))
        check_frame.pack_propagate(False)

        check_label = tk.Label(check_frame, text="□", font=check_font, fg="gray30", bg="white")
        check_label.pack(expand=True)

        def toggle(event=None, index=i, lbl=check_label, v=var):
            v.set(not v.get())
            lbl.config(text="✓" if v.get() else "□")

        check_frame.bind("<Button-1>", toggle)
        check_label.bind("<Button-1>", toggle)

        # 市町村
        tk.Label(row_frame, text=r["city"], font=normal_font, width=13, anchor="center", bg="white").pack(side="left")

        # タイトル（同じタブで上書き開く）
        title_label = tk.Label(row_frame, text=r["title"], font=normal_font, anchor="w", fg="blue", cursor="hand2", bg="white")
        title_label.pack(side="left", expand=True, fill="x", padx=(20, 0))
        # ★★★ 修正：同じタブで上書き（new=0） ★★★
        title_label.bind("<Button-1>", lambda e, url=r["url"]: webbrowser.open(url, new=0))

        # 薄い区切り線
        if i < len(records) - 1:
            tk.Frame(inner_frame, height=1, bg="#f0f0f0").pack(fill="x")

    # ==================================================
    # Canvasスクロール領域更新
    # ==================================================
    inner_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))


    # ==================================================
    # 結合ボタン
    # ==================================================
    def on_execute():
        selected = [records[i] for i, var in checked.items() if var.get()]
        if not selected:
            messagebox.showwarning("未選択", "PDFを選択してください")
            return
        city = selected[0]["city"]
        merge_selected_pdfs(selected, city)
        messagebox.showinfo("完了", f"{city} のPDF結合が完了しました")

    btn = tk.Button(root, text="PDF結合", font=("Meiryo UI", 16), command=on_execute, pady=6)
    btn.pack(side="bottom", pady=12)

    root.mainloop()


if __name__ == "__main__":
    show_pdf_selector()