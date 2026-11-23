#!/usr/bin/env bash
# =====================================================================
#  MSG203 - 11. Hafta | Sistem Sıkılaştırma LAB
#  kontrol.sh : Sıkılaştırma durumunu denetler ve 100 üzerinden puanlar
#  Kullanım: sudo bash kontrol.sh        (öncesi/sonrası karşılaştırma için)
# =====================================================================
[[ $EUID -ne 0 ]] && { echo "[-] root olarak çalıştırın: sudo bash $0"; exit 1; }

PUAN=0; TOPLAM=0
ok(){   echo -e "  \e[32m[GEÇTİ]\e[0m $1"; PUAN=$((PUAN+$2)); TOPLAM=$((TOPLAM+$2)); }
fail(){ echo -e "  \e[31m[KALDI]\e[0m $1  \e[90m-> ipucu: $3\e[0m"; TOPLAM=$((TOPLAM+$2)); }
chk(){  # chk "açıklama" puan "ipucu" komut...
  local d="$1" p="$2" h="$3"; shift 3
  if "$@" &>/dev/null; then ok "$d" "$p"; else fail "$d" "$p" "$h"; fi
}
baslik(){ echo -e "\n\e[1;36m== $1 ==\e[0m"; }

locked_or_gone(){ ! id "$1" &>/dev/null || passwd -S "$1" 2>/dev/null | awk '{exit !($2=="L"||$2=="LK")}'; }
svc_off(){ ! systemctl is-active --quiet "$1" && ! systemctl is-enabled --quiet "$1"; }

baslik "ALAN 1 - Kullanıcı & kimlik doğrulama"
chk "eskipersonel hesabı silinmiş/kilitli"            6 "userdel -r eskipersonel / passwd -l"   locked_or_gone eskipersonel
chk "root parolayla girişe kapalı (kilitli)"          4 "passwd -l root"                        bash -c "passwd -S root | awk '{exit !(\$2==\"L\")}'"
chk "pwquality minlen >= 12"                          5 "/etc/security/pwquality.conf"          bash -c "[[ \$(grep -E '^\s*minlen' /etc/security/pwquality.conf 2>/dev/null | tail -1 | tr -dc 0-9) -ge 12 ]]"
chk "pam_faillock etkin (hesap kilitleme)"            5 "/etc/pam.d/common-auth"                grep -q '^auth.*pam_faillock.so.*preauth' /etc/pam.d/common-auth
chk "PASS_MAX_DAYS <= 90"                             2 "/etc/login.defs"                       bash -c "[[ \$(awk '/^PASS_MAX_DAYS/{print \$2}' /etc/login.defs) -le 90 ]]"

baslik "ALAN 2 - Gereksiz servisler"
chk "lab-paylasim (8080) kapalı ve devre dışı"        5 "systemctl disable --now lab-paylasim"  svc_off lab-paylasim
chk "vsftpd kapalı ve devre dışı"                     4 "systemctl disable --now vsftpd"        svc_off vsftpd
chk "apache2 kapalı ve devre dışı"                    3 "systemctl disable --now apache2"       svc_off apache2

baslik "ALAN 3 - Ağ & güvenlik duvarı"
chk "ufw aktif"                                       6 "ufw enable"                            bash -c "ufw status | grep -q 'Status: active'"
chk "Gelen trafik varsayılanı: deny"                  5 "ufw default deny incoming"             bash -c "ufw status verbose | grep -q 'deny (incoming)'"
chk "8080 portu dinlemiyor"                           2 "ss -tulpn | grep 8080"                 bash -c "! ss -tlnH | grep -q ':8080 '"

baslik "ALAN 4 - Dosya izinleri & SUID"
chk "/etc/shadow herkese okunamaz (640/600)"          7 "chmod 640 /etc/shadow"                 bash -c "[[ \$(stat -c %a /etc/shadow) =~ ^(640|600|0)\$ ]]"
chk "find-yedek SUID biti kaldırılmış"                6 "chmod u-s / rm /usr/local/bin/find-yedek" bash -c "[[ ! -u /usr/local/bin/find-yedek ]]"
chk "/opt/yedek/yedek.sh herkese yazılamaz"           5 "chmod 700 + chown root"                bash -c "[[ ! -e /opt/yedek/yedek.sh ]] || [[ \$(( 0\$(stat -c %a /opt/yedek/yedek.sh) & 2 )) -eq 0 ]]"
chk "/etc altında world-writable dosya yok"           3 "find /etc -type f -perm -002"          bash -c "[[ -z \$(find /etc -xdev -type f -perm -002 2>/dev/null) ]]"

baslik "ALAN 5 - Güncelleme"
chk "unattended-upgrades paketi kurulu"               4 "apt install unattended-upgrades"       dpkg -s unattended-upgrades

baslik "ALAN 6 - Loglama & izleme"
chk "auditd çalışıyor"                                5 "systemctl enable --now auditd"         systemctl is-active --quiet auditd
chk "/etc/shadow ve /etc/passwd izleniyor"            5 "auditctl -w /etc/shadow -p wa -k ..."  bash -c "auditctl -l | grep -q /etc/shadow && auditctl -l | grep -q /etc/passwd"

baslik "ALAN 7 - SSH"
chk "PermitRootLogin no"                              5 "sshd_config.d/10-sikilastirma.conf"    bash -c "[[ \$(sshd -T | awk '\$1==\"permitrootlogin\"{print \$2}') == no ]]"
chk "PasswordAuthentication no"                       6 "önce ssh-copy-id ile anahtar kopyala"  bash -c "[[ \$(sshd -T | awk '\$1==\"passwordauthentication\"{print \$2}') == no ]]"
chk "MaxAuthTries <= 3"                               2 "MaxAuthTries 3"                        bash -c "[[ \$(sshd -T | awk '\$1==\"maxauthtries\"{print \$2}') -le 3 ]]"
chk "X11Forwarding no"                                1 "X11Forwarding no"                      bash -c "[[ \$(sshd -T | awk '\$1==\"x11forwarding\"{print \$2}') == no ]]"

baslik "BONUS - Çekirdek (sysctl)"
chk "ip_forward = 0"                                  1 "/etc/sysctl.d/99-sikilastirma.conf"    bash -c "[[ \$(sysctl -n net.ipv4.ip_forward) == 0 ]]"
chk "accept_redirects = 0"                            1 "net.ipv4.conf.all.accept_redirects"    bash -c "[[ \$(sysctl -n net.ipv4.conf.all.accept_redirects) == 0 ]]"
chk "tcp_syncookies = 1"                              1 "net.ipv4.tcp_syncookies"               bash -c "[[ \$(sysctl -n net.ipv4.tcp_syncookies) == 1 ]]"
chk "ASLR tam açık (randomize_va_space = 2)"          1 "kernel.randomize_va_space"             bash -c "[[ \$(sysctl -n kernel.randomize_va_space) == 2 ]]"

echo -e "\n\e[1m==============================================\e[0m"
echo -e "\e[1m  SIKILAŞTIRMA PUANI: $PUAN / $TOPLAM\e[0m"
echo -e "\e[1m==============================================\e[0m"
echo "  Rapor için: sudo bash kontrol.sh | tee kontrol-\$(date +%H%M).txt"
