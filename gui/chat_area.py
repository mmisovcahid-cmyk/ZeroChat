"""
ZeroChat - Sohbet Alanı (Sağ Panel)
Mesajların listelendiği ve yazıldığı alan.
"""

import tkinter as tk
from config import COLORS
from gui.message_bubble import MessageBubble


class ChatArea(tk.Frame):
    """Sağ panel - sohbet ekranı."""

    def __init__(self, parent, on_send_message):
        super().__init__(parent, bg=COLORS["chat_area"])
        self.on_send_message = on_send_message
        self.current_chat_id = None

        self._build_header()
        self._build_messages()
        self._build_input()

    def _build_header(self):
        """Sohbet başlığı."""
        self.header = tk.Frame(self, bg=COLORS["sidebar"], height=60)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        self.header_label = tk.Label(
            self.header,
            text="Bir sohbet seçin",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["sidebar"],
            fg=COLORS["text"],
        )
        self.header_label.pack(side="left", padx=15, pady=10)

        self.header_info = tk.Label(
            self.header,
            text="",
            font=("Consolas", 8),
            bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"],
        )
        self.header_info.pack(side="left")

    def _build_messages(self):
        """Mesaj listesi alanı."""
        self.msg_container = tk.Frame(self, bg=COLORS["chat_area"])
        self.msg_container.pack(fill="both", expand=True)

    def _build_input(self):
        """Mesaj yazma alanı."""
        input_frame = tk.Frame(self, bg=COLORS["sidebar"], height=60)
        input_frame.pack(fill="x", side="bottom")
        input_frame.pack_propagate(False)

        self.msg_entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 11),
            bg=COLORS["background"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10, ipady=5)
        self.msg_entry.bind("<Return>", self._on_send)

        send_btn = tk.Button(
            input_frame,
            text="Gönder",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["accent"],
            fg="white",
            relief="flat",
            padx=20,
            command=self._on_send,
        )
        send_btn.pack(side="right", padx=10, pady=10)

    def _on_send(self, event=None):
        """Gönder butonuna basıldığında."""
        text = self.msg_entry.get().strip()
        if text and self.current_chat_id:
            self.on_send_message(self.current_chat_id, text)
            self.msg_entry.delete(0, "end")

    def open_chat(self, contact_id, display_name, device_info=""):
        """Sohbeti açar.

        device_info: "IP • MAC" gibi ek cihaz bilgisi (boş olabilir)
        """
        self.current_chat_id = contact_id
        self.header_label.config(text=display_name)
        if device_info:
            self.header_info.config(text=device_info)
        else:
            self.header_info.config(text="")
        self.clear_messages()

    def clear_messages(self):
        """Mesajları temizler."""
        for widget in self.msg_container.winfo_children():
            widget.destroy()

    def add_message(self, text, is_outgoing, timestamp, sender_name=""):
        """Yeni mesaj balonu ekler."""
        bubble = MessageBubble(
            self.msg_container, text, is_outgoing, timestamp, sender_name
        )
        bubble.pack(fill="x", padx=5, pady=2)

        # En alta kaydır
        self.msg_container.update_idletasks()
