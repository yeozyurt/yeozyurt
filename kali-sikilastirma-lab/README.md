# Kali Linux – Sistem Sıkılaştırma Uygulama Labı (MSG203 / 11. Hafta)

11. Hafta "Sistem Sıkılaştırma" sunumunun uygulamalı karşılığı. Öğrenci
bilerek zayıflatılmış bir Kali VM'ini, derste anlatılan **7 alan** boyunca
(kullanıcı, servis, ağ, izin/SUID, güncelleme, loglama, SSH) sıkılaştırır ve
otomatik bir denetleyici ile 100 üzerinden puanlanır.

## Dosyalar
| Dosya | Kim çalıştırır | Ne yapar |
|---|---|---|
| `LAB-FOYU.md` | Öğrenci | Adım adım lab föyü (TARA→UYGULA→DENETLE) |
| `hazirla.sh` | Öğrenci (1 kez) | Sistemi bilerek zayıflatır (başlangıç durumu) |
| `kontrol.sh` | Öğrenci | Sıkılaştırmayı denetler, 100 üzerinden puanlar |
| `cozum.sh` | Eğitmen | Tüm adımları uygulayan referans çözüm |

## Hızlı başlangıç
```bash
sudo bash hazirla.sh          # sistemi zayıflat
sudo bash kontrol.sh          # başlangıç puanı (düşük olmalı)
# ... LAB-FOYU.md adımlarını uygula ...
sudo bash kontrol.sh          # puanın 90+ olmalı
```

## Gereksinimler
- Kali Linux **sanal makinesi** (snapshot alınmış)
- Paketler: `lynis nmap auditd libpam-pwquality ufw`

## ⚠️ Güvenlik
- Yalnızca **kendi lab VM'inizde** çalıştırın; `hazirla.sh` sistemi kasıtlı
  zayıflatır. Önce **snapshot** alın.
- SSH/PAM adımlarında kendinizi kilitlememek için ayrı bir terminalde
  `sudo -i` root oturumu açık tutun.
- Bu lab **defansif** bir çalışmadır: amaç mevcut sistemi sertleştirmektir.
