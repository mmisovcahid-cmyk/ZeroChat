"""
ZeroChat - Dosya Kartı Bileşeni
Gönderilen/alınan dosyaların ilerleme çubuğuyla gösterimi.
"""

import os
import tkinter as tk
from config import COLORS


def format_size(size):
    """Bayt değerini okunabilir metne çevirir."""
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / 1024 / 1024:.1f} MB"


class FileCard(tk.Frame):
    """Tek bir dosya kartı (ilerleme çubuğu + durum)."""

    def __init__(self, parent, file_id, meta, received=0, total=0, outgoing=False):
        super().__init__(parent, bg=COLORS["incoming_bubble"],
                         padx=10, pady=8)

        self.file_id = file_id
        self.meta = meta
        self.outgoing = outgoing
        self.status = "receiving"

        self._build(received, total)

    def _build(self, received, total):
        """Kart içeriğini oluşturur."""
        name = self.meta.get("name", "dosya")
        size = self.meta.get("size", 0)

        # Başlık satırı
        header = tk.Frame(self, bg=COLORS["incoming_bubble"])
        header.pack(fill="x")

        icon = "📤" if self.outgoing else "📥"
        tk.Label(
            header, text=f"{icon} {name}",
            font=("Segoe UI", 10, "bold"), bg=COLORS["incoming_bubble"],
            fg=COLORS["text"], anchor="w",
        ).pack(side="left")

        self.size_label = tk.Label(
            header, text=format_size(size),
            font=("Segoe UI", 8), bg=COLORS["incoming_bubble"],
            fg=COLORS["text_secondary"],
        )
        self.size_label.pack(side="right")

        # İlerleme çubuğu
        self.bar_frame = tk.Frame(self, bg=COLORS["background"], height=10)
        self.bar_frame.pack(fill="x", pady=(6, 3))
        self.bar_frame.pack_propagate(False)

        self.fill = tk.Frame(self.bar_frame, bg=COLORS["accent"])
        self.fill.place(x=0, y=0, relheight=1, relwidth=0)

        # Alt satır: durum
        self.status_label = tk.Label(
            self, text="Alınıyor...", font=("Segoe UI", 8),
            bg=COLORS["incoming_bubble"], fg=COLORS["text_secondary"],
        )
        self.status_label.pack(side="left")

        self.action_label = tk.Label(
            self, text="", font=("Segoe UI", 8, "bold"),
            bg=COLORS["incoming_bubble"], fg=COLORS["accent"],
            cursor="hand2",
        )
        self.action_label.pack(side="right")

        self.update_progress(received, total)

    def update_progress(self, received, total):
        """İlerleme çubuğunu günceller."""
        if total > 0:
            percent = min(100, received / total * 100)
            self.fill.place_configure(relwidth=percent / 100)
            self.status_label.config(text=f"Alınıyor... %{percent:.0f}")
        else:
            self.fill.place_configure(relwidth=1.0)
            self.status_label.config(text="Gönderiliyor...")

    def mark_done(self, path, name, size):
        """Transfer tamamlandı."""
        self.status = "done"
        self.fill.place_configure(relwidth=1.0)
        self.fill.config(bg=COLORS["accent"])
        self.status_label.config(text=f"✓ Kaydedildi: {os.path.basename(path)}",
                                 fg=COLORS["accent"])
        self.action_label.config(text="📂 Aç")

    def mark_failed(self, reason):
        """Transfer başarısız."""
        self.status = "failed"
        self.fill.config(bg="#DC3545")
        self.status_label.config(text=f"✗ {reason}", fg="#DC3545")
