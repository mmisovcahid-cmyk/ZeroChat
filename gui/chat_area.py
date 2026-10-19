"""
ZeroChat - Sohbet Alanı (Sağ Panel)
Mesajların listelendiği ve yazıldığı alan. Kaydırılabilir (scrollable).
"""

import tkinter as tk
from config import COLORS
from gui.message_bubble import MessageBubble


class ChatArea(tk.Frame):
    """Sağ panel - sohbet ekranı.

    Dış düzen grid ile kurulur (başlık / mesaj alanı / yazma alanı).
    Böylece mesaj alanı ekranı doldurur, yazma alanı her zaman
    görünür kalır - kaç mesaj olursa olsun.
    """

    def __init__(self, parent, on_send_message):
        super().__init__(parent, bg=COLORS["chat_area"])
        self.on_send_message = on_send_message
        self.current_chat_id = None

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self._build_header()
        self._build_messages()
        self._build_input()

    def _build_header(self):
        """Sohbet başlığı."""
        self.header = tk.Frame(self, bg=COLORS["sidebar"], height=60)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_propagate(False)

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
        """Mesaj listesi alanı - Canvas + Scrollbar.

        Canvas içine bir iç Frame yerleştirilir; mesaj balonları bu
        iç Frame'e eklenir. Böylece mesajlar çok fazla olsa bile
        pencere büyümez, kaydırılabilir.
        """
        messages_frame = tk.Frame(self, bg=COLORS["chat_area"])
        messages_frame.grid(row=1, column=0, sticky="nsew")
        messages_frame.rowconfigure(0, weight=1)
        messages_frame.columnconfigure(0, weight=1)

        # Kaydırma çubuğu (sağda)
        self.scrollbar = tk.Scrollbar(
            messages_frame,
            orient="vertical",
            command=self._on_scrollbar,
            bg=COLORS["background"],
            troughcolor=COLORS["chat_area"],
            width=12,
            relief="flat",
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Mesaj tuvali
        self.canvas = tk.Canvas(
            messages_frame,
            bg=COLORS["chat_area"],
            highlightthickness=0,
            bd=0,
            yscrollcommand=self.scrollbar.set,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Canvas içindeki konteyner
        self.msg_container = tk.Frame(self.canvas, bg=COLORS["chat_area"])
        self._canvas_window = self.canvas.create_window(
            (0, 0), window=self.msg_container, anchor="nw"
        )

        # Yeni mesajda en alta kaydır
        self.msg_container.bind("<Configure>", self._on_container_configure)

        # Fare tekerleği ile kaydırma
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.msg_container.bind("<MouseWheel>", self._on_mousewheel)

        # Canvas genişliği değişince iç konteyneri genişletir
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _build_input(self):
        """Mesaj yazma alanı."""
        input_frame = tk.Frame(self, bg=COLORS["sidebar"], height=60)
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.grid_propagate(False)

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

    # -- Kaydırma yardımcıları ------------------------------------------

    def _on_scrollbar(self, *args):
        """Kaydırma çubuğu hareket ederse canvas'u kaydırır."""
        self.canvas.yview(*args)

    def _on_container_configure(self, event):
        """İç konteyner büyüdüğünde kaydırma bölgesini günceller."""
        self._update_scrollregion()

    def _on_canvas_configure(self, event):
        """Canvas genişliği değişince iç konteyneri genişletir."""
        self.canvas.itemconfigure(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """Fare tekerleği ile kaydırır."""
        if event.delta:
            self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
        return "break"

    def _update_scrollregion(self):
        """Kaydırma bölgesini içerik yüksekliğine göre günceller."""
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=bbox)

    def scroll_to_bottom(self):
        """Görünümü en alta kaydırır (yeni mesaj geldiğinde)."""
        self.canvas.update_idletasks()
        self._update_scrollregion()
        self.canvas.yview_moveto(1.0)

    # -- Mesaj işlemleri ------------------------------------------------

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
        self._update_scrollregion()

    def add_message(self, text, is_outgoing, timestamp, sender_name=""):
        """Yeni mesaj balonu ekler ve görünümü en alta kaydırır."""
        bubble = MessageBubble(
            self.msg_container, text, is_outgoing, timestamp, sender_name
        )
        bubble.pack(fill="x", padx=5, pady=2)

        # Yeni mesajda en alta kaydır
        self.canvas.update_idletasks()
        self._update_scrollregion()
        self.canvas.yview_moveto(1.0)
