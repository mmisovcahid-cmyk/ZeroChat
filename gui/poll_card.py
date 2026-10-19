"""
ZeroChat - Anket Kartı Bileşeni
Canlı anket oluşturma, oy verme ve sonuç gösterme.
"""

import tkinter as tk
from config import COLORS
from gui.theme import FONTS


class PollCard(tk.Frame):
    """Tek bir anket kartı.

    Durumlar:
      - Açık + oy verilmemiş : seçenekler buton olarak görünür
      - Açık + oy verilmiş   : sonuç barları + oy verilen seçenek vurgulu
      - Kapalı              : sadece sonuçlar
    """

    def __init__(self, parent, poll_id, poll, on_vote, on_close, my_user_id):
        super().__init__(parent, bg=COLORS["incoming_bubble"],
                         padx=12, pady=10)

        self.poll_id = poll_id
        self.poll = poll
        self.on_vote = on_vote
        self.on_close = on_close
        self.my_user_id = my_user_id

        self.voted_index = poll.get("votes", {}).get(my_user_id, -1)
        self.is_creator = poll.get("creator") == my_user_id

        self._build()

    # -- Kurulum --------------------------------------------------------

    def _build(self):
        """Kart içeriğini oluşturur."""
        # Başlık satırı
        header = tk.Frame(self, bg=COLORS["incoming_bubble"])
        header.pack(fill="x")

        tk.Label(
            header, text="📊 ANKET",
            font=FONTS["tiny_bold"], bg=COLORS["incoming_bubble"],
            fg=COLORS["accent"],
        ).pack(side="left")

        if not self.poll.get("open", True):
            tk.Label(
                header, text="KAPANDI",
                font=FONTS["tiny_bold"], bg=COLORS["incoming_bubble"],
                fg=COLORS["text_secondary"],
            ).pack(side="right")

        # Soru
        tk.Label(
            self, text=self.poll.get("question", ""),
            font=FONTS["subtitle"], bg=COLORS["incoming_bubble"],
            fg=COLORS["text"], wraplength=380, justify="left",
        ).pack(anchor="w", pady=(4, 8))

        # Seçenekler
        self.option_widgets = []
        for index, option in enumerate(self.poll.get("options", [])):
            self._build_option(index, option)

        # Alt satır: toplam oy ve kapat butonu
        footer = tk.Frame(self, bg=COLORS["incoming_bubble"])
        footer.pack(fill="x", pady=(8, 0))

        total = len(self.poll.get("votes", {}))
        self.total_label = tk.Label(
            footer, text=f"{total} oy",
            font=FONTS["tiny"], bg=COLORS["incoming_bubble"],
            fg=COLORS["text_secondary"],
        )
        self.total_label.pack(side="left")

        if self.is_creator and self.poll.get("open", True):
            tk.Label(
                footer, text="Anketi Kapat", font=FONTS["tiny_bold"],
                bg=COLORS["incoming_bubble"], fg=COLORS["accent"],
                cursor="hand2",
            ).pack(side="right")
            footer.winfo_children()[-1].bind(
                "<Button-1>", lambda e: self.on_close(self.poll_id)
            )

    def _build_option(self, index, option):
        """Tek bir seçeneği oluşturur."""
        votes = self.poll.get("votes", {})
        total = len(votes)
        count = sum(1 for v in votes.values() if v == index)
        percent = (count / total * 100) if total else 0

        row = tk.Frame(self, bg=COLORS["incoming_bubble"])
        row.pack(fill="x", pady=2)

        # Oy verilmiş mi, henüz verilmemiş mi?
        can_vote = self.poll.get("open", True) and self.voted_index < 0

        if can_vote:
            # Buton görünümü
            btn = tk.Label(
                row, text=option, bg=COLORS["input_bg"], fg=COLORS["text"],
                font=FONTS["body"], anchor="w", cursor="hand2",
                padx=10, pady=6,
            )
            btn.pack(side="left", fill="x", expand=True)
            btn.bind("<Button-1>", lambda e, i=index: self._vote(i))
            self.option_widgets.append((row, None, btn))
        else:
            # Sonuç çubuğu (sol) + yüzde (sağ) - yan yana, çakışmadan
            bar_frame = tk.Frame(row, bg=COLORS["input_bg"], height=24)
            bar_frame.pack(side="left", fill="x", expand=True)
            bar_frame.pack_propagate(False)

            is_mine = (self.voted_index == index)
            bar_color = COLORS["accent"] if is_mine else "#8FD9A8"

            if percent > 0:
                fill = tk.Frame(bar_frame, bg=bar_color)
                fill.place(x=0, y=0, relheight=1, relwidth=percent / 100)

            tk.Label(
                bar_frame, text=option, bg=COLORS["input_bg"],
                fg=COLORS["text"], font=FONTS["small"], anchor="w",
            ).place(x=8, y=0, relheight=1)

            tk.Label(
                row, text=f"%{percent:.0f} ({count})",
                bg=COLORS["incoming_bubble"], fg=COLORS["text_secondary"],
                font=FONTS["tiny"], anchor="e", width=9,
            ).pack(side="right", padx=(6, 0))

            self.option_widgets.append((row, bar_frame, None))

    # -- Etkileşim ------------------------------------------------------

    def _vote(self, index):
        """Oyu gönderir."""
        if self.on_vote:
            self.on_vote(self.poll_id, index)

    def refresh(self, poll):
        """Kartı yeni verilerle yeniler."""
        self.poll = poll
        self.voted_index = poll.get("votes", {}).get(self.my_user_id, -1)
        self.is_creator = poll.get("creator") == self.my_user_id
        for widget in self.winfo_children():
            widget.destroy()
        self._build()
