# ZeroChat - Ağ Kavramları Rehberi

Bu proje öğrencilere temel ağ kavramlarını öğretir.
Her kavram, uygulamadaki karşılığıyla birlikte anlatılır.

---

## 1. IP Adresi

Her cihazın ağdaki benzersiz mantıksal adresi.

```
Örnek: 192.168.1.25
```

**ZeroChat'de:** Giriş ekranında kendi IP adresinizi görürsünüz. Üst çubukta
da yazılıdır. Kontak listesinde her cihazın IP adresi yazılıdır.

**Dikkat:** IP adresi değişebilir (DHCP). Bu yüzden kalıcı kimlik olarak
MAC adresi kullanılır.

---

## 2. MAC Adresi

Donanımın üzerinde yazılı, fabrika ayarı benzersiz adres.

```
Örnek: BB:66:77:88:99:AA
```

**ZeroChat'de:** MAC adresi sizin **kimliğinizdir**. Mesajlar MAC adresine
gönderilir. Bu sayede iki öğrenci aynı ismi seçse bile karışmazlar.

**Uygulamada nasıl bulunur?**
```python
import uuid
mac = ":".join(f"{(uuid.getnode() >> i) & 0xFF:02X}" for i in range(40, -1, -8))
```

---

## 3. Port

Uygulamaların birbirini bulduğu "kapı numarası".

```
ZeroChat Port: 5000
```

**Analoji:** IP adresi binanın adresi, port ise o binadaki kapı numarası.
Bir binada birden fazla program çalışabilir, çünkü her biri farklı kapıyı kullanır.

**ZeroChat'de:** `config.py` içinde `UDP_PORT = 5000` olarak tanımlıdır.

---

## 4. Switch

Ağdaki cihazları birbirine bağlayan cihaz. Gelen paketi **tüm** cihazlara iletir.

```
        ┌─────────────┐
        │   SWITCH    │
        └──┬───┬───┬──┘
      ┌────┘   │   └────┐
   ┌──┴──┐ ┌──┴──┐ ┌──┴──┐
   │  A  │ │  B  │ │  C  │
   └─────┘ └─────┘ └─────┘
```

**ZeroChat'de:** Mesajlar önce tüm cihazlara gider, sonra sadece hedef
cihaz mesajı ekranında gösterir. Diğerleri sessizce atar.

---

## 5. Broadcast

Tek paketin tüm ağa gönderilmesi.

```
Gönderen → 255.255.255.255:5000 → TÜM CİHAZLAR
```

**ZeroChat'de:** Her mesaj ve her tarama paketi broadcast ile gönderilir.

---

## 6. Heartbeat (Yaşam Sinyali)

Cihazın "ben buradayım" dediği periyodik sinyal.

```
t=0s   →  "Ben buradayım" (IP + MAC)
t=3s   →  "Ben buradayım"
t=6s   →  "Ben buradayım"
...
```

**ZeroChat'de:** `HEARTBEAT_INTERVAL = 3` saniye. Bu sayede:

1. Yeni açılan cihazlar otomatik olarak listede görünür
2. Kapanan cihazlar "çevrimdışı" olarak işaretlenir

**Öğrenci sorusu:** "Neden 3 saniye?"
- Çok sık (1 sn) → ağ yükü artar, gereksiz paket trafiği
- Çok nadiren (30 sn) → yeni cihazlar geç görünür, gecikme olur
- 3 saniye → denge noktası

---

## 7. Çevrimdışı Tespiti

Heartbeat gelmeyen cihaz nasıl anlaılır?

```
Son alınan heartbeat: 14:32:05
Şu an:                14:32:20   (fark: 15 sn > OFFLINE_TIMEOUT=12 sn)
Sonuç:                Çevrimdışı
```

**ZeroChat'de:** `OFFLINE_TIMEOUT = 12` saniye. Yani 4 heartbeat kaçırılırsa
cihaz "çevrimdışı" sayılır.

---

## 8. UDP vs TCP

| Özellik | UDP | TCP |
|---------|-----|-----|
| Bağlantı | Bağlantısız | Bağlantılı |
| Hız | Hızlı | Yavaş |
| Güvenilirlik | Garanti yok | Garantili |
| Sıralama | Yok | Var |
| Kullanım | Oyun, video, bu proje | Web, e-posta |

**ZeroChat:** UDP kullanır. Neden?
- Bağlantı kurulum süresi yok (hızlı)
- Basit ve anlaşılır
- Kayıp mesaj sorunu eğitim projesi için kabul edilebilir

**Öğrenci sorusu:** "TCP kullansaydık ne değişirdi?"
- 3 yol el sıkışması (SYN, SYN-ACK, ACK) gerekirdi
- Mesajlar sıralı ve garantili gelirdi
- Ama yavaş olurdu ve kod çok uzar

---

## 9. Threading (İş Parçacıkları)

Bir programın aynı anda birden fazla iş yapabilmesi.

**ZeroChat'de:** 3 thread var:

| Thread | Görev |
|--------|-------|
| Ana thread | GUI (Tkinter) |
| Dinleme thread'i | Gelen paketleri okur |
| Heartbeat thread'i | Her 3 saniyede tarama gönderir |

**Öğrenci sorusu:** "Neden thread gerekli?"
Yazarken aynı anda dinleyebilmek için. Tek thread olsaydı yazarken
mesaj gelse program takılırdı.

---

## 10. Tkinter ve Thread Güvenliği

Tkinter yalnızca ana thread'de kullanılabilir.

**ZeroChat'de çözüm:**
```python
# Ağ thread'inden gelen paket ana döngüye devredilir
def _on_packet(self, pkt):
    self.root.after(0, self._process_packet, pkt)
```

`root.after(0, ...)` çağrısı, işi ana thread'de sıraya alır.

---

## 11. Güvenlik

**ÖNEMLİ: Bu bir eğitim projesidir!**

| Risk | Açıklama |
|------|----------|
| Şifreleme yok | Mesajlar düz metin gönderilir, ağda okunabilir |
| Kimlik doğrulama yok | Herkes herhangi bir MAC ID ile mesaj gönderebilir |
| Yetkilendirme yok | Herkes herkese mesaj atabilir |
| Paket yakalama | Wireshark ile tüm mesajlar görülebilir |

**Güvenli bir versiyon için:**
- Şifreleme: AES veya ChaCha20
- İmza: RSA / Ed25519 ile kimlik doğrulama
- Tünel: VPN veya TLS

**Eğitim amacı:** Wireshark ile paketleri incelemek, mesajların
şifrelenmediğini görmek ve sonra şifrelemenin neden gerekli olduğunu
tartışmak mükemmel bir ders.

---

## 12. Örnek Sınav Soruları

1. ZeroChat neden TCP yerine UDP kullanıyor?
2. Aynı ismi seçen iki cihaz arasında mesajlar nasıl ayırt ediliyor?
3. Broadcast paketini alan ama mesajı göstermeyen cihaz, neden `target_id`
   kontrolü yapar?
4. Heartbeat paketleri ağda ne kadar trafik oluşturur? (Hesaplayınız)
5. Kullanıcı adını değiştirirsen cihazın MAC adresi değişir mi?
6. Uygulamayı iki bilgisayarda aynı anda çalıştırsanız, port çakışması
   olur mu? Neden?
7. `OFFLINE_TIMEOUT` değerini 3 saniyeye düşürürsen ne olur?
8. Güvenli sohbet için hangi iki mekanizma eklenmeli?
