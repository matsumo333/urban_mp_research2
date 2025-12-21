# utils/manual_check_ui.py
import tkinter as tk
import webbrowser


def show_manual_check_popup(city_name: str):
    root = tk.Tk()
    root.title("手動確認のお願い")
    root.geometry("520x260")
    root.attributes("-topmost", True)

    msg = (
        f"{city_name} の都市計画マスタープランは\n\n"
        "ホームページの構造や検索仕様の関係で\n"
        "システムでは自動取得できませんでした。\n\n"
        "Google検索画面を表示しますので、\n"
        "PDFを手動で確認してください。"
    )

    label = tk.Label(root, text=msg, justify="left", font=("MS Gothic", 11))
    label.pack(padx=20, pady=20)

    def open_google():
        query = f"{city_name} 都市計画 マスタープラン"
        webbrowser.open(f"https://www.google.com/search?q={query}")
        root.destroy()

    btn = tk.Button(root, text="Google検索画面を開く", command=open_google)
    btn.pack(pady=10)

    root.mainloop()
