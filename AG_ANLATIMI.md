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

## 5.1 Subnet Broadcast Adresi

Sınırlı broadcast (`255.255.255.255`) yerine, cihazın kendi subnet'inin
broadcast adresi kullanılır.

```
IP    : 192.168.100.17
Maske : 255.255.255.0
Yayın : 192.168.100.255   ← subnet broadcast
```

**Hesaplama:** IP adresini maskeleme ile "ters çevirip" OR işlemi yapılır.

```python
import ipaddress
network = ipaddress.ip_network("192.168.100.17/255.255.255.0", strict=False)
print(network.broadcast_address)   # 192.168.100.255
```

**Neden önemli?**

Bir bilgisayarda birden fazla ağ arayüzü olabilir:

```
Ethernet adapter Ethernet 2  → 192.168.56.1    (VirtualBox - sanal)
Wireless LAN adapter Wi-Fi   → 192.168.100.17  (gerçek ağ)
```

`255.255.255.255` gönderilirken işletim sistemi "en uygun" arayüzü seçer ve
bu **sanal** adaptörü seçebilir. Paketler sanal kabloya gider, WiFi'deki
arkadaşınıza asla ulaşmaz.

Subnet broadcast'u (`192.168.100.255`) ise **hangi ağa ait olduğu belli** olduğu
için doğru arayüzden çıkar.

**Öğrenci sorusu:** "Neden iki bilgisayar birbirini göremiyordu?"
Cihazın IP'si sanal adaptör seçildiği için broadcast paketleri yanlış
arayüzden çıkmıştı.

---

## 5.2 Arayüz Seçimi (Default Gateway)

Hangi adaptörün "gerçek ağ" olduğunu nasıl anlarız?

**Default Gateway** = o ağdan dışarı (internete) çıkış kapısı.

```
Wi-Fi:  IP 192.168.100.17  Gateway 192.168.100.1  → GERÇEK AĞ
Eth 2:  IP 192.168.56.1    Gateway (yok)          → SANAL
```

Sıralama kuralı:
1. Gateway'i olan + sanal olmayan adaptör
2. Sanal olmayan adaptör (gateway yoksa - sadece switch'e bağlı durum)
3. Gateway'i olan herhangi biri

**Sanal adaptör tespiti:**
- Ada bakılır: "VirtualBox", "Hyper-V", "VMware", "Docker"...
- MAC ön ekine bakılır: `0A-00-27` = VirtualBox, `00-15-5D` = Hyper-V
- IP aralığına bakılır: `192.168.56.x` = VirtualBox varsayılanı

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

## 11.1 Arayüz Seçimi (Elle Değiştirme)

Bilgisayarda birden fazla arayüz varsa (Wi-Fi + Ethernet) otomatik seçim
yanlış olabilir. Bu yüzden üst çubuktaki "Arayüz: ... ▾" yazısına tıklanır
ve listeden seçim yapılır:

```python
def _apply_interface(self, iface):
    self.network.set_interface(iface)   # IP + yayın adresi değişir
    settings = config.load_settings()
    settings["interface"] = iface.get("name", "")
    config.save_settings(settings)
```

**Önemli:** Arayüz değişince **cihaz kimliği (MAC) değişmez**. Sadece
gönderim yapılan IP ve yayın adresi değişir. Böylece sohbet geçmişi ve
arkadaş listesi bozulmaz.

---

## 12. Grup Sohbeti (Çok Hedefli Routing)

### Problem
Normal mesajlaşmada `target_id` tek bir MAC adresidir. Grup sohbetinde ise
bir mesaj birden fazla alıcıya gönderilir.

### Çözüm
Grup mesajlarının hedefi bir **grup kimliğidir**, MAC değil:

```
Birebir :  target_id = "BB:66:77:88:99:AA"   (tek cihaz)
Grup     :  target_id = "GRP:sinif"           (gruptaki herkes)
Herkes   :  target_id = "ALL"                 (ağdaki tüm cihazlar)
```

### Alma Mantığı

```python
def _is_message_for_me(self, target_id):
    if target_id == self.user_id:           # birebir
        return True
    if target_id == GROUP_ALL:              # herkese
        return True
    if target_id.startswith(GROUP_PREFIX):  # gruba mı üye?
        return target_id in self.groups
    return False
```

**Öğrenci sorusu:** "Neden `startswith` kullanıyoruz?"
Çünkü grup kimlikleri bir önek ile başlar (`GRP:`). Bu ayrım, MAC adresi
(`AA:BB:CC:DD:EE:FF`) ile grup kimliğini (`GRP:sinif`) karıştırmamızı sağlar.

### Grup Üyeliği

Grup önce **ağa duyurulur** (`create`), sonra üyeler bildirilir (`join`):

```json
{"type": "group_action", "action": "create", "group": "GRP:sinif",
 "name": "Sinif", "user_id": "AA:11:22:33:44:55", "visibility": "public"}

{"type": "group_action", "action": "join", "group": "GRP:sinif",
 "user_id": "BB:66:77:88:99:AA", "user_name": "Veli"}
```

**Öğrenci sorusu:** "Neden ayrı bir grup listesi var, presence paketiyle olsa?"
Çünkü grup üyeliği kalıcı bir bilgi (kim hangi grupta), presence ise geçici
(şu an online mı). Farklı yaşam süreleri için farklı paketler.

**Öğrenci sorusu:** "Neden `create` paketi gerekiyor, `join` yeterli değil mi?"
`join` paketi sadece "ben gruba katıldım" der; **grubun adını, yöneticisini ve
gizli mi herkese açık mı olduğunu** taşımaz. `create` paketi bu bilgiyi
taşıdığı için alıcı taraf grup kaydını kendisi oluşturabilir. Aksi halde
"Gruba Katıl" butonu hiçbir işe yaramazdı.

### Grup Duyurusu ve Yetki (Güvenlik)

Grup, ağa `create` paketiyle duyurulur. **Ağ güvenilmezdir**: herkes herkese
istediği paketi gönderebilir. Bu yüzden duyuru bir yetki kontrolünden geçer:

```python
existing = self.groups.get(group_id)
local_admin = existing.get("admin_id", "") if existing else ""

# Yerel kayıtta bir yönetici varsa duyuru yalnızca o yöneticinin
# kendisinden geliyorsa kabul edilir.
if existing and local_admin:
    if not (announced_admin == local_admin and admin_id == local_admin):
        return
```

**Öğrenci sorusu:** "Bunu yapmazsak ne olur?"
Aynı adlı bir grup duyuran kötü niyetli bir cihaz:
- yöneticinin **davet kodunu silebilir** (öğrenciler artık gruba giremez)
- kendini **üye olarak ekleyebilir** (onay olmadan)
- grubu **gizli -> herkese açık** yapabilir
- grubun **adını değiştirebilir**

**Öğrenci sorusu:** "Peki bir katılımcı yöneticiyi nasıl öğrenir?"
`create` paketi `admin_id` alanını taşır. Yönetici, bir katılım bildirimi
geldiğinde grubu yeniden duyurur; katılımcı bu duyurudan yöneticinin kim
olduğunu öğrenir. Yalnızca **yönetici** duyuru yapabilir, böylece yanlış
yönetici atanmaz.

### Grup Protokolü (Aksiyonlar)

| Aksiyon | Gönderen | Anlamı |
|---------|----------|--------|
| `create` | Yönetici | Grubu adı/görünürlüğüyle duyurur |
| `join` | Üye | Gruba katıldım |
| `leave` | Üye | Gruptan ayrıldım |
| `invite_request` | Aday | Gizli gruba katılma isteği (kod ile) |
| `invite_accept` | Yönetici | Davet kabul edildi |
| `invite_reject` | Yönetici | Kod yanlış, davet reddedildi |
| `remove_member` | Yönetici | Üyeyi çıkardı |
| `delete_group` | Yönetici | Grup silindi |
| `set_visibility` | Yönetici | Gizli/herkese açık değişti |
| `transfer_admin` | Yönetici | Yönetici devri (`target_id` = yeni yönetici) |

---

## 13. Mesaj Silme ve Düzenleme

### Benzersiz Mesaj Numarası (UUID)

Her mesaja benzersiz bir kimlik verilir:

```python
import uuid
msg_id = uuid.uuid4().hex[:8]   # 8 karakterlik benzersiz kod
```

**Neden gerekli?**
Mesajlar sırayla değil, `msg_id` ile referanslanır. "Şu balonu sil" dendiğinde
hangi mesajın silineceğini bilmek gerekir.

**Öğrenci sorusu:** "Sıra numarası (index) yetmez mi?"
Index değişebilir. Mesaj silinince diğerlerinin index'i kayar. `msg_id`
kararlıdır - mesaj silinse bile diğer mesajların ID'si değişmez.

### Sağ Tık Menüsü

```python
menu = tk.Menu(self, tearoff=0)
menu.add_command(label="Kopyala", command=self._copy)
menu.add_command(label="Düzenle", command=self._edit)
menu.add_command(label="Sil", command=self._delete)
menu.tk_popup(event.x_root, event.y_root)
```

**Öğrenci sorusu:** "Neden `tearoff=0`?"
Tkinter menüleri varsayılan olarak ayrı pencereye koparılabilir. `tearoff=0`
bunu engeller - menü hep pencereye bağlı kalır.

### Senkronizasyon

Silme ve düzenleme karşı tarafa da bildirilir:

```json
{"type": "delete_message", "msg_id": "a1b2c3d4", ...}
{"type": "edit_message", "msg_id": "a1b2c3d4", "content": "yeni metin", ...}
```

**Öğrenci sorusu:** "Neden sadece kendi ekranımda silmek yetmezdi?"
Çünkü karşı tarafta da mesaj durmalı. Yoksa bir tarafta mesaj var, diğerinde
yok - tutarsızlık. Bu, "dağıtık sistemlerde tutarlılık" konusunun basit bir
örneğidir.

---

## 14. Dosya I/O ve JSON

### Mesaj Geçmişi

```python
# Kaydetme
with open("history.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Yükleme
with open("history.json", "r", encoding="utf-8") as f:
    data = json.load(f)
```

### Neden `with` kullanıyoruz?

```python
# Kötü - dosya hata olursa kapanmayabilir
f = open("history.json", "w")
f.write("...")
f.close()

# İyi - hata olsa bile dosya otomatik kapanır
with open("history.json", "w") as f:
    f.write("...")
```

### Neden `encoding="utf-8"`?

Türkçe karakterler (ç, ğ, ı, ö, ş, ü) UTF-8 ile saklanır. encoding belirtmezsek
sistem varsayılanı (Windows'ta cp1254) kullanılır ve karakterler bozulur.

```python
json.dump(data, f, ensure_ascii=False)   # Türkçe karakterler okunabilir kalsın
```

**Öğrenci deneyimi:** `ensure_ascii=True` (varsayılan) ile `"ç"` yerine
`"\u00e7"` yazılır. `False` ile gerçek karakter yazılır.

### Hata Yönetimi

```python
try:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
except (OSError, json.JSONDecodeError) as e:
    print(f"Geçmiş okunamadı: {e}")
    return {}
```

**Öğrenci sorusu:** "Dosya bozuksa ne olur?"
`json.JSONDecodeError` fırlatır. Yakalamazsak program çöker. Yakalarsak
boş geçmişle devam eder - kullanıcı yeni sohbete başlayabilir.

---

## 15. Tkinter Düzen Yöneticileri (grid vs pack)

### Problem

`pack` ile düzen kurarken sıralama önemlidir. `expand=True` kullanan bir widget
alanın tamamını kapabilir.

### Çözüm: grid

```python
self.rowconfigure(1, weight=1)     # 1. satır esner
self.columnconfigure(0, weight=1)  # 0. sütun esner

self.header.grid(row=0, column=0, sticky="ew")
self.messages.grid(row=1, column=0, sticky="nsew")   # ortadaki alan esner
self.input.grid(row=2, column=0, sticky="ew")        # altta sabit
```

**Öğrenci sorusu:** "Neden `weight=1` gerekli?"
`weight` o satır/sütunun fazladan alanı ne kadar paylaşacağını belirler.
`weight=1` olmadan mesaj alanı büyümez, yazma alanı ekranı doldurur.

### Canvas + Scrollbar

Mesaj alanı için `Canvas` kullanılır:

```python
canvas = tk.Canvas(messages_frame, yscrollcommand=scrollbar.set)
scrollbar = tk.Scrollbar(messages_frame, command=canvas.yview)
inner = tk.Frame(canvas)
canvas.create_window((0, 0), window=inner, anchor="nw")
```

**Öğrenci sorusu:** "Neden `inner` frame gerekli?"
Canvas'a doğrudan widget koyamazsınız. İçine bir Frame koyup o Frame'e
balonları eklersiniz.

**Pencere genişliği uyumu:**
```python
def _on_canvas_configure(self, event):
    self.canvas.itemconfigure(self._canvas_window, width=event.width)
```
Canvas genişlediğinde iç Frame de genişler - böylece balonlar sağa dayalı
kalır.

---

## 16. Grup Yönetimi ve Yetkilendirme

### Admin (Yönetici) Modeli

Grubu **kuran** kişi yöneticidir. Yönetici bilgisi grup kaydında tutulur:

```python
self.groups[group_id] = {
    "name": "Sinif",
    "admin_id": "AA:11:22:33:44:55",   # yönetici
    "visibility": "private",
    "members": {user_id: user_name},
    "invite_code": "3TKKFK",
    "pending": {user_id: user_name},     # bekleyen davet istekleri
}
```

### Yetki Kontrolü

```python
def _is_admin(self, group_id):
    group = self.groups.get(group_id)
    if not group:
        return False
    return group.get("admin_id") == self.user_id
```

**Öğrenci sorusu:** "Yetki kontrolü neden iki yerde var?
Hem gönderen tarafta hem alan tarafta var."

Çünkü ağ **güvenilmez** bir ortamdır! Herkes herkese istediği paketi
gönderebilir. Eğer sadece gönderen taraf kontrol ederse, kötü niyetli bir
öğrenci "delete_group" paketi gönderip grubu silebilir.

**Doğru kural:** Yetkiyi **her iki tarafta** da kontrol et.
(Proje şu an alan tarafta kontrol ediyor - eğitirim için ideal.)

### Yetki Matrisi

| İşlem | Admin | Üye |
|-------|:-----:|:----:|
| Grup oluşturma | ✓ | ✓ |
| Gruba katılma (public) | ✓ | ✓ |
| Gruba katılma (gizli) | ✓ | kod + onay | kod + onay |
| Grup silme | ✓ | ✗ |
| Üye çıkarma | ✓ | ✗ |
| Görünürlük değiştirme | ✓ | ✗ |
| Davet kodu görme | ✓ | ✗ |

### Yönetici Devri

Yönetici ayrılırsa grupta üye kalıyorsa, bir sonraki üye yeni yönetici olur:

```python
if group["admin_id"] == self.user_id:
    if group["members"]:
        new_admin = next(iter(group["members"]))
        group["admin_id"] = new_admin
```

Bu değişiklik ağa `transfer_admin` paketi ile bildirilir; diğer cihazlar da
yeni yöneticinin kim olduğunu öğrenir.

---

## 17. Gizli Gruplar ve Davet Kodu

### Neden Kod?

Herkes grup adını biliyorsa (ör. "Sinif"), herkes katılabilir. Gizli grupta
katılım için **ek bir bilgi** gerekir: davet kodu.

### Kod Üretimi

```python
import random, string

def generate_invite_code(length=6):
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))
```

**Öğrenci sorusu:** "6 karakter yeterli mi?"
6 karakter, 36 alfabe ile ~2 milyar kombinasyon verir. Küçük bir sınıf için
fazlasıyla yeterli. İnternet'te olsa 8-10 karakter gerekirdi.

### Davet Akışı

```
Öğrenci                          Yönetici
   │ kod girer (A7K2M9)
   ├──── invite_request ────────►│
   │                            │  "Bekleyen istekler" listesine ekler
   │                            │
   │◄──── invite_accept ────────┤  (yönetici "Kabul" der)
   │  gruba katılır             │
```

**Öğrenci sorusu:** "Neden istek gönderiyoruz da direkt katılamıyoruz?"
Çünkü yönetcinin onayı, gizli grubun "kimin girdiğini" kontrol etmesini sağlar.
Aksi halde herhangi biri kodu tahmin edip gruba girerdi.

**Alternatif (daha basit):** Kod doğruysa direkt katıl. Proje kodunu
doğruladıktan sonra istek gönderir - iki aşamalı güvenlik.

---

## 18. El Kaldırma (Raise Hand)

Sınıfta öğretmen soru sorar, öğrenciler cevaplamak ister. El kaldırma
bunu sınıf içinde gösterir.

### Paket

```json
{"type": "hand_raise", "msg_id": "a1b2c3d4",
 "action": "raise", "user_id": "AA:11:...", "user_name": "Ahmet"}
```

### State Yönetimi

```python
self.hands = {}    # msg_id -> {user_id: user_name}
```

### Neden Mesaja Bağlı?

Bir sohbette birden fazla soru sorulabilir. El kaldırma mesaja bağlı
olursa öğretmen hangi soruya kaç kişinin el kaldırdığını görebilir.

**Öğrenci sorusu:** "El kaldırma neden mesajla ilişkilendirildi, sohbetle değil?"
Çünkü sohbette 5 soru sorulduysa hangi soruya el kaldırıldığını bilmek gerekir.

---

## 19. Canlı Anket (Broadcast + Toplama)

### Problem

Anket sonuçları nasıl hesaplanacak? Merkezi bir sunucu yok!

### Çözüm: Dağıtık Toplama

Her cihaz oyunu **kendi saklar** ve sonuçları hesaplar:

```python
poll = {
    "question": "En sevdiğin ders?",
    "options": ["Matematik", "Fizik", "Tarih"],
    "votes": {"AA:11...": 0, "BB:66...": 0, "CC:11...": 1},
    "open": True,
}
```

Yüzde hesabı:
```python
total = len(votes)
for i, option in enumerate(options):
    count = sum(1 for v in votes.values() if v == i)
    percent = count / total * 100
```

**Öğrenci sorusu:** "Her cihaz aynı sonucu nasıl buluyor?"
Çünkü oy paketleri broadcast ile **herkese** ulaşır. Her cihaz aynı oy
kümesini görür, aynı hesabı yapar. Merkezi sunucuya gerek yok!

**Öğrenci sorusu:** "Anketi açan kişi anketi kapatırsa ne olur?"
`open: False` yayınlanır, herkes kartı "KAPANDI" olarak gösterir. Oylar
silinmez, sadece yeni oy verilemez.

### Geri Bildirim Döngüsü (Feedback Loop)

**Önemli uyarı:** Alıcı cihaz, aldığı paketi **yeniden göndermemelidir**!

```python
# YANLIŞ - sonsuz döngü
def _handle_poll(self, pkt):
    self.polls[poll_id] = poll
    self.network.send_poll("create", poll_id, ...)   # ← sonsuz döngü!

# DOĞRU - sadece kendi durumunu güncelle
def _handle_poll(self, pkt):
    if poll_id not in self.polls:
        self.polls[poll_id] = poll
```

**Öğrenci sorusu:** "Neden alıcı da göndermemeli?"
Çünkü broadcast zaten herkese ulaşıyor. Herkes bir kez alıp durumunu
güncellerse yeter. Yeniden gönderim olursa:
```
A gönderir → B alır, gönderir → A alır, gönderir → B alır... ♾️
```

Bu konu **dağıtık sistemlerde "tek gönderim" (single-source) prensibi**
olarak çok önemlidir.

---

## 20. Gizli Mod ve Ağ Görünürlüğü

### Problem

Cihazınız presence paketleriyle "Ben buradayım" diyor. Bu paketler
broadcast ile **herkese** gider. Yani ağdaki herkes sizin varlığınızı bilir.

### Çözüm: Presence Göndermeme

```python
def _heartbeat(self):
    while self.running:
        if not self.stealth:        # gizli modda presence gönderme
            self.send_presence("online")
        ...
```

**Öğrenci sorusu:** "Gizli modda presence hiç gönderilmiyor mu?"
Evet. Cihaz ağda yokmuş gibi davranır. Ancak biri size mesaj atarsa, o
paket sizi tanımlar ve cihazınız listede görünür olur.

**Öğrenci sorusu:** "Bu gerçek gizlilik mi?"
Hayır! Bu sadece **uygulama seviyesinde** gizlilik. Ağ trafiğini izleyen biri
(Wireshark) paketleri hâlâ görür. Gerçek gizlilik için:
- Şifreleme (payload gizli)
- VPN (adres gizli)
- MAC randomization (donanım kimliği gizli)

**Karşı taraf "hidden" status'unu görürse ne yapar?**
Eğitim amaçlı olarak `👻` ikonuyla listede gösterir. `config.py`'de
`STEALTH_HIDE_COMPLETELY = True` ile tamamen gizlenebilir.

**Varsayılan davranış:** Gizli moda girerken "hidden" duyurusu **gönderilmez**.
Böylece cihaz gerçekten ağda görünmez olur (karşı taraf sizi 12 saniye sonra
"çevrimdışı" olarak görür). Eğitimde `👻` rozetini göstermek isterseniz
`config.py`'de `STEALTH_ANNOUNCE = True` yapabilirsiniz - ama bu durumda cihaz
bir kez olsa da kendini ele verir.

---

## 21. Zamanlı Mesaj (Scheduler)

### Basit Zamanlayıcı

```python
def _check_scheduled(self):
    now = time.time()
    for item in list(self.scheduled):
        if item["send_at"] <= now:
            self.network.send_message(item["target_id"], item["content"])
            self.scheduled.remove(item)
    self.root.after(1000, self._check_scheduled)
```

**Neden `list(...)` kopyası üzerinde dönüyoruz?**
Çünkü `remove()` çağırırken listeyi değiştiriyoruz. Kopyası üzerinde dönseydik
bir eleman atlanabilirdi.

**Öğrenci sorusu:** "Her saniye kontrol etmek verimli mi?"
Verimli değil ama basit. Gerçek uygulamalarda:
- `threading.Timer` ile her mesaj için ayrı zamanlayıcı
- `heapq` (öncelik kuyruğu) ile en yakın mesajı bulma
- `asyncio` ile event loop

**Öğrenci sorusu:** "Uygulama kapanırsa zamanlanmış mesajlar ne olur?"
Kaybolur! Çünkü sadece bellekte tutuluyorlar. Kalıcı olması için
`history.json` gibi diske yazılmalı ve açılışta geri yüklenmeli.

---

## 21.1 Büyük Paketler ve UDP Tamponu

UDP'de paketin alıcıya ulaşması için **önce tam alınması** gerekir.
Alma tamponu küçük tutulursa iki şey olur:

| İşletim Sistemi | Davranış |
|-----------------|----------|
| Linux | Paket **kırpılır**, JSON bozulur, mesaj sessizce düşer |
| Windows | `recvfrom` **WSAEMSGSIZE (10040)** fırlatır |

Windows'ta hata `except OSError: break` ile yakalanırsa **dinleme thread'i
ölür** ve cihaz bir daha hiçbir mesaj alamaz. Çözüm:

```python
BUFFER_SIZE = 65535        # IPv4'in en büyük UDP yükü

except OSError as e:
    if not self.running:   # soket kapandı
        break
    continue               # tek bir bozuk paket dinlemeyi öldürmemeli
```

**Öğrenci sorusu:** "Neden 65535?"
IPv4'in en büyük UDP yükü tam olarak 65535 bayttır. Daha küçük bir tampon
"normalde" yeterli görünür ama 4 KB üzerindeki tek bir mesaj bütün
bağlantıyı sessizce bozabilir.

---

## 22. Oturum Kaydı ve Protokol Analizi

### JSON Lines Formatı

```python
with open("session.log", "a", encoding="utf-8") as f:
    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
```

**Neden JSON Lines, normal JSON değil?**

| Format | Avantaj | Dezavantaj |
|--------|---------|------------|
| JSON Lines | Her satır bağımsız okunur, akış halinde yazılır | Tüm dosyayı parse etmek gerekir |
| Normal JSON | Tek dosya, standart | Her yazmada tüm dosyayı yeniden yazmak gerekir |

**Öğrenci sorusu:** "Neden `flush()` çağırıyoruz?"
Çünkü `f.write()` sadece Python'un belleğine yazar. `flush()` dosyaya iter.
Program çökerse `flush()` edilmemiş veri kaybolur.

**Öğrenci sorusu:** "Her paket için dosya açıp kapatmak yavaş olmaz mı?"
Evet, çok yavaş olur. Çözümler:
- Dosyayı bir kez aç, program boyunca açık tut (bu proje)
- `io.BufferedWriter` ile tamponlama
- `logging` modülü (Python'un standart çözümü)

### Wireshark vs ZeroChat

| | Wireshark | ZeroChat Oturum Kaydı |
|---|-----------|---------------------|
| **Katman** | Ağ (L2-L7) | Uygulama (L7) |
| **Ne görür** | IP/UDP/TCP başlıkları, hex dump | JSON mesaj içeriği |
| **Okunabilirlik** | Düşük (uzman gerekir) | Yüksek |
| **Kurulum** | Gerekir (Wireshark + BPF) | Gerekmez |
| **Filtreleme** | BPF filtresi | Python sorgusu |

**Öğrenci aktivitesi:** Bir ders sınıfında oturum kaydı açık bırakılır.
Ders sonunda `session.log` analiz edilir:
- Kim kaç mesaj attı?
- Anketin sonucu neydi?
- Gecikme (latency) ne kadar? (gönderme ve alma zamanları farkı)

---

## 23. Pairing Kodu (Sunurusuz Kimlik Doğrulama)

### Problem

MAC adresiyla eşleşmek zor: `A4:5E:60:D2:9F:11` yazmak gerekir ve
karşıdaki cihazın MAC'ini bilmen gerekir.

### Çözüm: Kullanıcı Kolaylığı

```
Cihaz A (kod gösterir)              Cihaz B (kod girer)
────────────────────────            ────────────────────
Kod: NNGL42 gösterir                 NNGL42 girer
   │                                  ├──── pair_request ────►│
   │◄──── pair_request ───────────────┤                      │
   │ "Ayşe eşleşmek istiyor" onayla   │                      │
   │──── pair_response (accept) ─────►│                      │
   │                                  │ Eşleşti!             │
```

### Paketler

```json
{"type": "pair_request", "user_id": "BB:66:...", "user_name": "Ayşe", "code": "NNGL42"}
{"type": "pair_response", "accept": true, "user_id": "AA:11:...", "target_id": "BB:66:..."}
```

### Güvenlik Analizi (ÖĞRENCİYE SOR)

Bu proje eğitim amaçlıdır. Gerçek bir sistemde şu sorular sorulmalı:

| Sorun | Açıklama | Çözüm |
|-------|----------|-------|
| **Kaba kuvvet** | 6 haneli = 36^6 ≈ 2 milyar, ama hızlı denenebilir | 8+ karakter, deneme sınırı |
| **Kod tahmini** | Kod 5 dk geçerli ama izlenebilir | Tek kullanımlık, kısa ömür |
| **Man-in-the-middle** | Kodu duyan kişi bağlanabilir | İmza doğrulama (RSA/Ed25519) |
| **Replay** | Kod tekrar kullanılabilir | Zaman damgası + nonce |

**Öğrenci sorusu:** "Bu güvenli mi?"
Hayır. Kod sadece **kolaylık** sağlar, güvenlik değil. Gerçek kimlik
doğrulama **asimmetrik şifreleme** ile yapılır: her cihazın bir çift anahtarı
olur, özel anahtarla imza atar, herkes açık anahtarla doğrular.

---


## 24. Modern Tkinter Teması (ttk)

### Problem

Tkinter'ın varsayılan widget'ları Windows 95 tarzıdır: 3B kabartmalı
kenarlar, gri butonlar, geniş kaydırma çubukları. Modern bir arayüz için
**ttk (themed tkinter)** kullanılır.

### Çözüm

```python
from tkinter import ttk

style = ttk.Style(root)
style.theme_use("clam")        # en özelleştirilebilir taban tema

style.configure("Accent.TButton",
    background=COLORS["accent"],
    foreground="#FFFFFF",
    borderwidth=0,             # kabartma yok
    relief="flat",             # düz
    focusthickness=0,
    padding=(18, 8))

style.map("Accent.TButton",
    background=[("active", COLORS["accent_dark"])])
```

**Öğrenci sorusu:** "ttk'nin `tk`dan farkı ne?"
`ttk` widget'lar "stil" (style) ile çizilir - görünüm merkezi olarak
tanımlanır. `tk` widget'lar ise her birine ayrı `bg`, `fg`, `relief`
parametreleri verilir. Tema değiştirmek için ttk çok daha kolaydır.

**Öğrenci sorusu:** "Neden `clam` teması?"
Tk 8.5'te `clam` Windows'un klasik temasını düzleştirir. Diğer temalar
(alt, vista, x11) platforma özgüdür ve özelleştirilemez.

### Düz Giriş Alanı

Varsayılan `tk.Entry` 3B çerçeve kullanır (90'lar). Modern görünüm:

```python
style.configure("Modern.TEntry",
    fieldbackground=COLORS["input_bg"],
    borderwidth=0,
    lightcolor=COLORS["input_bg"],
    darkcolor=COLORS["input_bg"],   # kenar rengi = zemin rengi
    insertcolor=COLORS["text"],
    padding=(10, 8))
```

`lightcolor` ve `darkcolor` alanlarını zemin rengiyle aynı yaparak
kabartma efektini kaldırıyoruz.

---

## 25. Koyu Tema

### Tema Paletleri

```python
COLORS_LIGHT = {
    "background": "#F0F2F5", "sidebar": "#FFFFFF",
    "accent": "#25D366", "text": "#111B21", ...
}

COLORS_DARK = {
    "background": "#111B21", "sidebar": "#202C33",
    "accent": "#00A884", "text": "#E9EDEF", ...
}

COLORS = dict(COLORS_LIGHT)   # aktif palet
```

### Tema Değiştirme

```python
def set_theme(name):
    if name == "dark":
        config.COLORS.clear()
        config.COLORS.update(config.COLORS_DARK)
    else:
        config.COLORS.clear()
        config.COLORS.update(config.COLORS_LIGHT)
```

**Önemli detay:** `clear()` + `update()` kullanıyoruz, `=` değil. Çünkü
modüller `from config import COLORS` ile **referans** alıyor. `COLORS = {...}`
yeni bir sözlük oluştururdu ve eski referanslar eski palette kalırdı.

**Öğrenci sorusu:** "Neden `clear/update` kullanıyoruz?"
Python'da sözlükler değişkenlerle referans alınır. `COLORS = yeni` yapmak
o sözlüğe işaret eden tüm referansları eskisinde bırakır. `clear()` +
`update()` **aynı nesneyi** değiştirir - tüm referanslar güncellenir.

### Ne Zaman Değiştirilir?

Tema **açılış ekranında** seçilir. Çünkü çalışma zamanında değiştirmek
için tüm widget'ların yeniden oluşturulması gerekir (Tkinter'da renkler
çalışma zamanında değiştirilebilir ama kalıcı değildir).

**Öğrenci sorusu:** "Çalışma zamanında neden değiştiremiyoruz?"
Değiştirebiliriz ama her widget'ın `bg`/`fg` değerini elle güncellemek
gerekir. Alternatif: uygulamayı yeniden başlatmak.

---


## 26. Tkinter Canvas ve Kaydırma (Scrollable Frame)

### Problem

Canvas içine yerleştirilen bir Frame, içerik büyüdükçe Canvas'ın dışına
taşar. Kaydırma çubuğu eklemek için "scrollregion" ayarlanmalıdır.

### Üç Kural (ve Bunları Öğrenmenin Bedeli)

**Kural 1: Frame'in yüksekliği elle atanır (propagate kapalı)**

```python
self.msg_container = tk.Frame(self.canvas, height=0)
self.msg_container.pack_propagate(False)
```

**Neden?** Canvas item'ına yükseklik verilirse widget zorlanır, propagate
kapanır ve doğal yükseklik **donup kalır**. Mesajlar üst üste binmeye başlar.

**Kural 2: Yükseklik çocuklardan elle hesaplanır**

```python
def _content_height(self):
    children = self.msg_container.winfo_children()
    if not children:
        return 0
    last = children[-1]
    return last.winfo_y() + last.winfo_height() + 2
```

Son çocuğun gerçek alt kenarı tüm pad değerlerini hesaba katar.

**Kural 3: Sonsuz döngüye karşı koruma bayrağı**

```python
if self._updating:
    return
self._updating = True
try:
    ...
finally:
    self._updating = False
```

Item'ın yüksekliği değişince `<Configure>` olayı tetiklenir, o da
`_update_scrollregion` çağırır, o da yüksekliği değiştirir... **sonsuz
döngü!** Bayrak bunu keser.

### Bir Başka Tuzak: Scrollregion Ortalama

Scrollregion canvas'tan küçükse Tk onu canvas'ın **ortasına** yerleştirir.
"En alta kaydır" çalışması görünümü boşluğa taşır ve mesajlar kaybolur.

**Çözüm:** Item yüksekliğini en az canvas yüksekliğinde tut.

```python
canvas_height = self.canvas.winfo_height()
if canvas_height > 1 and height < canvas_height:
    height = canvas_height
```

**Öğrenci sorusu:** "Tk neden böyle yapıyor?"
Canvas, içerik küçükse onu ortalamakla küçük resimleri bir "portre"
gibi gösterir. Ama scrollable bir sohbet için istemiyoruz.

---

## 27. Örnek Sınav Soruları

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
9. Bilgisayarında VirtualBox kuruluysa neden cihazlar birbirini göremeyebilir?
   (İpucu: arayüz seçimi)
10. `192.168.100.17` IP'li cihazın subnet broadcast adresi nedir? Hesaplayınız.
11. "GRP:sinif" hedefli bir mesaj, gruba üye olmayan bir cihaz tarafından
    neden ekranda gösterilmez?
12. Bir mesajı sildiğinde neden `msg_id` gerekir, index yeterli olmaz mu?
13. `ensure_ascii=False` yazmazsan Türkçe karakterler nasıl görünür?
14. `history.json` dosyası bozuksa uygulama ne yapar? Neden çökmemeli?
15. `grid` ve `pack` arasındaki temel fark nedir? Bu projede hangisi
    kullanıldı ve neden?
16. Bir öğrenci, admin olmadığı halde "delete_group" paketi gönderirse
    grup silinir mi? Neden?
17. Gizli grupta davet kodu doğruysa neden yine de yönetici onayı isteniyor?
18. Anket paketini alan cihaz neden onu yeniden göndermemeli? Bu hatayı
    yapsan ne olur?
19. Yönetici gruptan ayrılırsa ne olur? Yeni yönetici nasıl belirlenir?
20. El kaldırma neden mesaja bağlı, sohbete değil?
21. 6 haneli davet kodu kaç farklı kombinasyon üretir? Hesaplayınız.
22. Gizli modda presence paketi gönderiliyor mu? Neden?
26. Pairing kodu 6 haneli ise brute-force saldırısı ne kadar sürer?
27. Zamanlı mesaj kuyruğu uygulama kapanınca ne olur?
28. Oturum kaydı ile Wireshark arasındaki fark nedir?
29. `flush()` neden çağrılıyor? Çağırmasak ne olur?
30. Gizli mod gerçek gizlilik sağlar mı? Neden?
34. `ttk` ile `tk` arasındaki fark nedir? Tema değiştirmeyi kolaylaştıran nedir?
35. Neden `ttk.Style().theme_use("clam")` kullanıyoruz?
36. `COLORS = yeni_sözlük` yerine `COLORS.clear(); COLORS.update(...)` yazıyoruz. Neden?
40. Canvas'ta scrollable frame yaparken `pack_propagate(False)` neden şart?
41. Scrollregion canvas'tan küçükse ne olur ve nasıl önlenir?
42. `<Configure>` olayı neden sonsuz döngüye yol açıyor, nasıl engelleniyor?
