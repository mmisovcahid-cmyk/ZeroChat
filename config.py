"""
ZeroChat - Yapılandırma Dosyası
Tüm sabitler burada tanımlanır.
"""

import json
import os

# ---------------------------------------------------------------------------
# Proje Kökü
# ---------------------------------------------------------------------------
# Dosya yolları (history.json, sessions/ vb.) uygulamanın çalıştığı dizine
# değil, bu dosyanın bulunduğu klasöre göre çözülür. Böylece uygulama
# hangi dizinden başlatılırsa başlatılsın veriler aynı yerde durur.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Kullanıcı tercihleri (tema, seçili arayüz vb.)
SETTINGS_FILE = "settings.json"


def resolve_path(path):
    """Göreli bir yolu proje köküne göre mutlak yola çevirir."""
    if not path:
        return path
    if os.path.isabs(path):
        return path
    return os.path.join(BASE_DIR, path)


def load_settings():
    """Kayıtlı kullanıcı tercihlerini okur (yoksa boş sözlük)."""
    path = resolve_path(SETTINGS_FILE)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_settings(data):
    """Kullanıcı tercihlerini diske yazar."""
    path = resolve_path(SETTINGS_FILE)
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
        return True
    except (OSError, TypeError, ValueError):
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
        return False


# ---------------------------------------------------------------------------
# Tema
# ---------------------------------------------------------------------------
# "light" veya "dark". Açılış ekranından seçilir.
THEME = "light"

# Aydınlık tema
COLORS_LIGHT = {
    "background": "#F0F2F5",
    "sidebar": "#FFFFFF",
    "chat_area": "#EFEAE2",
    "outgoing_bubble": "#DCF8C6",
    "incoming_bubble": "#FFFFFF",
    "accent": "#25D366",
    "accent_dark": "#1EB855",
    "text": "#111B21",
    "text_secondary": "#667781",
    "hover": "#F5F6F6",
    "border": "#E9EDEF",
    "online": "#25D366",
    "offline": "#8696A0",
    "input_bg": "#F0F2F5",
    "card_bg": "#FFFFFF",
    "scrollbar": "#CFD8DC",
    "danger": "#DC3545",
    "warning": "#F0AD4E",
}

# Karanlık tema
COLORS_DARK = {
    "background": "#111B21",
    "sidebar": "#202C33",
    "chat_area": "#0B141A",
    "outgoing_bubble": "#005C4B",
    "incoming_bubble": "#202C33",
    "accent": "#00A884",
    "accent_dark": "#008069",
    "text": "#E9EDEF",
    "text_secondary": "#8696A0",
    "hover": "#2A3942",
    "border": "#222D34",
    "online": "#00A884",
    "offline": "#667781",
    "input_bg": "#2A3942",
    "card_bg": "#202C33",
    "scrollbar": "#374248",
    "danger": "#F15C6D",
    "warning": "#E8A33D",
}

# Aktif tema renkleri (theme.py tarafından güncellenir)
COLORS = dict(COLORS_LIGHT)

# ---------------------------------------------------------------------------
# Ağ Ayarları
# ---------------------------------------------------------------------------
UDP_PORT = 5000

# UDP datagramının alınabileceği en büyük boyut (65535 = IPv4 max payload).
# Daha küçük bir değer, uzun mesajların sessizce kesilmesine ve Windows'ta
# WSAEMSGSIZE hatasıyla dinleme thread'inin ölmesine yol açıyordu.
BUFFER_SIZE = 65535

# Tek bir mesajın en fazla kaç karakter olabileceği (gönderim öncesi kontrol).
MAX_MESSAGE_CHARS = 4000

# Broadcast Hedefi
#   None  -> Aktif arayüzün subnet broadcast adresi (önerilen)
#            Örnek: IP 192.168.100.17 / Maske 255.255.255.0 -> 192.168.100.255
#            Bu adres paketin DOGRU arayüzden (Wi-Fi/Ethernet) çıkmasını garanti eder.
#
#   "255.255.255.255" -> Sınırlı broadcast (tüm arayüzlere birden gider)
#            Çok sayıda sanal adaptör (VirtualBox/Hyper-V) varsa karışabilir.
BROADCAST_ADDRESS = None

# Subnet broadcast'un yanında sınırlı broadcast'a da gönderilsin mi?
SEND_TO_LIMITED_BROADCAST = False

# Otomatik Cihaz Keşfi (Heartbeat)
HEARTBEAT_INTERVAL = 3      # Kaç saniyede bir tarama yapılsın
OFFLINE_TIMEOUT = 12        # Kaç saniye sessizlik sonrası "Çevrimdışı" sayılsın
OFFLINE_CLEANUP_TIMEOUT = 600   # bu süre çevrimdışı kalan cihaz listeden silinir

# ---------------------------------------------------------------------------
# Grup Sohbeti
# ---------------------------------------------------------------------------
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
MAX_HISTORY_MESSAGES = 500       # sohbet başına saklanacak azami mesaj sayısı
HISTORY_AUTOSAVE_INTERVAL = 300  # otomatik kayıt aralığı (saniye)

# Gizli Mod (Stealth)
#   True  -> gizli cihazlar listede tamamen görünmez (sadece sayaç)
#   False -> gizli cihazlar listede "gölge" rozetiyle görünür (eğitim için)
STEALTH_HIDE_COMPLETELY = False

# Gizli moda girerken "hidden" duyurusu gönderilsin mi?
#   False -> hiçbir presence paketi gönderilmez, cihaz ağda yokmuş gibi davranır
#            (gerçek gizlilik; README'de anlatılan davranış)
#   True  -> bir kez "hidden" durumu bildirilir, karşı taraf listede 👻 rozeti
#            ile gösterir (eğitim amaçlı, ama cihazı yine de ele verir)
STEALTH_ANNOUNCE = False

# Oturum Kaydı (Wireshark alternatifi)
SESSION_LOG_ENABLED = True
SESSION_LOG_DIR = "sessions"
MAX_SESSION_FILES = 30           # tutulacak azami oturum dosyası sayısı

# Zamanlı Mesaj
SCHEDULE_CHECK_INTERVAL = 1      # saniye (kuyruk kontrol aralığı)
SCHEDULE_MAX_MINUTES = 60 * 24 * 7   # en fazla 1 hafta sonrasına

# Pairing Kodu (sunurusuz eşleştirme)
PAIR_CODE_LENGTH = 6
PAIR_CODE_TIMEOUT = 300          # kodun geçerlilik süresi (saniye)

# ---------------------------------------------------------------------------
# Pencere Boyutları
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
SIDEBAR_WIDTH = 320
