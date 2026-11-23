# MSG203 – 11. Hafta UYGULAMA LABI
## Kali Linux üzerinde Sistem Sıkılaştırma (System Hardening)

| | |
|---|---|
| **Süre** | 2 ders saati (~90 dk) |
| **Ortam** | Kali Linux sanal makinesi (VirtualBox/VMware), kullanıcı: `kali` |
| **Araçlar** | `lynis`, `nmap`, `ss`, `systemctl`, `ufw`, `find`, `auditd`, `sshd`, `sysctl` |
| **Senaryo dosyaları** | `hazirla.sh` (sistemi zayıflatır), `kontrol.sh` (100 üzerinden puanlar), `cozum.sh` (eğitmen) |
| **Teslim** | Öncesi/sonrası `kontrol.sh` + `lynis` çıktısı ve kısa rapor (Bölüm 10) |

---

### Senaryo
"Kurulup unutulmuş" bir Linux sunucusunu devraldınız: eski bir personelin hesabı, açık FTP, kimsenin hatırlamadığı bir dosya paylaşım servisi, root'la SSH girişi ve hatalı dosya izinleri var. Göreviniz derste gördüğümüz **döngüyü** uygulamak:

> **TARA → UYGULA → DENETLE → TEKRAR ET**

Her alanda önce açığı **tespit edecek**, sonra **kapatacak**, sonra **doğrulayacaksınız**. Bu lab tamamen **savunma (defansif)** bir çalışmadır: mevcut sistemi sertleştirmeyi öğretir.

> ⚠️ **Uyarı:** Bu lab yalnızca kendi sanal makinenizde yapılır. Başlamadan **VM snapshot** alın. SSH ve PAM adımlarında ayrı bir terminalde **`sudo -i` ile root oturumu açık tutun**; yanlış ayarda kendinizi kilitlerseniz o oturumdan düzeltirsiniz.

---

## 0. Hazırlık (5 dk)

```bash
cd ~/kali-sikilastirma-lab
```
```bash
sudo apt update && sudo apt install -y lynis nmap auditd audispd-plugins libpam-pwquality ufw
```
```bash
sudo bash hazirla.sh
```

Başlangıç (sıkılaştırılmamış) durumunu kaydedin:

```bash
sudo bash kontrol.sh | tee once-kontrol.txt
```
```bash
sudo lynis audit system --quick | tee once-lynis.txt
```

📝 **Not alın:** `kontrol.sh` puanı = ____ / 100 &nbsp;&nbsp; Lynis Hardening Index = ____

---

## 1. TARA – Saldırı yüzeyini çıkar (15 dk)

> Slayt 4: *"Saldırı yüzeyi, bir saldırganın ulaşmak için deneyebileceği tüm noktaların toplamıdır."*

**1.1 Dinleyen portlar ve servisler**
```bash
sudo ss -tulpn
```
```bash
systemctl list-units --type=service --state=running
```
```bash
sudo nmap -sV -p- 127.0.0.1
```
> Burada **8080 (lab-paylasim)**, **21 (vsftpd/FTP)**, **80 (apache2)** gibi gereksiz dinleyicileri görmelisiniz.

**1.2 Açık FTP'nin verdiği bilgiyi gör (riski somutlaştır)**
```bash
curl -s http://127.0.0.1:8080/   # unutulmuş http.server tüm kök dizini listeliyor
```
> Not: `/srv/paylasim/notlar.txt` gibi dosyaların kimlik doğrulaması olmadan okunabildiğini görün. Açık servis = veri sızıntısı.

**1.3 Kullanıcı hesapları (giriş yapabilenler)**
```bash
awk -F: '$7 ~ /(bash|sh|zsh)$/ {print $1, $3, $7}' /etc/passwd
```
```bash
sudo awk -F: '$2 ~ /^\$/ {print $1}' /etc/shadow   # parolası set edilmiş hesaplar
```

**1.4 İzin ve SUID sorunları**
```bash
ls -l /etc/shadow            # 644 => herkes okuyabiliyor! (kritik)
```
```bash
sudo find / -xdev -perm -4000 -type f 2>/dev/null        # SUID ikilileri
```
```bash
sudo find / -xdev -type f -perm -002 ! -path "/proc/*" 2>/dev/null   # herkese yazılabilir
```
```bash
cat /etc/cron.d/lab-yedek && ls -l /opt/yedek/yedek.sh
```
> Dikkat: `root` her dakika `/opt/yedek/yedek.sh` çalıştırıyor ama dosya **777** (herkes yazabilir) → bu bir **yetki yükseltme** zinciridir.

📝 **Tablo 1'i doldurun:**

| # | Bulgu | Alan (1–7) | Risk (Yüksek/Orta/Düşük) |
|---|---|---|---|
| 1 | /etc/shadow 644 okunabilir | 4 | |
| 2 | 8080 açık http.server | 2 | |
| 3 | eskipersonel hesabı aktif | 1 | |
| … | | | |

---

## 2. UYGULA – Alan alan sıkılaştırma (45 dk)

Her alt bölümü uyguladıktan sonra **`sudo bash kontrol.sh`** çalıştırıp puanın arttığını görebilirsiniz.

### Alan 1 — Kullanıcı & kimlik doğrulama
```bash
# Gereksiz / eski hesabı kaldır
sudo userdel -r eskipersonel
```
```bash
# Root'u parolayla girişe kapat (yönetim: normal kullanıcı + sudo)
sudo passwd -l root
```
```bash
# Parola politikası (uzunluk & karmaşıklık)
sudo tee /etc/security/pwquality.conf >/dev/null <<'EOF'
minlen = 12
minclass = 3
dcredit = -1
ucredit = -1
lcredit = -1
retry = 3
EOF
```
```bash
# Hesap kilitleme (başarısız denemede)
sudo sed -i '/pam_faillock.so/d' /etc/pam.d/common-auth
sudo sed -i '0,/^auth/s//auth    required    pam_faillock.so preauth silent deny=5 unlock_time=900\nauth/' /etc/pam.d/common-auth
```
```bash
# Parola yaşlandırma
sudo sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS\t90/' /etc/login.defs
```

### Alan 2 — Gereksiz servisleri kapat
```bash
sudo systemctl disable --now lab-paylasim vsftpd apache2
```
```bash
sudo ss -tulpn | grep -E ':(21|80|8080) ' || echo "Temiz: bu portlar artık kapalı"
```

### Alan 3 — Ağ & güvenlik duvarı (varsayılan: reddet)
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp          # yalnızca gerekli: SSH
sudo ufw --force enable
sudo ufw status verbose
```

### Alan 4 — Dosya izinleri & SUID
```bash
sudo chmod 640 /etc/shadow && sudo chown root:shadow /etc/shadow
```
```bash
# Gereksiz SUID bitini kaldır (sahte 'find-yedek')
sudo chmod u-s /usr/local/bin/find-yedek
```
```bash
# Herkesin yazabildiği cron betiğini düzelt
sudo chown root:root /opt/yedek/yedek.sh && sudo chmod 700 /opt/yedek/yedek.sh
```
```bash
# /etc içindeki world-writable dosyayı daralt
sudo chmod 644 /etc/lab-ayar.conf
```

### Alan 5 — Güncelleme & yama yönetimi
```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades    # "Yes" seçin
```

### Alan 6 — Loglama & izleme
```bash
sudo systemctl enable --now auditd
```
```bash
sudo tee /etc/audit/rules.d/hardening.rules >/dev/null <<'EOF'
-w /etc/shadow -p wa -k kimlik
-w /etc/passwd -p wa -k kimlik
-w /etc/sudoers -p wa -k yetki
EOF
sudo augenrules --load && sudo auditctl -l
```
```bash
# Başarısız SSH girişlerini gör
sudo grep "Failed password" /var/log/auth.log | tail
```

### Alan 7 — SSH sıkılaştırma
> Önce ayrı root oturumunuzun açık olduğundan emin olun.
```bash
sudo tee /etc/ssh/sshd_config.d/10-sikilastirma.conf >/dev/null <<'EOF'
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
X11Forwarding no
LoginGraceTime 30
EOF
```
```bash
# Zayıf lab ayarını kaldır, anahtarınızı kopyalayın, sonra test edin
sudo rm -f /etc/ssh/sshd_config.d/00-lab-zayif.conf
```
```bash
ssh-keygen -t ed25519 -f ~/.ssh/lab_key -N ""      # anahtar yoksa
ssh-copy-id -i ~/.ssh/lab_key.pub kali@127.0.0.1    # parola kapanmadan önce!
```
```bash
sudo sshd -t && sudo systemctl restart ssh          # sözdizimini test et, sonra uygula
```

### Bonus — Çekirdek (sysctl)
```bash
sudo tee /etc/sysctl.d/99-sikilastirma.conf >/dev/null <<'EOF'
net.ipv4.ip_forward = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.tcp_syncookies = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
kernel.randomize_va_space = 2
EOF
sudo rm -f /etc/sysctl.d/00-lab-zayif.conf
sudo sysctl --system
```

---

## 3. DENETLE – Sonucu doğrula ve puanla (10 dk)

```bash
sudo bash kontrol.sh | tee sonra-kontrol.txt
```
```bash
sudo lynis audit system --quick | tee sonra-lynis.txt
```

📝 **Karşılaştırma:**

| Ölçüt | Önce | Sonra |
|---|---|---|
| kontrol.sh puanı | / 100 | / 100 |
| Lynis Hardening Index | | |
| Açık port sayısı (`ss -tulpn`) | | |

Hedef: **kontrol.sh ≥ 90/100** ve Lynis index'inde belirgin artış.

---

## 4. TEKRAR ET
Slayt 16: sıkılaştırma bir **döngüdür**. `kontrol.sh` hâlâ `[KALDI]` gösteren maddeleri çözün ve yeniden tarayın. Her `[KALDI]` satırının sonunda **ipucu** yazılıdır.

---

## 5. Standartlarla bağ (slayt 15)
- `kontrol.sh` bir **mini kontrol listesidir** — gerçek dünyada bunun yerini **CIS Benchmark** ve **DISA STIG** alır.
- `lynis` açık kaynak **denetim/puanlama** aracıdır; `OpenSCAP` SCAP standardıyla, `CIS-CAT` ise CIS Benchmark'a göre otomatik uyumluluk ölçer.
- Ödev olarak: Lynis'in `once-lynis.txt` içindeki **"Suggestions"** bölümünden 5 öneri seçip uygulayın.

---

## 10. Teslim edilecekler
1. `once-kontrol.txt` ve `sonra-kontrol.txt`
2. `once-lynis.txt` ve `sonra-lynis.txt`
3. Doldurulmuş **Tablo 1** (saldırı yüzeyi bulguları)
4. 1 sayfalık rapor: *Hangi alanda hangi açığı buldum, nasıl kapattım, puan kaç arttı?*

---
*Eğitmen için: tüm adımları tek seferde uygulayan referans çözüm `cozum.sh` dosyasındadır.*
