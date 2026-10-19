"""
ZeroChat - UDP Socket Yönetimi

Gönderme, dinleme ve otomatik cihaz keşfi (heartbeat) işlemlerini yapar.

ÖNEMLİ - Arayüz Seçimi:
Bir bilgisayarda birden fazla ağ arayüzü olabilir (Wi-Fi, Ethernet, VirtualBox,
Hyper-V, WSL...). "connect() ile öğren" yöntemi bazen SANAL bir arayüz seçer
(örneğin VirtualBox 192.168.56.x) ve broadcast paketleri yanlış kabloya çıkar.
Bu yüzden gerçek ağ arayüzü "ipconfig" çıktısından, DEFAULT GATEWAY'e sahip
olan adaptör seçilerek bulunur.
"""

import ipaddress
import re
import socket
import subprocess
import threading
import uuid

from config import (
    UDP_PORT,
    BUFFER_SIZE,
    HEARTBEAT_INTERVAL,
    BROADCAST_ADDRESS,
    SEND_TO_LIMITED_BROADCAST,
    FILE_MAX_SIZE,
    FILE_CHUNK_SIZE,
)
from network import packet
from session_log import SessionLogger

LIMITED_BROADCAST = "255.255.255.255"


# ---------------------------------------------------------------------------
# Arayüz Tespiti
# ---------------------------------------------------------------------------

def get_active_interfaces():
    """Aktif ağ arayüzlerini liste olarak döndürür.

    Her arayüz için sözlük:
        {name, ip, mask, gateway, mac, virtual}
    Windows'ta ipconfig, Linux/Mac'te ip komutu kullanılır.
    """
    if _is_windows():
        return _windows_interfaces()
    return _unix_interfaces()


def _is_windows():
    return hasattr(subprocess, "STARTUPINFO")


def _run_command(cmd):
    """Komutu çalıştırıp çıktısını döndürür. Hata durumunda None."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout


def _windows_interfaces():
    """Windows: ipconfig /all çıktısını ayrıştırır."""
    output = _run_command(["ipconfig", "/all"])
    if output is None:
        return []

    interfaces = []
    current = None

    for line in output.splitlines():
        stripped = line.strip()

        # Yeni adaptör başlığı: "Ethernet adapter Wi-Fi:" / "Wireless LAN adapter Wi-Fi:"
        if stripped.endswith(":") and re.search(
            r"(adapter|bağdaştırıcısı|bağdaştiricisi)", stripped, re.IGNORECASE
        ):
            current = {
                "name": stripped.rstrip(":"),
                "ip": None,
                "mask": None,
                "gateway": None,
                "mac": None,
                "virtual": False,
            }
            interfaces.append(current)
            continue

        if current is None:
            continue

        if "Physical Address" in line or "Fiziksel Adres" in line:
            current["mac"] = _extract_value(line)
        elif "IPv4 Address" in line or "IPv4 Adresi" in line:
            current["ip"] = _extract_value(line)
        elif "Subnet Mask" in line or "Alt Ağ Maskesi" in line:
            current["mask"] = _extract_value(line)
        elif "Default Gateway" in line or "Varsayılan Ağ Geçidi" in line:
            current["gateway"] = _extract_value(line)

    # Sanal adaptörleri işaretle
    for iface in interfaces:
        iface["virtual"] = _is_virtual_iface(iface)

    return interfaces


def _unix_interfaces():
    """Linux/Mac: 'ip -o addr' çıktısını ayrıştırır."""
    output = _run_command(["ip", "-o", "-4", "addr", "show"])
    if output is None:
        return []

    interfaces = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        name = parts[1]
        if "/" not in parts[3]:
            continue
        ip = parts[3].split("/")[0]
        mask = _mask_from_prefix(parts[3].split("/")[1])
        interfaces.append({
            "name": name,
            "ip": ip,
            "mask": mask,
            "gateway": None,
            "mac": _mac_from_sysfs(name),
            "virtual": _is_virtual_name(name),
        })
    return interfaces


def _extract_value(line):
    """ipconfig satırındaki değeri alır (sondaki iki nokta üstü).

    Windows bazen "(Preferred)" gibi ekler, bunlar temizlenir.
    """
    if ":" not in line:
        return None
    value = line.rsplit(":", 1)[-1].strip()
    # "(Preferred)" ve benzeri parantez içi ekleri temizle
    value = re.sub(r"\(.*?\)", "", value).strip()
    return value or None


def _mask_from_prefix(prefix):
    """CIDR önekini noktalı maskeye çevirir (örn. 24 -> 255.255.255.0)."""
    try:
        return str(ipaddress.IPv4Network(f"0.0.0.0/{prefix}").netmask)
    except ValueError:
        return "255.255.255.0"


def _mac_from_sysfs(interface_name):
    """Linux: /sys/class/net/<ad>/address dosyasından MAC okur."""
    try:
        with open(f"/sys/class/net/{interface_name}/address", "r") as f:
            return f.read().strip().upper()
    except OSError:
        return None


def _is_virtual_name(name):
    """Sanal (gerçek ağa taşımayan) adaptör adlarını tanır."""
    name = name.lower()
    virtual_markers = (
        "virtualbox", "vmware", "hyper-v", "vethernet", "docker", "wsl",
        "loopback", "pseudo", "teredo", "isatap", "tap-", "npcap",
        "bluetooth", "bluetooth device", "vpn", "zerotier", "tailscale",
        "vbox", "vnic",
    )
    return any(marker in name for marker in virtual_markers)


def _is_virtual_iface(iface):
    """Adaptörün sanal olup olmadığını belirler.

    İpucu kaynakları:
      1. Adında sanal adaptör anahtar kelimesi var mı?
      2. MAC ön eki sanal üreticiye mi ait?
         (0A-00-27 = VirtualBox, 00-0C-29/00-50-56 = VMware,
          00-15-5D = Hyper-V, 00-16-3E = Xen)
      3. IP adresi sanal ağ aralığında mı? (192.168.56.x = VirtualBox varsayılanı)
    """
    if _is_virtual_name(iface.get("name", "")):
        return True

    mac = (iface.get("mac") or "").replace(":", "").replace("-", "").upper()
    virtual_mac_prefixes = (
        "0A0027",   # VirtualBox
        "000C29",   # VMware
        "005056",   # VMware
        "00155D",   # Hyper-V
        "00163E",   # Xen
        "080027",   # VirtualBox (eski)
    )
    if mac.startswith(virtual_mac_prefixes):
        return True

    # VirtualBox varsayılan host-only ağı: 192.168.56.0/24
    ip = iface.get("ip") or ""
    if ip.startswith("192.168.56."):
        return True

    return False


def select_primary_interface(interfaces=None):
    """Birincil ağ arayüzünü seçer.

    Öncelik sırası:
        1. Gerçek (sanal olmayan) + gateway'i olan adaptör
        2. Gerçek adaptör (gateway yoksa - sadece switch'e bağlı durum)
        3. Herhangi bir gateway'i olan adaptör
        4. İlk uygun adaptör
    """
    if interfaces is None:
        interfaces = get_active_interfaces()

    usable = [
        i for i in interfaces
        if i.get("ip") and not i["ip"].startswith("127.")
    ]
    if not usable:
        return None

    # 1) Gerçek + gateway
    for iface in usable:
        if not iface["virtual"] and iface.get("gateway"):
            return iface

    # 2) Gerçek adaptör (gateway olmasa da - switch-only ortam)
    for iface in usable:
        if not iface["virtual"]:
            return iface

    # 3) Gateway'i olan herhangi biri
    for iface in usable:
        if iface.get("gateway"):
            return iface

    # 4) İlk uygun
    return usable[0]


def get_local_ip():
    """Birincil arayüzün IP adresini döndürür."""
    iface = select_primary_interface()
    if iface:
        return iface["ip"]
    return _ip_by_connect()


def get_local_mask():
    """Birincil arayüzün subnet maskesini döndürür."""
    iface = select_primary_interface()
    if iface and iface.get("mask"):
        return iface["mask"]
    return "255.255.255.0"


def get_subnet_broadcast(ip=None, mask=None):
    """Subnet'in broadcast adresini hesaplar.

    Örnek: IP 192.168.100.17, Maske 255.255.255.0 -> 192.168.100.255
    """
    if ip is None:
        ip = get_local_ip()
    if mask is None:
        mask = get_local_mask()

    try:
        network = ipaddress.ip_network(f"{ip}/{mask}", strict=False)
        return str(network.broadcast_address)
    except ValueError:
        return LIMITED_BROADCAST


def _ip_by_connect():
    """Yedek yöntem: broadcast'a bağlanarak IP öğrenir."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.settimeout(0.5)
        sock.connect((LIMITED_BROADCAST, UDP_PORT))
        return sock.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"
    finally:
        sock.close()


# ---------------------------------------------------------------------------
# MAC Adresi
# ---------------------------------------------------------------------------

def get_mac_address(ip=None):
    """Cihazın MAC adresini bulur.

    Öncelik: verilen IP'ye ait adaptörün MAC'i (ipconfig'ten).
    Bulunamazsa uuid.getnode() (donanımdan okur).
    """
    if ip:
        for iface in get_active_interfaces():
            if iface.get("ip") == ip and iface.get("mac"):
                return _normalize_mac(iface["mac"])

    node = uuid.getnode()
    # uuid bazen gerçek olmayan bir multicast MAC döndürebilir.
    if (node >> 40) & 0x01:
        mac = _any_mac_from_ipconfig()
        if mac:
            return mac

    return format_mac(node)


def _normalize_mac(mac):
    """MAC adresini AA:BB:CC:DD:EE:FF formatına çevirir."""
    cleaned = mac.strip().replace("-", ":").replace(" ", ":").upper()
    parts = [p for p in cleaned.split(":") if p]
    if len(parts) == 6:
        return ":".join(parts)
    return mac.strip().upper()


def format_mac(node):
    """48 bitlik sayıyı AA:BB:CC:DD:EE:FF formatına çevirir."""
    return ":".join(f"{(node >> shift) & 0xFF:02X}" for shift in range(40, -8, -8))


def _any_mac_from_ipconfig():
    """ipconfig çıktısından herhangi bir fiziksel adres alır."""
    output = _run_command(["ipconfig", "/all"])
    if output is None:
        return None

    for line in output.splitlines():
        if "Physical Address" in line or "Fiziksel Adres" in line:
            value = _extract_value(line)
            if value:
                return _normalize_mac(value)
    return None


# ---------------------------------------------------------------------------
# Ağ Yöneticisi
# ---------------------------------------------------------------------------

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

        # Gizli mod: presence paketi gönderilmez
        self.stealth = False

        # Oturum kaydı
        self.logger = SessionLogger()

        # Cihaz kimliği: MAC adresi
        self.interface = select_primary_interface()
        self.ip = self.interface["ip"] if self.interface else _ip_by_connect()
        self.mac = get_mac_address(self.ip)

        # Broadcast hedefleri
        if BROADCAST_ADDRESS:
            self.broadcast_address = BROADCAST_ADDRESS
        else:
            self.broadcast_address = get_subnet_broadcast(self.ip)
        self.limited_broadcast = LIMITED_BROADCAST

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
            if not self.stealth:
                self.send_presence("offline")
            self.sock.close()
        self.logger.close()

    def set_stealth(self, enabled):
        """Gizli modu açar/kapatır.

        Gizli moddayken presence paketi gönderilmez, böylece cihaz
        ağ taramasında görünmez. Mesaj gönderildiğinde karşı taraf
        cihazı tanır.
        """
        self.stealth = enabled
        if enabled:
            # Gizli moda geçerken çıkış bildirimi gönderme
            self.send_presence("hidden")
        else:
            self.send_presence("online")

    def send_message(self, target_id, content):
        """Belirli bir cihaza (MAC ID veya grup kimliği) mesaj gönderir."""
        pkt = packet.create_message(
            self.user_id, self.user_name, target_id, content
        )
        self._send(pkt)
        return pkt["msg_id"]

    def send_group_action(self, action, group, target_id="", visibility="",
                          code=""):
        """Grup işlemi bildirimi gönderir."""
        pkt = packet.create_group_action(
            action, group, self.user_id, self.user_name,
            target_id=target_id, visibility=visibility, code=code,
        )
        self._send(pkt)

    def send_hand_raise(self, msg_id, action):
        """El kaldırma bildirimi gönderir."""
        pkt = packet.create_hand_raise(msg_id, action, self.user_id, self.user_name)
        self._send(pkt)

    def send_poll(self, action, poll_id, question="", options=None,
                  option_index=-1, target_id=""):
        """Anket bildirimi gönderir."""
        pkt = packet.create_poll(
            action, poll_id, question, options,
            self.user_id, self.user_name, option_index, target_id,
        )
        self._send(pkt)

    def send_delete_notice(self, msg_id, target_id):
        """Mesaj silme bildirimi gönderir."""
        pkt = packet.create_delete_notice(msg_id, self.user_id, target_id)
        self._send(pkt)

    def send_edit_notice(self, msg_id, new_content, target_id):
        """Mesaj düzenleme bildirimi gönderir."""
        pkt = packet.create_edit_notice(msg_id, new_content, self.user_id, target_id)
        self._send(pkt)

    def send_file_nack(self, file_id, missing_indexes, target_id):
        """Eksik parçaların tekrar istenmesini gönderir."""
        pkt = packet.create_file_nack(file_id, missing_indexes, target_id)
        self._send(pkt)

    def send_presence(self, status):
        """Kimlik/keşif paketi gönderir (IP ve MAC dahil)."""
        pkt = packet.create_presence(
            self.user_id, self.user_name, status, self.ip, self.mac
        )
        self._send(pkt)

    def send_pair_request(self, code):
        """Eşleştirme isteği gönderir."""
        pkt = packet.create_pair_request(
            self.user_id, self.user_name, code
        )
        self._send(pkt)

    def send_pair_response(self, accept, target_id, code=""):
        """Eşleştirme isteğini kabul/reddeder."""
        pkt = packet.create_pair_response(
            accept, self.user_id, self.user_name, target_id, code
        )
        self._send(pkt)

    def send_file(self, target_id, filepath, progress_callback=None):
        """Dosyayı parçalara bölerek gönderir.

        Returns: (file_id, sha256) veya hata durumunda (None, None)
        """
        import base64
        import hashlib
        import os
        import uuid

        try:
            with open(filepath, "rb") as f:
                data = f.read()
        except OSError as e:
            print(f"Dosya okunamadi: {e}")
            return None, None

        if len(data) > FILE_MAX_SIZE:
            raise ValueError(
                f"Dosya cok buyuk ({len(data) / 1024 / 1024:.1f} MB). "
                f"En fazla {FILE_MAX_SIZE / 1024 / 1024:.0f} MB."
            )

        file_id = uuid.uuid4().hex[:8]
        file_name = os.path.basename(filepath)
        total_chunks = max(1, (len(data) + FILE_CHUNK_SIZE - 1) // FILE_CHUNK_SIZE)
        sha256 = hashlib.sha256(data).hexdigest()
        mime = _guess_mime(file_name)

        # Başlangıç paketi
        start = packet.create_file_start(
            file_id, file_name, len(data), mime, total_chunks,
            FILE_CHUNK_SIZE, target_id, sha256,
        )
        self._send(start)

        # Parçalar
        for index in range(total_chunks):
            chunk = data[index * FILE_CHUNK_SIZE:(index + 1) * FILE_CHUNK_SIZE]
            pkt = packet.create_file_chunk(
                file_id, index, total_chunks,
                base64.b64encode(chunk).decode("ascii"), target_id,
            )
            self._send(pkt)
            if progress_callback:
                progress_callback(index + 1, total_chunks)

        # Bitiş paketi
        end = packet.create_file_end(file_id, sha256, target_id)
        self._send(end)

        return file_id, sha256

    def _send(self, pkt):
        """Paketi broadcast olarak gönderir.

        Önce subnet broadcast adresine (doğru arayüz), isteğe bağlı olarak
        sınırlı broadcast'a da gönderilir.
        """
        data = packet.encode(pkt)
        targets = [self.broadcast_address]
        if SEND_TO_LIMITED_BROADCAST and self.limited_broadcast != self.broadcast_address:
            targets.append(self.limited_broadcast)

        for target in targets:
            try:
                self.sock.sendto(data, (target, UDP_PORT))
            except Exception as e:
                print(f"Gönderme hatası ({target}): {e}")

        # Oturum kaydı
        self.logger.log_out(pkt, len(data))

    def _heartbeat(self):
        """Her HEARTBEAT_INTERVAL saniyede bir tarama yapar.

        Gizli modda presence gönderilmez - cihaz ağda görünmez.
        """
        while self.running:
            if not self.stealth:
                self.send_presence("online")
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
                    self.logger.log_in(pkt, len(data))
                    self.on_message(pkt)
            except socket.timeout:
                continue
            except OSError:
                break


def _guess_mime(filename):
    """Dosya adından MIME türü tahmin eder."""
    import mimetypes
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"
