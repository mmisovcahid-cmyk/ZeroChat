"""
ZeroChat - Sohbet Alanı (Sağ Panel)
Mesajların listelendiği ve yazıldığı alan. Kaydırılabilir (scrollable).
El kaldırma göstergesi ve anket kartlarını barındırır.
"""

import tkinter as tk
from config import COLORS
from gui.message_bubble import MessageBubble
from gui.poll_card import PollCard


class ChatArea(tk.Frame):
    """Sağ panel - sohbet ekranı.

    Dış düzen grid ile kurulur (başlık / mesaj alanı / yazma alanı).
    Böylece mesaj alanı ekranı doldurur, yazma alanı her zaman
    görünür kalır - kaç mesaj olursa olsun.
    """

    def __init__(self, parent, on_send_message, on_delete_message=None,
                 on_edit_message=None, on_copy_message=None,
                 on_hand_raise=None, on_poll_create=None,
                 on_poll_vote=None, on_poll_close=None, my_user_id=""):
        super().__init__(parent, bg=COLORS["chat_area"])
        self.on_send_message = on_send_message
        self.on_delete_message = on_delete_message
        self.on_edit_message = on_edit_message
        self.on_copy_message = on_copy_message
        self.on_hand_raise = on_hand_raise
        self.on_poll_create = on_poll_create
        self.on_poll_vote = on_poll_vote
        self.on_poll_close = on_poll_close
        self.my_user_id = my_user_id

        self.current_chat_id = None
        self.editing_msg_id = None
        # msg_id -> MessageBubble
        self.bubbles = {}
        # msg_id -> el kaldıran widget
        self.hands_widgets = {}
        # poll_id -> PollCard
        self.poll_cards = {}

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self._build_header()
        self._build_messages()
        self._build_input()

    # =====================================================================
    # Kurulum
    # =====================================================================

    def _build_header(self):
        """Sohbet başlığı."""
        self.header = tk.Frame(self, bg=COLORS["sidebar"], height=60)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_propagate(False)

        header_left = tk.Frame(self.header, bg=COLORS["sidebar"])
        header_left.pack(side="left", padx=15, pady=10)

        self.header_label = tk.Label(
            header_left, text="Bir sohbet seçin",
            font=("Segoe UI", 12, "bold"), bg=COLORS["sidebar"],
            fg=COLORS["text"], anchor="w",
        )
        self.header_label.pack(anchor="w")

        self.header_info = tk.Label(
            header_left, text="",
            font=("Consolas", 8), bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"], anchor="w",
        )
        self.header_info.pack(anchor="w")

        # Anket oluştur butonu
        self.poll_button = tk.Button(
            self.header, text="📊 Anket",
            font=("Segoe UI", 9, "bold"), bg=COLORS["sidebar"],
            fg=COLORS["accent"], relief="flat", padx=8,
            command=self._on_poll_button,
        )
        self.poll_button.pack(side="right", padx=10)

    def _build_messages(self):
        """Mesaj listesi alanı - Canvas + Scrollbar."""
        messages_frame = tk.Frame(self, bg=COLORS["chat_area"])
        messages_frame.grid(row=1, column=0, sticky="nsew")
        messages_frame.rowconfigure(0, weight=1)
        messages_frame.columnconfigure(0, weight=1)

        self.scrollbar = tk.Scrollbar(
            messages_frame, orient="vertical", command=self._on_scrollbar,
            bg=COLORS["background"], troughcolor=COLORS["chat_area"],
            width=12, relief="flat",
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.canvas = tk.Canvas(
            messages_frame, bg=COLORS["chat_area"],
            highlightthickness=0, bd=0, yscrollcommand=self.scrollbar.set,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.msg_container = tk.Frame(self.canvas, bg=COLORS["chat_area"])
        self._canvas_window = self.canvas.create_window(
            (0, 0), window=self.msg_container, anchor="nw"
        )

        self.msg_container.bind("<Configure>", self._on_container_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.msg_container.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _build_input(self):
        """Mesaj yazma alanı."""
        input_frame = tk.Frame(self, bg=COLORS["sidebar"], height=60)
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.grid_propagate(False)

        self.msg_entry = tk.Entry(
            input_frame, font=("Segoe UI", 11), bg=COLORS["background"],
            relief="flat", highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10, ipady=5)
        self.msg_entry.bind("<Return>", self._on_send)

        self.send_button = tk.Button(
            input_frame, text="Gönder",
            font=("Segoe UI", 10, "bold"), bg=COLORS["accent"], fg="white",
            relief="flat", padx=20, command=self._on_send,
        )
        self.send_button.pack(side="right", padx=10, pady=10)

    # =====================================================================
    # Kaydırma
    # =====================================================================

    def _on_scrollbar(self, *args):
        self.canvas.yview(*args)

    def _on_container_configure(self, event):
        self._update_scrollregion()

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        if event.delta:
            self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
        return "break"

    def _update_scrollregion(self):
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=bbox)

    def scroll_to_bottom(self):
        self.canvas.update_idletasks()
        self._update_scrollregion()
        self.canvas.yview_moveto(1.0)

    # =====================================================================
    # Mesaj işlemleri
    # =====================================================================

    def _on_send(self, event=None):
        """Gönder butonuna basıldığında."""
        text = self.msg_entry.get().strip()
        if not text:
            return

        if self.editing_msg_id:
            msg_id = self.editing_msg_id
            self.editing_msg_id = None
            self.set_editing_mode(False)
            if self.on_edit_message:
                self.on_edit_message(msg_id, text)
            self.msg_entry.delete(0, "end")
            return

        if self.current_chat_id:
            self.on_send_message(self.current_chat_id, text)
            self.msg_entry.delete(0, "end")

    def on_start_edit(self, msg_id, original_text):
        """Düzenleme modunu başlatır."""
        self.set_editing_mode(msg_id, original_text)

    def set_editing_mode(self, editing, original_text=""):
        """Düzenleme modunu açar/kapatır."""
        self.editing_msg_id = editing
        if editing:
            self.send_button.config(text="Kaydet")
            self.msg_entry.delete(0, "end")
            self.msg_entry.insert(0, original_text)
            self.msg_entry.focus()
            self.msg_entry.selection_range(0, "end")
        else:
            self.send_button.config(text="Gönder")

    def open_chat(self, contact_id, display_name, device_info=""):
        """Sohbeti açar."""
        self.current_chat_id = contact_id
        self.header_label.config(text=display_name)
        self.header_info.config(text=device_info if device_info else "")
        self.editing_msg_id = None
        self.send_button.config(text="Gönder")
        self.clear_messages()

    def clear_messages(self):
        """Mesajları temizler."""
        for widget in self.msg_container.winfo_children():
            widget.destroy()
        self.bubbles = {}
        self.hands_widgets = {}
        self.poll_cards = {}
        self._update_scrollregion()

    def add_message(self, text, is_outgoing, timestamp, sender_name="",
                    msg_id="", is_edited=False):
        """Yeni mesaj balonu ekler."""
        bubble = MessageBubble(
            self.msg_container, text, is_outgoing, timestamp, sender_name,
            msg_id=msg_id,
            is_edited=is_edited,
            on_delete=self.on_delete_message,
            on_edit=self.on_start_edit,
            on_copy=self.on_copy_message,
            on_hand_raise=self._on_bubble_hand_raise,
            my_user_id=self.my_user_id,
        )
        bubble.pack(fill="x", padx=5, pady=2)

        if msg_id:
            self.bubbles[msg_id] = bubble

        self.canvas.update_idletasks()
        self._update_scrollregion()
        self.canvas.yview_moveto(1.0)

    def remove_message(self, msg_id):
        """Mesajı ekrandan kaldırır."""
        bubble = self.bubbles.pop(msg_id, None)
        if bubble:
            bubble.destroy()
        hands = self.hands_widgets.pop(msg_id, None)
        if hands:
            hands.destroy()
        self._update_scrollregion()

    def update_message(self, msg_id, new_text, is_edited=True):
        """Mesaj metnini günceller."""
        bubble = self.bubbles.get(msg_id)
        if bubble:
            bubble.update_text(new_text, is_edited)

    # =====================================================================
    # El kaldırma
    # =====================================================================

    def _on_bubble_hand_raise(self, msg_id, raise_hand):
        """Balon menüsünden el kaldırma isteği."""
        if self.on_hand_raise:
            self.on_hand_raise(msg_id, raise_hand)

    def update_hands(self, msg_id, hands):
        """El kaldıran listesini günceller."""
        # Eski etiketi kaldır
        old = self.hands_widgets.pop(msg_id, None)
        if old:
            old.destroy()

        if not hands:
            self._update_scrollregion()
            return

        # Yeni etiket oluştur (mesajın altında)
        label = tk.Label(
            self.msg_container,
            text="✋ " + ", ".join(sorted(hands.values())),
            font=("Segoe UI", 8, "bold"),
            bg=COLORS["chat_area"],
            fg=COLORS["accent"],
            anchor="w",
        )
        label.pack(fill="x", padx=25, pady=(0, 3))

        self.hands_widgets[msg_id] = label
        self._update_scrollregion()

    # =====================================================================
    # Anket
    # =====================================================================

    def _on_poll_button(self):
        """Anket oluşturma penceresini açar."""
        if not self.current_chat_id:
            return

        dialog = tk.Toplevel(self)
        dialog.title("Anket Oluştur")
        dialog.geometry("440x420")
        dialog.configure(bg=COLORS["sidebar"])
        dialog.transient(self)

        tk.Label(
            dialog, text="Soru:",
            font=("Segoe UI", 10, "bold"), bg=COLORS["sidebar"],
            fg=COLORS["text"],
        ).pack(anchor="w", padx=15, pady=(15, 5))

        question_entry = tk.Entry(
            dialog, font=("Segoe UI", 11), bg=COLORS["background"],
            relief="flat", highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        question_entry.pack(fill="x", padx=15, ipady=5)
        question_entry.focus()

        tk.Label(
            dialog, text="Seçenekler (her satıra bir tane):",
            font=("Segoe UI", 10, "bold"), bg=COLORS["sidebar"],
            fg=COLORS["text"],
        ).pack(anchor="w", padx=15, pady=(15, 5))

        options_text = tk.Text(
            dialog, height=6, font=("Segoe UI", 11),
            bg=COLORS["background"], relief="flat",
            highlightthickness=1, highlightbackground=COLORS["border"],
        )
        options_text.pack(fill="both", expand=True, padx=15)

        def create():
            question = question_entry.get().strip()
            options = [
                line.strip()
                for line in options_text.get("1.0", "end").splitlines()
                if line.strip()
            ]

            if not question:
                from tkinter import messagebox
                messagebox.showwarning("Uyarı", "Soru metnini girin!")
                return
            if len(options) < 2:
                from tkinter import messagebox
                messagebox.showwarning("Uyarı", "En az 2 seçenek girin!")
                return

            if self.on_poll_create:
                self.on_poll_create(self.current_chat_id, question, options)
            dialog.destroy()

        tk.Button(
            dialog, text="Anketi Başlat", bg=COLORS["accent"], fg="white",
            relief="flat", font=("Segoe UI", 11, "bold"),
            pady=6, command=create,
        ).pack(pady=12)

    def show_poll(self, poll_id, poll):
        """Anket kartını ekrana ekler."""
        if poll_id in self.poll_cards:
            self.poll_cards[poll_id].refresh(poll)
            return

        card = PollCard(
            self.msg_container, poll_id, poll,
            on_vote=self._on_poll_vote,
            on_close=self._on_poll_close,
            my_user_id=self.my_user_id,
        )
        card.pack(fill="x", padx=25, pady=4)

        self.poll_cards[poll_id] = card
        self._update_scrollregion()
        self.canvas.yview_moveto(1.0)

    def refresh_poll(self, poll_id, poll):
        """Anket kartını günceller."""
        if not poll:
            return
        card = self.poll_cards.get(poll_id)
        if card:
            card.refresh(poll)
        else:
            self.show_poll(poll_id, poll)

    def _on_poll_vote(self, poll_id, option_index):
        if self.on_poll_vote:
            self.on_poll_vote(poll_id, option_index)

    def _on_poll_close(self, poll_id):
        if self.on_poll_close:
            self.on_poll_close(poll_id)
