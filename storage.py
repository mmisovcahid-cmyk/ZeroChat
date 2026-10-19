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

from config import HISTORY_FILE


def save_history(chats, filepath=HISTORY_FILE):
    """Sohbet geçmişini diske yazar.

    chats: {other_id: [(is_outgoing, mesaj_paketi), ...]}
    Returns: True başarılı, False hata oluştu
    """
    if not chats:
        return True

    # Sadece JSON'a çevrilebilir temel tipleri sakla
    data = {
        chat_id: [
            [is_outgoing, pkt]
            for is_outgoing, pkt in messages
        ]
        for chat_id, messages in chats.items()
        if messages
    }

    if not data:
        return True

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except (OSError, TypeError, ValueError) as e:
        print(f"Geçmiş kaydedilemedi: {e}")
        return False


def load_history(filepath=HISTORY_FILE):
    """Geçmişi diskten okur.

    Returns: {other_id: [(is_outgoing, mesaj_paketi), ...]}
    Dosya yoksa boş sözlük döner.
    """
    if not os.path.exists(filepath):
        return {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Geçmiş okunamadı: {e}")
        return {}

    chats = {}
    for chat_id, entries in raw.items():
        messages = []
        for entry in entries:
            try:
                is_outgoing, pkt = entry
                if isinstance(pkt, dict) and "content" in pkt:
                    messages.append((bool(is_outgoing), pkt))
            except (TypeError, ValueError):
                continue
        if messages:
            chats[chat_id] = messages

    return chats


def clear_history(filepath=HISTORY_FILE):
    """Geçmiş dosyasını siler."""
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
