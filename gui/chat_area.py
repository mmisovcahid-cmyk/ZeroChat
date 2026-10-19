"""
ZeroChat - Sohbet Alanı (Sağ Panel)
Mesajların listelendiği ve yazıldığı alan. Kaydırılabilir (scrollable).
Modern ttk temasi kullanılır.
"""

import tkinter as tk
from tkinter import ttk

from config import (
    COLORS,
    SCHEDULE_MAX_MINUTES,
    POLL_MIN_OPTIONS,
    POLL_MAX_OPTIONS,
    MAX_MESSAGE_CHARS,
)
from gui.theme import FONTS
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
                 on_poll_vote=None, on_poll_close=None, my_user_id="",
                 on_schedule_message=None, on_list_scheduled=None,
                 on_cancel_scheduled=None):
        super().__init__(parent, bg=COLORS["chat_area"])
        self.on_send_message = on_send_message
        self.on_delete_message = on_delete_message
        self.on_edit_message = on_edit_message
        self.on_copy_message = on_copy_message
        self.on_hand_raise = on_hand_raise
        self.on_poll_create = on_poll_create
        self.on_poll_vote = on_poll_vote
        self.on_poll_close = on_poll_close
        self.on_schedule_message = on_schedule_message
        self.on_list_scheduled = on_list_scheduled
        self.on_cancel_scheduled = on_cancel_scheduled
        self.my_user_id = my_user_id

        self.current_chat_id = None
        self.editing_msg_id = None
        self._updating = False
        self.bubbles = {}
        self.poll_cards = {}
        self._refresh_scheduled_list = None
        self.status_frame = None
        self.status_label = None
        self._status_job = None

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self._build_header()
        self._build_messages()
        self._build_input()

        self.bind("<Destroy>", self._on_destroy)

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
            font=FONTS["heading"], bg=COLORS["sidebar"],
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
        self.poll_button = tk.Label(
            self.header, text="📊  Anket",
            font=FONTS["tiny_bold"], bg=COLORS["sidebar"],
            fg=COLORS["accent"], cursor="hand2",
        )
        self.poll_button.pack(side="right", padx=16)
        self.poll_button.bind("<Button-1>", self._on_poll_button)

    def _build_messages(self):
        """Mesaj listesi alanı - Canvas + Scrollbar."""
        messages_frame = tk.Frame(self, bg=COLORS["chat_area"])
        messages_frame.grid(row=1, column=0, sticky="nsew")
        messages_frame.rowconfigure(0, weight=1)
        messages_frame.columnconfigure(0, weight=1)

        # İnce, modern kaydırma çubuğu (ttk)
        self.scrollbar = ttk.Scrollbar(
            messages_frame, orient="vertical",
            command=self._on_scrollbar,
            style="Modern.Vertical.TScrollbar",
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.canvas = tk.Canvas(
            messages_frame, bg=COLORS["chat_area"],
            highlightthickness=0, bd=0, yscrollcommand=self.scrollbar.set,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Canvas içindeki konteyner
        # Yüksekliği elle yönetilir (propagate kapalı) - bkz. _update_scrollregion
        self.msg_container = tk.Frame(self.canvas, bg=COLORS["chat_area"], height=0)
        self.msg_container.pack_propagate(False)
        self._canvas_window = self.canvas.create_window(
            (0, 0), window=self.msg_container, anchor="nw"
        )

        self.msg_container.bind("<Configure>", self._on_container_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.msg_container.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Linux'ta fare tekerleği <Button-4>/<Button-5> olarak gelir
        for widget in (self.canvas, self.msg_container):
            widget.bind("<Button-4>", self._on_mousewheel)
            widget.bind("<Button-5>", self._on_mousewheel)

    def _build_input(self):
        """Mesaj yazma alanı."""
        input_frame = tk.Frame(self, bg=COLORS["sidebar"], height=62)
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.grid_propagate(False)

        # Zamanlanmış mesaj
        schedule_btn = tk.Label(
            input_frame, text="⏰", font=("Segoe UI", 16),
            bg=COLORS["sidebar"], fg=COLORS["text_secondary"], cursor="hand2",
        )
        schedule_btn.pack(side="right", padx=8)
        schedule_btn.bind("<Button-1>", self._on_schedule_click)

        # Gönder butonu (ttk)
        self.send_button = ttk.Button(
            input_frame, text="Gönder",
            style="Accent.TButton", command=self._on_send,
        )
        self.send_button.pack(side="right", padx=(0, 12), pady=11)

        # Girdi alanı (ttk - sadece alt çizgi)
        self.msg_entry = ttk.Entry(
            input_frame, style="Modern.TEntry", font=FONTS["body"],
        )
        self.msg_entry.pack(side="left", fill="x", expand=True,
                            padx=12, pady=11)
        self.msg_entry.bind("<Return>", self._on_send)

    # =====================================================================
    # Kaydırma
    # =====================================================================

    def _on_scrollbar(self, *args):
        self.canvas.yview(*args)

    def _on_container_configure(self, event):
        """İç konteyner değiştiğinde kaydırma bölgesini günceller."""
        self._update_scrollregion()

    def _on_canvas_configure(self, event):
        """Canvas genişliği değişince iç konteyneri genişletir."""
        self.canvas.itemconfigure(self._canvas_window, width=event.width)
        self._update_scrollregion()

    def _on_mousewheel(self, event):
        """Fare tekerleği ile kaydırma (Windows / macOS / Linux).

        Windows'ta event.delta 120'nin katlarıdır. macOS ve Linux'ta
        küçük değerler gelir (1-10) ve Linux'ta <MouseWheel> yerine
        <Button-4>/<Button-5> olayları üretilir. Hepsinin doğru
        çalışması için üçü de desteklenir.
        """
        # Linux: tekerlek yukarı (4) / aşağı (5)
        button = getattr(event, "num", None)
        if button == 4:
            self.canvas.yview_scroll(-1, "units")
            return "break"
        if button == 5:
            self.canvas.yview_scroll(1, "units")
            return "break"

        delta = getattr(event, "delta", 0)
        if not delta:
            return "break"

        if abs(delta) >= 120:
            self.canvas.yview_scroll(-1 * (delta // 120), "units")
        else:
            # macOS / Linux: küçük adımlar (1-10)
            self.canvas.yview_scroll(-1 * delta, "units")
        return "break"

    def _update_scrollregion(self):
        """Canvas item'ını ve kaydırma bölgesini içerikle eşitler.

        ÖNEMLİ - Manuel scrollable frame deseni:
        msg_container'ın yüksekliği elle atanır (propagate kapalı). Çünkü
        Canvas item'ına yükseklik verilirse widget zorlanır, propagate
        kapanır ve doğal yükseklik donup kalır - mesajlar üst üste binmeye
        başlar.

        _updating bayrağı, item yüksekliği değişince tetiklenen
        <Configure> olayının tekrar tetiklenmesini (sonsuz döngü) engeller.
        """
        if self._updating:
            return

        self._updating = True
        try:
            width = self.canvas.winfo_width()
            if width <= 1:
                width = self.canvas.winfo_reqwidth()

            # Çocukların konumlanabilmesi için önce yeterli yükseklik ver
            self.msg_container.configure(height=2000)
            self.msg_container.update_idletasks()

            height = self._content_height()
            if height < 1:
                height = 1

            # Scrollregion canvas'tan küçükse Tk onu canvas'ın ORTASINA
            # yerleştirir ve "en alta kaydır" görünümü mesajların üst
            # kısmını kırpar. Bu yüzden item en az canvas yüksekliğinde
            # tutulur - mesajlar üstte, altta boşluk kalır.
            canvas_height = self.canvas.winfo_height()
            if canvas_height > 1 and height < canvas_height:
                height = canvas_height

            self.msg_container.configure(height=height)
            # Çocukların son konumlarını hesaplat
            self.msg_container.update_idletasks()

            self.canvas.itemconfigure(
                self._canvas_window, width=width, height=height
            )
            self.canvas.configure(scrollregion=(0, 0, width, height))
        finally:
            self._updating = False

    def _content_height(self):
        """Mesaj konteynerinin içerik yüksekliğini hesaplar.

        Son çocuğun GERÇEK alt kenarı kullanılır. Bu, tüm pad
        değerlerini (pady) otomatik olarak hesaba katar - reqheight
        kullanıldığında etiketlerin ölçümü eksik kalabiliyor.
        """
        children = self.msg_container.winfo_children()
        if not children:
            return 0
        last = children[-1]
        return last.winfo_y() + last.winfo_height() + 2

    def scroll_to_bottom(self):
        """Görünümü içeriğin sonuna taşır.

        İçerik canvas'tan kısaysa kaydırma yapılmaz - aksi halde
        görünüm boş alana kayar ve mesajlar ekrandan kaybolur.
        """
        self.canvas.update_idletasks()
        self._update_scrollregion()
        self._scroll_to_end()

    def _scroll_to_end(self):
        """İçerik canvas'tan büyükse en alta kaydırır."""
        bbox = self.canvas.bbox("all")
        if bbox and bbox[3] > self.canvas.winfo_height():
            self.canvas.yview_moveto(1.0)

    # =====================================================================
    # Durum bildirimi
    # =====================================================================

    def show_status(self, text, error=False, duration=4000):
        """Alt kısımda kısa süreli bilgi mesajı gösterir."""
        if self.status_frame is None:
            self.status_frame = tk.Frame(self, bg=COLORS["sidebar"])
            self.status_frame.grid(row=3, column=0, sticky="ew")
            self.status_label = tk.Label(
                self.status_frame, text="",
                font=FONTS["tiny_bold"], bg=COLORS["sidebar"],
                fg=COLORS["accent"], anchor="w",
            )
            self.status_label.pack(anchor="w", padx=12, pady=3)

        self.status_label.config(
            text=text, fg=COLORS["danger"] if error else COLORS["accent"]
        )

        self._cancel_status_job()
        self._status_job = self.after(duration, self._clear_status)

    def _cancel_status_job(self):
        """Bekleyen durum işini iptal eder."""
        if self._status_job is not None:
            try:
                self.after_cancel(self._status_job)
            except tk.TclError:
                pass
            self._status_job = None

    def _clear_status(self):
        """Durum mesajını temizler."""
        self._status_job = None
        try:
            if self.status_label is not None:
                self.status_label.config(text="")
        except tk.TclError:
            pass

    def _on_destroy(self, event=None):
        """Widget yok edilirken bekleyen işleri temizler."""
        if event is not None and event.widget is not self:
            return
        self._cancel_status_job()

    # =====================================================================
    # Mesaj işlemleri
    # =====================================================================

    def _on_send(self, event=None):
        """Gönder butonuna basıldığında."""
        text = self.msg_entry.get().strip()
        if not text:
            return

        if len(text) > MAX_MESSAGE_CHARS:
            from tkinter import messagebox
            messagebox.showwarning(
                "Mesaj Çok Uzun",
                f"Mesaj en fazla {MAX_MESSAGE_CHARS} karakter olabilir.\n"
                f"Şu an {len(text)} karakter yazdınız.",
            )
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
        self._scroll_to_end()

    def remove_message(self, msg_id):
        """Mesajı ekrandan kaldırır."""
        bubble = self.bubbles.pop(msg_id, None)
        if bubble:
            bubble.destroy()
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
        """El kaldıran listesini günceller.

        Liste mesajın kendi balonunun içinde gösterilir - böylece
        hangi mesaja ait olduğu belli olur. Mesaj bu sohbette yoksa
        (başka sohbetin mesajı) hiçbir şey yapılmaz.
        """
        bubble = self.bubbles.get(msg_id)
        if bubble is None:
            return

        names = sorted(hands.values()) if hands else []
        bubble.set_hands(names)
        self._update_scrollregion()

    # =====================================================================
    # Anket
    # =====================================================================

    def _on_poll_button(self, event=None):
        """Anket oluşturma penceresini açar."""
        if not self.current_chat_id:
            return

        dialog = tk.Toplevel(self)
        dialog.title("Anket Oluştur")
        dialog.geometry("440x420")
        dialog.configure(bg=COLORS["sidebar"])
        dialog.transient(self)

        tk.Label(
            dialog, text="Soru:", font=FONTS["subtitle"],
            bg=COLORS["sidebar"], fg=COLORS["text"],
        ).pack(anchor="w", padx=15, pady=(15, 5))

        question_entry = ttk.Entry(
            dialog, style="Modern.TEntry", font=FONTS["body"],
        )
        question_entry.pack(fill="x", padx=15, ipady=6, pady=(0, 5))
        question_entry.focus()

        tk.Label(
            dialog, text="Seçenekler (her satıra bir tane):",
            font=FONTS["subtitle"], bg=COLORS["sidebar"], fg=COLORS["text"],
        ).pack(anchor="w", padx=15, pady=(10, 5))

        options_text = tk.Text(
            dialog, height=6, font=FONTS["body"],
            bg=COLORS["input_bg"], relief="flat", bd=0,
            highlightthickness=0, insertbackground=COLORS["text"],
        )
        options_text.pack(fill="both", expand=True, padx=15, pady=(0, 5))

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
            if len(options) < POLL_MIN_OPTIONS:
                from tkinter import messagebox
                messagebox.showwarning(
                    "Uyarı", f"En az {POLL_MIN_OPTIONS} seçenek girin!"
                )
                return
            if len(options) > POLL_MAX_OPTIONS:
                from tkinter import messagebox
                messagebox.showwarning(
                    "Uyarı", f"En fazla {POLL_MAX_OPTIONS} seçenek girin!"
                )
                return

            if self.on_poll_create:
                self.on_poll_create(self.current_chat_id, question, options)
            dialog.destroy()

        ttk.Button(
            dialog, text="Anketi Başlat", style="Accent.TButton",
            command=create,
        ).pack(pady=12, padx=15, fill="x")

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
        self._scroll_to_end()

    def refresh_poll(self, poll_id, poll):
        """Anket kartını günceller (kart bu sohbette yoksa bir şey yapmaz).

        DİKKAT: Eski davranışta kart yoksa show_poll() çağrılıyordu ve
        anket YANLIŞ sohbete ekleniyordu. Artık kart yalnızca ait
        olduğu sohbette gösterilir.
        """
        if not poll:
            return
        card = self.poll_cards.get(poll_id)
        if card:
            card.refresh(poll)

    def _on_poll_vote(self, poll_id, option_index):
        if self.on_poll_vote:
            self.on_poll_vote(poll_id, option_index)

    def _on_poll_close(self, poll_id):
        if self.on_poll_close:
            self.on_poll_close(poll_id)

    # =====================================================================
    # Dosya paylaşımı
    # =====================================================================

    def _on_schedule_click(self, event=None):
        """Zamanlı mesaj penceresini açar."""
        if not self.current_chat_id:
            return
        if not self.on_schedule_message:
            return

        text = self.msg_entry.get().strip()
        if not text:
            from tkinter import messagebox
            messagebox.showwarning("Uyarı", "Önce mesajı yazın!")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Zamanlı Mesaj")
        dialog.geometry("380x320")
        dialog.configure(bg=COLORS["sidebar"])
        dialog.transient(self)

        tk.Label(
            dialog, text="Ne zaman gönderilsin?",
            font=FONTS["heading"], bg=COLORS["sidebar"], fg=COLORS["text"],
        ).pack(anchor="w", padx=15, pady=(15, 8))

        tk.Label(
            dialog, text=f"Mesaj: {text[:40]}{'...' if len(text) > 40 else ''}",
            font=FONTS["tiny"], bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"], wraplength=340, justify="left",
        ).pack(anchor="w", padx=15, pady=(0, 10))

        tk.Label(
            dialog, text="Dakika sonra:", font=FONTS["body"],
            bg=COLORS["sidebar"], fg=COLORS["text"],
        ).pack(anchor="w", padx=15)

        minutes_var = tk.IntVar(value=5)
        spin = ttk.Spinbox(
            dialog, from_=1, to=SCHEDULE_MAX_MINUTES,
            textvariable=minutes_var, font=FONTS["body"],
        )
        spin.pack(anchor="w", padx=15, pady=(4, 8))

        quick = tk.Frame(dialog, bg=COLORS["sidebar"])
        quick.pack(fill="x", padx=15, pady=(0, 10))
        for label, value in (("5 dk", 5), ("15 dk", 15), ("1 sa", 60), ("1 gün", 1440)):
            tk.Button(
                quick, text=label, bg=COLORS["input_bg"], fg=COLORS["text"],
                relief="flat", bd=0, font=FONTS["tiny"], padx=10, pady=3,
                command=lambda v=value: minutes_var.set(v),
            ).pack(side="left", padx=2)

        def schedule():
            minutes = minutes_var.get()
            if minutes < 1:
                return
            self.on_schedule_message(self.current_chat_id, text, minutes)
            self.msg_entry.delete(0, "end")
            dialog.destroy()

        ttk.Button(
            dialog, text="Zamanla", style="Accent.TButton", command=schedule,
        ).pack(pady=8, padx=15, fill="x")

        # --- Zamanlanmış mesajlar (iptal edilebilir) ---
        list_frame = tk.Frame(dialog, bg=COLORS["sidebar"])
        list_frame.pack(fill="both", expand=True, padx=15, pady=(12, 15))
        self._schedule_list_frame = list_frame

        def refresh_scheduled_list():
            for widget in list_frame.winfo_children():
                widget.destroy()

            pending = (self.on_list_scheduled() or []) if self.on_list_scheduled else []

            tk.Label(
                list_frame, text=f"ZAMANLANMIŞ MESAJLAR ({len(pending)})",
                font=FONTS["tiny_bold"], bg=COLORS["sidebar"],
                fg=COLORS["text_secondary"],
            ).pack(anchor="w", pady=(0, 3))

            if not pending:
                tk.Label(
                    list_frame, text="Bekleyen zamanlanmış mesaj yok.",
                    font=FONTS["tiny"], bg=COLORS["sidebar"],
                    fg=COLORS["offline"],
                ).pack(anchor="w")
                return

            for item in pending:
                row = tk.Frame(list_frame, bg=COLORS["sidebar"])
                row.pack(fill="x", pady=1)

                preview = item.get("content", "")
                if len(preview) > 28:
                    preview = preview[:28] + "..."

                tk.Label(
                    row, text=f"⏰ {preview}", font=FONTS["tiny"],
                    bg=COLORS["sidebar"], fg=COLORS["text"], anchor="w",
                ).pack(side="left")

                ttk.Button(
                    row, text="İptal", style="Ghost.TButton",
                    command=lambda iid=item.get("id"): self._cancel_scheduled(iid),
                ).pack(side="right", padx=2)

        self._refresh_scheduled_list = refresh_scheduled_list
        refresh_scheduled_list()

    def _cancel_scheduled(self, item_id):
        """Zamanlanmış mesajı iptal eder ve listeyi yeniler."""
        if self.on_cancel_scheduled:
            self.on_cancel_scheduled(item_id)
        refresh = getattr(self, "_refresh_scheduled_list", None)
        if refresh:
            refresh()
