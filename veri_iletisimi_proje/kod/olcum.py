#!/usr/bin/env python3
"""
Türkiye'de Kuantum Sonrası TLS Hazırlığı - Ölçüm Betiği
========================================================

Her siteye normal bir ziyaretçi gibi bağlanır ve herkese açık TLS el sıkışma
bilgisini kaydeder. Tarama veya güvenlik testi YAPMAZ.

Ölçülenler (site başına):
  - DNS çözümleme, TCP RTT (medyan)
  - Tarayıcı benzeri bağlantı (X25519MLKEM768 + X25519 + P-256 teklif edilir):
      TLS sürümü, sunucunun seçtiği grup, HelloRetryRequest olup olmadığı,
      sertifika anahtar türü/uzunluğu ve imza algoritması
  - Yalnız hibrit PQ (X25519MLKEM768) ile TLS 1.3 bağlantısı: destek var mı,
      el sıkışma süresi, ClientHello / ServerHello boyutu, toplam okunan/yazılan bayt
  - Yalnız klasik (X25519) ile TLS 1.3 bağlantısı: aynı metrikler (karşılaştırma için)
  - TLS 1.2 kabul ediliyor mu?
  - HTTP yanıt başlıkları: HTTP/3 ilanı (Alt-Svc: h3), CDN tespiti

Gereksinim: OpenSSL 3.5 veya üzeri (X25519MLKEM768 desteği), Python 3.8+.
Ek Python paketi gerekmez.

Kullanım:
  python3 olcum.py --girdi siteler.csv --cikti sonuclar.csv
  python3 olcum.py --girdi siteler.csv --cikti sonuclar.csv --tekrar 5 --bekleme 1.5
  python3 olcum.py --openssl /opt/openssl35/bin/openssl ...

Yarıda kalan bir ölçüm aynı komutla sürdürülebilir: çıktıda zaten bulunan
alan adları atlanır.
"""

import argparse
import csv
import datetime as dt
import http.client
import math
import os
import re
import socket
import ssl
import statistics
import subprocess
import sys
import time

# Windows'ta OpenSSL çıktısı (ör. sertifikadaki Türkçe karakterler) UTF-8 gelir;
# konsolun Türkçe kod sayfası (cp1254) ile okunursa hata verir. Bu yüzden tüm
# alt süreç çıktıları açıkça UTF-8 olarak okunur.

PQ_GRUBU = "X25519MLKEM768"
KLASIK_GRUP = "X25519"
# Chrome/Firefox'a benzer teklif: iki anahtar payı (*) gönderilir, P-256 yedekte.
TARAYICI_GRUPLARI = "*X25519MLKEM768:*X25519:P-256"
VARSAYILAN_MSS = 1460  # Ethernet MTU 1500 - IP(20) - TCP(20)

ALANLAR = [
    "olcum_zamani", "sektor", "alan_adi", "ip", "durum",
    "tcp_rtt_ms",
    # tarayıcı benzeri bağlantı
    "tls_surumu", "secilen_grup", "hrr_var",
    "tarayici_clienthello_bayt", "tarayici_clienthello_segment_tahmini", "tarayici_okunan_bayt",
    "sertifika_anahtar", "sertifika_bit", "sertifika_imza",
    # destek
    "tls13_destek", "tls12_kabul", "pq_destek",
    # hibrit PQ el sıkışması
    "pq_sure_ms", "pq_clienthello_bayt", "pq_serverhello_bayt",
    "pq_okunan_bayt", "pq_yazilan_bayt", "pq_clienthello_segment_tahmini",
    # klasik el sıkışma
    "klasik_sure_ms", "klasik_clienthello_bayt", "klasik_serverhello_bayt",
    "klasik_okunan_bayt", "klasik_yazilan_bayt", "klasik_clienthello_segment_tahmini",
    # HTTP katmanı
    "http3_ilani", "cdn", "server_basligi",
    "notlar",
]


# --------------------------------------------------------------------------
# Yardımcılar
# --------------------------------------------------------------------------

def openssl_kontrol(openssl):
    """OpenSSL sürümünü ve X25519MLKEM768 desteğini doğrular."""
    try:
        surum = subprocess.run([openssl, "version"], capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=10).stdout.strip()
        gruplar = subprocess.run([openssl, "list", "-tls-groups"],
                                 capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10).stdout
    except (OSError, subprocess.TimeoutExpired) as e:
        sys.exit(f"HATA: OpenSSL çalıştırılamadı ({openssl}): {e}")
    if PQ_GRUBU not in gruplar:
        sys.exit(
            f"HATA: '{surum}' {PQ_GRUBU} grubunu desteklemiyor.\n"
            "OpenSSL 3.5 veya üzeri gerekir. README'deki kurulum adımlarına bakın "
            "ya da --openssl ile doğru ikili dosyayı gösterin."
        )
    return surum


def adres_coz(alan_adi, port):
    """Alan adını bir kez çözer (IPv4 öncelikli). Ölçüm boyunca aynı IP kullanılır."""
    bilgiler = socket.getaddrinfo(alan_adi, port, type=socket.SOCK_STREAM)
    bilgiler.sort(key=lambda b: 0 if b[0] == socket.AF_INET else 1)
    return bilgiler[0][4][0]


def tcp_rtt(ip, port, tekrar, zaman_asimi):
    """TCP bağlantı kurma süresi (SYN -> SYN/ACK) ≈ 1 RTT. Medyan ms döner."""
    sureler = []
    aile = socket.AF_INET6 if ":" in ip else socket.AF_INET
    for _ in range(tekrar):
        s = socket.socket(aile, socket.SOCK_STREAM)
        s.settimeout(zaman_asimi)
        try:
            t0 = time.perf_counter()
            s.connect((ip, port))
            sureler.append((time.perf_counter() - t0) * 1000)
        except OSError:
            pass
        finally:
            s.close()
        time.sleep(0.2)
    return round(statistics.median(sureler), 2) if sureler else None


def s_client(openssl, ip, port, sni, ek_argumanlar, zaman_asimi):
    """openssl s_client'ı çalıştırır, (çıktı, duvar saati süresi ms) döner."""
    hedef = f"[{ip}]:{port}" if ":" in ip else f"{ip}:{port}"
    komut = [openssl, "s_client", "-connect", hedef, "-servername", sni,
             "-msg"] + ek_argumanlar
    t0 = time.perf_counter()
    try:
        p = subprocess.run(komut, input="", capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=zaman_asimi)
        cikti = p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        return None, None
    return cikti, (time.perf_counter() - t0) * 1000


def cikti_coz(cikti):
    """s_client çıktısından el sıkışma bilgilerini ayrıştırır."""
    sonuc = {}
    if not cikti:
        return {"basarili": False}

    m = re.search(r"^Protocol:\s*(\S+)", cikti, re.M) or \
        re.search(r"New, (TLSv[\d.]+), Cipher is (?!\(NONE\))", cikti)
    sonuc["protokol"] = m.group(1) if m else None

    m = re.search(r"Cipher is (\S+)", cikti)
    sifre = m.group(1) if m else None
    sonuc["basarili"] = bool(sifre and sifre != "(NONE)" and "0000" not in sifre)

    # TLS 1.3 PQ grupları "Negotiated TLS1.3 group:" ile, klasik gruplar
    # "Peer Temp Key:" / "Server Temp Key:" ile raporlanır.
    m = re.search(r"Negotiated TLS1\.3 group:\s*(\S+)", cikti)
    grup = m.group(1) if m and m.group(1) != "<NULL>" else None
    if not grup:
        # "Peer Temp Key: X25519, 253 bits" veya "Peer Temp Key: ECDH, prime256v1, 256 bits"
        m = re.search(r"(?:Peer|Server) Temp Key:\s*([^\n]+)", cikti)
        if m:
            parcalar = [p.strip() for p in m.group(1).split(",")]
            grup = parcalar[1] if parcalar[0] == "ECDH" and len(parcalar) > 2 else parcalar[0]
        else:
            grup = None
    sonuc["grup"] = grup

    # -msg satırları: ">>> TLS 1.3, Handshake [length 05c8], ClientHello"
    ch = re.findall(r">>> .*Handshake \[length ([0-9a-f]+)\], ClientHello", cikti)
    sh = re.findall(r"<<< .*Handshake \[length ([0-9a-f]+)\], ServerHello", cikti)
    sonuc["clienthello_bayt"] = int(ch[0], 16) if ch else None
    sonuc["serverhello_bayt"] = int(sh[-1], 16) if sh else None
    # İkinci bir ClientHello = sunucu HelloRetryRequest gönderdi (+1 RTT)
    sonuc["hrr"] = len(ch) > 1

    m = re.search(r"handshake has read (\d+) bytes and written (\d+) bytes", cikti)
    sonuc["okunan"] = int(m.group(1)) if m else None
    sonuc["yazilan"] = int(m.group(2)) if m else None

    # Sertifika zincirinin ilk halkası:
    # "   a:PKEY: RSA, 2048 (bit); sigalg: sha256WithRSAEncryption"
    m = re.search(r"a:PKEY:\s*([^,]+),\s*(\d+)\s*\(bit\);\s*sigalg:\s*(\S+)", cikti)
    if m:
        sonuc["sert_anahtar"], sonuc["sert_bit"], sonuc["sert_imza"] = \
            m.group(1).strip(), int(m.group(2)), m.group(3)
    else:
        m = re.search(r"Server public key is (\d+) bit", cikti)
        sonuc["sert_anahtar"], sonuc["sert_imza"] = None, None
        sonuc["sert_bit"] = int(m.group(1)) if m else None
    return sonuc


def segment_tahmini(bayt, mss=VARSAYILAN_MSS):
    """ClientHello'nun kaç TCP segmentine sığdığının tahmini (TLS kayıt başlığı +5)."""
    if not bayt:
        return None
    return math.ceil((bayt + 4 + 5) / mss)  # el sıkışma başlığı 4 + kayıt başlığı 5


def tekrarli_el_sikisma(openssl, ip, port, sni, argumanlar, tekrar, zaman_asimi):
    """Aynı el sıkışmayı N kez yapar; ilk başarılı çıktının bilgileri + medyan süre."""
    sureler, ilk = [], None
    for _ in range(tekrar):
        cikti, sure = s_client(openssl, ip, port, sni, argumanlar, zaman_asimi)
        c = cikti_coz(cikti)
        if c.get("basarili"):
            sureler.append(sure)
            ilk = ilk or c
        elif ilk is None and not sureler:
            # ilk deneme başarısızsa destek yok demektir; tekrar etme
            return c, None
        time.sleep(0.3)
    return ilk or {"basarili": False}, (round(statistics.median(sureler), 1) if sureler else None)


CDN_IMZALARI = [
    ("Cloudflare", lambda h: "cf-ray" in h or "cloudflare" in h.get("server", "")),
    ("Akamai", lambda h: "akamai" in h.get("server", "") or any(k.startswith("x-akamai") for k in h)),
    ("CloudFront", lambda h: "x-amz-cf-id" in h or "cloudfront" in h.get("via", "")),
    ("Fastly", lambda h: "fastly" in h.get("server", "") or "x-fastly-request-id" in h
     or "fastly" in h.get("via", "")),
    ("Google", lambda h: h.get("server", "") in ("gws", "google frontend", "gse", "esf")),
    ("Azure", lambda h: "x-azure-ref" in h or "x-msedge-ref" in h),
    ("Imperva", lambda h: "x-iinfo" in h or "incapsula" in h.get("x-cdn", "")),
    ("Medianova", lambda h: "medianova" in h.get("server", "") or "mncdn" in h.get("server", "")),
    ("CDN77", lambda h: "cdn77" in h.get("server", "")),
]


def http_bilgisi(alan_adi, ip, port, zaman_asimi):
    """Ana sayfaya tek bir HTTPS isteği atıp yanıt başlıklarını inceler."""
    sonuc = {"http3_ilani": None, "cdn": None, "server_basligi": None, "not": ""}
    for dogrula in (True, False):
        ctx = ssl.create_default_context()
        if not dogrula:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        try:
            baglanti = http.client.HTTPSConnection(alan_adi, port, timeout=zaman_asimi,
                                                   context=ctx)
            baglanti.request("GET", "/", headers={
                "User-Agent": "Mozilla/5.0 (akademik PQ-TLS olcum calismasi)",
                "Accept": "text/html"})
            yanit = baglanti.getresponse()
            basliklar = {k.lower(): v.lower() for k, v in yanit.getheaders()}
            baglanti.close()
            alt_svc = basliklar.get("alt-svc", "")
            sonuc["http3_ilani"] = bool(re.search(r'\bh3(-\d+)?="', alt_svc))
            sonuc["server_basligi"] = basliklar.get("server", "")[:60]
            sonuc["cdn"] = next((ad for ad, f in CDN_IMZALARI if f(basliklar)), "Yok/Bilinmiyor")
            if not dogrula:
                sonuc["not"] = "sertifika_dogrulanamadi"
            return sonuc
        except ssl.SSLCertVerificationError:
            continue
        except (OSError, http.client.HTTPException, ssl.SSLError) as e:
            sonuc["not"] = f"http_hatasi:{type(e).__name__}"
            return sonuc
    return sonuc


# --------------------------------------------------------------------------
# Tek site ölçümü
# --------------------------------------------------------------------------

def siteyi_olc(openssl, sektor, alan_adi, tekrar, zaman_asimi):
    satir = {k: "" for k in ALANLAR}
    satir.update(olcum_zamani=dt.datetime.now().isoformat(timespec="seconds"),
                 sektor=sektor, alan_adi=alan_adi)
    host, _, port = alan_adi.partition(":")
    port = int(port) if port else 443
    notlar = []

    try:
        ip = adres_coz(host, port)
    except OSError:
        satir["durum"] = "dns_hatasi"
        return satir
    satir["ip"] = ip

    satir["tcp_rtt_ms"] = tcp_rtt(ip, port, tekrar, zaman_asimi)
    if satir["tcp_rtt_ms"] is None:
        satir["durum"] = "ulasilamadi"
        return satir

    # 1) Tarayıcı benzeri bağlantı
    cikti, _ = s_client(openssl, ip, port, host, ["-groups", TARAYICI_GRUPLARI], zaman_asimi)
    v = cikti_coz(cikti)
    if not v.get("basarili"):
        satir["durum"] = "tls_hatasi" if cikti else "zaman_asimi"
        return satir
    satir.update(tls_surumu=v["protokol"], secilen_grup=v["grup"], hrr_var=v["hrr"],
                 sertifika_anahtar=v.get("sert_anahtar"), sertifika_bit=v.get("sert_bit"),
                 sertifika_imza=v.get("sert_imza"),
                 tarayici_clienthello_bayt=v.get("clienthello_bayt"),
                 tarayici_clienthello_segment_tahmini=segment_tahmini(v.get("clienthello_bayt")),
                 tarayici_okunan_bayt=v.get("okunan"))
    satir["tls13_destek"] = v["protokol"] == "TLSv1.3"

    # 2) TLS 1.2 kabulü
    c12, _ = s_client(openssl, ip, port, host, ["-tls1_2"], zaman_asimi)
    satir["tls12_kabul"] = cikti_coz(c12).get("protokol") == "TLSv1.2"

    # 3) Hibrit PQ ve klasik el sıkışmaları (yalnız TLS 1.3 varsa anlamlı)
    if satir["tls13_destek"]:
        for onek, grup in (("pq", PQ_GRUBU), ("klasik", KLASIK_GRUP)):
            c, sure = tekrarli_el_sikisma(openssl, ip, port, host,
                                          ["-tls1_3", "-groups", grup], tekrar, zaman_asimi)
            if onek == "pq":
                satir["pq_destek"] = bool(c.get("basarili") and c.get("grup") == PQ_GRUBU)
            if c.get("basarili"):
                satir[f"{onek}_sure_ms"] = sure
                satir[f"{onek}_clienthello_bayt"] = c.get("clienthello_bayt")
                satir[f"{onek}_serverhello_bayt"] = c.get("serverhello_bayt")
                satir[f"{onek}_okunan_bayt"] = c.get("okunan")
                satir[f"{onek}_yazilan_bayt"] = c.get("yazilan")
                satir[f"{onek}_clienthello_segment_tahmini"] = segment_tahmini(c.get("clienthello_bayt"))
    else:
        satir["pq_destek"] = False

    # 4) HTTP katmanı
    h = http_bilgisi(host, ip, port, zaman_asimi)
    satir.update(http3_ilani=h["http3_ilani"], cdn=h["cdn"], server_basligi=h["server_basligi"])
    if h["not"]:
        notlar.append(h["not"])

    satir["durum"] = "tamam"
    satir["notlar"] = ";".join(notlar)
    return satir


# --------------------------------------------------------------------------
# Ana akış
# --------------------------------------------------------------------------

def siteleri_oku(yol):
    siteler = []
    with open(yol, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            alan = (r.get("alan_adi") or "").strip().lower()
            alan = re.sub(r"^https?://", "", alan).rstrip("/")
            if alan and not alan.startswith("#"):
                siteler.append(((r.get("sektor") or "Diger").strip(), alan))
    return siteler


def main():
    ap = argparse.ArgumentParser(description="Kuantum sonrası TLS hazırlık ölçümü")
    ap.add_argument("--girdi", default="siteler.csv", help="sektor,alan_adi sütunlu CSV")
    ap.add_argument("--cikti", default="sonuclar.csv")
    ap.add_argument("--openssl", default=os.environ.get("OPENSSL", "openssl"),
                    help="OpenSSL 3.5+ ikili dosyası (varsayılan: PATH'teki openssl)")
    ap.add_argument("--tekrar", type=int, default=5, help="Süre ölçümlerinin tekrar sayısı")
    ap.add_argument("--bekleme", type=float, default=1.5,
                    help="Siteler arası bekleme (sn) - sunucuları yormamak için")
    ap.add_argument("--zaman-asimi", type=float, default=10.0)
    ap.add_argument("--sinir", type=int, default=0, help="Yalnız ilk N siteyi ölç (pilot)")
    a = ap.parse_args()

    surum = openssl_kontrol(a.openssl)
    siteler = siteleri_oku(a.girdi)
    if a.sinir:
        siteler = siteler[:a.sinir]

    yapilmis = set()
    yeni_dosya = not os.path.exists(a.cikti)
    if not yeni_dosya:
        with open(a.cikti, newline="", encoding="utf-8") as f:
            yapilmis = {r["alan_adi"] for r in csv.DictReader(f)}

    print(f"{surum} | {len(siteler)} site | {len(yapilmis)} tanesi zaten ölçülmüş")
    with open(a.cikti, "a", newline="", encoding="utf-8") as f:
        yazici = csv.DictWriter(f, fieldnames=ALANLAR)
        if yeni_dosya:
            yazici.writeheader()
        for i, (sektor, alan) in enumerate(siteler, 1):
            if alan in yapilmis:
                continue
            try:
                satir = siteyi_olc(a.openssl, sektor, alan, a.tekrar, a.zaman_asimi)
            except Exception as e:  # tek bir site tüm ölçümü durdurmasın
                satir = {k: "" for k in ALANLAR}
                satir.update(sektor=sektor, alan_adi=alan, durum="beklenmeyen_hata",
                             notlar=f"{type(e).__name__}: {e}"[:200])
            yazici.writerow(satir)
            f.flush()
            print(f"[{i:>3}/{len(siteler)}] {alan:<32} {satir['durum']:<12} "
                  f"TLS={satir['tls_surumu'] or '-':<8} PQ={satir['pq_destek']!s:<5} "
                  f"grup={satir['secilen_grup'] or '-'}")
            time.sleep(a.bekleme)
    print(f"Bitti. Sonuçlar: {a.cikti}")


if __name__ == "__main__":
    main()
