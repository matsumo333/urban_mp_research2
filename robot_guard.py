# robot_guard.py

from tkinter import Tk, messagebox
from bs4 import BeautifulSoup


def is_robot_warning(html: str) -> bool:
    """
    本物のロボットチェック画面かどうかを判定する
    """
    if not html:
        return False

    soup = BeautifulSoup(html, "html.parser")

    # =========================
    # ① reCAPTCHA iframe
    # =========================
    if soup.select_one("iframe[src*='recaptcha']"):
        return True

    # =========================
    # ② g-recaptcha クラス
    # =========================
    if soup.select_one(".g-recaptcha"):
        return True

    # =========================
    # ③ Cloudflare / verify系
    # =========================
    text = soup.get_text().lower()

    STRONG_PHRASES = [
        "i am not a robot",
        "私はロボットではありません",
        "captcha verification",
        "verify you are human",
        "checking your browser",
    ]

    return any(p in text for p in STRONG_PHRASES)


def handle_manual_if_needed(driver):
    """
    ロボット検知時のみ、GUIで手動操作を促す
    """
    html = driver.page_source

    if not is_robot_warning(html):
        return html  # ← ここが重要（誤検知しない）

    root = Tk()
    root.withdraw()

    print("\n⚠ 実際のロボットチェック画面を検出しました")

    messagebox.showinfo(
        "手動操作が必要です",
        "ロボットチェック画面が表示されています。\n\n"
        "ブラウザで以下を手動で行ってください：\n"
        "・「私はロボットではありません」をチェック\n"
        "・必要な認証を完了\n"
        "・通常の検索結果画面に遷移\n\n"
        "完了したら OK を押してください。"
    )

    return driver.page_source
