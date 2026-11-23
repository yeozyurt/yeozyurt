#!/usr/bin/env bash
# =====================================================================
#  MSG203 - 11. Hafta | Sistem Sıkılaştırma LAB - EĞİTMEN ÇÖZÜMÜ
#  cozum.sh : LAB-FOYU.md'deki tüm sıkılaştırma adımlarını uygular.
#  Amaç: kontrol.sh puanını ~100'e çıkarmak.
#  !!! SADECE LAB VM'inde. SSH adımından önce ayrı root oturumu açık tutun.
# =====================================================================
[[ $EUID -ne 0 ]] && { echo "[-] root olarak çalıştırın: sudo bash $0"; exit 1; }
say(){ echo -e "\e[32m[çözüm]\e[0m $*"; }

say "Alan 1 - Kullanıcı & kimlik"
userdel -r eskipersonel 2>/dev/null
passwd -l root >/dev/null
tee /etc/security/pwquality.conf >/dev/null <<'EOF'
minlen = 12
minclass = 3
dcredit = -1
ucredit = -1
lcredit = -1
retry = 3
EOF
sed -i '/pam_faillock.so/d' /etc/pam.d/common-auth
sed -i '0,/^auth/s//auth    required    pam_faillock.so preauth silent deny=5 unlock_time=900\nauth/' /etc/pam.d/common-auth
sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS\t90/' /etc/login.defs

say "Alan 2 - Gereksiz servisler"
systemctl disable --now lab-paylasim vsftpd apache2 2>/dev/null

say "Alan 3 - Güvenlik duvarı"
ufw --force reset >/dev/null
ufw default deny incoming >/dev/null
ufw default allow outgoing >/dev/null
ufw allow 22/tcp >/dev/null
ufw --force enable >/dev/null

say "Alan 4 - Dosya izinleri & SUID"
chmod 640 /etc/shadow; chown root:shadow /etc/shadow
chmod u-s /usr/local/bin/find-yedek 2>/dev/null
[[ -e /opt/yedek/yedek.sh ]] && { chown root:root /opt/yedek/yedek.sh; chmod 700 /opt/yedek/yedek.sh; }
[[ -e /etc/lab-ayar.conf ]] && chmod 644 /etc/lab-ayar.conf

say "Alan 5 - Güncelleme"
DEBIAN_FRONTEND=noninteractive apt-get install -y unattended-upgrades >/dev/null 2>&1 || say "unattended-upgrades kurulamadı (internet?)"

say "Alan 6 - Loglama"
systemctl enable --now auditd 2>/dev/null
tee /etc/audit/rules.d/hardening.rules >/dev/null <<'EOF'
-w /etc/shadow -p wa -k kimlik
-w /etc/passwd -p wa -k kimlik
-w /etc/sudoers -p wa -k yetki
EOF
augenrules --load 2>/dev/null

say "Alan 7 - SSH (dikkat: parola girişi kapatılıyor)"
rm -f /etc/ssh/sshd_config.d/00-lab-zayif.conf
tee /etc/ssh/sshd_config.d/10-sikilastirma.conf >/dev/null <<'EOF'
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
X11Forwarding no
LoginGraceTime 30
EOF
if sshd -t 2>/dev/null; then systemctl restart ssh; else say "sshd config testi başarısız - elle kontrol edin"; fi

say "Bonus - Çekirdek"
rm -f /etc/sysctl.d/00-lab-zayif.conf
tee /etc/sysctl.d/99-sikilastirma.conf >/dev/null <<'EOF'
net.ipv4.ip_forward = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.tcp_syncookies = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
kernel.randomize_va_space = 2
EOF
sysctl --system >/dev/null

echo; say "Bitti. Puan için: sudo bash kontrol.sh"
