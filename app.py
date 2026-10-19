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
)
from gui.sidebar import Sidebar
from gui.chat_area import ChatArea
from network.socket import NetworkManager
from network.packet import create_message


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
        # device_id -> [mesaj paketleri]
        self.chats = {}

        self.network = None
        self.sidebar = None
        self.chat_area = None

    def start(self, user_id, user_name):
        """Uygulamayı başlatır."""
        self.user_id = user_id
        self.user_name = user_name

        # Ağ manager'ı başlat
        self.network = NetworkManager(user_id, user_name, self._on_packet)
        self.network.start()
        self.my_ip = self.network.ip
        # user_id zaten MAC adresidir; ağda bu kimlikle tanınıyoruz
        self.my_mac = user_id
        self.broadcast_address = self.network.broadcast_address

        # GUI bileşenlerini oluştur
        self._build_gui()

        # Pencere kapatma olayı
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Çevrimdışı kontrol döngüsü
        self._schedule_offline_check()

        # Ana döngü
        self.root.mainloop()

    def _build_gui(self):
        """GUI bileşenlerini oluşturur."""
        # Üst bilgi çubuğu
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
        self.sidebar = Sidebar(self.root, self._on_contact_select, self.devices)
        self.sidebar.pack(side="left", fill="y")

        # Sağ panel
        self.chat_area = ChatArea(self.root, self._on_send_message)
        self.chat_area.pack(side="right", fill="both", expand=True)

    def _on_packet(self, pkt):
        """Ağ thread'inden gelen paket.

        Tkinter yalnızca ana thread'de güvenlidir, bu yüzden
        iş GUI'ye ana döngüye devredilir.
        """
        self.root.after(0, self._process_packet, pkt)

    def _process_packet(self, pkt):
        """Paketi ana thread'de işler."""
        pkt_type = pkt.get("type")
        if pkt_type == "message":
            self._handle_message(pkt)
        elif pkt_type == "presence":
            self._handle_presence(pkt)

    def _handle_message(self, pkt):
        """Gelen mesajı işler."""
        sender_id = pkt["sender_id"]
        target_id = pkt["target_id"]

        # Sadece bana gönderilmiş mesajları işle
        if target_id != self.user_id:
            return

        # Kendi yayınlarımı atla
        if sender_id == self.user_id:
            return

        # Sohbet geçmişine ekle
        self.chats.setdefault(sender_id, []).append(pkt)

        # Sidebar'ı güncelle
        if self.sidebar:
            self.sidebar.update_last_message(sender_id, pkt["content"])

        # Bu sohbet açıksa ekrana yaz
        if self.chat_area and self.chat_area.current_chat_id == sender_id:
            self.chat_area.add_message(
                pkt["content"],
                is_outgoing=False,
                timestamp=pkt["timestamp"],
                sender_name=pkt["sender_name"],
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
            # Cihaz açıkça çıktığını bildirdi
            if device_id in self.devices:
                self.devices[device_id]["online"] = False
                self.devices[device_id]["last_seen"] = time.time()
                if self.sidebar:
                    self.sidebar.set_status(device_id, False)
                self._update_online_count()
            return

        # Yeni cihaz mı, yoksa güncelleme mi?
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

    def _update_online_count(self):
        """Üst çubuktaki çevrimiçi sayacını günceller."""
        if not hasattr(self, "online_label"):
            return
        count = sum(1 for d in self.devices.values() if d["online"])
        self.online_label.config(text=f"Çevrimiçi: {count}")

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
        device = self.devices.get(contact_id)
        display_name = device["name"] if device else contact_id
        device_info = ""
        if device:
            device_info = f"{device['ip']}  •  {device['mac']}"

        self.chat_area.open_chat(contact_id, display_name, device_info)

        # Kayıtlı mesajları yükle
        for pkt in self.chats.get(contact_id, []):
            self.chat_area.add_message(
                pkt["content"],
                is_outgoing=False,
                timestamp=pkt["timestamp"],
                sender_name=pkt["sender_name"],
            )

    def _on_send_message(self, target_id, content):
        """Mesaj gönderildiğinde."""
        # Ağa gönder
        self.network.send_message(target_id, content)

        # Kendi ekranında göster
        pkt = create_message(self.user_id, self.user_name, target_id, content)
        self.chats.setdefault(target_id, []).append(pkt)

        self.chat_area.add_message(
            content,
            is_outgoing=True,
            timestamp=pkt["timestamp"],
        )

        if self.sidebar:
            self.sidebar.update_last_message(target_id, content)

    def _on_close(self):
        """Pencere kapatıldığında."""
        if self.network:
            self.network.stop()
        self.root.destroy()
