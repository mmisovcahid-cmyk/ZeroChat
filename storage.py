"""
ZeroChat - Mesaj Geçmişi (Dosya I/O)

Mesaj geçmişini JSON dosyasına kaydeder ve uygulama açılışında
geri yükler.

Öğrenme Konuları:
  - Dosya açma/kapatma (with bloğu)
  - JSON serileştirme (json.dump / json.load)
  - Hata yönetimi (FileNotFoundError, JSONDecodeError)
  - UTF-8 kodlama (Türkçe karakterler)
"""

import json
import os

from config import HISTORY_FILE, MAX_HISTORY_MESSAGES, resolve_path


def _normalize_packet(pkt):
    """Eksik alanları varsayılanlarla doldurur (bozuk/eskimiş kayıtlar)."""
    if not isinstance(pkt, dict):
        return None

    normalized = dict(pkt)
    normalized.setdefault("type", "message")
    normalized.setdefault("msg_id", "")
    normalized.setdefault("timestamp", "")
    normalized.setdefault("sender_name", "")
    normalized.setdefault("content", "")
    return normalized


def save_history(chats, filepath=HISTORY_FILE):
    """Sohbet geçmişini diske yazar.

    chats: {other_id: [(is_outgoing, mesaj_paketi), ...]}
    Returns: True başarılı, False hata oluştu

    Yazma ATOMİK'tir: önce geçici dosyaya yazılır, sonra asıl dosyanın
    üzerine taşınır. Böylece uygulama yazma sırasında kapanırsa geçmiş
    dosyası bozulmaz.
    """
    if not chats:
        return True

    filepath = resolve_path(filepath)

    # Sadece JSON'a çevrilebilir temel tipleri sakla.
    # Uzun sohbetlerde dosya şişmesin diye en yeni mesajlar tutulur.
    data = {}
    for chat_id, messages in chats.items():
        if not messages:
            continue
        if MAX_HISTORY_MESSAGES > 0 and len(messages) > MAX_HISTORY_MESSAGES:
            messages = messages[-MAX_HISTORY_MESSAGES:]
        data[chat_id] = [
            [is_outgoing, pkt]
            for is_outgoing, pkt in messages
        ]

    if not data:
        return True

    tmp_path = filepath + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, filepath)
        return True
    except (OSError, TypeError, ValueError) as e:
        print(f"Geçmiş kaydedilemedi: {e}")
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
        return False


def load_history(filepath=HISTORY_FILE):
    """Geçmişi diskten okur.

    Returns: {other_id: [(is_outgoing, mesaj_paketi), ...]}
    Dosya yoksa boş sözlük döner.
    """
    filepath = resolve_path(filepath)

    if not os.path.exists(filepath):
        return {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Geçmiş okunamadı: {e}")
        return {}

    if not isinstance(raw, dict):
        print("Geçmiş dosyası beklenen biçimde değil, atlanıyor.")
        return {}

    chats = {}
    for chat_id, entries in raw.items():
        messages = []
        if not isinstance(entries, list):
            continue
        for entry in entries:
            try:
                is_outgoing, pkt = entry
            except (TypeError, ValueError):
                continue
            normalized = _normalize_packet(pkt)
            if normalized is not None:
                messages.append((bool(is_outgoing), normalized))
        if messages:
            chats[chat_id] = messages

    return chats


def clear_history(filepath=HISTORY_FILE):
    """Geçmiş dosyasını siler."""
    filepath = resolve_path(filepath)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
        return True
    except OSError as e:
        print(f"Geçmiş silinemedi: {e}")
        return False


def get_history_stats(chats):
    """Geçmiş istatistiklerini döndürür (bilgi amaçlı)."""
    total = 0
    for messages in chats.values():
        total += len(messages)

    sent = 0
    for messages in chats.values():
        for is_outgoing, _ in messages:
            if is_outgoing:
                sent += 1

    return {
        "chats": len(chats),
        "messages": total,
        "sent": sent,
        "received": total - sent,
    }
