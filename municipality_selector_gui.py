import csv
import os
import tkinter as tk
from tkinter import ttk, messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "municipalities.csv")


def load_data():
    data = {}
    with open(CSV_FILE, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pref = row["prefecture"]
            data.setdefault(pref, []).append(row)
    return data


def select_municipality(parent):
    data = load_data()

    dialog = tk.Toplevel(parent)
    dialog.title("自治体選択")
    dialog.geometry("620x420")
    dialog.grab_set()

    result = {"url": None, "municipality": None}

    # -------------------------
    # 都道府県
    # -------------------------
    tk.Label(dialog, text="都道府県を選択").pack(pady=6)
    pref_combo = ttk.Combobox(dialog, values=sorted(data.keys()), state="readonly")
    pref_combo.pack(fill="x", padx=20)

    # -------------------------
    # 市町村
    # -------------------------
    tk.Label(dialog, text="市町村を選択").pack(pady=6)
    muni_combo = ttk.Combobox(dialog, state="readonly")
    muni_combo.pack(fill="x", padx=20)

    def on_pref_selected(event):
        pref = pref_combo.get()
        munis = [r["municipality"] for r in data[pref]]
        muni_combo["values"] = munis
        muni_combo.set("")

    pref_combo.bind("<<ComboboxSelected>>", on_pref_selected)

    # -------------------------
    # 決定
    # -------------------------
    def decide():
        pref = pref_combo.get()
        muni = muni_combo.get()

        if not pref or not muni:
            messagebox.showerror("エラー", "都道府県と市町村を選択してください")
            return

        for row in data[pref]:
            if row["municipality"] == muni:
                result["url"] = row["url"]
                result["municipality"] = muni
                dialog.destroy()
                return

    ttk.Button(dialog, text="決 定", command=decide).pack(pady=16)

    parent.wait_window(dialog)
    return result
