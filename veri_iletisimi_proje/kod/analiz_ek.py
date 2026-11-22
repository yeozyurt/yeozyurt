#!/usr/bin/env python3
"""
Ek analizler (ders raporu için):
  1) İki ölçüm turunun yüklenmesi, CDN sınıflandırmasının IP bloklarıyla tamamlanması
  2) Wilson %95 güven aralıkları, Fisher kesin testleri, katmanlı (CDN'e göre) permütasyon testi
  3) Ağ maliyeti (bayt / segment) özetleri
  4) Paket kaybı altında el sıkışma süresi: analitik model + Monte Carlo simülasyonu
  5) Grafikler (sekiller/ klasörüne)

Kullanım:
  python3 analiz_ek.py --veri ../veri --cikti ../analiz --sekiller ../sekiller

NOT: 4. bölüm bir SİMÜLASYONDUR; gerçek ağ deneyi değildir. Varsayımlar
raporun "Simülasyon" alt bölümünde açıkça listelenmiştir.
"""
import argparse
import csv
import json
import math
import os
import random
import statistics as st
from collections import Counter, defaultdict

from scipy import stats

import ipaddress

SEKTOR_AD = {"Banka": "Banka", "SigortaFinans": "Sigorta ve finans", "Kamu": "Kamu", "Saglik": "Sağlık",
             "Altyapi": "Kritik altyapı", "Universite": "Üniversite", "ETicaret": "E-ticaret"}
SEKTOR_SIRA = list(SEKTOR_AD)

# HTTP başlığıyla tanınamayan siteler için yalnızca iyi bilinen CDN adres blokları kullanılır.
CDN_BLOKLARI = {
    "Cloudflare": ["104.16.0.0/13", "104.24.0.0/14", "172.64.0.0/13", "162.158.0.0/15", "141.101.64.0/18",
                   "108.162.192.0/18", "188.114.96.0/20", "190.93.240.0/20", "198.41.128.0/17"],
    "Akamai": ["2.16.0.0/13", "23.32.0.0/11", "23.192.0.0/11"],
    "Fastly": ["151.101.0.0/16", "146.75.0.0/16", "199.232.0.0/16"],
    "Imperva": ["45.223.0.0/16", "45.60.0.0/16"],
}
_AGLAR = [(ad, ipaddress.ip_network(b)) for ad, bl in CDN_BLOKLARI.items() for b in bl]
# Ekim turundaki tek istisna: Akamai'nin ISS içi düğümü (aynı blokta www.lcw.com 'akamaighost' döndürüyor)
CDN_ALAN_DUZELTME = {"www.defacto.com.tr": "Akamai"}


def ip_cdn(ip):
    try:
        a = ipaddress.ip_address(ip)
    except ValueError:
        return None
    return next((ad for ad, ag in _AGLAR if a.version == ag.version and a in ag), None)


def evet(x):
    return str(x).strip().lower() == "true"


def sayi(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def yukle(yol):
    with open(yol, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f)]


def cdn_tamamla(*turlar):
    """Başlıkla tanınamayan CDN'leri IP bloklarından tamamlar; HTTP hatası nedeniyle başlığı boş kalan
    siteler için aynı IP'yi kullanan başka turun başlık bilgisini kullanır."""
    for tur in turlar:
        diger = {r["alan_adi"]: r for t in turlar if t is not tur for r in t}
        for r in tur:
            if r["durum"] != "tamam":
                continue
            if r["cdn"] == "" and r["alan_adi"] in diger and diger[r["alan_adi"]]["ip"] == r["ip"] \
                    and diger[r["alan_adi"]]["cdn"]:
                r["cdn"] = diger[r["alan_adi"]]["cdn"]; r["_cdn_kaynak"] = "diğer tur başlığı"
            if r["cdn"] in ("", "Yok/Bilinmiyor"):
                ad = ip_cdn(r["ip"]) or (CDN_ALAN_DUZELTME.get(r["alan_adi"]) if r["ip"].startswith("195.175.179.") else None)
                if ad:
                    r["cdn"] = ad; r["_cdn_kaynak"] = "IP bloğu"
            r["_cdnli"] = r["cdn"] not in ("", "Yok/Bilinmiyor")


def ust_p(p):
    """p değerini '10⁻⁷³' biçiminde üst sınır olarak yazar."""
    us = math.floor(math.log10(p)) + 1 if p > 0 else -300
    return "10" + str(us).translate(str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    m = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(100 * max(0, m - h), 1), round(100 * min(1, m + h), 1))


def oran(k, n):
    return round(100 * k / n, 1) if n else None


def sektor_ozeti(ok):
    satirlar = []
    for s in SEKTOR_SIRA + ["TÜMÜ"]:
        g = ok if s == "TÜMÜ" else [r for r in ok if r["sektor"] == s]
        n = len(g)
        pq = sum(evet(r["pq_destek"]) for r in g)
        t13 = sum(evet(r["tls13_destek"]) for r in g)
        cdn = sum(r["_cdnli"] for r in g)
        h3 = sum(evet(r["http3_ilani"]) for r in g)
        satirlar.append(dict(sektor=SEKTOR_AD.get(s, s), n=n, tls13=oran(t13, n), tls12=oran(n - t13, n),
                             pq=oran(pq, n), pq_k=pq, pq_ci=wilson(pq, n), cdn=oran(cdn, n), http3=oran(h3, n)))
    return satirlar


def permutasyon_katmanli(ok, tekrar=20000, tohum=1):
    """CDN katmanı içinde sektör etiketlerini karıştırarak sektör-PQ ilişkisini sınar.
    İstatistik: sektörler arası PQ oranlarının ki-kare benzeri sapma toplamı."""
    rnd = random.Random(tohum)
    katmanlar = defaultdict(list)
    for r in ok:
        katmanlar[r["_cdnli"]].append((r["sektor"], evet(r["pq_destek"])))

    def istatistik(veri):
        t = 0.0
        for kat in veri.values():
            n = len(kat)
            p = sum(y for _, y in kat) / n
            gruplar = defaultdict(list)
            for s, y in kat:
                gruplar[s].append(y)
            for ys in gruplar.values():
                t += len(ys) * (sum(ys) / len(ys) - p) ** 2
        return t

    gozlenen = istatistik(katmanlar)
    asan = 0
    for _ in range(tekrar):
        karisik = {}
        for k, kat in katmanlar.items():
            etiketler = [s for s, _ in kat]
            rnd.shuffle(etiketler)
            karisik[k] = list(zip(etiketler, [y for _, y in kat]))
        if istatistik(karisik) >= gozlenen - 1e-12:
            asan += 1
    return gozlenen, (asan + 1) / (tekrar + 1)


# ---------------------------------------------------------------------------
# Paket kaybı altında el sıkışma süresi (simülasyon)
# ---------------------------------------------------------------------------

def flight_gecikmesi(k, p, rto, rnd, max_tur=12):
    """k segmentlik bir uçuşun (flight) tamamının teslimi için harcanan EK süre.
    Her turda kaybolan segmentler bir RTO sonra birlikte yeniden gönderilir,
    RTO her başarısız turda iki katına çıkar (RFC 6298 üstel geri çekilme)."""
    kalan, ek, r = k, 0.0, rto
    for _ in range(max_tur):
        kalan = sum(1 for _ in range(kalan) if rnd.random() < p)
        if kalan == 0:
            return ek
        ek += r
        r *= 2
    return ek


def el_sikisma_suresi(p, rtt, ch_seg, sf_seg, rnd, rto_syn=1.0, rto_min=0.2):
    """TCP + TLS 1.3 el sıkışmasının istemci tarafında tamamlanma süresi (s).
    Taban: 2 RTT (TCP 3'lü el sıkışma + TLS 1-RTT)."""
    t = 2 * rtt
    # SYN ve SYN/ACK (her biri tek segment, ilk RTO = 1 s)
    r = rto_syn
    while rnd.random() < 1 - (1 - p) ** 2:
        t += r
        r *= 2
    rto = rtt + max(4 * rtt / 2, rto_min)  # SRTT + max(4·RTTVAR, 200 ms), RTTVAR = RTT/2
    t += flight_gecikmesi(ch_seg, p, rto, rnd)   # ClientHello uçuşu
    t += flight_gecikmesi(sf_seg, p, rto, rnd)   # Sunucu uçuşu (SH+EE+Cert+CV+Fin)
    return t


def simulasyon(senaryolar, kayiplar, rtt, n=40000, tohum=7):
    rnd = random.Random(tohum)
    sonuc = []
    for p in kayiplar:
        for ad, ch, sf in senaryolar:
            ts = sorted(el_sikisma_suresi(p, rtt, ch, sf, rnd) for _ in range(n))
            sonuc.append(dict(senaryo=ad, kayip=p, rtt_ms=rtt * 1000, ch_seg=ch, sf_seg=sf,
                              ortalama_ms=round(1000 * st.fmean(ts), 1),
                              medyan_ms=round(1000 * ts[n // 2], 1),
                              p95_ms=round(1000 * ts[int(0.95 * n)], 1),
                              gecikme_olasiligi=round(sum(t > 2 * rtt + 1e-9 for t in ts) / n, 4),
                              analitik_olasilik=round(1 - (1 - p) ** (2 + ch + sf), 4)))
    return sonuc


# ---------------------------------------------------------------------------
# Grafikler
# ---------------------------------------------------------------------------
RENK = {"pq": "#1b7f5a", "klasik": "#4a78c2", "tls12": "#c75b39", "gri": "#8a8f98", "koyu": "#22262e"}


def grafikler(ozet, ok, tur1, tur2, sim20, klasor):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10.5,
                         "axes.spines.top": False, "axes.spines.right": False})

    # Şekil: sektör bazında yığılmış hazırlık
    s = [o for o in ozet if o["sektor"] != "TÜMÜ"]
    ad = [o["sektor"] + f"\n(n={o['n']})" for o in s]
    pq = [o["pq"] for o in s]
    kl = [round(o["tls13"] - o["pq"], 1) for o in s]
    t12 = [o["tls12"] for o in s]
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.barh(ad, pq, color=RENK["pq"], label="Kuantum sonrası hazır (X25519MLKEM768)")
    ax.barh(ad, kl, left=pq, color=RENK["klasik"], label="Yalnız klasik TLS 1.3")
    ax.barh(ad, t12, left=[a + b for a, b in zip(pq, kl)], color=RENK["tls12"], label="Yalnız TLS 1.2")
    for i, o in enumerate(s):
        lo, hi = o["pq_ci"]
        ax.plot([lo, hi], [i, i], color="black", lw=1.2)
        ax.text(101, i, f"PQ %{o['pq']:.1f}".replace(".", ","), va="center", fontsize=9)
    ax.set_xlim(0, 115)
    ax.set_xlabel("Sitelerin yüzdesi (%)  —  siyah çizgi: PQ oranı için %95 Wilson güven aralığı")
    ax.invert_yaxis()
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.18), ncol=2, frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(klasor, "sekil_sektor_hazirlik.png"), dpi=220)
    plt.close(fig)

    # Şekil: CDN etkisi
    cdn = [r for r in ok if r["_cdnli"]]
    oz = [r for r in ok if not r["_cdnli"]]
    a, b = sum(evet(r["pq_destek"]) for r in cdn), sum(evet(r["pq_destek"]) for r in oz)
    fig, ax = plt.subplots(figsize=(6, 3.6))
    deg = [100 * a / len(cdn), 100 * b / len(oz)]
    ci = [wilson(a, len(cdn)), wilson(b, len(oz))]
    x = [f"CDN arkasında\n(n={len(cdn)})", f"Kendi sunucusu\n(n={len(oz)})"]
    ax.bar(x, deg, color=[RENK["pq"], RENK["gri"]], width=0.55)
    for i, (d, (lo, hi)) in enumerate(zip(deg, ci)):
        ax.plot([i, i], [lo, hi], color="black", lw=1.4)
        ax.text(i + 0.08, d + 3, f"%{d:.1f}".replace(".", ","), fontsize=11, fontweight="bold")
    ax.set_ylim(0, 110)
    ax.set_ylabel("Kuantum sonrası destek (%)")
    p_ = stats.fisher_exact([[a, len(cdn) - a], [b, len(oz) - b]])[1]
    ax.set_title(f"Fisher kesin testi: p < {ust_p(p_)}", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(klasor, "sekil_cdn_etkisi.png"), dpi=220)
    plt.close(fig)

    # Şekil: mesaj boyutları ve MSS
    ikili = [r for r in ok if evet(r["pq_destek"])]
    med = lambda k: st.median(sayi(r[k]) for r in ikili)
    tar = st.median(sayi(r["tarayici_clienthello_bayt"]) for r in ok)
    fig, ax = plt.subplots(figsize=(7.2, 4))
    etik = ["ClientHello\nklasik", "ClientHello\nhibrit", "ClientHello\ntarayıcı benzeri\n(iki pay)",
            "ServerHello\nklasik", "ServerHello\nhibrit"]
    deger = [med("klasik_clienthello_bayt"), med("pq_clienthello_bayt"), tar,
             med("klasik_serverhello_bayt"), med("pq_serverhello_bayt")]
    renk = [RENK["klasik"], RENK["pq"], RENK["pq"], RENK["klasik"], RENK["pq"]]
    ax.bar(etik, deger, color=renk, width=0.6)
    for i, v in enumerate(deger):
        ax.text(i, v + 25, f"{int(v)} B", ha="center", fontsize=9.5)
    ax.axhline(1460 - 9, ls="--", color=RENK["tls12"], lw=1.3)
    ax.text(4.45, 1460 - 9 + 30, "Tek TCP segmenti sınırı\n(MSS 1460 − 9 B başlık)", ha="right",
            fontsize=8.5, color=RENK["tls12"])
    ax.set_ylabel("Mesaj boyutu (bayt, medyan)")
    ax.set_ylim(0, 1850)
    fig.tight_layout()
    fig.savefig(os.path.join(klasor, "sekil_mesaj_boyutlari.png"), dpi=220)
    plt.close(fig)

    # Şekil: iki tur RTT karşılaştırması
    t2 = {r["alan_adi"]: r for r in tur2 if r["durum"] == "tamam"}
    xs, ys, cs = [], [], []
    for r in tur1:
        if r["durum"] == "tamam" and r["alan_adi"] in t2:
            xs.append(sayi(r["tcp_rtt_ms"]))
            ys.append(sayi(t2[r["alan_adi"]]["tcp_rtt_ms"]))
            cs.append(RENK["pq"] if r["_cdnli"] else RENK["gri"])
    fig, ax = plt.subplots(figsize=(5, 4.3))
    ax.scatter(xs, ys, c=cs, s=18, alpha=0.85)
    m = max(xs + ys) * 1.05
    ax.plot([0, m], [0, m], color="black", lw=0.8, ls=":")
    ax.set_xlabel("1. tur TCP RTT (ms)")
    ax.set_ylabel("2. tur TCP RTT (ms)")
    ax.scatter([], [], c=RENK["pq"], label="CDN arkasında")
    ax.scatter([], [], c=RENK["gri"], label="Kendi sunucusu")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(klasor, "sekil_rtt_turlar.png"), dpi=220)
    plt.close(fig)

    # Şekil: simülasyon
    fig, axs = plt.subplots(1, 2, figsize=(9.4, 3.9))
    for ad, renk, ls in (("Klasik", RENK["klasik"], "-"), ("Hibrit (tarayıcı)", RENK["pq"], "-"),
                         ("Tarayıcı → klasik sunucu", RENK["tls12"], "--")):
        g = [r for r in sim20 if r["senaryo"] == ad]
        axs[0].plot([100 * r["kayip"] for r in g], [r["ortalama_ms"] for r in g], ls, marker="o", ms=4,
                    color=renk, label=ad)
        axs[1].plot([100 * r["kayip"] for r in g], [100 * r["gecikme_olasiligi"] for r in g], ls, marker="o",
                    ms=4, color=renk, label=ad + " (simülasyon)")
    seg = {r["senaryo"]: (r["ch_seg"], r["sf_seg"]) for r in sim20}
    for (ch, sf), ls in ((seg["Klasik"], ":"), (seg["Hibrit (tarayıcı)"], "-.")):
        xs = [i / 10 for i in range(0, 101)]
        axs[1].plot(xs, [100 * (1 - (1 - x / 100) ** (2 + ch + sf)) for x in xs], ls, color="black", lw=0.9,
                    label=f"Analitik 1−(1−p)^{2 + ch + sf}")
    axs[0].set_title("Ortalama el sıkışma süresi", fontsize=10)
    axs[1].set_title("En az bir yeniden iletim olasılığı", fontsize=10)
    axs[0].set_ylabel("Süre (ms)")
    axs[1].set_ylabel("Olasılık (%)")
    for a_ in axs:
        a_.set_xlabel("Segment kayıp oranı p (%)")
    axs[0].legend(frameon=False, fontsize=8.5)
    axs[1].legend(frameon=False, fontsize=7.5)
    fig.suptitle("Monte Carlo simülasyonu, RTT = 20 ms (ölçülen medyan), her nokta 40 000 tekrar", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(klasor, "sekil_simulasyon_kayip.png"), dpi=220)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--veri", default="../veri")
    ap.add_argument("--cikti", default="../analiz")
    ap.add_argument("--sekiller", default="../sekiller")
    a = ap.parse_args()
    os.makedirs(a.cikti, exist_ok=True)
    os.makedirs(a.sekiller, exist_ok=True)

    tur1 = yukle(os.path.join(a.veri, "sonuclar_1.csv"))
    tur2 = yukle(os.path.join(a.veri, "sonuclar_2.csv"))
    tur3 = yukle(os.path.join(a.veri, "sonuclar_3.csv"))
    cdn_tamamla(tur1, tur2)
    cdn_tamamla(tur3)
    ok = [r for r in tur3 if r["durum"] == "tamam"]   # ana analiz: 3. tur (500 site, Kasım 2026)
    ok1 = [r for r in tur1 if r["durum"] == "tamam"]
    ok2 = [r for r in tur2 if r["durum"] == "tamam"]
    R = {"liste_boyutu": len(tur3), "durumlar": dict(Counter(r["durum"] for r in tur3)),
         "olcum_zamani": [min(r["olcum_zamani"] for r in tur3 if r["olcum_zamani"]),
                          max(r["olcum_zamani"] for r in tur3 if r["olcum_zamani"])],
         "olculemeyen": [(r["sektor"], r["durum"]) for r in tur3 if r["durum"] != "tamam"],
         "tur_bilgisi": "1. tur 7 Eki · 2. tur 8 Eki · 3. tur 22 Kas 2026"}

    # 1) Sektör özetleri
    R["sektor"] = sektor_ozeti(ok)

    # 2) Testler
    def pq_say(g):
        return sum(evet(r["pq_destek"]) for r in g), len(g)
    cdn = [r for r in ok if r["_cdnli"]]
    oz = [r for r in ok if not r["_cdnli"]]
    (a1, n1), (a2, n2) = pq_say(cdn), pq_say(oz)
    R["cdn_fisher"] = dict(cdn=f"{a1}/{n1}", kendi=f"{a2}/{n2}",
                          p=stats.fisher_exact([[a1, n1 - a1], [a2, n2 - a2]])[1],
                          cdn_ci=wilson(a1, n1), kendi_ci=wilson(a2, n2))
    bnk = [r for r in ok if r["sektor"] == "Banka"]
    etk = [r for r in ok if r["sektor"] == "ETicaret"]
    (b1, m1), (b2, m2) = pq_say(bnk), pq_say(etk)
    R["banka_eticaret_fisher"] = dict(banka=f"{b1}/{m1}", eticaret=f"{b2}/{m2}",
                                     p=stats.fisher_exact([[b1, m1 - b1], [b2, m2 - b2]])[1])
    # Kendi sunucusunu işleten siteler içinde sektör farkı var mı? (2xK -> her sektör vs diğerleri)
    oz_sektor = {SEKTOR_AD[s]: pq_say([r for r in oz if r["sektor"] == s]) for s in SEKTOR_SIRA}
    cdn_sektor = {SEKTOR_AD[s]: pq_say([r for r in cdn if r["sektor"] == s]) for s in SEKTOR_SIRA}
    R["katman_kendi_sunucu"] = {k: f"{x}/{n}" for k, (x, n) in oz_sektor.items()}
    R["katman_cdn"] = {k: f"{x}/{n}" for k, (x, n) in cdn_sektor.items()}
    # Ham (katmansız) sektör etkisi: ki-kare
    tablo = [[pq_say([r for r in ok if r["sektor"] == s])[0],
              pq_say([r for r in ok if r["sektor"] == s])[1] - pq_say([r for r in ok if r["sektor"] == s])[0]]
             for s in SEKTOR_SIRA]
    R["sektor_kikare_katmansiz"] = dict(chi2=round(stats.chi2_contingency(tablo)[0], 2),
                                       p=stats.chi2_contingency(tablo)[1])
    g, pval = permutasyon_katmanli(ok)
    R["sektor_permutasyon_cdn_katmanli"] = dict(istatistik=round(g, 3), p=round(pval, 4))

    # CDN dağılımı
    R["cdn_saglayicilar"] = dict(Counter(r["cdn"] for r in cdn))
    R["cdn_ip_duzeltme"] = sorted(r["alan_adi"] for r in ok if r.get("_cdn_kaynak") == "IP bloğu")
    R["cdn_arkasinda_destek_yok"] = [(r["alan_adi"].split(".")[1], r["tls_surumu"]) for r in cdn
                                     if not evet(r["pq_destek"])]
    R["kendi_sunucu_destek_var"] = [r["sektor"] for r in oz if evet(r["pq_destek"])]
    R["hrr"] = [(r["sektor"], r["secilen_grup"]) for r in ok if evet(r["hrr_var"])]
    R["secilen_grup_tls13_pqsiz"] = dict(Counter(r["secilen_grup"] for r in ok
                                                  if evet(r["tls13_destek"]) and not evet(r["pq_destek"])))
    sert = Counter((r["sertifika_anahtar"] or "EC", r["sertifika_bit"]) for r in ok)
    R["sertifika"] = {f"{k}-{b}": v for (k, b), v in sert.items()}

    # 3) Ağ maliyeti
    ikili = [r for r in ok if evet(r["pq_destek"])]
    def med(k, g=ikili):
        return st.median(sayi(r[k]) for r in g if sayi(r[k]) is not None)
    R["ag"] = dict(
        n=len(ikili),
        ch_klasik=med("klasik_clienthello_bayt"), ch_hibrit=med("pq_clienthello_bayt"),
        sh_klasik=med("klasik_serverhello_bayt"), sh_hibrit=med("pq_serverhello_bayt"),
        sh_hibrit_min=min(sayi(r["pq_serverhello_bayt"]) for r in ikili),
        sh_hibrit_max=max(sayi(r["pq_serverhello_bayt"]) for r in ikili),
        yazilan_fark=med_fark(ikili, "pq_yazilan_bayt", "klasik_yazilan_bayt"),
        okunan_fark=med_fark(ikili, "pq_okunan_bayt", "klasik_okunan_bayt"),
        okunan_klasik=med("klasik_okunan_bayt"), okunan_hibrit=med("pq_okunan_bayt"),
        tarayici_ch_medyan=med("tarayici_clienthello_bayt", ok),
        tarayici_ch_min=min(sayi(r["tarayici_clienthello_bayt"]) for r in ok),
        tarayici_ch_max=max(sayi(r["tarayici_clienthello_bayt"]) for r in ok),
        tarayici_iki_segment=sum(sayi(r["tarayici_clienthello_segment_tahmini"]) == 2 for r in ok),
        sure_farki_medyan_tur2=med_fark(ikili, "pq_sure_ms", "klasik_sure_ms"),
        sure_farki_medyan_tur1=med_fark([r for r in ok1 if evet(r["pq_destek"])], "pq_sure_ms", "klasik_sure_ms"),
        rtt_medyan_tur1=st.median(sayi(r["tcp_rtt_ms"]) for r in ok1),
        rtt_medyan_tur2=st.median(sayi(r["tcp_rtt_ms"]) for r in ok2),
        rtt_medyan_tur3=st.median(sayi(r["tcp_rtt_ms"]) for r in ok),
        rtt_medyan_cdn=st.median(sayi(r["tcp_rtt_ms"]) for r in cdn),
        rtt_medyan_kendi=st.median(sayi(r["tcp_rtt_ms"]) for r in oz),
    )
    # Wilcoxon işaretli sıra testi: hibrit - klasik süre farkı (tur 2)
    farklar = [sayi(r["pq_sure_ms"]) - sayi(r["klasik_sure_ms"]) for r in ikili]
    R["ag"]["sure_wilcoxon_p"] = stats.wilcoxon(farklar).pvalue
    # Tur tutarlılığı (Ekim: 1. ve 2. tur, 130 site)
    t1 = {r["alan_adi"]: r for r in ok1}
    ayni = sum(1 for r in ok2 if r["alan_adi"] in t1 and all(
        r[k] == t1[r["alan_adi"]][k] for k in ("tls_surumu", "pq_destek", "secilen_grup", "hrr_var",
                                                 "tls12_kabul", "sertifika_anahtar", "sertifika_bit")))
    ip_degisen = sum(1 for r in ok2 if r["alan_adi"] in t1 and r["ip"] != t1[r["alan_adi"]]["ip"])
    x = [sayi(t1[r["alan_adi"]]["tcp_rtt_ms"]) for r in ok2]
    y = [sayi(r["tcp_rtt_ms"]) for r in ok2]
    R["tutarlilik"] = dict(ayni_site=ayni, toplam=len(ok2), ip_degisen=ip_degisen,
                           rtt_pearson=round(stats.pearsonr(x, y)[0], 2),
                           rtt_ort_mutlak_fark=round(st.fmean(abs(a_ - b_) for a_, b_ in zip(x, y)), 1))
    # Zaman içi değişim (Ekim 2. tur → Kasım 3. tur; iki turda da ölçülen siteler)
    t3 = {r["alan_adi"]: r for r in ok}
    ortak = [r for r in ok2 if r["alan_adi"] in t3]
    degisim = []
    for r in ortak:
        y_ = t3[r["alan_adi"]]
        if (r["pq_destek"], r["tls_surumu"]) != (y_["pq_destek"], y_["tls_surumu"]):
            degisim.append(dict(sektor=SEKTOR_AD[r["sektor"]], eski_tls=r["tls_surumu"], eski_pq=evet(r["pq_destek"]),
                                yeni_tls=y_["tls_surumu"], yeni_pq=evet(y_["pq_destek"]),
                                cdn_eski=r["_cdnli"], cdn_yeni=y_["_cdnli"]))
    R["zaman"] = dict(ortak=len(ortak),
                      pq_ekim=sum(evet(r["pq_destek"]) for r in ortak),
                      pq_kasim=sum(evet(t3[r["alan_adi"]]["pq_destek"]) for r in ortak),
                      tls13_ekim=sum(evet(r["tls13_destek"]) for r in ortak),
                      tls13_kasim=sum(evet(t3[r["alan_adi"]]["tls13_destek"]) for r in ortak),
                      pq_kazanan=sum(1 for d in degisim if d["yeni_pq"] and not d["eski_pq"]),
                      pq_kaybeden=sum(1 for d in degisim if d["eski_pq"] and not d["yeni_pq"]),
                      tls_yukselten=sum(1 for d in degisim if d["eski_tls"] == "TLSv1.2" and d["yeni_tls"] == "TLSv1.3"),
                      kazanan_kendi_sunucu=sum(1 for d in degisim if d["yeni_pq"] and not d["eski_pq"] and not d["cdn_yeni"]),
                      degisimler=degisim)
    R["kendi_sunucu_pq_sunucu_basligi"] = dict(Counter((r["server_basligi"] or "(boş)").split("/")[0]
                                                       for r in ok if not r["_cdnli"] and evet(r["pq_destek"])))
    R["cdn_kaynak"] = dict(Counter(r.get("_cdn_kaynak", "başlık") for r in ok if r["_cdnli"]))
    R["cdn_pq"] = {ad: f"{sum(evet(r['pq_destek']) for r in ok if r['cdn'] == ad)}/{sum(1 for r in ok if r['cdn'] == ad)}"
                   for ad in sorted({r["cdn"] for r in ok if r["_cdnli"]})}
    R["tls12_yalniz"] = sum(1 for r in ok if not evet(r["tls13_destek"]))

    # Bant genişliği / ölçek analizi
    ek = R["ag"]["yazilan_fark"] + R["ag"]["okunan_fark"]
    R["olcek"] = dict(ek_bayt_el_sikisma=ek,
                      gunluk_1milyon_el_sikisma_GB=round(ek * 1e6 / 1e9, 2),
                      sayfa_2MB_orani_yuzde=round(100 * ek / 2_000_000, 3))

    # 4) Simülasyon
    sf_klasik = math.ceil(R["ag"]["okunan_klasik"] / 1460)
    sf_hibrit = math.ceil(R["ag"]["okunan_hibrit"] / 1460)
    senaryolar = [("Klasik", 1, sf_klasik), ("Hibrit (tarayıcı)", 2, sf_hibrit),
                  ("Tarayıcı → klasik sunucu", 2, sf_klasik)]
    kayiplar = [0.0, 0.005, 0.01, 0.02, 0.05, 0.10]
    sim20 = simulasyon(senaryolar, kayiplar, 0.020)
    sim65 = simulasyon(senaryolar, kayiplar, 0.065)
    R["simulasyon"] = dict(sf_klasik_seg=sf_klasik, sf_hibrit_seg=sf_hibrit, rtt20=sim20, rtt65=sim65)

    with open(os.path.join(a.cikti, "ek_analiz.json"), "w", encoding="utf-8") as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(a.cikti, "simulasyon.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sim20[0].keys()))
        w.writeheader()
        w.writerows(sim20 + sim65)
    grafikler(R["sektor"], ok, tur1, tur2, sim20, a.sekiller)
    print(json.dumps({k: v for k, v in R.items() if k != "simulasyon"}, ensure_ascii=False, indent=1, default=str))
    for r in sim20 + sim65:
        print(r)


def med_fark(g, a, b):
    return st.median(sayi(r[a]) - sayi(r[b]) for r in g if sayi(r[a]) is not None and sayi(r[b]) is not None)


if __name__ == "__main__":
    main()
