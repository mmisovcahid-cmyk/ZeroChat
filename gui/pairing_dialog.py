"""
ZeroChat - Pairing (Eşleştirme) Penceresi

Sunucusuz cihaz eşleştirme: iki cihaz birbirini 6 haneli kodla tanır.
"""

import tkinter as tk
from tkinter import ttk

from config import COLORS, PAIR_CODE_LENGTH, PAIR_CODE_TIMEOUT
from gui.theme import FONTS


class PairingDialog:
    """Pairing penceresi - kod gösterir / kod ister."""

    def __init__(self, parent, on_generate=None, on_join=None, on_activate=None,
                 on_accept=None, on_reject=None):
        self.parent = parent
        self.on_generate = on_generate
        self.on_join = on_join
        self.on_activate = on_activate
        self.on_accept = on_accept
        self.on_reject = on_reject

        self.window = None
        self.code_label = None
        self.join_entry = None
        self.status_label = None

    def show(self, current_code="", pending=None):
        """Pencereyi açar."""
        if self.window and self.window.winfo_exists():
            self.window.destroy()

        win = tk.Toplevel(self.parent)
        self.window = win
        win.title("Cihaz Eşleştirme")
        win.geometry("400x420")
        win.configure(bg=COLORS["sidebar"])
        win.transient(self.parent)

        tk.Label(
            win, text="🔗 Cihaz Eşleştirme",
            font=FONTS["title"], bg=COLORS["sidebar"],
            fg=COLORS["text"],
        ).pack(pady=(18, 4))

        tk.Label(
            win, text="Sunucu olmadan cihaz eşleştirme",
            font=FONTS["small"], bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"],
        ).pack(pady=(0, 14))

        # --- Bölüm 1: Kendi kodunu göster ---
        tk.Label(
            win, text="1) KODUNU GÖSTER",
            font=FONTS["tiny_bold"], bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w", padx=20)

        tk.Label(
            win, text="Karşı taraf bu kodu girerek sana bağlanabilir.",
            font=FONTS["tiny"], bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w", padx=20, pady=(2, 6))

        self.code_label = tk.Label(
            win, text=current_code or "------",
            font=("Consolas", 26, "bold"), bg=COLORS["input_bg"],
            fg=COLORS["accent"], padx=25, pady=8,
        )
        self.code_label.pack(pady=(0, 6))

        btn_row = tk.Frame(win, bg=COLORS["sidebar"])
        btn_row.pack(pady=(0, 12))

        ttk.Button(
            btn_row, text="Yeni Kod", style="Ghost.TButton",
            command=self._generate,
        ).pack(side="left", padx=3)

        ttk.Button(
            btn_row, text="Kopyala", style="Ghost.TButton",
            command=self._copy,
        ).pack(side="left", padx=3)

        tk.Label(
            win, text=f"Kod {PAIR_CODE_TIMEOUT // 60} dakika geçerlidir.",
            font=FONTS["tiny"], bg=COLORS["sidebar"],
            fg=COLORS["offline"],
        ).pack(pady=(0, 12))

        # --- Bölüm 2: Kod ile bağlan ---
        tk.Label(
            win, text="2) KOD İLE BAĞLAN",
            font=FONTS["tiny_bold"], bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w", padx=20)

        tk.Label(
            win, text="Arkadaşının kodunu gir:",
            font=FONTS["tiny"], bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w", padx=20, pady=(2, 4))

        self.join_entry = ttk.Entry(
            win, style="Modern.TEntry", font=("Consolas", 18, "bold"),
            justify="center",
        )
        self.join_entry.pack(fill="x", padx=20, ipady=6, pady=(0, 6))
        self.join_entry.bind("<Return>", lambda e: self._join())

        ttk.Button(
            win, text="Bağlan", style="Accent.TButton", command=self._join,
        ).pack(padx=20, fill="x", pady=(0, 10))

        self.status_label = tk.Label(
            win, text="", font=FONTS["small"],
            bg=COLORS["sidebar"], fg=COLORS["accent"],
        )
        self.status_label.pack(pady=(0, 8))

        # --- Bekleyen istekler ---
        self.pending_frame = tk.Frame(win, bg=COLORS["sidebar"])
        self.pending_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.refresh_pending(pending or {})

    def set_code(self, code):
        """Kodu ekranda günceller."""
        if self.code_label:
            self.code_label.config(text=code)

    def refresh_pending(self, pending):
        """Bekleyen eşleştirme isteklerini listeler."""
        if not self.pending_frame:
            return

        for widget in self.pending_frame.winfo_children():
            widget.destroy()

        if not pending:
            tk.Label(
                self.pending_frame, text="Bekleyen istek yok",
                font=FONTS["tiny"], bg=COLORS["sidebar"],
                fg=COLORS["offline"],
            ).pack(anchor="w")
            return

        tk.Label(
            self.pending_frame, text="BEKLEYEN İSTEKLER",
            font=FONTS["tiny_bold"], bg=COLORS["sidebar"],
            fg=COLORS["accent"],
        ).pack(anchor="w", pady=(0, 4))

        for user_id, user_name in pending.items():
            row = tk.Frame(self.pending_frame, bg=COLORS["sidebar"])
            row.pack(fill="x", pady=2)

            tk.Label(
                row, text=user_name, font=FONTS["body"],
                bg=COLORS["sidebar"], fg=COLORS["text"],
            ).pack(side="left")

            ttk.Button(
                row, text="Kabul", style="Accent.TButton",
                command=lambda uid=user_id: self._accept(uid),
            ).pack(side="right", padx=2)

            tk.Label(
                row, text="Reddet", font=FONTS["tiny"],
                bg=COLORS["sidebar"], fg=COLORS["text_secondary"],
                cursor="hand2",
            ).pack(side="right", padx=8)
            row.winfo_children()[-1].bind(
                "<Button-1>", lambda e, uid=user_id: self._reject(uid)
            )

    def _generate(self):
        """Yeni kod üretir."""
        if self.on_activate:
            self.on_activate()

    def _copy(self):
        """Kodu panoya kopyalar."""
        code = self.code_label.cget("text")
        self.window.clipboard_clear()
        self.window.clipboard_append(code)
        self.window.update()
        self._set_status("Kod kopyalandı")

    def _join(self):
        """Kod ile bağlanma isteği gönderir."""
        code = self.join_entry.get().strip().upper()
        if len(code) != PAIR_CODE_LENGTH:
            self._set_status(f"Kod {PAIR_CODE_LENGTH} karakter olmalı", error=True)
            return
        if self.on_join and self.on_join(code):
            self._set_status("Bağlanma isteği gönderildi...")
            self.join_entry.delete(0, "end")

    def _accept(self, user_id):
        """Eşleştirme isteğini kabul eder."""
        if self.on_accept:
            self.on_accept(user_id)
        self._set_status("Eşleştirme kabul edildi")

    def _reject(self, user_id):
        """Eşleştirme isteğini reddeder."""
        if self.on_reject:
            self.on_reject(user_id)
        self._set_status("İstek reddedildi")

    def _set_status(self, text, error=False):
        if self.status_label:
            self.status_label.config(
                text=text, fg="#DC3545" if error else COLORS["accent"]
            )
