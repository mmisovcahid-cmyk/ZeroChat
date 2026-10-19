"""
ZeroChat - Giriş Noktası
Uygulamayı başlatan ana dosya.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import config
from config import COLORS, UDP_PORT
from gui.theme import FONTS, apply_theme, set_theme
from app import ZeroChatApp, NetworkStartError
from network.socket import (
    get_local_ip,
    get_mac_address,
    get_subnet_broadcast,
    get_interface_by_name,
)
import storage


def show_login():
    """Kullanıcı adı giriş ekranı."""
    login_window = tk.Tk()
    login_window.title("ZeroChat - Giriş")
    login_window.geometry("420x430")
    login_window.minsize(420, 430)

    # Tema seçimi (açılışta) - son seçim hatırlanır
    settings = config.load_settings()
    theme_var = tk.StringVar(value=settings.get("theme", config.THEME))
    set_theme(theme_var.get())
    apply_theme(login_window)
    login_window.configure(bg=COLORS["sidebar"])

    tk.Label(
        login_window, text="ZeroChat",
        font=("Segoe UI", 28, "bold"),
        bg=COLORS["sidebar"], fg=COLORS["accent"],
    ).pack(pady=(24, 4))

    tk.Label(
        login_window, text="LAN Sohbet Uygulaması",
        font=FONTS["small"], bg=COLORS["sidebar"], fg=COLORS["text_secondary"],
    ).pack(pady=(0, 14))

    # Tema seçici
    theme_frame = tk.Frame(login_window, bg=COLORS["sidebar"])
    theme_frame.pack(pady=(0, 10))

    tk.Label(
        theme_frame, text="Tema:", font=FONTS["small"],
        bg=COLORS["sidebar"], fg=COLORS["text_secondary"],
    ).pack(side="left", padx=(0, 8))

    for name, label in (("light", "☀ Açık"), ("dark", "🌙 Koyu")):
        ttk.Radiobutton(
            theme_frame, text=label, variable=theme_var, value=name,
            style="Modern.TRadiobutton",
            command=lambda: _apply_theme_choice(theme_var.get(), login_window),
        ).pack(side="left", padx=4)

    tk.Label(
        login_window, text="Kullanıcı Adı:", font=FONTS["body"],
        bg=COLORS["sidebar"], fg=COLORS["text"],
    ).pack(anchor="w", padx=55)

    entry = ttk.Entry(login_window, style="Modern.TEntry", font=FONTS["heading"])
    entry.pack(fill="x", padx=55, ipady=6, pady=(4, 10))
    entry.focus()

    # Cihaz kimliği bilgisi
    # Kayıtlı arayüz tercihi varsa o arayüz kullanılır
    saved_name = settings.get("interface", "")
    saved_iface = get_interface_by_name(saved_name) if saved_name else None

    if saved_iface:
        local_ip = saved_iface["ip"]
        local_mac = get_mac_address(local_ip)
        local_broadcast = get_subnet_broadcast(local_ip, saved_iface.get("mask"))
    else:
        local_ip = get_local_ip()
        local_mac = get_mac_address(local_ip)
        local_broadcast = get_subnet_broadcast(local_ip)

    tk.Label(
        login_window, text="Cihaz Kimliğiniz (MAC):", font=FONTS["body"],
        bg=COLORS["sidebar"], fg=COLORS["text"],
    ).pack(anchor="w", padx=55)

    tk.Label(
        login_window, text=local_mac,
        font=("Consolas", 12, "bold"), bg=COLORS["sidebar"], fg=COLORS["accent"],
    ).pack(anchor="w", padx=55, pady=(2, 2))

    tk.Label(
        login_window, text=f"IP: {local_ip}   |   Yayın: {local_broadcast}",
        font=("Consolas", 9), bg=COLORS["sidebar"], fg=COLORS["text_secondary"],
    ).pack(anchor="w", padx=55, pady=(0, 4))

    # Kayıtlı geçmiş var mı?
    history = storage.load_history()
    if history:
        total = sum(len(m) for m in history.values())
        tk.Label(
            login_window, text=f"{len(history)} sohbet, {total} mesaj kayıtlı",
            font=FONTS["tiny"], bg=COLORS["sidebar"], fg=COLORS["online"],
        ).pack(anchor="w", padx=55, pady=(0, 10))

    def start():
        user_name = entry.get().strip()
        if not user_name:
            messagebox.showwarning("Uyarı", "Lütfen kullanıcı adı girin!")
            return

        try:
            app = ZeroChatApp()
            # Kullanıcı ID'si MAC adresi -> cihazlar birbirini bu ID ile tanır
            app.start(local_mac, user_name)
        except NetworkStartError as e:
            messagebox.showerror(
                "Ağ Hatası",
                f"ZeroChat ağ dinleyicisini başlatamadı.\n\n{e}\n\n"
                f"Port {UDP_PORT} başka bir program tarafından kullanılıyor olabilir. "
                "O programı kapatıp tekrar deneyin.",
            )
            return
        except Exception as e:  # beklenmeyen hata
            messagebox.showerror(
                "Hata", f"Uygulama başlatılırken hata oluştu:\n\n{e}"
            )
            return

        # Uygulama kapandı, giriş ekranını da kapat
        login_window.destroy()

    ttk.Button(
        login_window, text="Başla", style="Accent.TButton", command=start,
    ).pack(pady=6, padx=55, fill="x")

    entry.bind("<Return>", lambda e: start())

    login_window.mainloop()


def _apply_theme_choice(theme_name, window):
    """Tema seçimini uygular, pencereyi yeniden renklendirir ve kaydeder."""
    set_theme(theme_name)
    apply_theme(window)
    window.configure(bg=COLORS["sidebar"])
    _recolor(window)

    # Seçimi hatırla (bir sonraki açılışta aynı tema gelsin)
    settings = config.load_settings()
    settings["theme"] = theme_name
    config.save_settings(settings)


def _recolor(widget):
    """Widget ağacındaki tüm arka planları yeni tema rengine çevirir."""
    try:
        if "bg" in widget.keys():
            widget.configure(bg=COLORS["sidebar"])
    except tk.TclError:
        pass

    for child in widget.winfo_children():
        _recolor(child)


if __name__ == "__main__":
    show_login()
