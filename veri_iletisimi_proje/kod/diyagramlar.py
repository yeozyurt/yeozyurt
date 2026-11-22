#!/usr/bin/env python3
"""Rapor ve sunum için teknik diyagramlar (blok diyagramı, sıra diyagramı,
katman eşlemesi, paket/segment yapısı, ölçüm akış şeması)."""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

KLASOR = sys.argv[1] if len(sys.argv) > 1 else "../sekiller"
os.makedirs(KLASOR, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})

C = dict(pq="#1b7f5a", pqa="#d9efe6", kl="#4a78c2", kla="#dfe8f6", tur="#c75b39", tura="#f7e1d8",
         gri="#8a8f98", gria="#eceef1", koyu="#22262e", sari="#f3e7c4")


def kutu(ax, x, y, w, h, metin, renk="gria", kenar="koyu", fs=9.5, kalin=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=C[renk], ec=C[kenar], lw=1.2))
    ax.text(x + w / 2, y + h / 2, metin, ha="center", va="center", fontsize=fs,
            fontweight="bold" if kalin else "normal", color=C["koyu"])


def ok(ax, x1, y1, x2, y2, renk="koyu", metin=None, fs=8.5, ls="-", dx=0, dy=0.12, cift=False):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="<|-|>" if cift else "-|>", color=C[renk], lw=1.3, ls=ls,
                                shrinkA=2, shrinkB=2))
    if metin:
        ax.text((x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, metin, ha="center", va="bottom", fontsize=fs,
                color=C[renk])


def kaydet(fig, ad):
    fig.savefig(os.path.join(KLASOR, ad), dpi=220, bbox_inches="tight")
    plt.close(fig)


# 1) Sistem mimarisi / blok diyagramı ------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 5.4))
ax.set_xlim(0, 11); ax.set_ylim(0, 5.6); ax.axis("off")
ax.text(0.1, 5.35, "GÖNDERİCİ / ÖLÇÜM İSTEMCİSİ", fontsize=9, color=C["gri"], fontweight="bold")
ax.text(4.35, 5.35, "İLETİM KANALI", fontsize=9, color=C["gri"], fontweight="bold")
ax.text(7.55, 5.35, "ALICI / SUNUCU TARAFI", fontsize=9, color=C["gri"], fontweight="bold")
kutu(ax, 0.1, 4.2, 2.2, 0.8, "siteler.csv\n(130 alan adı, 4 sektör)", "sari")
kutu(ax, 0.1, 2.35, 2.2, 1.45, "olcum.py (Python 3)\nDNS → TCP RTT →\n5 bağlantı senaryosu\n→ HTTP başlıkları", "kla",
     kalin=False)
kutu(ax, 2.45, 2.35, 1.5, 1.45, "OpenSSL\n4.0.3\ns_client", "pqa")
kutu(ax, 0.1, 0.35, 2.2, 0.8, "sonuclar_1/2.csv\n(34 sütun/site)", "sari")
kutu(ax, 2.45, 0.35, 1.5, 0.8, "analiz.py\nanaliz_ek.py", "kla")
kutu(ax, 2.45, 4.2, 1.5, 0.8, "Wireshark 4.6.8\n(paket yakalama)", "gria")
ok(ax, 1.2, 4.2, 1.2, 3.8)
ok(ax, 1.2, 2.35, 1.2, 1.15)
ok(ax, 2.3, 0.75, 2.45, 0.75)
ok(ax, 2.3, 3.07, 2.45, 3.07, cift=True)
ax.plot([3.2, 3.2], [4.2, 3.8], color=C["gri"], ls=":", lw=1.2)
# kanal
kutu(ax, 4.35, 2.35, 2.6, 1.45, "Ev internet bağlantısı (TR)\nWi-Fi → modem → ISS\nIP / TCP (MSS 1460 B)\nmedyan RTT ≈ 20 ms",
     "gria")
ok(ax, 3.95, 3.07, 4.35, 3.07, cift=True)
# sunucu tarafı
kutu(ax, 7.55, 3.8, 1.75, 1.35, "CDN uç sunucusu\nCloudflare 21\nCloudFront 5\nAkamai 4 · Imperva 1", "pqa", fs=8.5)
kutu(ax, 9.5, 3.95, 1.4, 1.05, "Kurumun kaynak\nsunucusu (origin)", "gria", fs=8.5)
kutu(ax, 7.55, 1.5, 3.35, 1.05, "Kendi sunucusunu işleten kurum (98 site)\nTLS, kurumun kendi web sunucusunda\n"
     "sonlanır (Apache, nginx, IIS, BIG-IP)", "kla", fs=8.5)
ok(ax, 6.95, 3.3, 7.55, 4.35, metin="n = 31", renk="pq", dx=-0.25, dy=0.05)
ok(ax, 6.95, 2.8, 7.55, 2.1, metin="n = 98", renk="kl", dx=-0.25, dy=-0.32)
ok(ax, 9.3, 4.47, 9.5, 4.47, ls="--", renk="gri")
ax.text(9.4, 3.72, "ölçülemez\n(dışarıdan görünmez)", ha="center", fontsize=7.5, color=C["gri"], va="top")
ax.text(9.2, 0.85, "Ölçülen: TLS sürümü · seçilen grup · HRR · sertifika\nClientHello/ServerHello baytı · segment · RTT · Alt-Svc",
        ha="center", fontsize=8, color=C["koyu"])
kaydet(fig, "diyagram_sistem_mimarisi.png")


# 2) TLS 1.3 + TCP sıra diyagramı (normal ve HRR) ------------------------------------
fig, axs = plt.subplots(1, 2, figsize=(12.5, 5.6), gridspec_kw=dict(width_ratios=[1.15, 1]))
for ax in axs:
    ax.set_xlim(0, 10); ax.set_ylim(1.0, 10.5); ax.axis("off")


def hat(ax, x, ad):
    kutu(ax, x - 1.5, 9.6, 3.0, 0.8, ad, "gria", kalin=True)
    ax.plot([x, x], [1.0, 9.6], color=C["gri"], lw=1, ls="--")


def mesaj(ax, y1, y2, sol_sag, metin, renk="koyu", fs=8.3):
    x1, x2 = (2, 8) if sol_sag else (8, 2)
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color=C[renk], lw=1.4))
    ax.text(5, (y1 + y2) / 2 + 0.1, metin, ha="center", va="bottom", fontsize=fs, color=C[renk],
            bbox=dict(fc="white", ec="none", pad=0.5))


ax = axs[0]
ax.set_title("(a) Hibrit X25519MLKEM768 el sıkışması (1-RTT)", fontsize=10.5, loc="left")
hat(ax, 2, "İstemci\n(tarayıcı / olcum.py)"); hat(ax, 8, "Sunucu\n(CDN veya kurum)")
mesaj(ax, 9.1, 8.6, True, "TCP SYN", "gri")
mesaj(ax, 8.4, 7.9, False, "TCP SYN/ACK", "gri")
mesaj(ax, 7.7, 7.2, True, "TCP ACK", "gri")
ax.text(9.3, 8.4, "1 RTT\n(TCP)", fontsize=8, color=C["gri"], va="center")
mesaj(ax, 6.9, 6.25, True, "ClientHello  ≈1534 B → 2 TCP segmenti\nkey_share: X25519MLKEM768 (1216 B) + X25519 (32 B)",
      "pq")
mesaj(ax, 6.0, 5.3, False, "ServerHello 1210 B  [key_share: 1088 B ML-KEM şifre metni + 32 B]\n"
      "{EncryptedExtensions, Certificate, CertVerify, Finished}", "pq")
ax.text(9.3, 5.9, "1 RTT\n(TLS)", fontsize=8, color=C["pq"], va="center")
mesaj(ax, 4.9, 4.4, True, "{Finished}  +  HTTP GET (şifreli)", "kl")
mesaj(ax, 4.1, 3.6, False, "HTTP yanıtı (şifreli)", "kl")
ax.text(0.15, 2.7, "Paylaşılan gizli değer = HKDF( X25519 sırrı ‖ ML-KEM-768 sırrı )\n"
        "Biri kırılsa bile diğeri oturumu korur (hibrit güvenlik).", fontsize=8.5, color=C["koyu"],
        bbox=dict(fc=C["pqa"], ec=C["pq"], boxstyle="round,pad=0.4"))
ax.text(0.15, 1.8, "{ } : el sıkışma anahtarıyla şifreli kayıtlar", fontsize=8, color=C["gri"])

ax = axs[1]
ax.set_title("(b) HelloRetryRequest durumu (+1 RTT)", fontsize=10.5, loc="left")
hat(ax, 2, "İstemci"); hat(ax, 8, "Sunucu (yalnız P-256)")
mesaj(ax, 9.1, 8.5, True, "ClientHello  [pay: X25519MLKEM768, X25519]", "pq")
mesaj(ax, 8.2, 7.6, False, "HelloRetryRequest  [grup: P-256]", "tur")
mesaj(ax, 7.3, 6.7, True, "ClientHello (2.)  [pay: P-256]", "kl")
mesaj(ax, 6.4, 5.8, False, "ServerHello + {…Finished}", "kl")
mesaj(ax, 5.5, 4.9, True, "{Finished} + HTTP", "kl")
ax.text(5, 3.6, "Ölçümde 1 banka sitesi bu davranışı gösterdi:\nher bağlantıda +1 RTT ≈ +20 ms", ha="center",
        fontsize=8.8, color=C["tur"], bbox=dict(fc=C["tura"], ec=C["tur"], boxstyle="round,pad=0.4"))
fig.tight_layout()
kaydet(fig, "diyagram_tls13_sira.png")


# 3) OSI / TCP-IP katman eşlemesi ---------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5.2))
ax.set_xlim(0, 10); ax.set_ylim(0, 7.6); ax.axis("off")
osi = ["7 Uygulama", "6 Sunum", "5 Oturum", "4 Taşıma", "3 Ağ", "2 Veri bağı", "1 Fiziksel"]
tcpip = [("Uygulama", 0, 3), ("Taşıma", 3, 4), ("İnternet", 4, 5), ("Ağ erişimi", 5, 7)]
proto = [("HTTP/1.1 · HTTP/2 · Alt-Svc (h3 ilanı)", 0, 1, "kla"),
         ("TLS 1.3: el sıkışma,\nX25519MLKEM768, sertifika", 1, 3, "pqa"),
         ("TCP: 3'lü el sıkışma, MSS 1460 B,\nsegmentasyon, RTO", 3, 4, "kla"),
         ("IPv4 / IPv6 · DNS çözümleme · CDN anycast", 4, 5, "gria"),
         ("Ethernet / Wi-Fi çerçevesi\n(MTU 1500 B, TSO)", 5, 7, "gria")]
olc = [("pq_destek · secilen_grup\nhrr_var · sertifika\nClientHello/ServerHello baytı", 1, 3),
       ("tcp_rtt_ms · segment sayısı", 3, 4), ("ip · CDN adres bloğu", 4, 5),
       ("Wireshark: 369 / 1591 B çerçeve", 5, 7), ("http3_ilani · cdn başlıkları", 0, 1)]
for i, k in enumerate(osi):
    kutu(ax, 0.1, 6.7 - i * 0.95, 1.7, 0.82, k, "gria", fs=9)
for ad, a, b in tcpip:
    kutu(ax, 2.0, 6.7 - (b - 1) * 0.95, 1.5, (b - a) * 0.95 - 0.13, ad, "gria", fs=9, kalin=True)
for ad, a, b, r in proto:
    kutu(ax, 3.7, 6.7 - (b - 1) * 0.95, 3.4, (b - a) * 0.95 - 0.13, ad, r, fs=7.6)
for ad, a, b in olc:
    kutu(ax, 7.3, 6.7 - (b - 1) * 0.95, 2.6, (b - a) * 0.95 - 0.13, ad, "sari", fs=7.2)
for x, t in ((0.95, "OSI"), (2.75, "TCP/IP"), (5.4, "Protokol / mekanizma"), (8.6, "Bu çalışmada ölçülen")):
    ax.text(x, 7.6, t, ha="center", fontsize=9.5, fontweight="bold", color=C["koyu"])
kaydet(fig, "diyagram_katman_esleme.png")


# 4) ClientHello yapısı ve TCP segmentasyonu ---------------------------------------
fig, axs = plt.subplots(2, 1, figsize=(11, 4.4))
RN = {"bas": C["gria"], "ort": C["kla"], "mlkem": C["pqa"], "x": "#b9cdee"}
for ax, baslik, parcalar in (
        (axs[0], "(a) Klasik ClientHello (yalnız X25519): 232 B + 9 B başlık = 241 B → tek TCP segmenti",
         [("bas", 9, ""), ("ort", 196, "ortak alanlar + uzantılar"), ("x", 36, "")]),
        (axs[1], "(b) Tarayıcı benzeri hibrit ClientHello: 1534 B + 9 B başlık = 1543 B → MSS (1460 B) aşılır, 2 segment",
         [("bas", 9, ""), ("ort", 278, "ortak alanlar\n+ uzantılar"),
          ("mlkem", 1220, "key_share girdisi: X25519MLKEM768 = 1184 B ML-KEM-768 kapsülleme anahtarı + 32 B X25519"),
          ("x", 36, "")])):
    ax.set_xlim(-10, 1720); ax.set_ylim(-0.1, 1.45); ax.axis("off")
    ax.set_title(baslik, fontsize=9.6, loc="left")
    x = 0
    for r, w, ad in parcalar:
        ax.add_patch(plt.Rectangle((x, 0.5), w, 0.6, fc=RN[r], ec=C["koyu"], lw=0.8))
        if ad:
            ax.text(x + w / 2, 0.8, ad, ha="center", va="center", fontsize=7.8)
        x += w
    ax.axvline(1460, ymin=0.25, ymax=0.85, color=C["tur"], ls="--", lw=1.5)
    ax.text(1470, 0.25, "1460 B: 1. segmentin sonu", fontsize=7.8, color=C["tur"])
    if x > 1460:
        ax.annotate("", xy=(0, 0.38), xytext=(1460, 0.38), arrowprops=dict(arrowstyle="<->", color=C["gri"]))
        ax.text(730, 0.18, "1. TCP segmenti (1460 B)", ha="center", fontsize=7.8, color=C["gri"])
        ax.annotate("", xy=(1460, 0.38), xytext=(x, 0.38), arrowprops=dict(arrowstyle="<->", color=C["gri"]))
        ax.text((1460 + x) / 2 + 40, 0.02, "2. segment\n(83 B)", ha="center", fontsize=7.5, color=C["gri"])
axs[0].legend(handles=[plt.Rectangle((0, 0), 1, 1, fc=RN[k], ec=C["koyu"]) for k in ("bas", "ort", "mlkem", "x")],
              labels=["TLS kayıt (5 B) + el sıkışma (4 B) başlığı", "ortak alanlar ve diğer uzantılar",
                      "ML-KEM-768 içeren hibrit pay", "X25519 payı (32 B + 4 B)"],
              loc="center", bbox_to_anchor=(0.5, 0.55), fontsize=7.8, frameon=False, ncol=2)
fig.tight_layout()
kaydet(fig, "diyagram_clienthello_segment.png")


# 5) Ölçüm algoritması akış şeması ----------------------------------------------------
fig, ax = plt.subplots(figsize=(10.5, 6.2))
ax.set_xlim(0, 10.5); ax.set_ylim(0, 8.4); ax.axis("off")
adim = [("Site listesini oku (sektör, alan adı)", "sari"), ("DNS: alan adını bir kez çöz → sabit IP", "gria"),
        ("TCP bağlantı süresi ×5 → medyan RTT", "kla"),
        ("1) Tarayıcı benzeri: *X25519MLKEM768:*X25519:P-256\n→ TLS sürümü, seçilen grup, HRR, sertifika", "pqa"),
        ("2) TLS 1.2 kabul testi (-tls1_2)", "kla")]
for i, (t, r) in enumerate(adim):
    kutu(ax, 0.3, 7.5 - i * 1.25, 4.6, 0.85, t, r, fs=8.6)
    if i:
        ok(ax, 2.6, 7.5 - (i - 1) * 1.25, 2.6, 7.5 - i * 1.25 + 0.85)
# karar
ax.add_patch(plt.Polygon([[7.4, 7.95], [8.9, 7.4], [7.4, 6.85], [5.9, 7.4]], fc=C["tura"], ec=C["koyu"]))
ax.text(7.4, 7.4, "TLS 1.3\nvar mı?", ha="center", va="center", fontsize=8.6)
ax.plot([4.9, 5.3, 5.3], [2.93, 2.93, 7.4], color=C["koyu"], lw=1.3)
ok(ax, 5.3, 7.4, 5.9, 7.4)
kutu(ax, 5.6, 5.35, 3.6, 1.05, "3) Yalnız X25519MLKEM768 ×5\n→ pq_destek, süre, CH/SH baytı", "pqa", fs=8.6)
kutu(ax, 5.6, 4.0, 3.6, 1.05, "4) Yalnız X25519 ×5 (karşılaştırma)\n→ süre, CH/SH baytı", "kla", fs=8.6)
ok(ax, 7.4, 6.85, 7.4, 6.4, metin="evet", dx=0.3, dy=-0.05)
ok(ax, 7.4, 5.35, 7.4, 5.05)
ax.plot([8.9, 10.0, 10.0], [7.4, 7.4, 2.82], color=C["koyu"], lw=1.3)
ok(ax, 10.0, 2.82, 9.6, 2.82)
ax.text(9.45, 7.55, "hayır → pq_destek = False", fontsize=8, ha="center")
kutu(ax, 5.6, 2.3, 4.0, 1.05, "5) HTTPS GET / → Alt-Svc (h3),\nCDN başlıkları (cf-ray, x-amz-cf-id…)", "kla",
     fs=8.6)
ok(ax, 7.4, 4.0, 7.4, 3.35)
kutu(ax, 5.6, 0.6, 4.0, 1.05, "Satırı CSV'ye yaz (34 sütun) → 1,5 s bekle\n→ sıradaki site", "sari", fs=8.6)
ok(ax, 7.4, 2.3, 7.4, 1.65)
kutu(ax, 0.3, 0.6, 4.6, 1.05, "Hata yönetimi: dns_hatasi · ulasilamadi ·\ntls_hatasi · zaman_asimi (10 s) · kaldığı yerden devam",
     "gria", fs=8.2)
kaydet(fig, "diyagram_olcum_akis.png")
print("Diyagramlar:", sorted(f for f in os.listdir(KLASOR) if f.startswith("diyagram")))
