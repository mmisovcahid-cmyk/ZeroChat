"""
ZeroChat - Sol Panel (Kontak Listesi)
WhatsApp tarzı sol panel: cihaz ismi, IP, MAC ve çevrimiçi durumu.
Ayrıca grup yönetimi (admin, gizli/public, davet) içerir.
"""

import tkinter as tk
from tkinter import messagebox

from config import (
    COLORS,
    SIDEBAR_WIDTH,
    GROUP_ALL,
    GROUP_PREFIX,
    GROUP_PUBLIC,
    GROUP_PRIVATE,
    INVITE_CODE_LENGTH,
)


class Sidebar(tk.Frame):
    """Sol panel - otomatik keşfedilen cihazların listesi ve gruplar."""

    def __init__(self, parent, on_contact_select, contacts,
                 on_group_create=None, on_group_join=None, on_group_leave=None,
                 on_group_manage=None, on_invite_accept=None,
                 on_invite_reject=None, on_remove_member=None,
                 on_set_visibility=None, on_delete_group=None,
                 on_toggle_stealth=None, on_generate_pair_code=None,
                 on_pair_accept=None, on_pair_reject=None,
                 on_pair_request=None, on_add_shared_file=None):
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
        self.on_add_shared_file = on_add_shared_file
        self.contacts = contacts

        self.contact_frames = {}
        self.group_frames = {}
        # Grup yönetim penceresi referansı
        self.manager_window = None
        self.manager_group_id = None
        self.manager_admin_id = None
        self.manager_refs = {}
        # group_id -> grup bilgisi (davet kodu araması için)
        self.group_data = {}
        # Pairing istek satırları
        self.pair_request_frames = {}
        # Paylaşılan dosya satırları
        self.shared_file_frames = {}

        self._build_header()
        self._build_search()
        self._build_group_section()
        self._build_contact_list()
        self._build_new_chat_button()

    # =====================================================================
    # Kurulum
    # =====================================================================

    def _build_header(self):
        header = tk.Frame(self, bg=COLORS["sidebar"], height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="Sohbetler",
            font=("Segoe UI", 14, "bold"),
            bg=COLORS["sidebar"], fg=COLORS["text"],
        ).pack(side="left", padx=15, pady=10)

        # Araç çubuğu
        tools = tk.Frame(header, bg=COLORS["sidebar"])
        tools.pack(side="right", padx=8)

        # Gizli mod
        self.stealth_button = tk.Label(
            tools, text="👻", font=("Segoe UI", 13),
            bg=COLORS["sidebar"], fg=COLORS["text_secondary"],
            cursor="hand2",
        )
        self.stealth_button.pack(side="right", padx=4)
        self.stealth_button.bind("<Button-1>", self._on_toggle_stealth)

        # Pairing kodu
        self.pair_button = tk.Label(
            tools, text="🔗", font=("Segoe UI", 12),
            bg=COLORS["sidebar"], fg=COLORS["text_secondary"],
            cursor="hand2",
        )
        self.pair_button.pack(side="right", padx=4)
        self.pair_button.bind("<Button-1>", self._on_pairing)

    def _build_search(self):
        search_frame = tk.Frame(self, bg=COLORS["sidebar"])
        search_frame.pack(fill="x", padx=10, pady=5)

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame, textvariable=self.search_var,
            font=("Segoe UI", 10), bg=COLORS["background"],
            relief="flat", highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        search_entry.pack(fill="x", ipady=5)
        search_entry.insert(0, "Ara...")
        self.search_var.trace_add("write", lambda *_: self._filter_contacts())

    def _build_group_section(self):
        group_header = tk.Frame(self, bg=COLORS["sidebar"])
        group_header.pack(fill="x", padx=10, pady=(8, 2))

        tk.Label(
            group_header, text="GRUPLAR",
            font=("Segoe UI", 8, "bold"),
            bg=COLORS["sidebar"], fg=COLORS["text_secondary"],
        ).pack(side="left")

        tk.Button(
            group_header, text="+ Katıl",
            font=("Segoe UI", 8, "bold"), bg=COLORS["sidebar"],
            fg=COLORS["accent"], relief="flat", padx=4,
            command=self._on_join_group,
        ).pack(side="right", padx=(0, 8))

        tk.Button(
            group_header, text="+ Oluştur",
            font=("Segoe UI", 8, "bold"), bg=COLORS["sidebar"],
            fg=COLORS["accent"], relief="flat", padx=4,
            command=self._on_create_group,
        ).pack(side="right")

        self.group_container = tk.Frame(self, bg=COLORS["sidebar"])
        self.group_container.pack(fill="x", padx=5)

    def _build_contact_list(self):
        tk.Label(
            self, text="CİHAZLAR",
            font=("Segoe UI", 8, "bold"),
            bg=COLORS["sidebar"], fg=COLORS["text_secondary"],
        ).pack(anchor="w", padx=15, pady=(10, 2))

        self.contact_container = tk.Frame(self, bg=COLORS["sidebar"])
        self.contact_container.pack(fill="both", expand=True)

        # Durum mesajı (altta)
        self.sidebar_status = tk.Label(
            self, text="", font=("Segoe UI", 8, "bold"),
            bg=COLORS["sidebar"], fg=COLORS["accent"],
        )
        self.sidebar_status.pack(anchor="w", padx=10, pady=(0, 2))

    def _build_new_chat_button(self):
        btn_frame = tk.Frame(self, bg=COLORS["sidebar"])
        btn_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(
            btn_frame, text="+ Yeni Sohbet",
            font=("Segoe UI", 10, "bold"), bg=COLORS["accent"], fg="white",
            relief="flat", padx=20, pady=8, command=self._on_new_chat,
        ).pack(fill="x")

    # =====================================================================
    # Yeni sohbet / grup pencereleri
    # =====================================================================

    def _on_new_chat(self):
        """Yeni sohbet - hedef cihaz seçimi."""
        dialog = tk.Toplevel(self)
        dialog.title("Yeni Sohbet")
        dialog.geometry("420x300")
        dialog.configure(bg=COLORS["sidebar"])
        dialog.transient(self)

        tk.Label(
            dialog, text="Hedef cihazın MAC adresini girin:",
            font=("Segoe UI", 10), bg=COLORS["sidebar"], fg=COLORS["text"],
        ).pack(anchor="w", padx=15, pady=(15, 5))

        entry = tk.Entry(
            dialog, font=("Consolas", 11), bg=COLORS["background"],
            relief="flat", highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        entry.pack(fill="x", padx=15, ipady=5)
        entry.focus()

        tk.Label(
            dialog, text="Örnek: A4:5E:60:D2:9F:11",
            font=("Segoe UI", 8), bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w", padx=15, pady=(3, 10))

        def connect():
            target = entry.get().strip().upper()
            if target:
                self.on_contact_select(target)
                dialog.destroy()

        tk.Button(
            dialog, text="Bağlan", bg=COLORS["accent"], fg="white",
            relief="flat", padx=20, pady=5, command=connect,
        ).pack(pady=5)

        entry.bind("<Return>", lambda e: connect())

    def _on_create_group(self):
        """Yeni grup oluşturma penceresi."""
        dialog = tk.Toplevel(self)
        dialog.title("Grup Oluştur")
        dialog.geometry("400x330")
        dialog.configure(bg=COLORS["sidebar"])
        dialog.transient(self)

        tk.Label(
            dialog, text="Grup adı:",
            font=("Segoe UI", 10), bg=COLORS["sidebar"], fg=COLORS["text"],
        ).pack(anchor="w", padx=15, pady=(15, 5))

        name_entry = tk.Entry(
            dialog, font=("Segoe UI", 12), bg=COLORS["background"],
            relief="flat", highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        name_entry.pack(fill="x", padx=15, ipady=5)
        name_entry.focus()

        # Gizli / Public seçimi
        tk.Label(
            dialog, text="Erişim:",
            font=("Segoe UI", 10), bg=COLORS["sidebar"], fg=COLORS["text"],
        ).pack(anchor="w", padx=15, pady=(15, 5))

        visibility = tk.StringVar(value=GROUP_PUBLIC)

        tk.Radiobutton(
            dialog, text="Herkese açık (herkes katılabilir)",
            variable=visibility, value=GROUP_PUBLIC,
            font=("Segoe UI", 9), bg=COLORS["sidebar"],
            fg=COLORS["text"], selectcolor=COLORS["sidebar"],
            activebackground=COLORS["sidebar"],
        ).pack(anchor="w", padx=25)

        tk.Radiobutton(
            dialog, text="Gizli (sadece davet kodu ile)",
            variable=visibility, value=GROUP_PRIVATE,
            font=("Segoe UI", 9), bg=COLORS["sidebar"],
            fg=COLORS["text"], selectcolor=COLORS["sidebar"],
            activebackground=COLORS["sidebar"],
        ).pack(anchor="w", padx=25, pady=(2, 15))

        def create():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Uyarı", "Grup adı girin!")
                return
            group_id = self._make_group_id(name)
            if self.on_group_create:
                self.on_group_create(group_id, name, visibility.get())
            dialog.destroy()

        tk.Button(
            dialog, text="Oluştur", bg=COLORS["accent"], fg="white",
            relief="flat", padx=20, pady=5, command=create,
        ).pack(pady=5)

        name_entry.bind("<Return>", lambda e: create())

    def _on_join_group(self):
        """Gruba katılma penceresi (kod ile)."""
        dialog = tk.Toplevel(self)
        dialog.title("Gruba Katıl")
        dialog.geometry("360x200")
        dialog.configure(bg=COLORS["sidebar"])
        dialog.transient(self)

        tk.Label(
            dialog, text="Grup adı (veya kodu):",
            font=("Segoe UI", 10), bg=COLORS["sidebar"], fg=COLORS["text"],
        ).pack(anchor="w", padx=15, pady=(15, 5))

        entry = tk.Entry(
            dialog, font=("Segoe UI", 12), bg=COLORS["background"],
            relief="flat", highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        entry.pack(fill="x", padx=15, ipady=5)
        entry.focus()

        tk.Label(
            dialog,
            text="Gizli gruplar için davet kodunu girebilirsiniz.",
            font=("Segoe UI", 8), bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w", padx=15, pady=(5, 10))

        def join():
            value = entry.get().strip()
            if not value:
                return
            # Kod gibi görünüyorsa (6 karakter, büyük harf/rakam)
            if len(value) == INVITE_CODE_LENGTH and value.isalnum():
                group_id = self._find_group_by_code(value)
                if group_id:
                    self.on_group_join(group_id, value.upper())
                else:
                    messagebox.showerror(
                        "Bulunamadı",
                        "Bu koda sahip bir grup bulunamadı.\n"
                        "Grubu önce gruba katılın, sonra kodu girin.",
                    )
            else:
                group_id = self._make_group_id(value)
                self.on_group_join(group_id, "")
            dialog.destroy()

        tk.Button(
            dialog, text="Katıl", bg=COLORS["accent"], fg="white",
            relief="flat", padx=20, pady=5, command=join,
        ).pack(pady=5)

        entry.bind("<Return>", lambda e: join())

    @staticmethod
    def _make_group_id(name):
        """Grup adından grup kimliği üretir."""
        return GROUP_PREFIX + name.strip().lower().replace(" ", "_")

    def _find_group_by_code(self, code):
        """Davet koduna sahip grubu bulur (yerel kayıtlardan)."""
        for group_id, group in getattr(self, "group_data", {}).items():
            if group.get("invite_code", "").upper() == code.upper():
                return group_id
        return None

    # =====================================================================
    # Cihaz / grup listesi
    # =====================================================================

    def add_device(self, device_id, name, ip, mac, hidden=False):
        """Keşfedilen cihazı listeye ekler."""
        if device_id in self.contact_frames:
            self.update_device(device_id, name=name, ip=ip, mac=mac, hidden=hidden)
            return

        frame = tk.Frame(self.contact_container, bg=COLORS["sidebar"])
        frame.pack(fill="x", padx=5, pady=2)

        top_row = tk.Frame(frame, bg=COLORS["sidebar"])
        top_row.pack(fill="x", padx=10, pady=(6, 0))

        name_label = tk.Label(
            top_row, text=self._device_title(name, hidden),
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["sidebar"], fg=COLORS["text"], anchor="w",
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
        info_label.pack(fill="x", padx=10, pady=(1, 0))

        preview_label = tk.Label(
            frame, text="", font=("Segoe UI", 9),
            bg=COLORS["sidebar"], fg=COLORS["text_secondary"], anchor="w",
        )
        preview_label.pack(fill="x", padx=10, pady=(0, 6))

        for widget in (frame, top_row, name_label, info_label, preview_label, status_label):
            widget.bind("<Button-1>", lambda e, did=device_id: self.on_contact_select(did))

        self.contact_frames[device_id] = {
            "frame": frame, "name": name_label, "info": info_label,
            "preview": preview_label, "status": status_label,
        }

    @staticmethod
    def _device_title(name, hidden):
        """Cihaz başlığı (gizli cihazlarda hayalet ikonu)."""
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
            self.stealth_button.config(text="👻", fg=COLORS["accent"])
        else:
            self.stealth_button.config(text="👻", fg=COLORS["text_secondary"])

    def _on_toggle_stealth(self, event=None):
        """Gizli modu açar/kapatır."""
        if self.on_toggle_stealth:
            self.on_toggle_stealth()

    def _on_pairing(self, event=None):
        """Eşleştirme penceresini açar."""
        if self.on_pair_request:
            self.on_pair_request()

    # -- Pairing istekleri ----------------------------------------------

    def show_pair_request(self, user_id, user_name):
        """Eşleştirme isteğini listede gösterir."""
        if user_id in self.pair_request_frames:
            return

        frame = tk.Frame(self.contact_container, bg=COLORS["background"])
        frame.pack(fill="x", padx=5, pady=2)

        tk.Label(
            frame, text=f"🔗 {user_name} eşleşmek istiyor",
            font=("Segoe UI", 9, "bold"), bg=COLORS["background"],
            fg=COLORS["text"], anchor="w",
        ).pack(side="left", padx=8, pady=4)

        tk.Label(
            frame, text="Kabul", font=("Segoe UI", 8, "bold"),
            bg=COLORS["accent"], fg="white", cursor="hand2", padx=6, pady=2,
        ).pack(side="right", padx=2)
        tk.Label(
            frame, text="Reddet", font=("Segoe UI", 8),
            bg=COLORS["background"], fg=COLORS["text_secondary"],
            cursor="hand2", padx=6, pady=2,
        ).pack(side="right", padx=2)

        frame.winfo_children()[-2].bind(
            "<Button-1>", lambda e, uid=user_id: self._accept_pair(uid))
        frame.winfo_children()[-1].bind(
            "<Button-1>", lambda e, uid=user_id: self._reject_pair(uid))

        self.pair_request_frames[user_id] = frame

    def remove_pair_request(self, user_id):
        """Eşleştirme isteğini kaldırır."""
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

    # -- Paylaşılan dosyalar (sınıf panosu) ----------------------------

    def add_shared_file(self, info):
        """Paylaşılan dosyayı sınıf panosuna ekler."""
        file_id = info.get("file_id", "")
        if file_id in self.shared_file_frames:
            return

        frame = tk.Frame(self.contact_container, bg=COLORS["background"])
        frame.pack(fill="x", padx=5, pady=2)

        name = info.get("name", "dosya")
        size = info.get("size", 0)
        size_text = f"{size / 1024:.0f} KB" if size < 1024 * 1024 \
            else f"{size / 1024 / 1024:.1f} MB"

        tk.Label(
            frame, text=f"📎 {name}", font=("Segoe UI", 9, "bold"),
            bg=COLORS["background"], fg=COLORS["text"], anchor="w",
        ).pack(side="left", padx=8, pady=3)

        tk.Label(
            frame, text=size_text, font=("Segoe UI", 8),
            bg=COLORS["background"], fg=COLORS["text_secondary"],
        ).pack(side="right", padx=8)

        self.shared_file_frames[file_id] = frame

    def add_group(self, group_id, display_name, member_count=0,
                 visibility=GROUP_PUBLIC, is_admin=False, pending=0,
                 invite_code="", admin_id="", can_leave=True):
        """Grubu grup listesine ekler."""
        # Davet kodu araması için sakla
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
        frame.pack(fill="x", padx=5, pady=2)

        top_row = tk.Frame(frame, bg=COLORS["sidebar"])
        top_row.pack(fill="x", padx=10, pady=(4, 0))

        name_label = tk.Label(
            top_row, text=self._group_title(display_name, visibility, is_admin),
            font=("Segoe UI", 10, "bold"), bg=COLORS["sidebar"],
            fg=COLORS["text"], anchor="w",
        )
        name_label.pack(side="left")

        # Yönet / ayrıl butonu
        if is_admin:
            action_text = "⋯"
        elif can_leave:
            action_text = "✕"
        else:
            action_text = ""

        action_btn = tk.Label(
            top_row, text=action_text,
            font=("Segoe UI", 11, "bold"), bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"], cursor="hand2",
        )
        action_btn.pack(side="right")

        info_label = tk.Label(
            frame, text=self._group_info_text(member_count, pending),
            font=("Segoe UI", 8), bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"], anchor="w",
        )
        info_label.pack(fill="x", padx=10, pady=(0, 4))

        for widget in (frame, top_row, name_label, info_label):
            widget.bind("<Button-1>", lambda e, gid=group_id: self.on_contact_select(gid))

        if is_admin:
            action_btn.bind(
                "<Button-1>",
                lambda e, gid=group_id: self.on_group_manage(gid),
            )
        elif can_leave:
            action_btn.bind(
                "<Button-1>",
                lambda e, gid=group_id: self._leave_group(gid, display_name),
            )

        self.group_frames[group_id] = {
            "frame": frame, "name": name_label, "info": info_label,
        }

    @staticmethod
    def _group_title(display_name, visibility, is_admin):
        """Grup başlığını oluşturur (kilit / yönetici rozeti)."""
        icon = "🔒" if visibility == GROUP_PRIVATE else "👥"
        title = f"{icon} {display_name}"
        if is_admin:
            title += "  ★"
        return title

    @staticmethod
    def _group_info_text(member_count, pending):
        """Grup alt bilgi metni."""
        text = f"{member_count} üye"
        if pending:
            text += f"  •  {pending} istek"
        return text

    def update_group_members(self, group_id, member_count):
        """Grup üye sayısını günceller."""
        entry = self.group_frames.get(group_id)
        if entry:
            entry["info"].config(text=self._group_info_text(member_count, 0))

    def update_group_preview(self, group_id, message):
        """Grup için son mesaj önizlemesini günceller."""
        entry = self.group_frames.get(group_id)
        if not entry:
            return
        preview = message if len(message) <= 32 else message[:32] + "..."
        entry["info"].config(text=preview)

    def remove_group(self, group_id):
        """Grubu listeden kaldırır."""
        entry = self.group_frames.pop(group_id, None)
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
        """Son mesaj önizlemesini günceller."""
        entry = self.contact_frames.get(device_id)
        if not entry:
            return
        preview = message if len(message) <= 32 else message[:32] + "..."
        entry["preview"].config(text=preview)

    def _leave_group(self, group_id, display_name):
        """Gruptan ayrılma onayı ister."""
        if messagebox.askyesno(
            "Gruptan Ayrıl", f"'{display_name}' grubundan ayrılmak istiyor musun?"
        ):
            if self.on_group_leave:
                self.on_group_leave(group_id)

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
        win.geometry("440x520")
        win.configure(bg=COLORS["sidebar"])
        win.transient(self)

        # Başlık
        tk.Label(
            win, text=group["name"], font=("Segoe UI", 14, "bold"),
            bg=COLORS["sidebar"], fg=COLORS["text"],
        ).pack(anchor="w", padx=15, pady=(15, 5))

        visibility_text = (
            "Gizli (sadece davet kodu ile)" if group["visibility"] == GROUP_PRIVATE
            else "Herkese açık"
        )
        tk.Label(
            win, text=f"Erişim: {visibility_text}",
            font=("Segoe UI", 9), bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w", padx=15)

        # Admin durumu
        if is_admin:
            tk.Label(
                win, text="★ Bu grubun yöneticisisiniz",
                font=("Segoe UI", 9, "bold"), bg=COLORS["sidebar"],
                fg=COLORS["accent"],
            ).pack(anchor="w", padx=15, pady=(3, 10))
        else:
            tk.Label(
                win, text="Yönetici: " + group.get("admin_id", "-"),
                font=("Segoe UI", 8), bg=COLORS["sidebar"],
                fg=COLORS["text_secondary"],
            ).pack(anchor="w", padx=15, pady=(3, 10))

        # --- Bölüm: Davet Kodu ---
        tk.Label(
            win, text="DAVET KODU", font=("Segoe UI", 8, "bold"),
            bg=COLORS["sidebar"], fg=COLORS["text_secondary"],
        ).pack(anchor="w", padx=15)

        code_frame = tk.Frame(win, bg=COLORS["sidebar"])
        code_frame.pack(fill="x", padx=15, pady=(3, 5))

        code_label = tk.Label(
            code_frame, text=group.get("invite_code", "-"),
            font=("Consolas", 18, "bold"), bg=COLORS["background"],
            fg=COLORS["accent"], padx=15, pady=6,
        )
        code_label.pack(side="left")

        tk.Button(
            code_frame, text="Kopyala", bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"], relief="flat",
            command=lambda: self._copy_code(code_label.cget("text")),
        ).pack(side="left", padx=8)

        self.manager_refs["code_label"] = code_label

        # --- Bölüm: Bekleyen Davetler ---
        pending = group.get("pending", {})
        if pending:
            tk.Label(
                win, text="BEKLEYEN DAVET İSTEKLERİ",
                font=("Segoe UI", 8, "bold"), bg=COLORS["sidebar"],
                fg=COLORS["accent"],
            ).pack(anchor="w", padx=15, pady=(12, 3))

            for user_id, user_name in list(pending.items()):
                row = tk.Frame(win, bg=COLORS["sidebar"])
                row.pack(fill="x", padx=15, pady=2)

                tk.Label(
                    row, text=f"{user_name}", font=("Segoe UI", 10),
                    bg=COLORS["sidebar"], fg=COLORS["text"],
                ).pack(side="left")

                tk.Button(
                    row, text="Kabul", bg=COLORS["accent"], fg="white",
                    relief="flat", font=("Segoe UI", 8, "bold"),
                    command=lambda uid=user_id: self._accept_invite(group_id, uid),
                ).pack(side="right", padx=2)

                tk.Button(
                    row, text="Reddet", bg=COLORS["sidebar"],
                    fg=COLORS["text_secondary"], relief="flat",
                    font=("Segoe UI", 8),
                    command=lambda uid=user_id: self._reject_invite(group_id, uid),
                ).pack(side="right", padx=2)

        # --- Bölüm: Üyeler ---
        tk.Label(
            win, text=f"ÜYELER ({len(group['members'])})",
            font=("Segoe UI", 8, "bold"), bg=COLORS["sidebar"],
            fg=COLORS["text_secondary"],
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
                row, text=label_text, font=("Segoe UI", 10),
                bg=COLORS["sidebar"], fg=COLORS["text"],
            ).pack(side="left")

            # Admin kendini ve admini çıkaramaz
            if is_admin and user_id != group.get("admin_id"):
                tk.Button(
                    row, text="Çıkar", bg=COLORS["sidebar"],
                    fg=COLORS["text_secondary"], relief="flat",
                    font=("Segoe UI", 8),
                    command=lambda uid=user_id: self._remove_member(group_id, uid),
                ).pack(side="right")

        # --- Alt: Admin işlemleri ---
        if is_admin:
            tk.Label(
                win, text="YÖNETİCİ İŞLEMLERİ",
                font=("Segoe UI", 8, "bold"), bg=COLORS["sidebar"],
                fg=COLORS["text_secondary"],
            ).pack(anchor="w", padx=15, pady=(10, 3))

            btn_row = tk.Frame(win, bg=COLORS["sidebar"])
            btn_row.pack(fill="x", padx=15)

            # Görünürlük değiştir
            new_visibility = (
                GROUP_PUBLIC if group["visibility"] == GROUP_PRIVATE else GROUP_PRIVATE
            )
            toggle_text = (
                "Herkese Açık Yap" if group["visibility"] == GROUP_PRIVATE
                else "Gizli Yap"
            )
            tk.Button(
                btn_row, text=toggle_text, bg=COLORS["background"],
                fg=COLORS["text"], relief="flat", font=("Segoe UI", 9),
                command=lambda: self._toggle_visibility(group_id, new_visibility),
            ).pack(side="left", padx=2)

            # Grubu sil
            tk.Button(
                btn_row, text="Grubu Sil", bg="#DC3545", fg="white",
                relief="flat", font=("Segoe UI", 9, "bold"),
                command=lambda: self._delete_group(group_id),
            ).pack(side="right", padx=2)

        # Katıl / Ayrıl
        join_frame = tk.Frame(win, bg=COLORS["sidebar"])
        join_frame.pack(fill="x", padx=15, pady=12)

        if is_admin:
            tk.Button(
                join_frame, text="Grubu Sil ve Kapat", bg="#DC3545",
                fg="white", relief="flat", font=("Segoe UI", 10, "bold"),
                pady=6, command=lambda: self._delete_group(group_id),
            ).pack(fill="x")
        else:
            tk.Button(
                join_frame, text="Gruptan Ayrıl", bg=COLORS["background"],
                fg=COLORS["text_secondary"], relief="flat",
                font=("Segoe UI", 10), pady=6,
                command=lambda: self._leave_and_close(group_id, group["name"]),
            ).pack(fill="x")

    def refresh_group_manager(self, group_id, group):
        """Yönetim penceresini yeniler."""
        if self.manager_window and self.manager_window.winfo_exists():
            self.open_group_manager(
                group_id, group, group.get("admin_id") == self.manager_admin_id
            )

    def _copy_code(self, code):
        """Davet kodunu panoya kopyalar."""
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
        """Üyeyi çıkar (uygulama seviyesinde admin kontrolü yapılır)."""
        from tkinter import messagebox
        if messagebox.askyesno("Üyeyi Çıkar", "Bu üyeyi gruptan çıkarmak istiyor musun?"):
            if self.on_remove_member:
                self.on_remove_member(group_id, user_id)

    def _toggle_visibility(self, group_id, new_visibility):
        if self.on_set_visibility:
            self.on_set_visibility(group_id, new_visibility)

    def _delete_group(self, group_id):
        from tkinter import messagebox
        if messagebox.askyesno(
            "Grubu Sil",
            "Bu grubu silmek istiyor musun?\n"
            "Gruptaki tüm üyeler çıkarılacak.",
        ):
            if self.on_delete_group:
                self.on_delete_group(group_id)
            if self.manager_window and self.manager_window.winfo_exists():
                self.manager_window.destroy()

    def _leave_and_close(self, group_id, name):
        from tkinter import messagebox
        if messagebox.askyesno("Gruptan Ayrıl", f"'{name}' grubundan ayrılmak istiyor musun?"):
            if self.on_group_leave:
                self.on_group_leave(group_id)
            if self.manager_window and self.manager_window.winfo_exists():
                self.manager_window.destroy()
