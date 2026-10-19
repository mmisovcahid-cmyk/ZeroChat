"""
ZeroChat - Yapılandırma Dosyası
Tüm sabitler burada tanımlanır.
"""

# Ağ Ayarları
UDP_PORT = 5000
BUFFER_SIZE = 4096

# Broadcast Hedefi
#   None  -> Aktif arayüzün subnet broadcast adresi (önerilen)
#            Örnek: IP 192.168.100.17 / Maske 255.255.255.0 -> 192.168.100.255
#            Bu adres paketin DOGRU arayüzden (Wi-Fi/Ethernet) çıkmasını garanti eder.
#
#   "255.255.255.255" -> Sınırlı broadcast (tüm arayüzlere birden gider)
#            Çok sayıda sanal adaptör (VirtualBox/Hyper-V) varsa karışabilir.
BROADCAST_ADDRESS = None

# Subnet broadcast'un yanında sınırlı broadcast'a da gönderilsin mi?
# İki hedef açıkken aynı mesaj iki kez gelebilir; mesajlar yinelenmez (dedupe).
SEND_TO_LIMITED_BROADCAST = False

# Otomatik Cihaz Keşfi (Heartbeat)
HEARTBEAT_INTERVAL = 3      # Kaç saniyede bir tarama yapılsın
OFFLINE_TIMEOUT = 12        # Kaç saniye sessizlik sonrası "Çevrimdışı" sayılsın

# Grup Sohbeti
GROUP_ALL = "ALL"           # Tüm ağa gönderilen grup mesajları
GROUP_PREFIX = "GRP:"       # Özel grup kimliği öneki (örn. "GRP:sinifA")
GROUP_PUBLIC = "public"     # Herkes katılabilir
GROUP_PRIVATE = "private"   # Sadece davet kodu ile (admin onaylı)
INVITE_CODE_LENGTH = 6      # Davet kodu uzunluğu

# Canlı Anket
POLL_MIN_OPTIONS = 2
POLL_MAX_OPTIONS = 6

# Mesaj Geçmişi (dosya)
HISTORY_FILE = "history.json"
HISTORY_SAVE_ON_CLOSE = True

# Renk Teması (WhatsApp Sade)
COLORS = {
    "background": "#F0F2F5",
    "sidebar": "#FFFFFF",
    "chat_area": "#EFEAE2",
    "outgoing_bubble": "#DCF8C6",
    "incoming_bubble": "#FFFFFF",
    "accent": "#25D366",
    "text": "#111B21",
    "text_secondary": "#667781",
    "hover": "#F5F6F6",
    "border": "#E9EDEF",
    "online": "#25D366",
    "offline": "#8696A0",
}

# Pencere Boyutları
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
SIDEBAR_WIDTH = 320
