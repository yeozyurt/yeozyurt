# Türkiye'de Kuantum Sonrası TLS Hazırlığı – Ölçüm Aracı

Veri İletişimi dersi projesi için ölçüm ve analiz araçları.

| Dosya | Görevi |
|---|---|
| `olcum.py` | Her siteye bağlanıp TLS ve ağ metriklerini `sonuclar.csv`'ye yazar |
| `analiz.py` | Sonuçları sektör bazında özetler, tablo ve grafik üretir |
| `siteler.csv` | Başlangıç site listesi (130 site, 4 sektör) – genişletilecek |
| `Dockerfile` | OpenSSL 3.5 hazır ortam (OpenSSL kurmakla uğraşmamak için) |

## 1. Kurulum

Tek gereksinim **OpenSSL 3.5 veya üzeri** ve Python 3.8+. Kontrol:

```bash
openssl version                                  # 3.5.x veya üzeri olmalı
openssl list -tls-groups | grep X25519MLKEM768   # bir satır çıkmalı
```

Sisteminize göre seçenekler:

- **Docker (her sistemde en kolayı, Windows dahil):**
  ```bash
  docker build -t pqtls .
  docker run --rm -v "$PWD/veri:/veri" pqtls --sinir 20     # pilot
  docker run --rm -v "$PWD/veri:/veri" pqtls                # tam ölçüm
  ```
- **macOS:** `brew install openssl@3 python` → `--openssl $(brew --prefix openssl@3)/bin/openssl`
- **Ubuntu 25.10+ / Fedora 42+:** sistem OpenSSL'i yeterli.
- **Ubuntu 24.04 / Windows WSL:** sistem OpenSSL'i 3.0'dır; Docker'ı kullanın.

## 2. Pilot ölçüm (önce bunu yapın)

```bash
python3 olcum.py --girdi siteler.csv --cikti pilot.csv --sinir 20
```

Çıktıda `durum` sütununun çoğunlukla `tamam` olduğunu kontrol edin. `dns_hatasi`
çıkan alan adları listede yanlış yazılmıştır, düzeltin.

## 3. Tam ölçüm

```bash
python3 olcum.py --girdi siteler.csv --cikti sonuclar_1.csv --tekrar 5 --bekleme 1.5
```

- 130 site yaklaşık 40–60 dakika sürer (site başına ~15 bağlantı + bekleme).
- Yarıda keserseniz aynı komutla devam eder; ölçülmüş siteler atlanır.
- Tutarlılık için **farklı bir gün** `sonuclar_2.csv` adıyla tekrarlayın.
- Ölçümü hep aynı ağdan (ör. ev internetiniz) yapın ve raporda belirtin.

## 4. Analiz

```bash
python3 analiz.py --girdi sonuclar_1.csv --cikti-klasoru rapor
```

`rapor/` altında `ozet_sektor.csv`, makaleye aktarılabilir `ozet.md` tabloları ve
grafikler (`sektor_hazirlik.png`, `cdn_etkisi.png`) oluşur. Grafikler için
`pip install matplotlib` gerekir.

## Ölçülen sütunlar

| Sütun | Anlamı |
|---|---|
| `tcp_rtt_ms` | TCP bağlantı kurma süresi (≈ 1 RTT), 5 ölçümün medyanı |
| `tls_surumu`, `tls13_destek`, `tls12_kabul` | Desteklenen TLS sürümleri |
| `secilen_grup` | Tarayıcı gibi PQ + klasik teklif edildiğinde sunucunun seçtiği grup |
| `hrr_var` | Sunucu HelloRetryRequest istedi mi (+1 RTT maliyet) |
| `pq_destek` | Yalnız X25519MLKEM768 ile TLS 1.3 bağlantısı kurulabildi mi |
| `tarayici_clienthello_bayt` / `_segment_tahmini` | İki anahtar paylı (Chrome benzeri) ClientHello boyutu ve MSS=1460 ile kaç TCP segmentine sığdığı |
| `pq_*` / `klasik_*` | Hibrit ve klasik el sıkışmanın süresi, ClientHello/ServerHello boyutu, toplam okunan/yazılan bayt |
| `sertifika_*` | Sertifika anahtar türü, uzunluğu ve imza algoritması |
| `http3_ilani` | `Alt-Svc` başlığında h3 ilan ediliyor mu |
| `cdn` | Yanıt başlıklarından CDN tespiti (Cloudflare, Akamai, CloudFront…) |

**Süre ölçümü hakkında:** Süreler `openssl s_client`'ın duvar saati süresidir ve
işlem başlatma yükünü (birkaç ms) içerir. Bu yük iki modda da aynı olduğundan
*hibrit – klasik farkı* güvenilirdir; makalede mutlak değer yerine farkı yorumlayın.

## Wireshark ile görsel kanıt (makale ve sunum için)

1. Wireshark'ı açıp filtreye `tls.handshake.type == 1 || tls.handshake.type == 2` yazın.
2. Aynı siteye bir klasik, bir hibrit bağlantı kurun:
   ```bash
   openssl s_client -connect www.ornek.com.tr:443 -groups X25519 < /dev/null
   openssl s_client -connect www.ornek.com.tr:443 -groups '*X25519MLKEM768:*X25519' < /dev/null
   ```
3. Klasik ClientHello tek pakette, hibrit ClientHello ise iki TCP segmentinde görünür
   ("[2 Reassembled TCP Segments]"). Bu ekran görüntülerini makaleye ekleyin.

## Etik ilkeler

- Her siteye normal bir ziyaretçi gibi bağlanılır; tarama, port taraması veya güvenlik testi yapılmaz.
- Siteler arası `--bekleme` süresini 1 saniyenin altına indirmeyin.
- Yayında kurum adı vermeyin; sonuçları sektör bazında sunun.
