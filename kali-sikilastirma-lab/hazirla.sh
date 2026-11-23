#!/usr/bin/env bash
# =====================================================================
#  MSG203 - 11. Hafta | Sistem Sıkılaştırma LAB
#  hazirla.sh : Kali VM'i BİLEREK zayıf hale getirir (öğrenci bunu düzeltecek)
#
#  !!! SADECE LAB SANAL MAKİNESİNDE ÇALIŞTIRIN !!!
#  !!! Çalıştırmadan önce VM SNAPSHOT alın !!!
# =====================================================================
set -u
[[ $EUID -ne 0 ]] && { echo "[-] root olarak çalıştırın: sudo bash $0"; exit 1; }

read -rp "[?] Bu makine bir LAB VM'i mi ve snapshot aldınız mı? (evet/hayir): " c
[[ "$c" != "evet" ]] && { echo "[-] İptal edildi."; exit 1; }

say(){ echo -e "\e[33m[+]\e[0m $*"; }

# ---------- ALAN 1: Kullanıcı & kimlik ----------
say "Zayıf parolalı kullanıcılar oluşturuluyor"
id stajyer      &>/dev/null || useradd -m -s /bin/bash stajyer
id eskipersonel &>/dev/null || useradd -m -s /bin/bash eskipersonel
echo 'stajyer:123456'       | chpasswd
echo 'eskipersonel:password' | chpasswd
echo 'root:toor'            | chpasswd
passwd -u root &>/dev/null || true
# Parola yaşlandırma kapalı
sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS\t99999/' /etc/login.defs

# ---------- ALAN 2: Gereksiz servisler ----------
say "Gereksiz servisler açılıyor (apache2, vsftpd, lab-paylasim:8080)"
export DEBIAN_FRONTEND=noninteractive
apt-get install -y apache2 vsftpd openssh-server &>/dev/null || say "apt kurulumu kısmen başarısız (internet?)"
if [[ -f /etc/vsftpd.conf ]]; then
  sed -i 's/^anonymous_enable=.*/anonymous_enable=YES/' /etc/vsftpd.conf
  grep -q '^anonymous_enable' /etc/vsftpd.conf || echo 'anonymous_enable=YES' >> /etc/vsftpd.conf
fi
mkdir -p /srv/paylasim && echo "gizli_proje_notlari" > /srv/paylasim/notlar.txt
cat > /etc/systemd/system/lab-paylasim.service <<'EOF'
[Unit]
Description=LAB - Unutulmus dosya paylasim servisi
After=network.target
[Service]
WorkingDirectory=/
ExecStart=/usr/bin/python3 -m http.server 8080 --bind 0.0.0.0
Restart=always
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now apache2 vsftpd lab-paylasim ssh &>/dev/null

# ---------- ALAN 3: Ağ & firewall ----------
say "Güvenlik duvarı kapatılıyor"
command -v ufw &>/dev/null && ufw --force disable &>/dev/null
command -v ufw &>/dev/null && ufw --force reset &>/dev/null

# ---------- ALAN 4: Dosya izinleri & SUID ----------
say "Hatalı izinler ve SUID ikilileri bırakılıyor"
chmod 644 /etc/shadow                                     # herkes okuyabilir!
cp /usr/bin/find /usr/local/bin/find-yedek && chmod 4755 /usr/local/bin/find-yedek
mkdir -p /opt/yedek
cat > /opt/yedek/yedek.sh <<'EOF'
#!/bin/bash
tar czf /tmp/etc-yedek.tgz /etc 2>/dev/null
EOF
chmod 777 /opt/yedek/yedek.sh                               # herkes yazabilir!
echo '* * * * * root /opt/yedek/yedek.sh' > /etc/cron.d/lab-yedek
chmod 644 /etc/cron.d/lab-yedek   # root her dakika, herkesin yazabildiği betiği çalıştırır
touch /etc/lab-ayar.conf && chmod 666 /etc/lab-ayar.conf    # /etc içinde world-writable

# ---------- ALAN 6: Loglama ----------
say "auditd durduruluyor"
systemctl disable --now auditd &>/dev/null || true

# ---------- ALAN 7: SSH ----------
say "SSH zayıf yapılandırılıyor"
mkdir -p /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/00-lab-zayif.conf <<'EOF'
# LAB: bilerek zayif ayarlar
PermitRootLogin yes
PasswordAuthentication yes
PermitEmptyPasswords no
MaxAuthTries 10
X11Forwarding yes
LoginGraceTime 2m
EOF
grep -q '^Include /etc/ssh/sshd_config.d' /etc/ssh/sshd_config || \
  sed -i '1i Include /etc/ssh/sshd_config.d/*.conf' /etc/ssh/sshd_config
systemctl restart ssh

# ---------- Çekirdek ----------
say "Çekirdek parametreleri zayıflatılıyor"
cat > /etc/sysctl.d/00-lab-zayif.conf <<'EOF'
net.ipv4.ip_forward = 1
net.ipv4.conf.all.accept_redirects = 1
net.ipv4.conf.all.send_redirects = 1
net.ipv4.conf.all.accept_source_route = 1
net.ipv4.tcp_syncookies = 0
net.ipv4.icmp_echo_ignore_broadcasts = 0
kernel.randomize_va_space = 0
EOF
sysctl --system &>/dev/null

echo
say "HAZIR. Sistem artık bilerek ZAYIF. Başlangıç puanı için: sudo bash kontrol.sh"
