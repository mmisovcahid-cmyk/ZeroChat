"""
ZeroChat - Sol Panel (Kontak Listesi)
WhatsApp tarzı sol panel: cihaz ismi, IP, MAC ve çevrimiçi durumu.
"""

import tkinter as tk
from config import COLORS, SIDEBAR_WIDTH


class Sidebar(tk.Frame):
    """Sol panel - otomatik keşfedilen cihazların listesi."""

    def __init__(self, parent, on_contact_select, contacts):
        super().__init__(parent, bg=COLORS["sidebar"], width=SIDEBAR_WIDTH)
        self.on_contact_select = on_contact_select
        self.contacts = contacts
        # device_id -> {"frame", "name_label", "info_label", "preview_label"}
        self.contact_frames = {}

        self._build_header()
        self._build_search()
        self._build_contact_list()
        self._build_new_chat_button()

    def _build_header(self):
        """Üst başlık."""
        header = tk.Frame(self, bg=COLORS["sidebar"], height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="Sohbetler",
            font=("Segoe UI", 14, "bold"),
            bg=COLORS["sidebar"],
            fg=COLORS["text"],
        )
        title.pack(side="left", padx=15, pady=10)

    def _build_search(self):
        """Arama kutusu."""
        search_frame = tk.Frame(self, bg=COLORS["sidebar"])
        search_frame.pack(fill="x", padx=10, pady=5)

        self.search_var = tk.StringVar()

        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Segoe UI", 10),
            bg=COLORS["background"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        search_entry.pack(fill="x", ipady=5)
        search_entry.insert(0, "Ara...")

        # Arama metni değişince listeyi filtrele
        self.search_var.trace_add("write", lambda *_: self._filter_contacts())

    def _build_contact_list(self):
        """Kontak listesi alanı."""
        self.contact_container = tk.Frame(self, bg=COLORS["sidebar"])
        self.contact_container.pack(fill="both", expand=True)

    def _build_new_chat_button(self):
        """Yeni sohbet butonu."""
        btn_frame = tk.Frame(self, bg=COLORS["sidebar"])
        btn_frame.pack(fill="x", padx=10, pady=10)

        new_btn = tk.Button(
            btn_frame,
            text="+ Yeni Sohbet",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["accent"],
            fg="white",
            relief="flat",
            padx=20,
            pady=8,
            command=self._on_new_chat,
        )
        new_btn.pack(fill="x")

    def _on_new_chat(self):
        """Yeni sohbet butonu - hedef cihaz seçim penceresi."""
        dialog = tk.Toplevel(self)
        dialog.title("Yeni Sohbet")
        dialog.geometry("420x340")
        dialog.configure(bg=COLORS["sidebar"])
        dialog.transient(self)

        tk.Label(
            dialog,
            text="Hedef cihazın MAC adresini girin:",
            font=("Segoe UI", 10),
            bg=COLORS["sidebar"],
            fg=COLORS["text"],
        ).pack(anchor="w", padx=15, pady=(15, 5))

        entry = tk.Entry(
            dialog,
            font=("Consolas", 11),
            bg=COLORS["background"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        entry.pack(fill="x", padx=15, ipady=5)
        entry.focus()

        tk.Label(
            dialog,
            text="Örnek: A4:5E:60:D2:9F:11",
            font=("Segoe UI", 8),
            bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w", padx=15, pady=(3, 10))

        def connect():
            target = entry.get().strip().upper()
            if target:
                self.on_contact_select(target)
                dialog.destroy()

        tk.Button(
            dialog,
            text="Bağlan",
            bg=COLORS["accent"],
            fg="white",
            relief="flat",
            padx=20,
            pady=5,
            command=connect,
        ).pack(pady=5)

        entry.bind("<Return>", lambda e: connect())

    def add_device(self, device_id, name, ip, mac):
        """Keşfedilen cihazı listeye ekler (yoksa) veya günceller."""
        if device_id in self.contact_frames:
            return

        frame = tk.Frame(self.contact_container, bg=COLORS["sidebar"])
        frame.pack(fill="x", padx=5, pady=2)

        # Üst satır: isim + durum noktası
        top_row = tk.Frame(frame, bg=COLORS["sidebar"])
        top_row.pack(fill="x", padx=10, pady=(6, 0))

        name_label = tk.Label(
            top_row,
            text=name,
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["sidebar"],
            fg=COLORS["text"],
            anchor="w",
        )
        name_label.pack(side="left")

        status_label = tk.Label(
            top_row,
            text="●",
            font=("Segoe UI", 10),
            bg=COLORS["sidebar"],
            fg=COLORS["online"],
        )
        status_label.pack(side="right")

        # Orta satır: IP + MAC
        info_label = tk.Label(
            frame,
            text=f"{ip}  •  {mac}",
            font=("Consolas", 8),
            bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"],
            anchor="w",
        )
        info_label.pack(fill="x", padx=10, pady=(1, 0))

        # Alt satır: son mesaj önizlemesi
        preview_label = tk.Label(
            frame,
            text="",
            font=("Segoe UI", 9),
            bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"],
            anchor="w",
        )
        preview_label.pack(fill="x", padx=10, pady=(0, 6))

        for widget in (frame, top_row, name_label, info_label, preview_label, status_label):
            widget.bind("<Button-1>", lambda e, did=device_id: self.on_contact_select(did))

        self.contact_frames[device_id] = {
            "frame": frame,
            "name": name_label,
            "info": info_label,
            "preview": preview_label,
            "status": status_label,
        }

    def set_status(self, device_id, online):
        """Cihazın çevrimiçi/çevrimdışı durumunu günceller."""
        entry = self.contact_frames.get(device_id)
        if not entry:
            return
        if online:
            entry["status"].config(text="●", fg=COLORS["online"])
        else:
            entry["status"].config(text="○", fg=COLORS["offline"])
            entry["frame"].configure(bg=COLORS["hover"])

    def update_last_message(self, device_id, message):
        """Son mesaj önizlemesini günceller."""
        entry = self.contact_frames.get(device_id)
        if not entry:
            return
        preview = message if len(message) <= 32 else message[:32] + "..."
        entry["preview"].config(text=preview)

    def _filter_contacts(self):
        """Arama kutusuna göre listeyi filtreler."""
        term = self.search_var.get().strip().lower()
        for entry in self.contact_frames.values():
            if not term:
                entry["frame"].pack(fill="x", padx=5, pady=2)
                continue

            name = entry["name"].cget("text").lower()
            info = entry["info"].cget("text").lower()
            if term in name or term in info:
                entry["frame"].pack(fill="x", padx=5, pady=2)
            else:
                entry["frame"].pack_forget()

    def highlight_contact(self, contact_id):
        """Kontakı vurgular."""
        entry = self.contact_frames.get(contact_id)
        if entry:
            entry["frame"].configure(bg=COLORS["hover"])
