"""
ZeroChat - Mesaj Balonu Bileşeni
WhatsApp tarzı mesaj balonlarını oluşturur.
"""

import tkinter as tk
from config import COLORS


class MessageBubble(tk.Frame):
    """Tek mesaj balonu."""

    def __init__(self, parent, text, is_outgoing, timestamp, sender_name=""):
        super().__init__(parent, bg=COLORS["chat_area"])

        bubble_bg = COLORS["outgoing_bubble"] if is_outgoing else COLORS["incoming_bubble"]

        # Balon çerçevesi
        bubble = tk.Frame(self, bg=bubble_bg, padx=10, pady=6)
        bubble.pack(
            side="right" if is_outgoing else "left",
            anchor="e" if is_outgoing else "w",
            padx=10,
            pady=2,
        )

        # Gönderen adı (gelen mesajlarda)
        if not is_outgoing and sender_name:
            name_label = tk.Label(
                bubble,
                text=sender_name,
                font=("Segoe UI", 8, "bold"),
                bg=bubble_bg,
                fg=COLORS["text_secondary"],
            )
            name_label.pack(anchor="w")

        # Mesaj metni
        msg_label = tk.Label(
            bubble,
            text=text,
            font=("Segoe UI", 10),
            bg=bubble_bg,
            fg=COLORS["text"],
            wraplength=350,
            justify="left",
        )
        msg_label.pack(anchor="w")

        # Zaman damgası
        time_label = tk.Label(
            bubble,
            text=timestamp,
            font=("Segoe UI", 7),
            bg=bubble_bg,
            fg=COLORS["text_secondary"],
        )
        time_label.pack(anchor="e")
