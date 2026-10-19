"""
ZeroChat - Paket Oluşturma ve Çözümleme
Mesajları JSON formatında paketler.
"""

import json
from datetime import datetime


def create_message(sender_id, sender_name, target_id, content):
    """Mesaj paketi oluşturur.

    sender_id / target_id: MAC adresi (cihaz kimliği)
    """
    return {
        "type": "message",
        "sender_id": sender_id,
        "sender_name": sender_name,
        "target_id": target_id,
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M"),
    }


def create_presence(user_id, user_name, status="online", ip="", mac=""):
    """Kimlik/keşif paketi oluşturur.

    Bu paket 3 saniyede bir gönderilir. Karşı taraf bunu alarak
    ağdaki cihazları otomatik olarak listeler.
    """
    return {
        "type": "presence",
        "user_id": user_id,      # MAC adresi (benzersiz cihaz kimliği)
        "user_name": user_name,  # kullanıcının seçtiği görünen isim
        "ip": ip,                # cihazın IP adresi
        "mac": mac,              # cihazın MAC adresi
        "status": status,        # online / offline
        "timestamp": datetime.now().strftime("%H:%M"),
    }


def encode(packet):
    """Paketi JSON string'e çevirip byte'lara encode eder."""
    return json.dumps(packet, ensure_ascii=False).encode("utf-8")


def decode(data):
    """Byte'ları JSON string'e çevirip paket olarak döndürür."""
    try:
        return json.loads(data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
