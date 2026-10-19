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

## Dosya Yapısı

```
ZeroChat/
├── main.py              # Giriş ekranı
├── app.py               # Ana uygulama (GUI + ağ yönetimi)
├── config.py            # Port, aralık, renk tanımları
├── gui/
│   ├── sidebar.py       # Sol panel - cihaz listesi, arama
│   ├── chat_area.py     # Sağ panel - mesaj alanı
│   └── message_bubble.py # Mesaj balonu
├── network/
│   ├── socket.py        # UDP socket, IP/MAC tespiti, heartbeat
│   └── packet.py        # JSON paket oluşturma/çözümleme
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
