"""
ZeroChat - Paket Oluşturma ve Çözümleme
Mesajları JSON formatında paketler.
"""

import json
import random
import string
import uuid
from datetime import datetime


# ---------------------------------------------------------------------------
# Mesaj
# ---------------------------------------------------------------------------

def create_message(sender_id, sender_name, target_id, content, msg_id=None):
    """Mesaj paketi oluşturur.

    sender_id / target_id: MAC adresi veya grup kimliği
    msg_id: benzersiz mesaj numarası (silme/düzenleme için)
    """
    return {
        "type": "message",
        "msg_id": msg_id or uuid.uuid4().hex[:8],
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


# ---------------------------------------------------------------------------
# Grup işlemleri
# ---------------------------------------------------------------------------

def create_group_action(action, group, user_id, user_name="",
                        target_id="", visibility="", code="",
                        name="", target_name="", admin_id=""):
    """Grup işlemi paketi oluşturur.

    action: create, join, leave, invite_request, invite_accept, invite_reject,
            remove_member, delete_group, set_visibility, transfer_admin

    create       -> grubu ağa duyurur (ad, görünürlük ve admin bilgisi ile)
    join         -> gruba katılma bildirimi
    transfer_admin -> yönetici devri (target_id yeni yönetici)
    admin_id     -> grubun o anki yöneticisi (create duyurusunda)
    """
    return {
        "type": "group_action",
        "action": action,
        "group": group,
        "user_id": user_id,
        "user_name": user_name,
        "target_id": target_id,   # işlem hedefi (üye, yeni admin vb.)
        "target_name": target_name,
        "visibility": visibility, # public / private
        "code": code,             # davet kodu
        "name": name,             # grup adı (create duyurusu için)
        "admin_id": admin_id,     # grubun yöneticisi (create duyurusu için)
        "timestamp": datetime.now().strftime("%H:%M"),
    }


def generate_invite_code(length=6):
    """Rastgele davet kodu üretir (BÜYÜK HARF + RAKAM)."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def create_group_announce(group, name, admin_id, admin_name, visibility):
    """Yeni bir grubu ağa duyuran paket (grup oluşturma).

    Karşı taraf bu paketi alınca grupu yerel listesine ekler ve
    kurucuyu yönetici + üye olarak tanır.
    """
    return {
        "type": "group_action",
        "action": "create",
        "group": group,
        "name": name,
        "user_id": admin_id,
        "user_name": admin_name,
        "target_id": "",
        "target_name": "",
        "visibility": visibility,
        "code": "",
        "timestamp": datetime.now().strftime("%H:%M"),
    }


# ---------------------------------------------------------------------------
# Mesaj düzenleme / silme
# ---------------------------------------------------------------------------

def create_delete_notice(msg_id, user_id, target_id):
    """Mesaj silme bildirimi oluşturur."""
    return {
        "type": "delete_message",
        "msg_id": msg_id,
        "user_id": user_id,
        "target_id": target_id,
        "timestamp": datetime.now().strftime("%H:%M"),
    }


def create_edit_notice(msg_id, new_content, user_id, target_id):
    """Mesaj düzenleme bildirimi oluşturur."""
    return {
        "type": "edit_message",
        "msg_id": msg_id,
        "content": new_content,
        "user_id": user_id,
        "target_id": target_id,
        "timestamp": datetime.now().strftime("%H:%M"),
    }


# ---------------------------------------------------------------------------
# El kaldırma
# ---------------------------------------------------------------------------

def create_hand_raise(msg_id, action, user_id, user_name=""):
    """El kaldırma bildirimi oluşturur.

    action: "raise" (el kaldır) veya "lower" (el indir)
    """
    return {
        "type": "hand_raise",
        "msg_id": msg_id,
        "action": action,
        "user_id": user_id,
        "user_name": user_name,
        "timestamp": datetime.now().strftime("%H:%M"),
    }


# ---------------------------------------------------------------------------
# Canlı anket
# ---------------------------------------------------------------------------

def create_poll(action, poll_id, question="", options=None, user_id="",
                user_name="", option_index=-1, target_id=""):
    """Anket paketi oluşturur.

    action: "create" (anket aç), "vote" (oy ver), "close" (anketi kapat)
    target_id: anketin hangi sohbette açıldığı
    """
    return {
        "type": "poll",
        "action": action,
        "poll_id": poll_id,
        "question": question,
        "options": options or [],
        "user_id": user_id,
        "user_name": user_name,
        "option_index": option_index,
        "target_id": target_id,
        "timestamp": datetime.now().strftime("%H:%M"),
    }


# ---------------------------------------------------------------------------
# Pairing (sunucusuz eşleştirme)
# ---------------------------------------------------------------------------

def create_pair_request(user_id, user_name, code):
    """Eşleştirme isteği oluşturur (kodu bilen cihaz gönderir)."""
    return {
        "type": "pair_request",
        "user_id": user_id,
        "user_name": user_name,
        "code": code,
        "timestamp": datetime.now().strftime("%H:%M"),
    }


def create_pair_response(accept, user_id, user_name, target_id, code=""):
    """Eşleştirme isteğine kabul/ret cevabı oluşturur."""
    return {
        "type": "pair_response",
        "accept": accept,
        "user_id": user_id,
        "user_name": user_name,
        "target_id": target_id,
        "code": code,
        "timestamp": datetime.now().strftime("%H:%M"),
    }


# ---------------------------------------------------------------------------
# Serileştirme
# ---------------------------------------------------------------------------

def encode(packet):
    """Paketi JSON string'e çevirip byte'lara encode eder."""
    return json.dumps(packet, ensure_ascii=False).encode("utf-8")


def decode(data):
    """Byte'ları JSON string'e çevirip paket olarak döndürür."""
    try:
        return json.loads(data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
