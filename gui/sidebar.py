"""
ZeroChat - Sol Panel (Kontak Listesi)
WhatsApp tarzı sol panel: gruplar, cihazlar, sınıf panosu.
Modern ttk teması kullanılır.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from config import (
    COLORS,
    SIDEBAR_WIDTH,
    GROUP_PREFIX,
    GROUP_PUBLIC,
    GROUP_PRIVATE,
    INVITE_CODE_LENGTH,
)
from gui.theme import FONTS


class Sidebar(tk.Frame):
    """Sol panel - gruplar, cihaz listesi ve sınıf panosu."""

    def __init__(self, parent, on_contact_select, contacts,
                 on_group_create=None, on_group_join=None, on_group_leave=None,
                 on_group_manage=None, on_invite_accept=None,
                 on_invite_reject=None, on_remove_member=None,
                 on_set_visibility=None, on_delete_group=None,
                 on_toggle_stealth=None, on_generate_pair_code=None,
                 on_pair_accept=None, on_pair_reject=None,
                 on_pair_request=None):
        super().__init__(parent, bg=COLORS["sidebar"], width=SIDEBAR_WIDTH)
        self.on_contact_select = on_contact_select
        self.on_group_create = on_group_create
        self.on_group_join = on_group_join
        self.on_group_leave = on_group_leave
        self.on_group_manage = on_group_manage
        self.on_invite_accept = on_invite_accept
        self.on_invite_reject = on_invite_reject
        self.on_remove_member = on_remove_member
        self.on_set_visibility = on_set_visibility
        self.on_delete_group = on_delete_group
        self.on_toggle_stealth = on_toggle_stealth
        self.on_generate_pair_code = on_generate_pair_code
        self.on_pair_accept = on_pair_accept
        self.on_pair_reject = on_pair_reject
        self.on_pair_request = on_pair_request
        self.contacts = contacts

        self.contact_frames = {}
        self.group_frames = {}
        self.manager_window = None
        self.manager_group_id = None
        self.manager_admin_id = None
        self.manager_refs = {}
        self.group_data = {}
        self.pair_request_frames = {}

        self._build_header()
        self._build_search()
        self._build_group_section()
        self._build_contact_list()
        self._build_new_chat_button()

    # =====================================================================
    # Kurulum
    # =====================================================================

    def _build_header(self):
        header = tk.Frame(self, bg=COLORS["sidebar"], height=58)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="Sohbetler", font=FONTS["title"],
            bg=COLORS["sidebar"], fg=COLORS["text"],
        ).pack(side="left", padx=15, pady=10)

        tools = tk.Frame(header, bg=COLORS["sidebar"])
        tools.pack(side="right", padx=6)

        # Gizli mod
        self.stealth_button = tk.Label(
            tools, text="👻", font=("Segoe UI", 13),
            bg=COLORS["sidebar"], fg=COLORS["text_secondary"], cursor="hand2",
        )
        self.stealth_button.pack(side="right", padx=4)
        self.stealth_button.bind("<Button-1>", self._on_toggle_stealth)

        # Pairing kodu
        self.pair_button = tk.Label(
            tools, text="🔗", font=("Segoe UI", 12),
            bg=COLORS["sidebar"], fg=COLORS["text_secondary"], cursor="hand2",
        )
        self.pair_button.pack(side="right", padx=4)
        self.pair_button.bind("<Button-1>", self._on_pairing)

    def _build_search(self):
        search_frame = tk.Frame(self, bg=COLORS["sidebar"])
        search_frame.pack(fill="x", padx=12, pady=(0, 6))

        # "Ara..." bir placeholder metin olarak tutulur. Arama terimi
        # "ara..." ile birleşmesin diye odak girince temizlenir.
        self.search_placeholder = "Ara..."
        self.search_var = tk.StringVar(value=self.search_placeholder)
        self.search_entry = ttk.Entry(
            search_frame, style="Modern.TEntry", textvariable=self.search_var,
            font=FONTS["small"],
        )
        self.search_entry.pack(fill="x", ipady=5)
        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out)
        self.search_var.trace_add("write", lambda *_: self._filter_contacts())

    def _on_search_focus_in(self, event=None):
        """Odak girince placeholder metni temizlenir."""
        if self.search_var.get() == self.search_placeholder:
            self.search_var.set("")
            self._search_active = True

    def _on_search_focus_out(self, event=None):
        """Odak çıkınca boşsa placeholder geri gelir."""
        if not self.search_var.get().strip():
            self.search_var.set(self.search_placeholder)

    def _build_group_section(self):
        group_header = tk.Frame(self, bg=COLORS["sidebar"])
        group_header.pack(fill="x", padx=14, pady=(6, 2))

        tk.Label(
            group_header, text="GRUPLAR", font=FONTS["tiny_bold"],
            bg=COLORS["sidebar"], fg=COLORS["text_secondary"],
        ).pack(side="left")

        tk.Label(
            group_header, text="+ Katıl", font=FONTS["tiny_bold"],
            bg=COLORS["sidebar"], fg=COLORS["accent"], cursor="hand2",
        ).pack(side="right", padx=(0, 10))
        group_header.winfo_children()[-1].bind("<Button-1>", self._on_join_group)

        tk.Label(
            group_header, text="+ Oluştur", font=FONTS["tiny_bold"],
            bg=COLORS["sidebar"], fg=COLORS["accent"], cursor="hand2",
        ).pack(side="right")
        group_header.winfo_children()[-1].bind("<Button-1>", self._on_create_group)

        self.group_container = tk.Frame(self, bg=COLORS["sidebar"])
        self.group_container.pack(fill="x", padx=5)

    def _build_contact_list(self):
        tk.Label(
            self, text="CİHAZLAR", font=FONTS["tiny_bold"],
            bg=COLORS["sidebar"], fg=COLORS["text_secondary"],
        ).pack(anchor="w", padx=14, pady=(10, 2))

        self.contact_container = tk.Frame(self, bg=COLORS["sidebar"])
        self.contact_container.pack(fill="both", expand=True)

        self.sidebar_status = tk.Label(
            self, text="", font=FONTS["tiny_bold"],
            bg=COLORS["sidebar"], fg=COLORS["accent"],
        )
        self.sidebar_status.pack(anchor="w", padx=14, pady=(0, 2))

    def _build_new_chat_button(self):
        btn_frame = tk.Frame(self, bg=COLORS["sidebar"])
        btn_frame.pack(fill="x", padx=12, pady=10)

        ttk.Button(
            btn_frame, text="+ Yeni Sohbet", style="Accent.TButton",
            command=self._on_new_chat,
        ).pack(fill="x")

    # =====================================================================
    # Yeni sohbet / grup pencereleri
    # =====================================================================

    def _on_new_chat(self):
        dialog = tk.Toplevel(self)
        dialog.title("Yeni Sohbet")
        dialog.geometry("420x300")
        dialog.configure(bg=COLORS["sidebar"])
        dialog.transient(self)

        tk.Label(
            dialog, text="Hedef cihazın MAC adresini girin:",
            font=FONTS["body"], bg=COLORS["sidebar"], fg=COLORS["text"],
        ).pack(anchor="w", padx=15, pady=(15, 5))

        entry = ttk.Entry(dialog, style="Modern.TEntry", font=("Consolas", 11))
        entry.pack(fill="x", padx=15, ipady=5)
        entry.focus()

        tk.Label(
            dialog, text="Örnek: A4:5E:60:D2:9F:11",
            font=FONTS["tiny"], bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w", padx=15, pady=(3, 10))

        def connect():
            target = entry.get().strip().upper()
            if target:
                self.on_contact_select(target)
                dialog.destroy()

        ttk.Button(
            dialog, text="Bağlan", style="Accent.TButton", command=connect,
        ).pack(pady=5, padx=15, fill="x")

        entry.bind("<Return>", lambda e: connect())

    def _on_create_group(self, event=None):
        dialog = tk.Toplevel(self)
        dialog.title("Grup Oluştur")
        dialog.geometry("400x340")
        dialog.configure(bg=COLORS["sidebar"])
        dialog.transient(self)

        tk.Label(
            dialog, text="Grup adı:", font=FONTS["body"],
            bg=COLORS["sidebar"], fg=COLORS["text"],
        ).pack(anchor="w", padx=15, pady=(15, 5))

        name_entry = ttk.Entry(dialog, style="Modern.TEntry", font=FONTS["heading"])
        name_entry.pack(fill="x", padx=15, ipady=5)
        name_entry.focus()

        tk.Label(
            dialog, text="Erişim:", font=FONTS["body"],
            bg=COLORS["sidebar"], fg=COLORS["text"],
        ).pack(anchor="w", padx=15, pady=(14, 5))

        visibility = tk.StringVar(value=GROUP_PUBLIC)

        ttk.Radiobutton(
            dialog, text="Herkese açık (herkes katılabilir)",
            variable=visibility, value=GROUP_PUBLIC,
            style="Modern.TRadiobutton",
        ).pack(anchor="w", padx=25)

        ttk.Radiobutton(
            dialog, text="Gizli (sadece davet kodu ile)",
            variable=visibility, value=GROUP_PRIVATE,
            style="Modern.TRadiobutton",
        ).pack(anchor="w", padx=25, pady=(2, 14))

        def create():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Uyarı", "Grup adı girin!")
                return
            group_id = self._make_group_id(name)
            if self.on_group_create:
                self.on_group_create(group_id, name, visibility.get())
            dialog.destroy()

        ttk.Button(
            dialog, text="Oluştur", style="Accent.TButton", command=create,
        ).pack(pady=5, padx=15, fill="x")

        name_entry.bind("<Return>", lambda e: create())

    def _on_join_group(self, event=None):
        dialog = tk.Toplevel(self)
        dialog.title("Gruba Katıl")
        dialog.geometry("360x210")
        dialog.configure(bg=COLORS["sidebar"])
        dialog.transient(self)

        tk.Label(
            dialog, text="Grup adı (veya kodu):", font=FONTS["body"],
            bg=COLORS["sidebar"], fg=COLORS["text"],
        ).pack(anchor="w", padx=15, pady=(15, 5))

        entry = ttk.Entry(dialog, style="Modern.TEntry", font=FONTS["heading"])
        entry.pack(fill="x", padx=15, ipady=5)
        entry.focus()

        tk.Label(
            dialog, text="Gizli gruplar için davet kodunu, herkese açık "
                         "gruplar için grup adını girin.",
            font=FONTS["tiny"], bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"], wraplength=320, justify="left",
        ).pack(anchor="w", padx=15, pady=(5, 10))

        def join():
            value = entry.get().strip()
            if not value:
                return

            looks_like_code = len(value) == INVITE_CODE_LENGTH and value.isalnum()

            # 1) Bilinen bir grubun davet kodu mu?
            group_id = self._find_group_by_code(value)
            if group_id:
                self.on_group_join(group_id, value.upper())
                dialog.destroy()
                return

            # 2) Bilinen bir grubun adı mı?
            group_id = self._find_group_by_name(value)
            if group_id:
                self.on_group_join(group_id, "")
                dialog.destroy()
                return

            # 3) Henüz duyurulmamış grup: ad olarak dene,
            #    kod biçimindeyse davet isteği olarak gönder.
            group_id = self._make_group_id(value)
            self.on_group_join(group_id, value.upper() if looks_like_code else "")
            dialog.destroy()

        ttk.Button(
            dialog, text="Katıl", style="Accent.TButton", command=join,
        ).pack(pady=5, padx=15, fill="x")

        entry.bind("<Return>", lambda e: join())

    @staticmethod
    def _make_group_id(name):
        return GROUP_PREFIX + name.strip().lower().replace(" ", "_")

    def _find_group_by_code(self, code):
        """Davet koduna sahip yerel grubu bulur."""
        for group_id, group in self.group_data.items():
            if group.get("invite_code", "") and \
                    group.get("invite_code", "").upper() == code.upper():
                return group_id
        return None

    def _find_group_by_name(self, name):
        """Adı (büyük/küçük harf duyarsız) eşleşen yerel grubu bulur."""
        target = name.strip().lower()
        for group_id, group in self.group_data.items():
            if group.get("name", "").strip().lower() == target:
                return group_id
        return None

    # =====================================================================
    # Cihaz listesi
    # =====================================================================

    def add_device(self, device_id, name, ip, mac, hidden=False):
        """Keşfedilen cihazı listeye ekler."""
        if device_id in self.contact_frames:
            self.update_device(device_id, name=name, ip=ip, mac=mac, hidden=hidden)
            return

        frame = tk.Frame(self.contact_container, bg=COLORS["sidebar"])
        frame.pack(fill="x", padx=6, pady=1)

        top_row = tk.Frame(frame, bg=COLORS["sidebar"])
        top_row.pack(fill="x", padx=8, pady=(6, 0))

        name_label = tk.Label(
            top_row, text=self._device_title(name, hidden),
            font=FONTS["body_bold"], bg=COLORS["sidebar"],
            fg=COLORS["text"], anchor="w",
        )
        name_label.pack(side="left")

        status_label = tk.Label(
            top_row, text="●", font=("Segoe UI", 10),
            bg=COLORS["sidebar"], fg=COLORS["online"],
        )
        status_label.pack(side="right")

        info_label = tk.Label(
            frame, text=f"{ip}  •  {mac}", font=("Consolas", 8),
            bg=COLORS["sidebar"], fg=COLORS["text_secondary"], anchor="w",
        )
        info_label.pack(fill="x", padx=8, pady=(1, 0))

        preview_label = tk.Label(
            frame, text="", font=FONTS["small"],
            bg=COLORS["sidebar"], fg=COLORS["text_secondary"], anchor="w",
        )
        preview_label.pack(fill="x", padx=8, pady=(0, 5))

        widgets = (frame, top_row, name_label, info_label, preview_label, status_label)
        for widget in widgets:
            widget.bind("<Button-1>", lambda e, did=device_id: self.on_contact_select(did))
            widget.bind("<Enter>", lambda e, f=frame: f.configure(bg=COLORS["hover"]))
            widget.bind("<Leave>", lambda e, f=frame: f.configure(bg=COLORS["sidebar"]))

        self.contact_frames[device_id] = {
            "frame": frame, "name": name_label, "info": info_label,
            "preview": preview_label, "status": status_label,
            "widgets": widgets,
        }

    @staticmethod
    def _device_title(name, hidden):
        return f"👻 {name}" if hidden else name

    def update_device(self, device_id, name=None, ip=None, mac=None, hidden=None):
        """Cihaz bilgilerini günceller."""
        entry = self.contact_frames.get(device_id)
        if not entry:
            return
        if name is not None:
            current_hidden = hidden
            if current_hidden is None:
                current_hidden = entry["name"].cget("text").startswith("👻")
            entry["name"].config(text=self._device_title(name, current_hidden))
        if ip is not None and mac is not None:
            entry["info"].config(text=f"{ip}  •  {mac}")

    def set_stealth_state(self, enabled):
        """Gizli mod butonunun görünümünü günceller."""
        if enabled:
            self.stealth_button.config(fg=COLORS["accent"])
        else:
            self.stealth_button.config(fg=COLORS["text_secondary"])

    def _on_toggle_stealth(self, event=None):
        if self.on_toggle_stealth:
            self.on_toggle_stealth()

    def _on_pairing(self, event=None):
        if self.on_pair_request:
            self.on_pair_request()

    # -- Pairing istekleri ----------------------------------------------

    def show_pair_request(self, user_id, user_name):
        """Eşleştirme isteğini listede gösterir."""
        if user_id in self.pair_request_frames:
            return

        frame = tk.Frame(self.contact_container, bg=COLORS["input_bg"])
        frame.pack(fill="x", padx=6, pady=2)

        tk.Label(
            frame, text=f"🔗 {user_name} eşleşmek istiyor",
            font=FONTS["tiny_bold"], bg=COLORS["input_bg"],
            fg=COLORS["text"], anchor="w",
        ).pack(side="left", padx=8, pady=5)

        accept = tk.Label(
            frame, text="Kabul", font=FONTS["tiny_bold"],
            bg=COLORS["accent"], fg="white", cursor="hand2", padx=8, pady=3,
        )
        accept.pack(side="right", padx=3, pady=3)
        accept.bind("<Button-1>", lambda e, uid=user_id: self._accept_pair(uid))

        reject = tk.Label(
            frame, text="Reddet", font=FONTS["tiny"],
            bg=COLORS["input_bg"], fg=COLORS["text_secondary"],
            cursor="hand2", padx=8, pady=3,
        )
        reject.pack(side="right", padx=3, pady=3)
        reject.bind("<Button-1>", lambda e, uid=user_id: self._reject_pair(uid))

        self.pair_request_frames[user_id] = frame

    def remove_pair_request(self, user_id):
        frame = self.pair_request_frames.pop(user_id, None)
        if frame:
            frame.destroy()

    def _accept_pair(self, user_id):
        if self.on_pair_accept:
            self.on_pair_accept(user_id)

    def _reject_pair(self, user_id):
        if self.on_pair_reject:
            self.on_pair_reject(user_id)

    def show_pair_result(self, user_name, accepted):
        """Eşleştirme sonucunu kısa süre gösterir."""
        if accepted:
            text = f"✅ {user_name} ile eşleştiniz"
        else:
            text = f"❌ {user_name} eşleşmeyi reddetti"
        self.sidebar_status.config(text=text, fg=COLORS["accent"])
        self.winfo_toplevel().after(3000, lambda: self.sidebar_status.config(
            text="", fg=COLORS["text_secondary"]))

    # =====================================================================
    # Sınıf Panosu
    # =====================================================================

    def add_group(self, group_id, display_name, member_count=0,
                 visibility=GROUP_PUBLIC, is_admin=False, pending=0,
                 invite_code="", admin_id="", can_leave=True):
        """Grubu grup listesine ekler."""
        self.group_data[group_id] = {
            "name": display_name,
            "invite_code": invite_code,
            "admin_id": admin_id,
        }

        if group_id in self.group_frames:
            entry = self.group_frames[group_id]
            entry["info"].config(text=self._group_info_text(member_count, pending))
            entry["name"].config(text=self._group_title(display_name, visibility, is_admin))
            return

        frame = tk.Frame(self.group_container, bg=COLORS["sidebar"])
        frame.pack(fill="x", padx=6, pady=1)

        top_row = tk.Frame(frame, bg=COLORS["sidebar"])
        top_row.pack(fill="x", padx=8, pady=(5, 0))

        name_label = tk.Label(
            top_row, text=self._group_title(display_name, visibility, is_admin),
            font=FONTS["body_bold"], bg=COLORS["sidebar"],
            fg=COLORS["text"], anchor="w",
        )
        name_label.pack(side="left")

        if is_admin:
            action_text = "⋯"
        elif can_leave:
            action_text = "✕"
        else:
            action_text = ""

        action_btn = tk.Label(
            top_row, text=action_text, font=("Segoe UI", 11, "bold"),
            bg=COLORS["sidebar"], fg=COLORS["text_secondary"], cursor="hand2",
        )
        action_btn.pack(side="right")

        info_label = tk.Label(
            frame, text=self._group_info_text(member_count, pending),
            font=FONTS["tiny"], bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"], anchor="w",
        )
        info_label.pack(fill="x", padx=8, pady=(0, 4))

        # Son mesaj önizlemesi AYRI bir etikette - üye sayısı ezilmez
        preview_label = tk.Label(
            frame, text="", font=FONTS["small"],
            bg=COLORS["sidebar"], fg=COLORS["text_secondary"], anchor="w",
        )
        preview_label.pack(fill="x", padx=8, pady=(0, 4))

        for widget in (frame, top_row, name_label, info_label, preview_label):
            widget.bind("<Button-1>", lambda e, gid=group_id: self.on_contact_select(gid))
            widget.bind("<Enter>", lambda e, f=frame: f.configure(bg=COLORS["hover"]))
            widget.bind("<Leave>", lambda e, f=frame: f.configure(bg=COLORS["sidebar"]))

        if is_admin:
            action_btn.bind("<Button-1>", lambda e, gid=group_id: self.on_group_manage(gid))
        elif can_leave:
            action_btn.bind(
                "<Button-1>",
                lambda e, gid=group_id: self._leave_group(gid, display_name),
            )

        self.group_frames[group_id] = {
            "frame": frame, "name": name_label, "info": info_label,
            "preview": preview_label,
        }

    @staticmethod
    def _group_title(display_name, visibility, is_admin):
        icon = "🔒" if visibility == GROUP_PRIVATE else "👥"
        title = f"{icon} {display_name}"
        if is_admin:
            title += "  ★"
        return title

    @staticmethod
    def _group_info_text(member_count, pending):
        text = f"{member_count} üye"
        if pending:
            text += f"  •  {pending} istek"
        return text

    def update_group_preview(self, group_id, message):
        """Grubun son mesajını önizleme etiketine yazar."""
        entry = self.group_frames.get(group_id)
        if not entry:
            return
        preview = message if len(message) <= 32 else message[:32] + "..."
        entry["preview"].config(text=preview)

    def remove_group(self, group_id):
        entry = self.group_frames.pop(group_id, None)
        if entry:
            entry["frame"].destroy()

    def remove_device(self, device_id):
        """Cihazı listeden tamamen kaldırır (uzun süre çevrimdışı kalanlar)."""
        entry = self.contact_frames.pop(device_id, None)
        if entry:
            entry["frame"].destroy()

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
        entry = self.contact_frames.get(device_id)
        if not entry:
            return
        preview = message if len(message) <= 32 else message[:32] + "..."
        entry["preview"].config(text=preview)

    def _leave_group(self, group_id, display_name):
        if messagebox.askyesno(
            "Gruptan Ayrıl", f"'{display_name}' grubundan ayrılmak istiyor musun?"
        ):
            if self.on_group_leave:
                self.on_group_leave(group_id)

    def _filter_contacts(self):
        """Arama kutusuna göre cihaz ve grup listelerini filtreler."""
        term = self.search_var.get().strip().lower()
        if term == self.search_placeholder.lower():
            term = ""

        for entry in self.contact_frames.values():
            name = entry["name"].cget("text").lower()
            info = entry["info"].cget("text").lower()
            if not term or term in name or term in info:
                entry["frame"].pack(fill="x", padx=6, pady=1)
            else:
                entry["frame"].pack_forget()

        for entry in self.group_frames.values():
            name = entry["name"].cget("text").lower()
            if not term or term in name:
                entry["frame"].pack(fill="x", padx=6, pady=1)
            else:
                entry["frame"].pack_forget()

    # =====================================================================
    # Grup yönetim penceresi
    # =====================================================================

    def open_group_manager(self, group_id, group, is_admin):
        """Grup yönetim penceresini açar."""
        if self.manager_window and self.manager_window.winfo_exists():
            self.manager_window.destroy()

        self.manager_group_id = group_id
        self.manager_admin_id = group.get("admin_id", "")
        self.manager_refs = {}

        win = tk.Toplevel(self)
        self.manager_window = win
        win.title(f"Grup Yönetimi - {group['name']}")
        win.geometry("440x540")
        win.configure(bg=COLORS["sidebar"])
        win.transient(self)

        tk.Label(
            win, text=group["name"], font=FONTS["title"],
            bg=COLORS["sidebar"], fg=COLORS["text"],
        ).pack(anchor="w", padx=15, pady=(15, 4))

        visibility_text = (
            "Gizli (sadece davet kodu ile)" if group["visibility"] == GROUP_PRIVATE
            else "Herkese açık"
        )
        tk.Label(
            win, text=f"Erişim: {visibility_text}", font=FONTS["small"],
            bg=COLORS["sidebar"], fg=COLORS["text_secondary"],
        ).pack(anchor="w", padx=15)

        if is_admin:
            tk.Label(
                win, text="★ Bu grubun yöneticisisiniz", font=FONTS["small"],
                bg=COLORS["sidebar"], fg=COLORS["accent"],
            ).pack(anchor="w", padx=15, pady=(3, 10))
        else:
            tk.Label(
                win, text="Yönetici: " + group.get("admin_id", "-"),
                font=FONTS["tiny"], bg=COLORS["sidebar"],
                fg=COLORS["text_secondary"],
            ).pack(anchor="w", padx=15, pady=(3, 10))

        # Davet Kodu (sadece yönetici görebilir)
        tk.Label(
            win, text="DAVET KODU", font=FONTS["tiny_bold"],
            bg=COLORS["sidebar"], fg=COLORS["text_secondary"],
        ).pack(anchor="w", padx=15)

        code_frame = tk.Frame(win, bg=COLORS["sidebar"])
        code_frame.pack(fill="x", padx=15, pady=(3, 5))

        if is_admin:
            code_text = group.get("invite_code") or "-"
        else:
            code_text = "••••••"

        code_label = tk.Label(
            code_frame, text=code_text,
            font=("Consolas", 18, "bold"), bg=COLORS["input_bg"],
            fg=COLORS["accent"] if is_admin else COLORS["text_secondary"],
            padx=15, pady=6,
        )
        code_label.pack(side="left")

        if is_admin:
            tk.Label(
                code_frame, text="Kopyala", font=FONTS["tiny"],
                bg=COLORS["sidebar"], fg=COLORS["accent"], cursor="hand2",
            ).pack(side="left", padx=8)
            code_frame.winfo_children()[-1].bind(
                "<Button-1>", lambda e, c=code_label.cget("text"): self._copy_code(c)
            )
        else:
            tk.Label(
                code_frame, text="(yalnızca yönetici görebilir)",
                font=FONTS["tiny"], bg=COLORS["sidebar"],
                fg=COLORS["text_secondary"],
            ).pack(side="left", padx=8)

        self.manager_refs["code_label"] = code_label

        # Bekleyen Davetler
        pending = group.get("pending", {})
        if pending:
            tk.Label(
                win, text="BEKLEYEN DAVET İSTEKLERİ", font=FONTS["tiny_bold"],
                bg=COLORS["sidebar"], fg=COLORS["accent"],
            ).pack(anchor="w", padx=15, pady=(12, 3))

            for user_id, user_name in list(pending.items()):
                row = tk.Frame(win, bg=COLORS["sidebar"])
                row.pack(fill="x", padx=15, pady=2)

                tk.Label(
                    row, text=user_name, font=FONTS["body"],
                    bg=COLORS["sidebar"], fg=COLORS["text"],
                ).pack(side="left")

                ttk.Button(
                    row, text="Kabul", style="Accent.TButton",
                    command=lambda uid=user_id: self._accept_invite(group_id, uid),
                ).pack(side="right", padx=2)

                tk.Label(
                    row, text="Reddet", font=FONTS["tiny"],
                    bg=COLORS["sidebar"], fg=COLORS["text_secondary"],
                    cursor="hand2",
                ).pack(side="right", padx=8)
                row.winfo_children()[-1].bind(
                    "<Button-1>", lambda e, uid=user_id: self._reject_invite(group_id, uid)
                )

        # Üyeler
        tk.Label(
            win, text=f"ÜYELER ({len(group['members'])})", font=FONTS["tiny_bold"],
            bg=COLORS["sidebar"], fg=COLORS["text_secondary"],
        ).pack(anchor="w", padx=15, pady=(12, 3))

        members_frame = tk.Frame(win, bg=COLORS["sidebar"])
        members_frame.pack(fill="both", expand=True, padx=15)

        for user_id, user_name in group["members"].items():
            row = tk.Frame(members_frame, bg=COLORS["sidebar"])
            row.pack(fill="x", pady=1)

            label_text = user_name
            if user_id == group.get("admin_id"):
                label_text += "  ★ yönetici"

            tk.Label(
                row, text=label_text, font=FONTS["body"],
                bg=COLORS["sidebar"], fg=COLORS["text"],
            ).pack(side="left")

            if is_admin and user_id != group.get("admin_id"):
                tk.Label(
                    row, text="Çıkar", font=FONTS["tiny"],
                    bg=COLORS["sidebar"], fg=COLORS["danger"], cursor="hand2",
                ).pack(side="right")
                row.winfo_children()[-1].bind(
                    "<Button-1>", lambda e, uid=user_id: self._remove_member(group_id, uid)
                )

        # Admin işlemleri
        if is_admin:
            tk.Label(
                win, text="YÖNETİCİ İŞLEMLERİ", font=FONTS["tiny_bold"],
                bg=COLORS["sidebar"], fg=COLORS["text_secondary"],
            ).pack(anchor="w", padx=15, pady=(10, 3))

            btn_row = tk.Frame(win, bg=COLORS["sidebar"])
            btn_row.pack(fill="x", padx=15)

            new_visibility = (
                GROUP_PUBLIC if group["visibility"] == GROUP_PRIVATE else GROUP_PRIVATE
            )
            toggle_text = (
                "Herkese Açık Yap" if group["visibility"] == GROUP_PRIVATE
                else "Gizli Yap"
            )
            ttk.Button(
                btn_row, text=toggle_text, style="Ghost.TButton",
                command=lambda: self._toggle_visibility(group_id, new_visibility),
            ).pack(side="left", padx=2)

            ttk.Button(
                btn_row, text="Grubu Sil", style="Danger.TButton",
                command=lambda: self._delete_group(group_id),
            ).pack(side="right", padx=2)

        # Alt
        bottom = tk.Frame(win, bg=COLORS["sidebar"])
        bottom.pack(fill="x", padx=15, pady=12)

        if is_admin:
            ttk.Button(
                bottom, text="Grubu Sil ve Kapat", style="Danger.TButton",
                command=lambda: self._delete_group(group_id),
            ).pack(fill="x")
        else:
            ttk.Button(
                bottom, text="Gruptan Ayrıl", style="Ghost.TButton",
                command=lambda: self._leave_and_close(group_id, group["name"]),
            ).pack(fill="x")

    def refresh_group_manager(self, group_id, group):
        """Yönetim penceresini yeniler."""
        if self.manager_window and self.manager_window.winfo_exists():
            self.open_group_manager(
                group_id, group, group.get("admin_id") == self.manager_admin_id
            )

    def _copy_code(self, code):
        self.clipboard_clear()
        self.clipboard_append(code)
        self.update()

    def _accept_invite(self, group_id, user_id):
        if self.on_invite_accept:
            self.on_invite_accept(group_id, user_id)

    def _reject_invite(self, group_id, user_id):
        if self.on_invite_reject:
            self.on_invite_reject(group_id, user_id)

    def _remove_member(self, group_id, user_id):
        if messagebox.askyesno("Üyeyi Çıkar", "Bu üyeyi gruptan çıkarmak istiyor musun?"):
            if self.on_remove_member:
                self.on_remove_member(group_id, user_id)

    def _toggle_visibility(self, group_id, new_visibility):
        if self.on_set_visibility:
            self.on_set_visibility(group_id, new_visibility)

    def _delete_group(self, group_id):
        if messagebox.askyesno(
            "Grubu Sil",
            "Bu grubu silmek istiyor musun?\nGruptaki tüm üyeler çıkarılacak.",
        ):
            if self.on_delete_group:
                self.on_delete_group(group_id)
            if self.manager_window and self.manager_window.winfo_exists():
                self.manager_window.destroy()

    def _leave_and_close(self, group_id, name):
        if messagebox.askyesno("Gruptan Ayrıl", f"'{name}' grubundan ayrılmak istiyor musun?"):
            if self.on_group_leave:
                self.on_group_leave(group_id)
            if self.manager_window and self.manager_window.winfo_exists():
                self.manager_window.destroy()
