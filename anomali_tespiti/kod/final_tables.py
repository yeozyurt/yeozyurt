"""Tüm sonuç tabloları (markdown + csv) ve istatistik testleri."""
import numpy as np, pandas as pd
from scipy.stats import wilcoxon
from pathlib import Path
O = Path("tablolar"); O.mkdir(exist_ok=True)
SN = ["6", "0", "-6"]; md = []
def fmt(g):  # g: DataFrame index rows, cols SN, values (mean,std)
    return g
def summ(d, met="auc"):
    """önce 4 ID ortalaması (tohum başına), sonra tohumlar üzerinden ortalama ± std"""
    a = d.groupby(["snr", "seed"])[met].mean().groupby("snr").agg(["mean", "std"]).reindex(SN)
    return [f"{m:.3f} ± {s:.3f}" if not np.isnan(s) else f"{m:.3f}" for m, s in zip(a["mean"], a["std"])]
TABLES = {}
def table(title, rows, cols=("Yöntem", "+6 dB", "0 dB", "−6 dB")):
    TABLES[title.split(":")[0]] = dict(title=title, cols=list(cols), rows=[list(map(str, r)) for r in rows])
    md.append(f"\n### {title}\n\n| " + " | ".join(cols) + " |\n|" + "---|" * len(cols))
    for r in rows: md.append("| " + " | ".join(map(str, r)) + " |")
D = pd.read_csv("ozet_denge.csv", dtype={"snr": str})
T = pd.read_csv("ozet_tez.csv", dtype={"snr": str}) if Path("ozet_tez.csv").exists() else None
S = pd.read_csv("sel_h_ch1.csv", dtype={"snr": str})
def sel_best(S, sel, det, proto="F", by="sel_auc"):
    x = S[(S.protocol == proto) & (S.selector == sel) & (S.detector == det)]
    return x.loc[x.groupby(["snr", "id", "seed"])[by].idxmax()]
MAIN = [("Dense AE, log-mel (Hafta 3-6 temel)", "dense_ae", "ch1"),
        ("El yapımı 145 öznitelik + kNN", "el_knn", "ch1"),
        ("Log-mel bant istatistiği + kNN, 8 kanal güç ort.", "bant_knn", "gort8"),
        ("Makine ID sınıflandırıcısı (CNN)", "id_sinif", "ch1"),
        ("ID-XAI + kNN topluluğu, 1. kanal", "idxai_ens", "ch1"),
        ("ID-XAI + kNN topluluğu, 1. kanal + 8 kanal ort. (önerilen)", "idxai_ens", "both"),
        ("Füzyon: ID sınıflandırıcısı + önerilen", "fuzyon(id_sinif+idxai_ens_both)", "-")]
for met in ("auc", "pauc"):
    rows = [(n, *summ(D[(D.method == m) & (D["mode"] == mo)], met)) for n, m, mo in MAIN if len(D[(D.method == m) & (D["mode"] == mo)])]
    for det in ("knn", "ae"):
        b = sel_best(S, "etiket_F", det); rows.append((f"Referans (yarı gözetimli): arıza etiketli XAI seçimi + {det.upper()}, Protokol F", *summ(b, met)))
    table(f"Tablo A ({met.upper()}): dengeli protokol, 4 fan ID ortalaması, 3 tohum (ort. ± std)", rows)
# ID bazında önerilen
x = D[(D.method == "idxai_ens") & (D["mode"] == "both")]
t = x.groupby(["id", "snr"]).auc.mean().unstack()[SN]
table("Tablo B: önerilen yöntem, ID bazında AUC (3 tohum ort.)", [(i, *[f"{v:.3f}" for v in r]) for i, r in t.iterrows()] + [("Ortalama", *[f"{v:.3f}" for v in t.mean()])], ("ID", "+6 dB", "0 dB", "−6 dB"))
# literatür
LIT = [("MIMII baseline AE [Purohit 2019]", .913, .795, .663), ("AE [MemNMF Tablo III]", .953, .849, .687), ("VAE", .948, .849, .715), ("GRLNet", .953, .866, .699),
       ("MemNMF-768 (2026)", .929, .873, .764), ("Li vd. 2024, LNS-AE", .950, .862, .716), ("Li vd. 2024, en iyi (TM-LGS)", .971, .902, .762)]
ours = x.groupby(["snr", "seed"]).auc.mean().groupby("snr").mean().reindex(SN)
table("Tablo C: literatürle kıyas (fan, 4 ID ortalaması, etiketsiz, AUC)", [(n, a, b, c) for n, a, b, c in LIT] + [("Bu çalışma: ID-XAI topluluğu (etiketsiz)", *[f"{v:.3f}" for v in ours])])
# tez kıyası (+6 dB, ID bazında)
tz = {"id_00": .9880, "id_02": .9998, "id_04": .9936, "id_06": 1.0}
rows = [("Tez: XAI seçimli AE (etiketli seçim)", *[f"{tz[i]:.4f}" for i in tz], f"{np.mean(list(tz.values())):.4f}")]
for det in ("ae", "knn", "if"):
    b = sel_best(S, "etiket_tez", det, "tez", "auc"); b = b[b.snr == "6"].groupby("id").auc.mean()
    rows.append((f"Bu çalışma, tez protokolü, etiketli seçim + {det.upper()} (en iyi k)", *[f"{b[i]:.4f}" for i in tz], f"{b.mean():.4f}"))
if T is not None:
    for mo, lab in (("both", "1. kanal + 8 kanal ort."), ("ort8", "8 kanal ort."), ("ch1", "1. kanal")):
        y = T[(T.method == "idxai_ens") & (T["mode"] == mo) & (T.snr == "6")].groupby("id").auc.mean()
        if len(y): rows.append((f"Bu çalışma, tez protokolü, ETİKETSİZ ID-XAI ({lab})", *[f"{y[i]:.4f}" for i in tz], f"{y.mean():.4f}"))
table("Tablo D: +6 dB'de tezle kıyas (tez protokolü, AUC)", rows, ("Yöntem", "id_00", "id_02", "id_04", "id_06", "Ort."))
# ablasyonlar: k ve detektör (Protokol F, id_xai)
x = S[(S.protocol == "F") & (S.selector.isin(["id_xai", "tum"]))]
g = x.groupby(["selector", "k", "detector", "snr", "seed"]).auc.mean().groupby(["selector", "k", "detector", "snr"]).mean().unstack("snr")[SN]
table("Tablo E: ID-XAI ablasyonu (Protokol F, 4 ID ort., 3 tohum): öznitelik sayısı k ve detektör", [(f"{'tüm öznitelik' if s == 'tum' else 'ID-XAI'}, k={k}, {d.upper()}", *[f"{v:.3f}" for v in r]) for (s, k, d), r in g.iterrows()])
for tn, f, lab in (("F1", "sel_h_ch1_seviyesiz.csv", "seviye öznitelikleri çıkarılmış (89 öznitelik)"), ("F2", "sel_h_ort8.csv", "8 kanal ortalaması öznitelikleri")):
    if not Path(f).exists(): continue
    z = pd.read_csv(f, dtype={"snr": str}); z = z[z.protocol == "F"]
    g = z.groupby(["selector", "k", "detector", "snr", "seed"]).auc.mean().groupby(["selector", "k", "detector", "snr"]).mean().unstack("snr").reindex(columns=SN)
    table(f"Tablo {tn}: {lab}, Protokol F", [(f"{s}, k={k}, {d.upper()}", *[f"{v:.3f}" for v in r]) for (s, k, d), r in g.iterrows()])
# Wilcoxon: önerilen vs diğerleri (ID x tohum çiftleri)
rows = []
P = D[(D.method == "idxai_ens") & (D["mode"] == "both")].set_index(["snr", "id", "seed"]).auc
for n, m, mo in MAIN:
    if m == "idxai_ens" and mo == "both": continue
    Q = D[(D.method == m) & (D["mode"] == mo)].set_index(["snr", "id", "seed"]).auc
    r = [n]
    for s in SN:
        a, b = P.loc[s].align(Q.loc[s] if s in Q.index.get_level_values(0) else Q.iloc[:0], join="inner") if s in Q.index.get_level_values(0) else (None, None)
        if a is None or len(a) < 5: r.append("-"); continue
        diff = (a - b).mean(); p = wilcoxon(a, b).pvalue if (a != b).any() else 1.0
        r.append(f"{diff:+.3f} (p={p:.3g}, n={len(a)})")
    rows.append(r)
table("Tablo G: önerilen yönteme göre AUC farkı (önerilen − yöntem), Wilcoxon işaretli sıra testi, ID×tohum çiftleri", rows)
Path("tablolar/tablolar.md").write_text("\n".join(md)); print("\n".join(md))
import json; Path("tablolar/tablolar.json").write_text(json.dumps(TABLES, ensure_ascii=False, indent=1))
