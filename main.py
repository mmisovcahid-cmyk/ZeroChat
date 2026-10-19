"""
ZeroChat - Giriş Noktası
Uygulamayı başlatan ana dosya.
"""

import tkinter as tk
from tkinter import messagebox

from config import COLORS
from app import ZeroChatApp
from network.socket import get_local_ip, get_mac_address


def show_login():
    """Kullanıcı adı giriş ekranı."""
    login_window = tk.Tk()
    login_window.title("ZeroChat - Giriş")
    login_window.geometry("380x320")
    login_window.configure(bg=COLORS["sidebar"])
    login_window.resizable(False, False)

    tk.Label(
        login_window,
        text="ZeroChat",
        font=("Segoe UI", 24, "bold"),
        bg=COLORS["sidebar"],
        fg=COLORS["accent"],
    ).pack(pady=(25, 8))

    tk.Label(
        login_window,
        text="LAN Sohbet Uygulaması",
        font=("Segoe UI", 11),
        bg=COLORS["sidebar"],
        fg=COLORS["text_secondary"],
    ).pack(pady=(0, 15))

    tk.Label(
        login_window,
        text="Kullanıcı Adı:",
        font=("Segoe UI", 10),
        bg=COLORS["sidebar"],
        fg=COLORS["text"],
    ).pack(anchor="w", padx=55)

    entry = tk.Entry(
        login_window,
        font=("Segoe UI", 12),
        bg=COLORS["background"],
        relief="flat",
        highlightthickness=1,
        highlightbackground=COLORS["border"],
    )
    entry.pack(fill="x", padx=55, ipady=5, pady=(5, 12))
    entry.focus()

    # Cihaz kimliği bilgisi
    local_ip = get_local_ip()
    local_mac = get_mac_address()

    tk.Label(
        login_window,
        text="Cihaz Kimliğiniz (MAC):",
        font=("Segoe UI", 10),
        bg=COLORS["sidebar"],
        fg=COLORS["text"],
    ).pack(anchor="w", padx=55)

    tk.Label(
        login_window,
        text=local_mac,
        font=("Consolas", 11, "bold"),
        bg=COLORS["sidebar"],
        fg=COLORS["accent"],
    ).pack(anchor="w", padx=55, pady=(2, 2))

    tk.Label(
        login_window,
        text=f"IP: {local_ip}",
        font=("Consolas", 9),
        bg=COLORS["sidebar"],
        fg=COLORS["text_secondary"],
    ).pack(anchor="w", padx=55, pady=(0, 15))

    def start():
        user_name = entry.get().strip()
        if not user_name:
            messagebox.showwarning("Uyarı", "Lütfen kullanıcı adı girin!")
            return

        login_window.destroy()
        app = ZeroChatApp()
        # Kullanıcı ID'si MAC adresi -> cihazlar birbirini bu ID ile tanır
        app.start(local_mac, user_name)

    tk.Button(
        login_window,
        text="Başla",
        font=("Segoe UI", 12, "bold"),
        bg=COLORS["accent"],
        fg="white",
        relief="flat",
        padx=40,
        pady=8,
        command=start,
    ).pack()

    entry.bind("<Return>", lambda e: start())

    login_window.mainloop()


if __name__ == "__main__":
    show_login()
