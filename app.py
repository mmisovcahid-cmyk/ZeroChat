"""
ZeroChat - Ana Uygulama Sınıfı
GUI ve ağ yönetimini birleştirir.
"""

import time
import tkinter as tk

from config import (
    COLORS,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    OFFLINE_TIMEOUT,
    HISTORY_SAVE_ON_CLOSE,
    GROUP_ALL,
    GROUP_PREFIX,
    GROUP_PUBLIC,
    GROUP_PRIVATE,
)
from gui.sidebar import Sidebar
from gui.chat_area import ChatArea
from network.socket import NetworkManager
from network.packet import create_message, generate_invite_code
import storage


class ZeroChatApp:
    """Ana uygulama sınıfı."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ZeroChat - LAN Sohbet")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=COLORS["background"])
        self.root.resizable(True, True)

        self.user_id = ""      # MAC adresi (benzersiz cihaz kimliği)
        self.user_name = ""    # kullanıcının seçtiği görünen isim
        self.my_ip = ""
        self.my_mac = ""
        self.broadcast_address = ""

        # device_id -> {"name", "ip", "mac", "last_seen", "online"}
        self.devices = {}
        # device_id -> [(is_outgoing, mesaj_paketi), ...]
        self.chats = {}

        # group_id -> {
        #   "name", "admin_id", "visibility", "members", "invite_code", "pending"
        # }
        self.groups = {
            GROUP_ALL: {
                "name": "Tüm Ağ",
                "admin_id": "",
                "visibility": GROUP_PUBLIC,
                "members": {},
                "invite_code": "",
                "pending": {},
            }
        }

        # msg_id -> {user_id: user_name}  (el kaldıranlar)
        self.hands = {}

        # poll_id -> {
        #   "question", "options", "votes", "open", "creator", "target"
        # }
        self.polls = {}

        self.network = None
        self.sidebar = None
        self.chat_area = None

    # =====================================================================
    # Başlatma / GUI
    # =====================================================================

    def start(self, user_id, user_name):
        """Uygulamayı başlatır."""
        self.user_id = user_id
        self.user_name = user_name

        # Diskten geçmişi yükle
        self.chats = storage.load_history()
        if self.chats:
            print(f"{len(self.chats)} sohbet geçmişi yüklendi.")

        # Ağ manager'ı başlat
        self.network = NetworkManager(user_id, user_name, self._on_packet)
        self.network.start()
        self.my_ip = self.network.ip
        self.my_mac = user_id
        self.broadcast_address = self.network.broadcast_address

        self._build_gui()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._schedule_offline_check()
        self.root.mainloop()

    def _build_gui(self):
        """GUI bileşenlerini oluşturur."""
        info_bar = tk.Frame(self.root, bg=COLORS["accent"], height=28)
        info_bar.pack(fill="x")
        info_bar.pack_propagate(False)

        tk.Label(
            info_bar,
            text=f"Ben: {self.user_name}  |  IP: {self.my_ip}  |  MAC: {self.my_mac}",
            font=("Segoe UI", 8),
            bg=COLORS["accent"],
            fg="white",
        ).pack(side="left", padx=10)

        tk.Label(
            info_bar,
            text=f"Yayın: {self.broadcast_address}",
            font=("Segoe UI", 8),
            bg=COLORS["accent"],
            fg="white",
        ).pack(side="left", padx=(0, 10))

        self.online_label = tk.Label(
            info_bar,
            text="Çevrimiçi: 0",
            font=("Segoe UI", 8, "bold"),
            bg=COLORS["accent"],
            fg="white",
        )
        self.online_label.pack(side="right", padx=10)

        # Sol panel
        self.sidebar = Sidebar(
            self.root,
            self._on_contact_select,
            self.devices,
            on_group_create=self._on_group_create,
            on_group_join=self._on_group_join,
            on_group_leave=self._on_group_leave,
            on_group_manage=self._on_group_manage,
            on_invite_accept=self._on_invite_accept,
            on_invite_reject=self._on_invite_reject,
            on_remove_member=self._remove_member,
            on_set_visibility=self._set_visibility,
            on_delete_group=self._delete_group,
        )
        self.sidebar.pack(side="left", fill="y")

        # Sağ panel
        self.chat_area = ChatArea(
            self.root,
            self._on_send_message,
            on_delete_message=self._on_delete_message,
            on_edit_message=self._on_edit_message,
            on_copy_message=self._on_copy_message,
            on_hand_raise=self._on_hand_raise,
            on_poll_create=self._on_poll_create,
            on_poll_vote=self._on_poll_vote,
            on_poll_close=self._on_poll_close,
            my_user_id=self.user_id,
        )
        self.chat_area.pack(side="right", fill="both", expand=True)

    # =====================================================================
    # Paket işleme
    # =====================================================================

    def _on_packet(self, pkt):
        """Ağ thread'inden gelen paket -> ana thread'e devret."""
        self.root.after(0, self._process_packet, pkt)

    def _process_packet(self, pkt):
        """Paketi ana thread'de işler."""
        handlers = {
            "message": self._handle_message,
            "presence": self._handle_presence,
            "group_action": self._handle_group_action,
            "delete_message": self._handle_delete_notice,
            "edit_message": self._handle_edit_notice,
            "hand_raise": self._handle_hand_raise,
            "poll": self._handle_poll,
        }
        handler = handlers.get(pkt.get("type"))
        if handler:
            handler(pkt)

    def _is_message_for_me(self, target_id):
        """Mesajın bana gelip gelmediğini kontrol eder."""
        if target_id == self.user_id:
            return True
        if target_id == GROUP_ALL:
            return True
        if target_id.startswith(GROUP_PREFIX):
            return target_id in self.groups
        return False

    def _handle_message(self, pkt):
        """Gelen mesajı işler."""
        sender_id = pkt["sender_id"]
        target_id = pkt["target_id"]

        if not self._is_message_for_me(target_id):
            return
        if sender_id == self.user_id:
            return

        self.chats.setdefault(sender_id, []).append((False, pkt))

        if target_id.startswith(GROUP_PREFIX):
            if self.sidebar:
                self.sidebar.update_group_preview(target_id, pkt["content"])
        elif self.sidebar:
            self.sidebar.update_last_message(sender_id, pkt["content"])

        if self.chat_area and self.chat_area.current_chat_id == sender_id:
            self.chat_area.add_message(
                pkt["content"],
                is_outgoing=False,
                timestamp=pkt["timestamp"],
                sender_name=pkt["sender_name"],
                msg_id=pkt.get("msg_id", ""),
            )

    def _handle_presence(self, pkt):
        """Kimlik/keşif paketini işler."""
        device_id = pkt.get("user_id", "")
        user_name = pkt.get("user_name", device_id)
        ip = pkt.get("ip", "?")
        mac = pkt.get("mac", device_id)
        status = pkt.get("status", "online")

        if not device_id or device_id == self.user_id:
            return

        if status == "offline":
            if device_id in self.devices:
                self.devices[device_id]["online"] = False
                self.devices[device_id]["last_seen"] = time.time()
                if self.sidebar:
                    self.sidebar.set_status(device_id, False)
                self._update_online_count()
            return

        if device_id not in self.devices:
            self.devices[device_id] = {
                "name": user_name,
                "ip": ip,
                "mac": mac,
                "last_seen": time.time(),
                "online": True,
            }
            if self.sidebar:
                self.sidebar.add_device(device_id, user_name, ip, mac)
        else:
            device = self.devices[device_id]
            device["name"] = user_name
            device["ip"] = ip
            device["mac"] = mac
            device["last_seen"] = time.time()
            if not device["online"]:
                device["online"] = True
                if self.sidebar:
                    self.sidebar.set_status(device_id, True)

        self._update_online_count()

    def _handle_delete_notice(self, pkt):
        """Mesaj silme bildirimini işler."""
        msg_id = pkt.get("msg_id", "")
        if not msg_id:
            return

        for chat_id, messages in self.chats.items():
            self.chats[chat_id] = [
                (is_outgoing, m) for is_outgoing, m in messages
                if m.get("msg_id") != msg_id
            ]

        if self.chat_area:
            self.chat_area.remove_message(msg_id)
            self.chat_area.update_hands(msg_id, {})

    def _handle_edit_notice(self, pkt):
        """Mesaj düzenleme bildirimini işler."""
        msg_id = pkt.get("msg_id", "")
        new_content = pkt.get("content", "")
        if not msg_id:
            return

        for messages in self.chats.values():
            for is_outgoing, m in messages:
                if m.get("msg_id") == msg_id:
                    m["content"] = new_content
                    m["edited"] = True

        if self.chat_area:
            self.chat_area.update_message(msg_id, new_content)

    # =====================================================================
    # Grup işlemleri
    # =====================================================================

    def _get_group(self, group_id):
        """Grup bilgisini döndürür (yoksa None)."""
        return self.groups.get(group_id)

    def _is_admin(self, group_id):
        """Kullanıcının grup yöneticisi olup olmadığını kontrol eder."""
        group = self.groups.get(group_id)
        if not group:
            return False
        return group.get("admin_id") == self.user_id

    def _ensure_group(self, group_id, name="", admin_id="", visibility=GROUP_PUBLIC):
        """Grup kaydını yoksa oluşturur."""
        if group_id not in self.groups:
            self.groups[group_id] = {
                "name": name or group_id.replace(GROUP_PREFIX, ""),
                "admin_id": admin_id,
                "visibility": visibility,
                "members": {},
                "invite_code": generate_invite_code(),
                "pending": {},
            }
        return self.groups[group_id]

    def _handle_group_action(self, pkt):
        """Grup işlem bildirimini işler."""
        action = pkt.get("action", "")
        group_id = pkt.get("group", "")
        user_id = pkt.get("user_id", "")
        user_name = pkt.get("user_name", user_id)

        if not group_id or user_id == self.user_id:
            return

        if action == "join":
            self._handle_group_join(group_id, user_id, user_name)
        elif action == "leave":
            self._handle_group_leave(group_id, user_id)
        elif action == "invite_request":
            self._handle_invite_request(group_id, user_id, user_name, pkt.get("code", ""))
        elif action == "invite_accept":
            self._handle_invite_accept(group_id, user_id, user_name)
        elif action == "invite_reject":
            self._handle_invite_reject(group_id, user_id)
        elif action == "remove_member":
            self._handle_remove_member(group_id, user_id, pkt.get("target_id", ""))
        elif action == "delete_group":
            self._handle_delete_group(group_id, user_id)
        elif action == "set_visibility":
            self._handle_set_visibility(group_id, user_id, pkt.get("visibility", ""))

        self._refresh_group_list()

    def _handle_group_join(self, group_id, user_id, user_name):
        """Biri gruba katıldı."""
        group = self.groups.get(group_id)
        if not group:
            return
        # Gizli gruba sadece admin ekleyebilir
        if group["visibility"] == GROUP_PRIVATE and group["admin_id"] != user_id:
            return
        group["members"][user_id] = user_name

    def _handle_group_leave(self, group_id, user_id):
        """Biri gruptan ayrıldı."""
        group = self.groups.get(group_id)
        if not group:
            return
        group["members"].pop(user_id, None)
        group["pending"].pop(user_id, None)

    def _handle_invite_request(self, group_id, user_id, user_name, code):
        """Gizli gruba katılma isteği geldi (admin'e)."""
        group = self.groups.get(group_id)
        if not group:
            return
        if group["visibility"] != GROUP_PRIVATE:
            return
        if code and group["invite_code"] and code.upper() != group["invite_code"]:
            return  # Kod yanlış, istek yok sayılır
        group["pending"][user_id] = user_name

    def _handle_invite_accept(self, group_id, user_id, user_name):
        """Admin daveti kabul etti."""
        group = self.groups.get(group_id)
        if not group:
            return
        group["pending"].pop(user_id, None)
        group["members"][user_id] = user_name

    def _handle_invite_reject(self, group_id, user_id):
        """Admin daveti reddetti."""
        group = self.groups.get(group_id)
        if not group:
            return
        group["pending"].pop(user_id, None)

    def _handle_remove_member(self, group_id, admin_id, target_id):
        """Admin bir üyeyi çıkardı."""
        group = self.groups.get(group_id)
        if not group or group["admin_id"] != admin_id:
            return
        group["members"].pop(target_id, None)
        group["pending"].pop(target_id, None)

    def _handle_delete_group(self, group_id, admin_id):
        """Admin grubu sildi."""
        group = self.groups.get(group_id)
        if not group or group["admin_id"] != admin_id:
            return
        del self.groups[group_id]
        if self.sidebar:
            self.sidebar.remove_group(group_id)

    def _handle_set_visibility(self, group_id, admin_id, visibility):
        """Admin grubun görünürlüğünü değiştirdi."""
        group = self.groups.get(group_id)
        if not group or group["admin_id"] != admin_id:
            return
        if visibility in (GROUP_PUBLIC, GROUP_PRIVATE):
            group["visibility"] = visibility
            if visibility == GROUP_PRIVATE and not group["invite_code"]:
                group["invite_code"] = generate_invite_code()

    # -- Yerel (kendi tarafımızda) eylemler -----------------------------

    def _on_group_create(self, group_id, group_name, visibility):
        """Yeni grup oluşturur (oluşturan kişi admin olur)."""
        group = self._ensure_group(
            group_id, group_name, admin_id=self.user_id, visibility=visibility
        )
        group["admin_id"] = self.user_id
        group["members"][self.user_id] = self.user_name

        # Ağa bildir
        self.network.send_group_action(
            "join", group_id, visibility=visibility, code=group["invite_code"]
        )

        self._refresh_group_list()
        self._on_contact_select(group_id)

    def _on_group_join(self, group_id, code=""):
        """Gruba katılır (public ise direkt, private ise kod ile istek)."""
        group = self.groups.get(group_id)
        if not group:
            return

        if group["visibility"] == GROUP_PRIVATE:
            # Gizli grup: kod doğrulanırsa istek gönderilir
            if code and group["invite_code"] and code.upper() != group["invite_code"]:
                from tkinter import messagebox
                messagebox.showerror(
                    "Hatalı Kod",
                    "Davet kodu yanlış. Gruba katılmak için doğru kodu girin.",
                )
                return

            self.network.send_group_action(
                "invite_request", group_id, code=code.upper()
            )
            from tkinter import messagebox
            messagebox.showinfo(
                "İstek Gönderildi",
                "Grup yöneticisine katılma isteğiniz gönderildi.\n"
                "Onaylandığında gruba katılacaksınız.",
            )
            return

        # Public grup: direkt katıl
        group["members"][self.user_id] = self.user_name
        self.network.send_group_action("join", group_id)
        self._refresh_group_list()
        self._on_contact_select(group_id)

    def _on_group_leave(self, group_id):
        """Gruptan ayrılır."""
        group = self.groups.get(group_id)
        if not group:
            return

        self.network.send_group_action("leave", group_id)

        group["members"].pop(self.user_id, None)
        if not group["members"] and group["admin_id"] == self.user_id:
            # Admin ve üye kalmadı -> grup silinir
            del self.groups[group_id]
        elif group["admin_id"] == self.user_id:
            # Admin ayrıldı ama üye var -> yeni admin seçilir
            if group["members"]:
                new_admin = next(iter(group["members"]))
                group["admin_id"] = new_admin
                self.network.send_group_action(
                    "join", group_id, target_id=new_admin
                )

        self._refresh_group_list()

    def _on_group_manage(self, group_id):
        """Grup yönetim penceresini açar (admin işlemleri)."""
        group = self.groups.get(group_id)
        if not group:
            return
        if self.sidebar:
            self.sidebar.open_group_manager(group_id, group, self._is_admin(group_id))

    def _on_invite_accept(self, group_id, user_id):
        """Davet isteğini kabul eder."""
        group = self.groups.get(group_id)
        if not group:
            return
        user_name = group["pending"].pop(user_id, user_id)
        group["members"][user_id] = user_name
        self.network.send_group_action(
            "invite_accept", group_id, target_id=user_id
        )
        self._refresh_group_list()

    def _on_invite_reject(self, group_id, user_id):
        """Davet isteğini reddeder."""
        group = self.groups.get(group_id)
        if not group:
            return
        group["pending"].pop(user_id, None)
        self.network.send_group_action(
            "invite_reject", group_id, target_id=user_id
        )
        self._refresh_group_list()

    def _remove_member(self, group_id, target_id):
        """Üyeyi gruptan çıkarır (sadece admin)."""
        if not self._is_admin(group_id):
            return
        group = self.groups.get(group_id)
        if not group:
            return
        group["members"].pop(target_id, None)
        self.network.send_group_action(
            "remove_member", group_id, target_id=target_id
        )
        self._refresh_group_list()
        if self.sidebar:
            self.sidebar.refresh_group_manager(group_id, group)

    def _delete_group(self, group_id):
        """Grubu siler (sadece admin)."""
        if not self._is_admin(group_id):
            return
        group = self.groups.get(group_id)
        if not group:
            return
        self.network.send_group_action("delete_group", group_id)
        del self.groups[group_id]
        self._refresh_group_list()

    def _set_visibility(self, group_id, visibility):
        """Grubun görünürlüğünü değiştirir (sadece admin)."""
        if not self._is_admin(group_id):
            return
        group = self.groups.get(group_id)
        if not group:
            return
        group["visibility"] = visibility
        if visibility == GROUP_PRIVATE and not group["invite_code"]:
            group["invite_code"] = generate_invite_code()
        self.network.send_group_action(
            "set_visibility", group_id, visibility=visibility
        )
        self._refresh_group_list()
        if self.sidebar:
            self.sidebar.refresh_group_manager(group_id, group)

    def _refresh_group_list(self):
        """Grup listesini günceller."""
        if not self.sidebar:
            return
        for group_id in list(self.sidebar.group_frames.keys()):
            if group_id not in self.groups:
                self.sidebar.remove_group(group_id)

        online_count = sum(1 for d in self.devices.values() if d["online"])

        for group_id, group in self.groups.items():
            if group_id == GROUP_ALL:
                count = online_count
            else:
                count = len(group["members"])

            self.sidebar.add_group(
                group_id,
                group["name"],
                count,
                visibility=group["visibility"],
                is_admin=(group["admin_id"] == self.user_id),
                pending=len(group["pending"]),
                invite_code=group.get("invite_code", ""),
                admin_id=group.get("admin_id", ""),
                can_leave=(group_id != GROUP_ALL),
            )

    # =====================================================================
    # El kaldırma
    # =====================================================================

    def _handle_hand_raise(self, pkt):
        """El kaldırma bildirimini işler."""
        msg_id = pkt.get("msg_id", "")
        action = pkt.get("action", "raise")
        user_id = pkt.get("user_id", "")
        user_name = pkt.get("user_name", user_id)

        if not msg_id or not user_id:
            return

        hands = self.hands.setdefault(msg_id, {})
        if action == "raise":
            hands[user_id] = user_name
        else:
            hands.pop(user_id, None)

        if self.chat_area:
            self.chat_area.update_hands(msg_id, hands)

    def _on_hand_raise(self, msg_id, raise_hand):
        """El kaldırır veya elini indirir."""
        hands = self.hands.setdefault(msg_id, {})
        if raise_hand:
            hands[self.user_id] = self.user_name
            self.network.send_hand_raise(msg_id, "raise")
        else:
            hands.pop(self.user_id, None)
            self.network.send_hand_raise(msg_id, "lower")

        if self.chat_area:
            self.chat_area.update_hands(msg_id, hands)

    # =====================================================================
    # Canlı anket
    # =====================================================================

    def _handle_poll(self, pkt):
        """Anket bildirimini işler."""
        action = pkt.get("action", "")
        poll_id = pkt.get("poll_id", "")
        target = pkt.get("target_id", "")

        if action == "create":
            # Zaten biliyorsak tekrar oluşturma (kendi broadcast'imiz geri geldi)
            if poll_id not in self.polls:
                poll = {
                    "question": pkt.get("question", ""),
                    "options": pkt.get("options", []),
                    "votes": {},
                    "open": True,
                    "creator": pkt.get("user_id", ""),
                    "target": target,
                }
                self.polls[poll_id] = poll
            else:
                poll = self.polls[poll_id]

        elif action == "vote":
            poll = self.polls.get(poll_id)
            if not poll:
                return
            poll["votes"][pkt.get("user_id", "")] = pkt.get("option_index", -1)

        elif action == "close":
            poll = self.polls.get(poll_id)
            if poll:
                poll["open"] = False

        if self.chat_area:
            if self._poll_shows_in_current_chat(target):
                self.chat_area.show_poll(poll_id, self.polls.get(poll_id))
            else:
                self.chat_area.refresh_poll(poll_id, self.polls.get(poll_id))

    def _poll_shows_in_current_chat(self, target):
        """Anketin açık sohbette gösterilip gösterilmeyeceğini kontrol eder."""
        if not self.chat_area:
            return False
        current = self.chat_area.current_chat_id
        if not current:
            return False
        if target == current:
            return True
        if target == GROUP_ALL:
            return True
        if target.startswith(GROUP_PREFIX) and target in self.groups:
            return True
        return False

    def _on_poll_create(self, target_id, question, options):
        """Yeni anket açar."""
        import uuid

        poll_id = uuid.uuid4().hex[:8]
        poll = {
            "question": question,
            "options": options,
            "votes": {},
            "open": True,
            "creator": self.user_id,
            "target": target_id,
        }
        self.polls[poll_id] = poll

        # Ağa gönder
        self.network.send_poll(
            "create", poll_id, question, options, target_id=target_id
        )

        if self.chat_area:
            self.chat_area.show_poll(poll_id, poll)

    def _on_poll_vote(self, poll_id, option_index):
        """Ankete oy verir."""
        poll = self.polls.get(poll_id)
        if not poll or not poll["open"]:
            return
        poll["votes"][self.user_id] = option_index
        self.network.send_poll("vote", poll_id, option_index=option_index)

        if self.chat_area:
            self.chat_area.refresh_poll(poll_id, poll)

    def _on_poll_close(self, poll_id):
        """Anketi kapatır (sadece anketi açan kişi)."""
        poll = self.polls.get(poll_id)
        if not poll or poll["creator"] != self.user_id:
            return
        poll["open"] = False
        self.network.send_poll("close", poll_id)

        if self.chat_area:
            self.chat_area.refresh_poll(poll_id, poll)

    # =====================================================================
    # Mesaj işlemleri
    # =====================================================================

    def _update_online_count(self):
        """Üst çubuktaki çevrimiçi sayacını günceller."""
        if not hasattr(self, "online_label"):
            return
        count = sum(1 for d in self.devices.values() if d["online"])
        self.online_label.config(text=f"Çevrimiçi: {count}")
        if self.sidebar:
            self._refresh_group_list()

    def _schedule_offline_check(self):
        """Periyodik olarak sessiz kalan cihazları çevrimdışı yapar."""
        now = time.time()
        for device_id, device in self.devices.items():
            if device["online"] and (now - device["last_seen"]) > OFFLINE_TIMEOUT:
                device["online"] = False
                if self.sidebar:
                    self.sidebar.set_status(device_id, False)
        self._update_online_count()
        self.root.after(2000, self._schedule_offline_check)

    def _on_contact_select(self, contact_id):
        """Kontak seçildiğinde sohbeti açar."""
        display_name = contact_id
        device_info = ""

        if contact_id in self.groups:
            group = self.groups[contact_id]
            icon = "👥"
            if group["visibility"] == GROUP_PRIVATE:
                icon = "🔒"
            display_name = f"{icon} {group['name']}"
            if group["admin_id"] == self.user_id:
                display_name += "  (yönetici)"
            device_info = f"{len(group['members'])} üye"
        else:
            device = self.devices.get(contact_id)
            if device:
                display_name = device["name"]
                device_info = f"{device['ip']}  •  {device['mac']}"

        self.chat_area.open_chat(contact_id, display_name, device_info)

        # Kayıtlı mesajları yükle
        for is_outgoing, pkt in self.chats.get(contact_id, []):
            self.chat_area.add_message(
                pkt["content"],
                is_outgoing=is_outgoing,
                timestamp=pkt["timestamp"],
                sender_name=pkt["sender_name"],
                msg_id=pkt.get("msg_id", ""),
                is_edited=pkt.get("edited", False),
            )

        # Bu sohbete ait anketleri göster
        for poll_id, poll in self.polls.items():
            if poll.get("target") == contact_id:
                self.chat_area.show_poll(poll_id, poll)

    def _on_send_message(self, target_id, content):
        """Mesaj gönderildiğinde."""
        msg_id = self.network.send_message(target_id, content)

        pkt = create_message(
            self.user_id, self.user_name, target_id, content, msg_id=msg_id
        )
        self.chats.setdefault(target_id, []).append((True, pkt))

        self.chat_area.add_message(
            content, is_outgoing=True, timestamp=pkt["timestamp"], msg_id=msg_id
        )

        if target_id.startswith(GROUP_PREFIX):
            if self.sidebar:
                self.sidebar.update_group_preview(target_id, content)
        elif self.sidebar:
            self.sidebar.update_last_message(target_id, content)

    def _on_delete_message(self, msg_id):
        """Mesaj silme işlemi."""
        from tkinter import messagebox

        if not messagebox.askyesno("Mesajı Sil", "Bu mesajı silmek istiyor musun?"):
            return

        for chat_id, messages in self.chats.items():
            self.chats[chat_id] = [
                (is_outgoing, m) for is_outgoing, m in messages
                if m.get("msg_id") != msg_id
            ]

        if self.chat_area:
            self.chat_area.remove_message(msg_id)
            self.chat_area.update_hands(msg_id, {})

        if self.chat_area and self.chat_area.current_chat_id:
            self.network.send_delete_notice(msg_id, self.chat_area.current_chat_id)

    def _on_edit_message(self, msg_id, new_content):
        """Mesaj düzenleme işlemi."""
        target_id = self.chat_area.current_chat_id
        if not target_id:
            return

        for messages in self.chats.values():
            for is_outgoing, m in messages:
                if m.get("msg_id") == msg_id:
                    m["content"] = new_content
                    m["edited"] = True

        if self.chat_area:
            self.chat_area.update_message(msg_id, new_content)

        self.network.send_edit_notice(msg_id, new_content, target_id)

    def _on_copy_message(self, text):
        """Mesajı panoya kopyalar."""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

    # =====================================================================
    # Kapanış
    # =====================================================================

    def _on_close(self):
        """Pencere kapatıldığında."""
        if HISTORY_SAVE_ON_CLOSE:
            if storage.save_history(self.chats):
                print("Geçmiş kaydedildi.")

        if self.network:
            self.network.stop()
        self.root.destroy()
