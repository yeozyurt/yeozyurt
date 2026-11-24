"""Hafta 9-10 şekilleri."""
import pandas as pd, numpy as np, matplotlib, matplotlib.ticker; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d = pd.read_csv("ozet_denge.csv", dtype={"snr": str}); SN = ["6", "0", "-6"]; X = [6, 0, -6]
SEL = [("dense_ae", "ch1", "Dense AE, log-mel (önceki temel)", "#9aa0a6", "o"),
       ("el_knn", "ch1", "145 öznitelik + kNN (seçimsiz)", "#e8710a", "s"),
       ("id_sinif", "ch1", "Makine ID sınıflandırıcısı (CNN)", "#1a73e8", "^"),
       ("idxai_ens", "both", "ID-XAI + kNN topluluğu (önerilen)", "#188038", "D")]
LIT = {"MIMII baseline AE": [.913, .795, .663], "MemNMF (2026)": [.929, .873, .764], "Li vd. (2024) en iyi": [.971, .902, .762]}
fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.5))
for k, met in enumerate(["auc", "pauc"]):
    for meth, mode, lab, c, mk in SEL:
        r = d[(d.method == meth) & (d["mode"] == mode)]
        if r.empty: continue
        g = r.groupby(["snr", "seed"])[met].mean().groupby("snr").agg(["mean", "std"]).reindex(SN)
        ax[k].errorbar(X, g["mean"], yerr=g["std"].fillna(0), label=lab, color=c, marker=mk, capsize=3, lw=2)
    if met == "auc":
        for (n, v), ls in zip(LIT.items(), [":", "-.", "--"]): ax[k].plot(X, v, ls, color="k", lw=1, alpha=.6, label=f"Literatür: {n}")
    ax[k].axhline(0.5, ls="--", c="grey", lw=0.7); ax[k].set_xticks(X); ax[k].set_xticklabels(["+6 dB", "0 dB", "−6 dB"]); ax[k].invert_xaxis()
    ax[k].set_ylim(0.45, 1.01); ax[k].set_title(("AUC" if met == "auc" else "pAUC (FPR ≤ 0,1)") + ", 4 fan ID ortalaması"); ax[k].grid(alpha=.3); ax[k].set_xlabel("SNR (sağa doğru gürültü artıyor)")
ax[0].legend(fontsize=7.5, loc="lower left"); plt.tight_layout(); plt.savefig("sekil8_hafta9.png", dpi=170)
fig, ax = plt.subplots(1, 4, figsize=(16, 3.6))
for k, (meth, mode, lab, _, _) in enumerate(SEL):
    r = d[(d.method == meth) & (d["mode"] == mode)]
    t = r.groupby(["id", "snr"]).auc.mean().unstack().reindex(columns=SN)
    im = ax[k].imshow(t.values, vmin=0.5, vmax=1, cmap="viridis")
    for i in range(t.shape[0]):
        for j in range(t.shape[1]):
            v = t.values[i, j]
            if not np.isnan(v): ax[k].text(j, i, f"{v:.2f}", ha="center", va="center", color="w" if v < .8 else "k", fontsize=9)
    ax[k].set_xticks(range(3)); ax[k].set_xticklabels(["+6", "0", "−6"]); ax[k].set_yticks(range(len(t))); ax[k].set_yticklabels(t.index); ax[k].set_title(lab, fontsize=8.5)
fig.colorbar(im, ax=ax, shrink=.85, label="AUC"); plt.savefig("sekil9_hafta9.png", dpi=170, bbox_inches="tight")
S = pd.read_csv("sel_h_ch1.csv", dtype={"snr": str}); S = S[(S.protocol == "F") & (S.detector == "knn")]
fig, ax = plt.subplots(1, 3, figsize=(13, 3.8), sharey=True)
for j, s in enumerate(SN):
    for sel, lab, c in (("etiket_F", "Arıza etiketli XAI seçimi (yarı gözetimli)", "#d93025"), ("id_xai", "ID-XAI (etiketsiz, önerilen)", "#188038")):
        g = S[(S.snr == s) & (S.selector == sel)].groupby(["k", "seed"]).auc.mean().groupby("k").agg(["mean", "std"])
        ax[j].errorbar(g.index, g["mean"], yerr=g["std"], marker="o", capsize=3, color=c, label=lab)
    a = S[(S.snr == s) & (S.selector == "tum")].groupby("seed").auc.mean().mean()
    ax[j].axhline(a, color="#e8710a", ls="--", label="Tüm 145 öznitelik"); ax[j].set_xscale("log"); ax[j].set_xticks([5, 10, 20, 33, 60]); ax[j].set_xticklabels([5, 10, 20, 33, 60]); ax[j].xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax[j].set_title(f"{'+' if s == '6' else ''}{s} dB"); ax[j].set_xlabel("seçilen öznitelik sayısı k"); ax[j].grid(alpha=.3)
ax[0].set_ylabel("AUC (kNN, Protokol F)"); ax[0].legend(fontsize=7.5); plt.tight_layout(); plt.savefig("sekil10_hafta10.png", dpi=170)
print("şekiller kaydedildi")
