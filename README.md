# ZeroChat - LAN Sohbet Uygulaması

İnternet gerektirmeden, aynı yerel ağda çalışan WhatsApp benzeri sohbet uygulaması.
Öğrenciler için ağ kavramlarını (IP, MAC, port, broadcast) öğretmek amacıyla tasarlandı.

## Özellikler

- **Sunucusuz mimari** - Her cihaz hem gönderen hem alıcıdır
- **Otomatik cihaz keşfi** - 3 saniyede bir ağ taranır, bulunan cihazlar listeye eklenir
- **MAC tabanlı kimlik** - Her cihaz MAC adresiyle tanınır (isim çakışması olmaz)
- **IP + MAC gösterimi** - Kontak listesinde her cihazın IP ve MAC adresi görünür
- **Özel mesajlaşma** - Mesajlar sadece hedef cihaza gösterilir
- **Çevrimiçi/çevrimdışı durumu** - Yeşil nokta (çevrimiçi) / gri nokta (çevrimdışı)
- **Grup sohbeti** - "Tüm Ağ" veya adlandırılmış gruplar (GRP:sinif)
- **Gizli mod** - 👻 ikonu ile cihazın ağda görünmez olması
- **Zamanlı mesaj** - ⏰ ile ileriye dönük mesaj gönderme
- **Oturum kaydı** - `sessions/` klasörüne Wireshark benzeri paket kaydı
- **Pairing kodu** - 🔗 ile sunucusuz cihaz eşleştirme
- **Dosya paylaşımı** - 📎 ile resim/PDF/video gönderme (parçalı + SHA256)
- **Grup yönetimi** - Admin belirler, üye çıkarır, grubu siler
- **Gizli / herkese açık gruplar** - Davet kodu ile gizli gruplar
- **Canlı anket** - Öğretmen anket açar, sonuçlar anında görünür
- **Eller kaldırma** - Mesaja sağ tıkla, el kaldır
- **Mesaj geçmişi** - Sohbetler `history.json` dosyasına kaydedilir, açılışta geri yüklenir
- **Mesaj silme / düzenleme** - Sağ tık menüsü ile
- **Kaydırılabilir mesaj alanı** - Çok fazla mesajda ekran bozulmaz
- **Türkçe arayüz** - Öğrenciler için sade ve anlaşılır

## Kurulum

### Gereksinimler
- Python 3.8 veya üzeri
- Tüm bilgisayarlar aynı switch'e / WLAN'a bağlı
- Windows Firewall'da Python'a izin verilmiş

### Adımlar

1. Bu klasörü her bilgisayara kopyalayın
2. Her bilgisayarda uygulamayı çalıştırın:

```bash
python main.py
```

3. Kullanıcı adınızı girin ve "Başla" butonuna tıklayın
4. Cihazınızın MAC adresi giriş ekranında görünür - bu sizin kimliğinizdir

## Kullanım

1. Sol panelde bulunan cihazlar otomatik olarak listelenir (3 saniyede bir tarama)
2. Bir cihaza tıklayarak sohbeti açın
3. Mesaj yazın ve Enter'a basın veya "Gönder" butonuna tıklayın

Cihaz listede yoksa "+ Yeni Sohbet" ile MAC adresini elle girebilirsiniz.

## Grup Sohbeti

Sol panelde **GRUPLAR** bölümü vardır:

- **Tüm Ağ** - Herkese birden gönderim (her zaman mevcut)
- **+ Oluştur** ile yeni grup, **+ Katıl** ile mevcut gruba katılım

Aynı grup adını kullanan herkes aynı gruba katılır. Grup üyeliği ağ üzerinden
bildirilir, üye sayısı listede görünür.

### Grup Yönetimi (Admin)

Grubu **kuran kişi yöneticidir** (★ rozeti). Yönetici, grup adının yanındaki
**⋯** butonuna basarak yönetim penceresini açar:

| Yetki | Yönetici | Üye |
|-------|:--------:|:----:|
| Grubu silme | ✓ | ✗ |
| Üye çıkarma | ✓ | ✗ |
| Görünürlük değiştirme | ✓ | ✗ |
| Davet kodu görme | ✓ | ✗ |

Yönetici ayrılırsa ve üye kalırsa, bir sonraki üye yeni yönetici olur.

### Gizli / Herkese Açık Gruplar

Grup oluştururken erişim seçilir:

- **Herkese açık** - Herkes "Gruba Katıl" ile direkt girer
- **Gizli** - 6 haneli davet kodu gerekir (örn. `3TKKFK`)

Gizli grupta katılım şöyle işler:
1. Öğrenci kodu girer → gruba katılma **isteği** yöneticinin listesine düşer
2. Yönetici "Kabul" der → öğrenci gruba katılır

Yönetici penceresinde bekleyen istekler listelenir, her biri için
**Kabul / Reddet** butonu vardır.

## Canlı Anket

Sağ paneldeki **📊 Anket** butonuna basın:

1. Soruyu ve seçenekleri girin (her seçenek ayrı satırda)
2. Anket açılır ve gruba yayınlanır
3. Herkes oy verir, sonuçlar **anında** güncellenir
4. Anketi açan kişi "Anketi Kapat" diyerek bitirir

Oy veren kişinin seçtği seçenek yeşil vurgulanır. Sonuçlar yüzde ve oy
sayısı olarak gösterilir.

## Eller Kaldırma

Bir mesaja **sağ tıklayın** → "✋ El Kaldır". Mesajın altında el kaldıranların
listesi görünür. Tekrar sağ tıklayıp "Elini İndir" ile kaldırılabilir.

Öğretmen sınıfa bir soru sorduğunda öğrenciler el kaldırır, öğretmen kimin
takıldığını anında görür.

## Gizli Mod (Stealth)

Sol paneldeki **👻** ikonuna basın. Gizli mod açıkken cihazınız **presence
paketi göndermez**, böylece ağ taramasında görünmezsiniz.

- Karşı taraf sizinle konuşmaya başlarsa cihazınız tanınır ve listede görünür
- Gizli cihazlar listede `👻` ikonuyla işaretlenir (eğitim için görünür)
- `config.py`'de `STEALTH_HIDE_COMPLETELY = True` yaparsanız tamamen gizlenir

## Zamanlı Mesaj

Yazma alanının yanındaki **⏰** ikonuna basın. Mesajı yazıp kaç dakika sonra
gönderileceğini seçin. Kuyruk her saniye kontrol edilir, zamanı gelince
mesaj gönderilir.

## Oturum Kaydı (Wireshark Alternatifi)

Uygulama açıldığından itibaren tüm gönderilen ve alınan paketler
`sessions/session_YYYYMMDD_HHMMSS.log` dosyasına yazılır.

Format: **JSON Lines** (her satır bir paket)
```json
{"t": 1729372845.123, "time": "14:32:05", "dir": "OUT", "type": "message", "size": 142, "user_id": "AA:11:...", "content": "Merhaba"}
```

`dir` alanı `OUT` (gönderilen) veya `IN` (alınan) olur. Dosyayı bir metin
editörü veya `session_log.py` ile inceleyebilirsiniz.

**Wireshark'tan farkı:** Wireshark ağ seviyesinde (IP/UDP başlıkları) yakalar,
ZeroChat uygulama seviyesinde (JSON içeriği) kaydeder. Daha okunabilir ama
alt seviye detay yoktur.

## Pairing Kodu (Sunurusuz Eşleştirme)

Sol paneldeki **🔗** ikonuna basın:

1. **Kodunu göster** - 6 haneli kodunuz (`NNGL42`) ekranda görünür, karşı taraf
   girerek size bağlanabilir
2. **Kod ile bağlan** - arkadaşınızın kodunu girin, bağlanma isteği gider
3. Karşı taraf "Kabul" derse eşleşme tamamlanır

Kod 5 dakika geçerlidir. **Güvenlik notu:** 6 haneli kod tahmin edilebilir -
gerçek sistemlerde daha uzun, zaman aşımlı ve tek kullanımlık kodlar kullanılır.

## Dosya Paylaşımı

Yazma alanının yanındaki **📎** ikonuyla dosya seçin ve gönderin.

**Nasıl çalışır:**
1. Dosya okunur, SHA256 hash'i hesaplanır
2. 800 bayt parçalara bölünür, base64 ile metne çevrilir
3. Her parça ayrı UDP paketi olarak gönderilir
4. Alıcı parçaları birleştirir, hash'i doğrular
5. Eksik parça varsa tekrar istenir (NACK)
6. Dosya `downloads/` klasörüne yazılır

**Sınırlar:** Maks 5 MB, aynı anda 1 dosya.

## Mesaj Silme / Düzenleme

Herhangi bir mesaja **sağ tıklayın**:

| Seçenek | Ne yapar |
|---------|----------|
| **Kopyala** | Panoya kopyalar |
| **Düzenle** | Mesajı düzenleme moduna alır (buton "Kaydet" olur) |
| **Sil** | Onay ister, mesajı siler |

Silme ve düzenleme karşı tarafa da bildirilir, ekranlar senkron kalır.

## Mesaj Geçmişi

Uygulama kapanırken sohbetler `history.json` dosyasına yazılır. Uygulama
açıldığında otomatik geri yüklenir.

Dosya formatı (JSON):
```json
{
  "BB:66:77:88:99:AA": [
    [false, {"type": "message", "msg_id": "a1b2c3d4", "content": "Merhaba", ...}],
    [true,  {"type": "message", "msg_id": "e5f6g7h8", "content": "Selam", ...}]
  ]
}
```

`[is_outgoing, mesaj]` — `true` = sizin gönderdiğiniz, `false` = karşı tarafın.

## Dosya Yapısı

```
ZeroChat/
├── main.py              # Giriş ekranı
├── app.py               # Ana uygulama (GUI + ağ yönetimi)
├── config.py            # Port, aralık, grup ve renk tanımları
├── storage.py           # Mesaj geçmişi (JSON dosya I/O)
├── session_log.py       # Oturum kaydı (paket analizi)
├── gui/
│   ├── sidebar.py       # Sol panel - gruplar, cihaz listesi, arama
│   ├── chat_area.py     # Sağ panel - mesaj alanı (kaydırılabilir)
│   ├── message_bubble.py # Mesaj balonu (sağ tık menüsü)
│   ├── poll_card.py     # Anket kartı
│   ├── file_card.py     # Dosya kartı (ilerleme çubuğu)
│   └── pairing_dialog.py # Eşleştirme penceresi
├── network/
│   ├── socket.py        # UDP socket, IP/MAC tespiti, heartbeat
│   └── packet.py        # JSON paket oluşturma/çözümleme
├── history.json         # Otomatik oluşur (geçmiş dosyası)
├── sessions/            # Otomatik oluşur (oturum kayıtları)
├── downloads/           # Otomatik oluşur (indirilen dosyalar)
├── README.md
└── AG_ANLATIMI.md       # Ağ kavramları rehberi (öğrenciler için)
```

## Ağ Ayarları

`config.py` dosyasından değiştirilebilir:

| Ayar | Varsayılan | Açıklama |
|------|-----------|----------|
| `UDP_PORT` | 5000 | Dinleme portu |
| `BROADCAST_ADDRESS` | `None` | `None` = otomatik subnet broadcast. `"255.255.255.255"` = sınırlı broadcast |
| `SEND_TO_LIMITED_BROADCAST` | `False` | Subnet broadcast'un yanında sınırlı broadcast'a da gönder |
| `HEARTBEAT_INTERVAL` | 3 | Tarama aralığı (saniye) |
| `OFFLINE_TIMEOUT` | 12 | Çevrimdışı sayılma süresi (saniye) |
| `GROUP_ALL` | `"ALL"` | Tüm ağa gönderim kimliği |
| `GROUP_PREFIX` | `"GRP:"` | Özel grup kimliği öneki |
| `GROUP_PUBLIC` | `"public"` | Herkese açık grup |
| `GROUP_PRIVATE` | `"private"` | Gizli grup (davet kodu ile) |
| `INVITE_CODE_LENGTH` | 6 | Davet kodu uzunluğu |
| `POLL_MIN_OPTIONS` | 2 | Ankette asgari seçenek sayısı |
| `POLL_MAX_OPTIONS` | 6 | Ankette azami seçenek sayısı |
| `HISTORY_FILE` | `"history.json"` | Geçmiş dosyası adı |
| `HISTORY_SAVE_ON_CLOSE` | `True` | Kapanırken geçmişi kaydet |
| `STEALTH_HIDE_COMPLETELY` | `False` | Gizli cihazları tamamen gizle |
| `SESSION_LOG_ENABLED` | `True` | Oturum kaydı açık mı |
| `SESSION_LOG_DIR` | `"sessions"` | Oturum kayıtları klasörü |
| `SCHEDULE_CHECK_INTERVAL` | 1 | Zamanlı mesaj kontrol aralığı (sn) |
| `PAIR_CODE_LENGTH` | 6 | Pairing kodu uzunluğu |
| `PAIR_CODE_TIMEOUT` | 300 | Pairing kodu geçerlilik süresi (sn) |
| `FILE_MAX_SIZE` | 5 MB | Maks dosya boyutu |
| `FILE_CHUNK_SIZE` | 800 | Parça boyutu (bayt) |
| `DOWNLOAD_DIR` | `"downloads"` | İndirilen dosyaların klasörü |

## Arayüz Seçimi (Önemli)

Bilgisayarınızda birden fazla ağ arayüzü olabilir (Wi-Fi, Ethernet, VirtualBox,
Hyper-V, Docker, WSL). Uygulama **gerçek ağ adaptörünü** otomatik seçer:

1. Default Gateway'i olan + sanal olmayan adaptör
2. Sanal olmayan adaptör (sadece switch'e bağlıysanız)
3. Diğerleri

Sanal adaptörler şu yollarla tespit edilir:
- Adaptör adı (`VirtualBox`, `Hyper-V`, `VMware`, `Docker`...)
- MAC ön eki (`0A-00-27` = VirtualBox, `00-15-5D` = Hyper-V)
- IP aralığı (`192.168.56.x` = VirtualBox varsayılan ağı)

Broadcast paketleri **subnet broadcast adresine** gönderilir
(ör. `192.168.100.255`), böylece doğru arayüzden çıkar.

Üst çubukta seçilen arayüzü görebilirsiniz: `Yayın: 192.168.100.255`

## Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| Cihazlar görünmüyor | Firewall'da Python'a izin verin (Özel ağlar için) |
| Yanlış IP görünüyor | Üst çubuktaki `Yayın:` adresine bakın, `192.168.x.255` olmalı |
| Broadcast engellendi | `netsh advfirewall firewall add rule name="ZeroChat" dir=in action=allow protocol=UDP localport=5000` |
| "Address already in use" | Başka bir ZeroChat örneği çalışıyor, kapatın |
| Farklı subnet | `ipconfig` ile IP'leri karşılaştırın, aynı `192.168.x.x` olmalı |
| Mesajlar ulaşmıyor | Ağ yöneticisinde "AP Isolation" kapalı mı kontrol edin |
