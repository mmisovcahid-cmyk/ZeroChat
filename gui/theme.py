"""
ZeroChat - Modern Tema

Tkinter'ın varsayılan widget stilleri 90'lar tarzıdır (Windows 95 gibi).
Burada ttk (themed tkinter) kullanılarak "clam" teması özelleştirilir
ve modern, düz bir görünüm elde edilir.

Ayrıca koyu tema desteği sağlar.
"""

import tkinter as tk
from tkinter import ttk

import config


# ---------------------------------------------------------------------------
# Font tanımları
# ---------------------------------------------------------------------------

FONTS = {
    "title": ("Segoe UI", 14, "bold"),
    "heading": ("Segoe UI", 12, "bold"),
    "subtitle": ("Segoe UI", 10, "bold"),
    "body": ("Segoe UI", 10),
    "body_bold": ("Segoe UI", 10, "bold"),
    "small": ("Segoe UI", 9),
    "tiny": ("Segoe UI", 8),
    "tiny_bold": ("Segoe UI", 8, "bold"),
    "code": ("Consolas", 10),
    "code_bold": ("Consolas", 14, "bold"),
}


# ---------------------------------------------------------------------------
# Tema uygulama
# ---------------------------------------------------------------------------

def set_theme(name):
    """Aktif temayı ayarlar ve COLORS sözlüğünü günceller."""
    if name == "dark":
        config.COLORS.clear()
        config.COLORS.update(config.COLORS_DARK)
        config.THEME = "dark"
    else:
        config.COLORS.clear()
        config.COLORS.update(config.COLORS_LIGHT)
        config.THEME = "light"


def current_theme():
    """Aktif tema adını döndürür."""
    return config.THEME


def is_dark():
    """Koyu tema aktif mi."""
    return config.THEME == "dark"


def apply_theme(root):
    """Modern ttk stillerini uygular. Uygulama açılışında çağrılır."""
    c = config.COLORS
    style = ttk.Style(root)

    # "clam" ttk'nin en özelleştirilebilir taban temasıdır.
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # --- Butonlar ---
    style.configure(
        "Accent.TButton",
        background=c["accent"],
        foreground="#FFFFFF",
        borderwidth=0,
        focusthickness=0,
        relief="flat",
        padding=(18, 8),
        font=FONTS["body_bold"],
    )
    style.map(
        "Accent.TButton",
        background=[("active", c["accent_dark"]), ("pressed", c["accent_dark"])],
        foreground=[("disabled", c["text_secondary"])],
    )

    style.configure(
        "Ghost.TButton",
        background=c["sidebar"],
        foreground=c["text"],
        borderwidth=0,
        focusthickness=0,
        relief="flat",
        padding=(10, 5),
        font=FONTS["tiny"],
    )
    style.map(
        "Ghost.TButton",
        background=[("active", c["hover"])],
        foreground=[("active", c["text"])],
    )

    style.configure(
        "Danger.TButton",
        background=c["danger"],
        foreground="#FFFFFF",
        borderwidth=0,
        focusthickness=0,
        relief="flat",
        padding=(12, 6),
        font=FONTS["tiny_bold"],
    )
    style.map("Danger.TButton", background=[("active", "#B02A37")])

    # --- Girdi alanı (sadece alt çizgi - modern görünüm) ---
    style.configure(
        "Modern.TEntry",
        fieldbackground=c["input_bg"],
        foreground=c["text"],
        borderwidth=0,
        lightcolor=c["input_bg"],
        darkcolor=c["input_bg"],
        insertcolor=c["text"],
        padding=(10, 8),
        font=FONTS["body"],
    )
    style.map(
        "Modern.TEntry",
        lightcolor=[("focus", c["accent"])],
        darkcolor=[("focus", c["accent"])],
    )

    # --- Scrollbar (ince, ok'suz) ---
    style.configure(
        "Modern.Vertical.TScrollbar",
        background=c["scrollbar"],
        troughcolor=c["chat_area"],
        bordercolor=c["chat_area"],
        lightcolor=c["chat_area"],
        darkcolor=c["chat_area"],
        arrowcolor=c["chat_area"],
        borderwidth=0,
        arrowsize=0,
        width=8,
    )
    style.map(
        "Modern.Vertical.TScrollbar",
        background=[("active", c["text_secondary"])],
    )

    # --- Onay kutusu / radyo (düz görünüm) ---
    style.configure(
        "Modern.TCheckbutton",
        background=c["sidebar"],
        foreground=c["text"],
        focusthickness=0,
        borderwidth=0,
        font=FONTS["small"],
    )
    style.map("Modern.TCheckbutton", background=[("active", c["sidebar"])])

    style.configure(
        "Modern.TRadiobutton",
        background=c["sidebar"],
        foreground=c["text"],
        focusthickness=0,
        borderwidth=0,
        font=FONTS["small"],
    )
    style.map("Modern.TRadiobutton", background=[("active", c["sidebar"])])

    # --- Progressbar (dosya indirme) ---
    style.configure(
        "Modern.Horizontal.TProgressbar",
        background=c["accent"],
        troughcolor=c["border"],
        borderwidth=0,
        thickness=6,
    )

    # --- Frame ---
    style.configure("Modern.TFrame", background=c["sidebar"])
    style.configure("Card.TFrame", background=c["card_bg"])

    return style


# ---------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# ---------------------------------------------------------------------------

def current_palette():
    """Aktif renk sözlüğünün kopyasını döndürür."""
    return dict(config.COLORS)
