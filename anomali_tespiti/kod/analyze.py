"""Sonuç tabloları + skor füzyonu. Kullanım: python analyze.py [denge|tez]"""
import sys, numpy as np, pandas as pd
from pathlib import Path
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score
proto = sys.argv[1] if len(sys.argv) > 1 else "denge"
SC = Path("scores" if proto == "denge" else "scores_tez")
rows = []
for f in SC.glob("*.npz"):
    snr, mid1, mid2, mode, *meth, seed = f.stem.split("_")
    d = np.load(f); rows.append(dict(snr=snr, id=mid1 + "_" + mid2, mode=mode, method="_".join(meth), seed=int(seed), s=d["s"], y=d["y"]))
D = pd.DataFrame(rows)
def get(snr, mid, mode, meth, seed):
    r = D[(D.snr == snr) & (D.id == mid) & (D["mode"] == mode) & (D.method == meth) & (D.seed == seed)]
    return (r.iloc[0].s, r.iloc[0].y) if len(r) else (None, None)
# füzyon: etiket kullanmadan, test skorlarının sıra (rank) ortalaması
FUS = {"fuzyon(id_sinif+el_knn)": [("ch1", "id_sinif"), ("ch1", "el_knn")],
       "fuzyon(id_sinif_ch1+id_sinif_gort8+el_knn)": [("ch1", "id_sinif"), ("gort8", "id_sinif"), ("ch1", "el_knn")],
       "fuzyon(id_sinif+idxai_ens_both)": [("ch1", "id_sinif"), ("both", "idxai_ens")]}
for (snr, mid, seed), _ in D.groupby(["snr", "id", "seed"]):
    for name, parts in FUS.items():
        ss = [get(snr, mid, mo, me, seed) for mo, me in parts]
        if any(s is None for s, _ in ss): continue
        s = np.mean([rankdata(s) / len(s) for s, _ in ss], 0)
        rows.append(dict(snr=snr, id=mid, mode="-", method=name, seed=seed, s=s, y=ss[0][1]))
D = pd.DataFrame(rows)
D["auc"] = [roc_auc_score(y, s) for y, s in zip(D.y, D.s)]
D["pauc"] = [roc_auc_score(y, s, max_fpr=0.1) for y, s in zip(D.y, D.s)]
D.drop(columns=["s", "y"]).to_csv(f"ozet_{proto}.csv", index=False)
for met in ("auc", "pauc"):
    g = D.groupby(["method", "mode", "snr", "id"])[met].mean().unstack("id")
    g["ort"] = g.mean(axis=1)
    print(f"\n==== {proto} | {met} (tohum ortalaması) ====")
    print(g.round(3).to_string())
