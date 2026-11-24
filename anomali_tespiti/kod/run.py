import sys, csv, time, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); from exp import *
from sklearn.ensemble import IsolationForest
snr, ids, methods = sys.argv[1], sys.argv[2].split(","), sys.argv[3].split(",")
modes = sys.argv[4].split(",") if len(sys.argv) > 4 else ["ch1", "ort8", "gort8"]
seeds = [int(s) for s in sys.argv[5].split(",")] if len(sys.argv) > 5 else [42, 43, 44]
import os
PROTO = os.environ.get("PROTO", "denge")
FE = Path("feat"); OUT = Path("results.csv" if PROTO == "denge" else "results_tez.csv")
D = {m: np.load(FE / f"lm_{snr}_{m}.npz") for m in ids}
SC = Path("scores" if PROTO == "denge" else "scores_tez"); SC.mkdir(exist_ok=True)
def log(scores=None, y=None, **r):
    if scores is not None:
        r["auc"], r["pauc"] = auc2(y, scores)
        np.savez(SC / f"{r['snr']}_{r['id']}_{r['mode']}_{r['method']}_{r['seed']}.npz", s=scores, y=y)
    new = not OUT.exists()
    with open(OUT, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["snr", "id", "mode", "method", "seed", "auc", "pauc"]); new and w.writeheader(); w.writerow(r)
    print(r, flush=True)
for seed in seeds:
    for mode in modes:
        sp = {m: split(D[m]["y"], seed) for m in ids}
        S = {m: D[m][mode] for m in ids} if mode != "both" else None
        for m in ids:
            tr, te = sp[m]; y = D[m]["y"][te]
            if "knn" in methods:
                F = np.array([bandstats(s) for s in S[m]]); log(snr=snr, id=m, mode=mode, method="bant_knn", seed=seed, scores=knn_score(F[tr], F[te]), y=y)
            if "hand" in methods and mode != "gort8":
                H = D[m]["h_" + mode]; mu, sd = H[tr].mean(0), H[tr].std(0) + 1e-6; Z = (H - mu) / sd
                log(snr=snr, id=m, mode=mode, method="el_knn", seed=seed, scores=knn_score(H[tr], H[te]), y=y)
                ifs = -IsolationForest(n_estimators=200, random_state=seed).fit(Z[tr]).score_samples(Z[te])
                log(snr=snr, id=m, mode=mode, method="el_if", seed=seed, scores=ifs, y=y)
            if "dense" in methods:
                sc = dense_ae([S[m][i] for i in tr], [S[m][i] for i in te], seed)
                log(snr=snr, id=m, mode=mode, method="dense_ae", seed=seed, scores=sc, y=y)
        if "idxai" in methods and mode in ("ch1", "ort8", "both"):
            getH = lambda m: np.concatenate([D[m]["h_ch1"], D[m]["h_ort8"]], 1) if mode == "both" else D[m]["h_" + mode]
            out = idxai_scores({m: getH(m) for m in ids}, {m: sp[m][0] for m in ids}, {m: sp[m][1] for m in ids}, seed)
            for m in ids:
                y = D[m]["y"][sp[m][1]]
                for kk, sc in out[m][0].items(): log(snr=snr, id=m, mode=mode, method=f"idxai_{kk}", seed=seed, scores=sc, y=y)
        if "idc" in methods and len(ids) > 1:
            t0 = time.time()
            out = id_classifier({c: [S[m][i] for i in sp[m][0]] for c, m in enumerate(ids)},
                                {c: [S[m][i] for i in sp[m][1]] for c, m in enumerate(ids)}, seed, epochs=int(__import__("os").environ.get("IDC_EP", 40)), w=int(__import__("os").environ.get("IDC_W", 32)))
            for c, m in enumerate(ids):
                y = D[m]["y"][sp[m][1]]; sc, etr, ete = out[c]
                log(snr=snr, id=m, mode=mode, method="id_sinif", seed=seed, scores=sc, y=y)
                log(snr=snr, id=m, mode=mode, method="id_emb_knn", seed=seed, scores=knn_score(etr, ete), y=y)
            print("idc süre", int(time.time() - t0), flush=True)
