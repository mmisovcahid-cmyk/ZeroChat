"""
ZeroChat - Oturum Kaydı (Session Log)

Ağ üzerindeki tüm paketleri diske yazar. Wireshark'ın uygulama
seviyesindeki karşılığıdır: paketlerin JSON içeriğini okunabilir
şekilde kaydeder.

Format: JSON Lines (her satır bir JSON nesnesi)
"""

import json
import os
import time
from datetime import datetime

from config import SESSION_LOG_DIR, SESSION_LOG_ENABLED


class SessionLogger:
    """Paketleri JSON Lines formatında diske yazar."""

    def __init__(self, directory=SESSION_LOG_DIR, enabled=SESSION_LOG_ENABLED):
        self.directory = directory
        self.enabled = enabled
        self.file = None
        self.filepath = None
        self.count = 0
        self.byte_count = 0

        if self.enabled:
            self._open()

    def _open(self):
        """Yeni bir oturum dosyası açar."""
        try:
            os.makedirs(self.directory, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.filepath = os.path.join(self.directory, f"session_{stamp}.log")
            self.file = open(self.filepath, "a", encoding="utf-8")
        except OSError as e:
            print(f"Oturum kaydi acilamadi: {e}")
            self.enabled = False

    def log(self, direction, pkt, size=0):
        """Paketi kaydeder.

        direction: "OUT" (gonderilen) veya "IN" (alinan)
        """
        if not self.enabled or self.file is None:
            return

        entry = {
            "t": round(time.time(), 3),
            "time": datetime.now().strftime("%H:%M:%S"),
            "dir": direction,
            "type": pkt.get("type", "?"),
            "size": size,
        }

        # Paket içeriğini düzleştir (iç içe sözlük olmasın)
        for key in ("user_id", "user_name", "target_id", "content", "action",
                    "group", "visibility", "code", "msg_id", "question",
                    "option_index", "poll_id", "file_name", "file_id",
                    "index", "total", "sha256", "status", "ip", "mac",
                    "sender_id", "sender_name"):
            if key in pkt:
                entry[key] = pkt[key]

        try:
            self.file.write(json.dumps(entry, ensure_ascii=False) + "\n")
            # Her yazmada tamponu boşalt (veri kaybı olmasın)
            self.file.flush()
            self.count += 1
            self.byte_count += size
        except (OSError, TypeError, ValueError):
            pass

    def log_out(self, pkt, size=0):
        """Gönderilen paketi kaydeder."""
        self.log("OUT", pkt, size)

    def log_in(self, pkt, size=0):
        """Alınan paketi kaydeder."""
        self.log("IN", pkt, size)

    def close(self):
        """Dosyayı kapatır."""
        if self.file:
            try:
                self.file.close()
            except OSError:
                pass
            self.file = None

    def summary(self):
        """Oturum özetini döndürür."""
        return {
            "file": self.filepath,
            "packets": self.count,
            "bytes": self.byte_count,
        }


# ---------------------------------------------------------------------------
# Oturum dosyalarını listeleme / okuma
# ---------------------------------------------------------------------------

def list_sessions(directory=SESSION_LOG_DIR):
    """Kayıtlı oturum dosyalarını listeler (yeni en önce)."""
    if not os.path.isdir(directory):
        return []

    files = []
    for name in os.listdir(directory):
        if name.startswith("session_") and name.endswith(".log"):
            path = os.path.join(directory, name)
            try:
                stat = os.stat(path)
                files.append({
                    "name": name,
                    "path": path,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                })
            except OSError:
                continue

    files.sort(key=lambda f: f["modified"], reverse=True)
    return files


def read_session(filepath, limit=2000):
    """Oturum dosyasını okur ve kayıtları listeler."""
    entries = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
                if len(entries) >= limit:
                    break
    except OSError as e:
        print(f"Oturum okunamadi: {e}")
        return []

    return entries


def analyze_session(entries):
    """Oturum istatistiklerini hesaplar."""
    stats = {
        "total": len(entries),
        "in": 0,
        "out": 0,
        "bytes_in": 0,
        "bytes_out": 0,
        "types": {},
        "users": {},
        "messages": [],
        "first": None,
        "last": None,
    }

    for entry in entries:
        direction = entry.get("dir", "IN")
        if direction == "IN":
            stats["in"] += 1
            stats["bytes_in"] += entry.get("size", 0)
        else:
            stats["out"] += 1
            stats["bytes_out"] += entry.get("size", 0)

        pkt_type = entry.get("type", "?")
        stats["types"][pkt_type] = stats["types"].get(pkt_type, 0) + 1

        user_id = entry.get("user_id") or entry.get("sender_id")
        if user_id:
            stats["users"][user_id] = stats["users"].get(user_id, 0) + 1

        if pkt_type == "message":
            stats["messages"].append(entry)

        if stats["first"] is None:
            stats["first"] = entry.get("time")
        stats["last"] = entry.get("time")

    return stats
