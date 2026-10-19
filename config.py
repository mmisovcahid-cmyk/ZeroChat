"""
ZeroChat - Yapılandırma Dosyası
Tüm sabitler burada tanımlanır.
"""

# Ağ Ayarları
UDP_PORT = 5000
BROADCAST_ADDRESS = "255.255.255.255"
BUFFER_SIZE = 4096

# Otomatik Cihaz Keşfi (Heartbeat)
HEARTBEAT_INTERVAL = 3      # Kaç saniyede bir tarama yapılsın
OFFLINE_TIMEOUT = 12        # Kaç saniye sessizlik sonrası "Çevrimdışı" sayılsın

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
