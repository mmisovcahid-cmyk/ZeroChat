"""
ZeroChat - UDP Socket Yönetimi
Gönderme, dinleme ve otomatik cihaz keşfi (heartbeat) işlemlerini yapar.
"""

import socket
import subprocess
import threading
import uuid

from config import (
    UDP_PORT,
    BROADCAST_ADDRESS,
    BUFFER_SIZE,
    HEARTBEAT_INTERVAL,
)
from network import packet


def get_local_ip():
    """Cihazın yerel IP adresini bulur.

    Broadcast adresine bağlanarak işletim sisteminin
    hangi arayüzü kullanacağını öğrenir. Gerçek veri gönderilmez.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.settimeout(0.5)
        sock.connect((BROADCAST_ADDRESS, UDP_PORT))
        return sock.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"
    finally:
        sock.close()


def get_mac_address():
    """Cihazın MAC adresini bulur.

    Önce uuid.getnode() (donanımdan okur), başarısız olursa
    Windows'ta ipconfig çıktısından IP'ye eşleşen MAC'i arar.
    """
    node = uuid.getnode()

    # uuid bazen gerçek olmayan bir multicast MAC döndürebilir.
    # Bunu kontrol edip alternatif yönteme düşüyoruz.
    if (node >> 40) & 0x01:
        mac = _mac_from_ipconfig()
        if mac:
            return mac

    return format_mac(node)


def format_mac(node):
    """48 bitlik sayıyı AA:BB:CC:DD:EE:FF formatına çevirir."""
    return ":".join(f"{(node >> shift) & 0xFF:02X}" for shift in range(40, -8, -8))


def _mac_from_ipconfig():
    """Windows ipconfig çıktısından ilk fiziksel adresi alır."""
    try:
        result = subprocess.run(
            ["ipconfig", "/all"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    for line in result.stdout.splitlines():
        if "Physical Address" in line or "Fiziksel Adres" in line:
            if ":" in line:
                value = line.split(":")[-1].strip()
                if value and value.count(":") == 5:
                    return value.upper()
    return None


class NetworkManager:
    """UDP socket ile ağ iletişimini yönetir.

    Her cihaz hem gönderen hem alıcıdır (sunucusuz mimari).
    """

    def __init__(self, user_id, user_name, on_message_callback):
        self.user_id = user_id
        self.user_name = user_name
        self.on_message = on_message_callback
        self.sock = None
        self.running = False
        self.listener_thread = None
        self.heartbeat_thread = None

        # Cihaz kimliği: MAC adresi
        self.mac = get_mac_address()
        self.ip = get_local_ip()

    def start(self):
        """Socket oluşturur, dinlemeye ve taramaya başlar."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", UDP_PORT))
        self.sock.settimeout(0.5)

        self.running = True

        # Dinleme thread'i (gelen paketleri işler)
        self.listener_thread = threading.Thread(target=self._listen, daemon=True)
        self.listener_thread.start()

        # Tarama thread'i (her 3 saniyede bir kimlik paketi gönderir)
        self.heartbeat_thread = threading.Thread(target=self._heartbeat, daemon=True)
        self.heartbeat_thread.start()

    def stop(self):
        """Durdurur ve çıkış bildirimi gönderir."""
        self.running = False
        if self.sock:
            self.send_presence("offline")
            self.sock.close()

    def send_message(self, target_id, content):
        """Belirli bir cihaza (MAC ID) mesaj gönderir."""
        pkt = packet.create_message(
            self.user_id, self.user_name, target_id, content
        )
        self._send(pkt)

    def send_presence(self, status):
        """Kimlik/keşif paketi gönderir (IP ve MAC dahil)."""
        pkt = packet.create_presence(
            self.user_id, self.user_name, status, self.ip, self.mac
        )
        self._send(pkt)

    def _send(self, pkt):
        """Paketi broadcast olarak gönderir."""
        try:
            data = packet.encode(pkt)
            self.sock.sendto(data, (BROADCAST_ADDRESS, UDP_PORT))
        except Exception as e:
            print(f"Gönderme hatası: {e}")

    def _heartbeat(self):
        """Her HEARTBEAT_INTERVAL saniyede bir tarama yapar.

        Bu sayede ağa bağlı tüm cihazlar birbirini otomatik bulur.
        """
        while self.running:
            self.send_presence("online")
            # 0.5 saniyelik bekleme yerine kısa aralıklarla kontrol
            for _ in range(int(HEARTBEAT_INTERVAL / 0.5)):
                if not self.running:
                    return
                threading.Event().wait(0.5)

    def _listen(self):
        """Sürekli dinleme döngüsü."""
        while self.running:
            try:
                data, addr = self.sock.recvfrom(BUFFER_SIZE)
                pkt = packet.decode(data)
                if pkt:
                    self.on_message(pkt)
            except socket.timeout:
                continue
            except OSError:
                break
