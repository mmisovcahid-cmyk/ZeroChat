"""
ZeroChat - Mesaj Balonu Bileşeni
WhatsApp tarzı mesaj balonlarını oluşturur.
Sağ tık menüsü ile silme / düzenleme / kopyalama / el kaldırma.
"""

import tkinter as tk
from config import COLORS


class MessageBubble(tk.Frame):
    """Tek mesaj balonu.

    msg_id: benzersiz mesaj numarası (silme/düzenleme/el kaldırma için)
    on_delete / on_edit / on_copy / on_hand_raise: geri çağrı fonksiyonları
    """

    def __init__(self, parent, text, is_outgoing, timestamp, sender_name="",
                 msg_id="", is_edited=False,
                 on_delete=None, on_edit=None, on_copy=None,
                 on_hand_raise=None, my_user_id=""):
        super().__init__(parent, bg=COLORS["chat_area"])

        self.text = text
        self.msg_id = msg_id
        self.is_outgoing = is_outgoing
        self.is_edited = is_edited
        self.on_delete = on_delete
        self.on_edit = on_edit
        self.on_copy = on_copy
        self.on_hand_raise = on_hand_raise
        self.my_user_id = my_user_id
        self.hand_raised = False

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
        name_label = None
        if not is_outgoing and sender_name:
            name_label = tk.Label(
                bubble, text=sender_name,
                font=("Segoe UI", 8, "bold"),
                bg=bubble_bg, fg=COLORS["text_secondary"],
            )
            name_label.pack(anchor="w")

        # Mesaj metni
        self.msg_label = tk.Label(
            bubble, text=self._display_text(),
            font=("Segoe UI", 10), bg=bubble_bg, fg=COLORS["text"],
            wraplength=350, justify="left",
        )
        self.msg_label.pack(anchor="w")

        # Zaman damgası + düzenlendi işareti
        time_label = tk.Label(
            bubble, text=timestamp + ("  ✓" if is_edited else ""),
            font=("Segoe UI", 7), bg=bubble_bg, fg=COLORS["text_secondary"],
        )
        time_label.pack(anchor="e")

        # Sağ tık menüsü
        self._bind_menu(bubble, self.msg_label, time_label)
        if name_label is not None:
            self._bind_menu(name_label)

    def _display_text(self):
        """Balonda gösterilecek metin."""
        if self.is_edited:
            return f"{self.text}  (düzenlendi)"
        return self.text

    def _bind_menu(self, *widgets):
        """Balon parçalarına sağ tık menüsünü bağlar."""
        for widget in widgets:
            widget.bind("<Button-3>", self._show_context_menu)
            widget.bind("<Button-2>", self._show_context_menu)  # macOS

    def _build_menu(self):
        """Sağ tık menüsünü oluşturur."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Kopyala", command=self._copy)
        menu.add_command(label="Düzenle", command=self._edit)
        menu.add_command(label="Sil", command=self._delete)
        if self.on_hand_raise:
            if self.hand_raised:
                menu.add_command(label="✋ Elini İndir", command=self._lower_hand)
            else:
                menu.add_command(label="✋ El Kaldır", command=self._raise_hand)
        return menu

    def _show_context_menu(self, event):
        """Sağ tık menüsünü gösterir."""
        menu = self._build_menu()
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _copy(self):
        """Mesajı panoya kopyalar."""
        if self.on_copy:
            self.on_copy(self.text)

    def _edit(self):
        """Düzenleme modunu başlatır."""
        if self.on_edit:
            self.on_edit(self.msg_id, self.text)

    def _delete(self):
        """Mesajı siler."""
        if self.on_delete:
            self.on_delete(self.msg_id)

    def _raise_hand(self):
        """El kaldırır."""
        self.hand_raised = True
        if self.on_hand_raise:
            self.on_hand_raise(self.msg_id, True)

    def _lower_hand(self):
        """Elini indirir."""
        self.hand_raised = False
        if self.on_hand_raise:
            self.on_hand_raise(self.msg_id, False)

    def update_text(self, text, is_edited=True):
        """Mesaj metnini günceller."""
        self.text = text
        self.is_edited = is_edited
        self.msg_label.config(text=self._display_text())
