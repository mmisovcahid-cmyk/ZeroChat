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
- **Modern tema** - ttk (themed tkinter) ile düz, çağdaş arayüz
- **Açık / koyu tema** - Giriş ekranından seçilir
- **Grup yönetimi** - Admin belirler, üye çıkarır, grubu siler
- **Gizli / herkese açık gruplar** - Davet kodu ile gizli gruplar
- **Canlı anket** - Öğretmen anket açar, sonuçlar anında görünür
- **Eller kaldırma** - Mesaja sağ tıkla, el kaldır
- **Mesaj geçmişi** - Sohbetler `history.json` dosyasına kaydedilir, açılışta geri yüklenir
- **Otomatik kayıt** - Geçmiş 5 dakikada bir otomatik kaydedilir (çökmede veri kaybı olmaz)
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

Grup adını kullanan herkes aynı gruba katılır. Grup **ağa duyurulur**:
oluşturan kişi `create` paketi gönderir, diğer cihazlar grubu otomatik
listelerine ekler. Üyelik ve üye sayısı da ağ üzerinden bildirilir.

### Gruba Katılma

- **Grup adı** yazarsanız (ör. `sinif`) → herkese açık gruba katılırsınız
- **Davet kodu** yazarsanız (6 karakter, ör. `3TKKFK`) → gizli grup için
  yöneticiye katılma isteği gönderilir

Grubu daha önce hiç duyurmamış olsanız bile katılabilirsiniz: sistem grubu
yerel listenize ekler ve ağa katılma bildiriminizi gönderir.

### Grup Yönetimi (Admin)

Grubu **kuran kişi yöneticidir** (★ rozeti). Yönetici, grup adının yanındaki
**⋯** butonuna basarak yönetim penceresini açar:

| Yetki | Yönetici | Üye |
|-------|:--------:|:----:|
| Grubu silme | ✓ | ✗ |
| Üye çıkarma | ✓ | ✗ |
| Görünürlük değiştirme | ✓ | ✗ |
| Davet kodu görme | ✓ | ✗ |

Yönetici ayrılırsa ve üye kalırsa, bir sonraki üye yeni yönetici olur
(`transfer_admin` paketi ile ağa bildirilir).

### Gizli / Herkese Açık Gruplar

Grup oluştururken erişim seçilir:

- **Herkese açık** - Herkes "Gruba Katıl" ile direkt girer
- **Gizli** - 6 haneli davet kodu gerekir (örn. `3TKKFK`)

Gizli grupta katılım şöyle işler:
1. Öğrenci kodu girer → gruba katılma **isteği** yöneticinin listesine düşer
2. Yönetici "Kabul" der → öğrenci gruba katılır

Kod yanlışsa istek reddedilir ve öğrenciye bilgi verilir.

> **Dikkat:** Davet kodu yalnızca yöneticide görünür, üyelerde `••••••`
> olarak maskelenir. Ancak ağ broadcast ile çalıştığı için kod, ağdaki
> diğer cihazlar tarafından paket yakalama ile görülebilir. Bu bir
> eğitim projesidir, gerçek güvenlik sağlamaz.

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

- Karşı taraf size mesaj gönderirse cihazınız tanınır ve listede görünür
- Gizli mod açıldığı anda bir "hidden" duyurusu **gönderilmez** (cihazı
  elem vermek için). Bu yüzden karşı taraf sizi 12 saniye sonra "çevrimdışı"
  olarak görür
- `config.py` ayarları:
  - `STEALTH_ANNOUNCE = True` → gizli moda girerken bir kez "hidden" duyurusu
    gönderilir, karşı taraf listede `👻` ikonuyla gösterir (eğitim amaçlı,
    ama cihazı yine de ele verir)
  - `STEALTH_HIDE_COMPLETELY = True` → "hidden" duyurusu alan cihaz listede
    hiç görünmez, sadece sayaçta tutulur

## Zamanlı Mesaj

Yazma alanının yanındaki **⏰** ikonuna basın. Mesajı yazıp kaç dakika sonra
gönderileceğini seçin. Kuyruk her saniye kontrol edilir, zamanı gelince
mesaj gönderilir.

Aynı pencerenin altında **zamanlanmış mesajlar** listesi görünür. Buradan
bekleyen mesajı **İptal** edebilirsiniz. Zamanlanan mesaj da normal mesaj
gibi geçmişe yazılır ve karşı tarafta düzenlenebilir/silinebilir.

## Oturum Kaydı (Wireshark Alternatifi)

Uygulama açıldığından itibaren tüm gönderilen ve alınan paketler
`sessions/session_YYYYMMDD_HHMMSS.log` dosyasına yazılır.

Format: **JSON Lines** (her satır bir paket)
```json
{"t": 1729372845.123, "time": "14:32:05", "dir": "OUT", "type": "message", "size": 142, "user_id": "AA:11:...", "content": "Merhaba"}
```

`dir` alanı `OUT` (gönderilen) veya `IN` (alınan) olur. Dosyayı bir metin
editörü veya `session_log.py` ile inceleyebilirsiniz:

```python
from session_log import list_sessions, read_session, analyze_session

for f in list_sessions():
    print(f["name"], f["size"], "byte")

entries = read_session("sessions/session_20261020_004431.log")
stats = analyze_session(entries)
print(stats["total"], stats["in"], stats["out"], stats["types"])
```

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


## Tema

Giriş ekranından **☀ Açık** veya **🌙 Koyu** seçilir. Seçiminiz
`settings.json` dosyasına kaydedilir, bir sonraki açılışta hatırlanır.

Arayüz üst çubuğundaki **"Arayüz: ... ▾"** yazısı ise hangi ağ arayüzünün
kullanıldığını gösterir ve tıklandığında arayüz değiştirme menüsünü açar.

Arayüz `ttk` (themed tkinter) kullanır. Tkinter'ın varsayılan widget'ları
Windows 95 tarzı kabartmalı görünür; `ttk.Style().theme_use("clam")` ile
özelleştirilerek düz ve modern bir görünüm elde edilir:
- Butonlar düz, köşesiz, hover'da koyulaşır
- Giriş alanlarında 3B çerçeve yerine sadece alt çizgi
- Kaydırma çubuğu ince ve renkli

## Mesaj Silme / Düzenleme

Bir mesaja **sağ tıklayın**:

| Seçenek | Ne yapar |
|---------|----------|
| **Kopyala** | Panoya kopyalar |
| **Düzenle** | Mesajı düzenleme moduna alır (buton "Kaydet" olur) |
| **Sil** | Onay ister, mesajı siler |

**Düzenle** ve **Sil** yalnızca **kendi gönderdiğiniz** mesajlarda görünür.
Başkasının mesajını değiştiremezsiniz.

Silme ve düzenleme karşı tarafa da bildirilir, ekranlar senkron kalır.

## Mesaj Geçmişi

Uygulama kapanırken sohbetler `history.json` dosyasına yazılır. Ayrıca
**her 5 dakikada bir otomatik** kaydedilir, böylece uygulama çökse bile
mesajlar kaybolmaz.

Dosya yolu **proje klasörüne göre** çözülür; uygulamayı hangi dizinden
başlatırsanız başlatın veriler aynı yerde durur. Yazma **atomiktir** (önce
geçici dosya, sonra taşıma) - uygulama yazma sırasında kapanırsa geçmiş
dosyası bozulmaz.

Uzun sohbetlerde dosyanın şişmemesi için her sohbette en fazla
`MAX_HISTORY_MESSAGES` (500) mesaj saklanır.

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
├── main.py              # Giriş ekranı (tema seçimi)
├── app.py               # Ana uygulama (GUI + ağ yönetimi)
├── config.py            # Port, aralık, grup, renk ve tema tanımları
├── storage.py           # Mesaj geçmişi (JSON dosya I/O)
├── session_log.py       # Oturum kaydı (paket analizi)
├── gui/
│   ├── theme.py         # Modern ttk teması + koyu mod
│   ├── sidebar.py       # Sol panel - gruplar, cihazlar, sınıf panosu
│   ├── chat_area.py     # Sağ panel - mesaj alanı (kaydırılabilir)
│   ├── message_bubble.py # Mesaj balonu (sağ tık menüsü)
│   ├── poll_card.py     # Anket kartı
│   └── pairing_dialog.py # Eşleştirme penceresi
├── network/
│   ├── socket.py        # UDP socket, IP/MAC tespiti, heartbeat
│   └── packet.py        # JSON paket oluşturma/çözümleme
├── history.json         # Otomatik oluşur (geçmiş dosyası)
├── sessions/            # Otomatik oluşur (oturum kayıtları)
├── README.md
└── AG_ANLATIMI.md       # Ağ kavramları rehberi (öğrenciler için)
```

## Ağ Ayarları

`config.py` dosyasından değiştirilebilir:

| Ayar | Varsayılan | Açıklama |
|------|-----------|----------|
| `UDP_PORT` | 5000 | Dinleme portu |
| `BUFFER_SIZE` | 65535 | Alınabilen en büyük UDP paketi (65535 = IPv4 max) |
| `MAX_MESSAGE_CHARS` | 4000 | Tek mesajın en fazla karakter sayısı |
| `BROADCAST_ADDRESS` | `None` | `None` = otomatik subnet broadcast. `"255.255.255.255"` = sınırlı broadcast |
| `SEND_TO_LIMITED_BROADCAST` | `False` | Subnet broadcast'un yanında sınırlı broadcast'a da gönder |
| `HEARTBEAT_INTERVAL` | 3 | Tarama aralığı (saniye) |
| `OFFLINE_TIMEOUT` | 12 | Çevrimdışı sayılma süresi (saniye) |
| `OFFLINE_CLEANUP_TIMEOUT` | 600 | Bu süre çevrimdışı kalan cihaz listeden silinir |
| `GROUP_ALL` | `"ALL"` | Tüm ağa gönderim kimliği |
| `GROUP_PREFIX` | `"GRP:"` | Özel grup kimliği öneki |
| `GROUP_PUBLIC` | `"public"` | Herkese açık grup |
| `GROUP_PRIVATE` | `"private"` | Gizli grup (davet kodu ile) |
| `INVITE_CODE_LENGTH` | 6 | Davet kodu uzunluğu |
| `POLL_MIN_OPTIONS` | 2 | Ankette asgari seçenek sayısı |
| `POLL_MAX_OPTIONS` | 6 | Ankette azami seçenek sayısı |
| `HISTORY_FILE` | `"history.json"` | Geçmiş dosyası adı (proje klasörüne göre çözülür) |
| `HISTORY_SAVE_ON_CLOSE` | `True` | Kapanırken geçmişi kaydet |
| `MAX_HISTORY_MESSAGES` | 500 | Sohbet başına saklanacak azami mesaj sayısı |
| `HISTORY_AUTOSAVE_INTERVAL` | 300 | Otomatik kayıt aralığı (saniye) |
| `STEALTH_HIDE_COMPLETELY` | `False` | "hidden" duyurusu alan cihazı tamamen gizle |
| `STEALTH_ANNOUNCE` | `False` | Gizli moda girerken "hidden" duyurusu gönder |
| `SESSION_LOG_ENABLED` | `True` | Oturum kaydı açık mı |
| `SESSION_LOG_DIR` | `"sessions"` | Oturum kayıtları klasörü (proje klasörüne göre çözülür) |
| `MAX_SESSION_FILES` | 30 | Tutulacak azami oturum dosyası sayısı (eski dosyalar silinir) |
| `SCHEDULE_CHECK_INTERVAL` | 1 | Zamanlı mesaj kontrol aralığı (sn) |
| `PAIR_CODE_LENGTH` | 6 | Pairing kodu uzunluğu |
| `PAIR_CODE_TIMEOUT` | 300 | Pairing kodu geçerlilik süresi (sn) |
| `THEME` | `"light"` | Aktif tema (`light` / `dark`) |

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

Üst çubuktaki **"Arayüz: ... ▾"** yazısına tıklayarak arayüzü **elle
değiştirebilirsiniz**. Seçiminiz `settings.json` dosyasına kaydedilir ve
bir sonraki açılışta hatırlanır. (Cihaz kimliğiniz olan MAC değişmez, sadece
gönderim yapılan IP ve yayın adresi değişir.)

Broadcast paketleri **subnet broadcast adresine** gönderilir
(ör. `192.168.100.255`), böylece doğru arayüzden çıkar.

Üst çubukta seçilen arayüzü görebilirsiniz: `Yayın: 192.168.100.255`

## Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| Cihazlar görünmüyor | Firewall'da Python'a izin verin (Özel ağlar için) |
| Yanlış IP görünüyor | Üst çubuktaki `Arayüz:` yazısına tıklayıp doğru arayüzü seçin |
| Broadcast engellendi | `netsh advfirewall firewall add rule name="ZeroChat" dir=in action=allow protocol=UDP localport=5000` |
| "Ağ Hatası" penceresi çıkıyor | Port 5000 başka bir ZeroChat örneği tarafından kullanılıyor, diğerini kapatın |
| Mesajlar ulaşmıyor | Ağ yöneticisinde "AP Isolation" kapalı mı kontrol edin |
| Uzun mesaj gönderilemiyor | En fazla `MAX_MESSAGE_CHARS` (4000) karakter. Daha uzunu gönderilmez |
| Kaydırma çalışmıyor (Linux) | Pencereye tıklayıp tekrar deneyin (odak kaydırma tuşunu yakalar) |
