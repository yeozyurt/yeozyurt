#!/usr/bin/env python3
"""
Ölçüm sonuçlarının sektör bazında analizi.

Kullanım:
  python3 analiz.py --girdi sonuclar.csv --cikti-klasoru rapor

Üretilenler:
  rapor/ozet_sektor.csv   Sektör bazında oranlar ve medyanlar
  rapor/ozet.md           Makaleye aktarılabilir Markdown tablolar
  rapor/*.png             Grafikler (matplotlib kuruluysa)
"""

import argparse
import csv
import os
import statistics
from collections import defaultdict


def evet(x):
    return str(x).strip().lower() == "true"


def sayi(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def yuzde(pay, payda):
    return round(100 * pay / payda, 1) if payda else None


def medyan(degerler):
    d = [v for v in degerler if v is not None]
    return round(statistics.median(d), 1) if d else None


def ozetle(satirlar):
    """Bir site grubunun (sektör veya tümü) özet istatistikleri."""
    ok = [r for r in satirlar if r["durum"] == "tamam"]
    n = len(ok)
    cdnli = [r for r in ok if r["cdn"] not in ("", "Yok/Bilinmiyor")]
    cdnsiz = [r for r in ok if r["cdn"] in ("", "Yok/Bilinmiyor")]
    ikili = [r for r in ok if sayi(r["pq_sure_ms"]) and sayi(r["klasik_sure_ms"])]
    return {
        "toplam_site": len(satirlar),
        "olculen_site": n,
        "tls13_%": yuzde(sum(evet(r["tls13_destek"]) for r in ok), n),
        "yalniz_tls12_%": yuzde(sum(not evet(r["tls13_destek"]) for r in ok), n),
        "pq_destek_%": yuzde(sum(evet(r["pq_destek"]) for r in ok), n),
        "tarayicida_pq_secilen_%": yuzde(sum(r["secilen_grup"] == "X25519MLKEM768" for r in ok), n),
        "hrr_%": yuzde(sum(evet(r["hrr_var"]) for r in ok), n),
        "http3_%": yuzde(sum(evet(r["http3_ilani"]) for r in ok), n),
        "cdn_%": yuzde(len(cdnli), n),
        "pq_destek_cdnli_%": yuzde(sum(evet(r["pq_destek"]) for r in cdnli), len(cdnli)),
        "pq_destek_cdnsiz_%": yuzde(sum(evet(r["pq_destek"]) for r in cdnsiz), len(cdnsiz)),
        "ecdsa_sertifika_%": yuzde(sum("EC" in (r["sertifika_anahtar"] or "") for r in ok), n),
        "medyan_rtt_ms": medyan(sayi(r["tcp_rtt_ms"]) for r in ok),
        "medyan_klasik_sure_ms": medyan(sayi(r["klasik_sure_ms"]) for r in ikili),
        "medyan_pq_sure_ms": medyan(sayi(r["pq_sure_ms"]) for r in ikili),
        "medyan_sure_farki_ms": medyan(sayi(r["pq_sure_ms"]) - sayi(r["klasik_sure_ms"]) for r in ikili),
        "medyan_serverhello_klasik_bayt": medyan(sayi(r["klasik_serverhello_bayt"]) for r in ikili),
        "medyan_serverhello_pq_bayt": medyan(sayi(r["pq_serverhello_bayt"]) for r in ikili),
        "medyan_tarayici_clienthello_bayt": medyan(sayi(r["tarayici_clienthello_bayt"]) for r in ok),
    }


def markdown_tablo(basliklar, satirlar):
    out = ["| " + " | ".join(basliklar) + " |", "|" + "---|" * len(basliklar)]
    for s in satirlar:
        out.append("| " + " | ".join("–" if v is None else str(v) for v in s) + " |")
    return "\n".join(out)


def grafikler(ozet, klasor):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib kurulu değil; grafikler atlandı (pip install matplotlib).")
        return
    sektorler = [s for s in ozet if s != "TÜMÜ"]

    # 1) Sektör bazında hazırlık
    fig, ax = plt.subplots(figsize=(8, 4.5))
    metrikler = [("tls13_%", "TLS 1.3"), ("pq_destek_%", "Kuantum sonrası (X25519MLKEM768)"),
                 ("http3_%", "HTTP/3 ilanı")]
    gen = 0.8 / len(metrikler)
    for i, (k, ad) in enumerate(metrikler):
        ax.bar([x + i * gen for x in range(len(sektorler))],
               [ozet[s][k] or 0 for s in sektorler], gen, label=ad)
    ax.set_xticks([x + gen for x in range(len(sektorler))], sektorler)
    ax.set_ylabel("Sitelerin yüzdesi (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Sektöre göre TLS 1.3, kuantum sonrası ve HTTP/3 desteği")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(klasor, "sektor_hazirlik.png"), dpi=200)
    plt.close(fig)

    # 2) CDN etkisi
    fig, ax = plt.subplots(figsize=(8, 4))
    x = range(len(sektorler))
    ax.bar([i - 0.2 for i in x], [ozet[s]["pq_destek_cdnli_%"] or 0 for s in sektorler], 0.4, label="CDN arkasında")
    ax.bar([i + 0.2 for i in x], [ozet[s]["pq_destek_cdnsiz_%"] or 0 for s in sektorler], 0.4, label="Kendi sunucusu")
    ax.set_xticks(list(x), sektorler)
    ax.set_ylabel("PQ destekleyen site (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Kuantum sonrası destek: CDN ve kendi sunucusu")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(klasor, "cdn_etkisi.png"), dpi=200)
    plt.close(fig)
    print(f"Grafikler {klasor}/ altına kaydedildi.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--girdi", default="sonuclar.csv")
    ap.add_argument("--cikti-klasoru", default="rapor")
    a = ap.parse_args()
    os.makedirs(a.cikti_klasoru, exist_ok=True)

    with open(a.girdi, newline="", encoding="utf-8") as f:
        satirlar = list(csv.DictReader(f))
    gruplar = defaultdict(list)
    for r in satirlar:
        gruplar[r["sektor"]].append(r)

    ozet = {s: ozetle(g) for s, g in sorted(gruplar.items())}
    ozet["TÜMÜ"] = ozetle(satirlar)

    alanlar = list(ozet["TÜMÜ"].keys())
    with open(os.path.join(a.cikti_klasoru, "ozet_sektor.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sektor"] + alanlar)
        for s, o in ozet.items():
            w.writerow([s] + [o[k] for k in alanlar])

    t1 = markdown_tablo(
        ["Sektör", "Ölçülen", "TLS 1.3 (%)", "Yalnız TLS 1.2 (%)", "PQ destek (%)", "HTTP/3 (%)", "CDN (%)"],
        [[s, o["olculen_site"], o["tls13_%"], o["yalniz_tls12_%"], o["pq_destek_%"], o["http3_%"], o["cdn_%"]]
         for s, o in ozet.items()])
    t2 = markdown_tablo(
        ["Sektör", "RTT (ms)", "Klasik el sıkışma (ms)", "Hibrit el sıkışma (ms)", "Fark (ms)",
         "ServerHello klasik (B)", "ServerHello hibrit (B)"],
        [[s, o["medyan_rtt_ms"], o["medyan_klasik_sure_ms"], o["medyan_pq_sure_ms"], o["medyan_sure_farki_ms"],
          o["medyan_serverhello_klasik_bayt"], o["medyan_serverhello_pq_bayt"]] for s, o in ozet.items()])
    durumlar = defaultdict(int)
    for r in satirlar:
        durumlar[r["durum"]] += 1
    t3 = markdown_tablo(["Durum", "Site sayısı"], sorted(durumlar.items()))

    with open(os.path.join(a.cikti_klasoru, "ozet.md"), "w", encoding="utf-8") as f:
        f.write("# Ölçüm Özeti\n\n## Hazırlık oranları\n\n" + t1 +
                "\n\n## Ağ performansı (medyan değerler)\n\n" + t2 +
                "\n\nNot: El sıkışma süreleri openssl s_client'ın duvar saati süresidir; süreç başlatma "
                "yükü iki modda da aynı olduğundan fark sütunu karşılaştırma için kullanılmalıdır.\n\n"
                "## Ölçüm durumu\n\n" + t3 + "\n")
    print(t1, "\n")
    print(t2, "\n")
    grafikler(ozet, a.cikti_klasoru)


if __name__ == "__main__":
    main()
