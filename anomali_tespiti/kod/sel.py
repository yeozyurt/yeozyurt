"""XAI ile öznitelik seçimi + gözetimsiz detektör, 4 fan ID x 3 SNR.
Seçiciler:
  etiket_F  : arıza etiketli seçim (tezdeki gibi) ama ayrı seçim kümesinde; test hiç görülmez (yarı gözetimli, dürüst)
  etiket_tez: tez protokolü; seçim tüm etiketli veriyle, en iyi k test AUC'sine göre (iyimser, tezle birebir kıyas)
  id_xai    : YENİ, arıza etiketi kullanmaz. RF yalnızca normal kayıtlarla 'bu ses bu ID mi?' (bire karşı diğerleri) öğrenir,
              önem sıralamasından ilk k öznitelik seçilir.
Detektörler: kNN, Isolation Forest, autoencoder (Hafta 7 FeatAE)."""
import sys, csv, numpy as np, torch, torch.nn as nn
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import MinMaxScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import roc_auc_score
torch.set_num_threads(2)
IDS = ["id_00", "id_02", "id_04", "id_06"]; KS = [5, 10, 20, 33, 60]
snrs = sys.argv[1].split(","); seeds = [int(s) for s in sys.argv[2].split(",")]; FEAT = sys.argv[3] if len(sys.argv) > 3 else "h_ch1"
import os
DROP = os.environ.get("DROP_LEVEL") == "1"; KS = [int(k) for k in os.environ.get("KS", ",".join(map(str, KS))).split(",")]
PROTOS = os.environ.get("PROTOS", "F,tez").split(",")
OUT = Path(f"sel_{FEAT}{'_seviyesiz' if DROP else ''}.csv")
SEVIYE = ("rms", "db", "envelope", "hilbert", "magnitude", "psd", "cqt")
def auc2(y, s): return round(roc_auc_score(y, s), 4), round(roc_auc_score(y, s, max_fpr=0.1), 4)
class FeatAE(nn.Module):
    def __init__(s, d, h=64, z=8):
        super().__init__()
        s.enc = nn.Sequential(nn.Linear(d, h), nn.ReLU(), nn.Dropout(0.1), nn.Linear(h, z), nn.ReLU()); s.dec = nn.Sequential(nn.Linear(z, h), nn.ReLU(), nn.Linear(h, d))
    def forward(s, x): return s.dec(s.enc(x))
def det_ae(Xtr, Xev, seed, epochs=100):
    torch.manual_seed(seed); sc = MinMaxScaler().fit(Xtr); A = torch.tensor(sc.transform(Xtr), dtype=torch.float32)
    m = FeatAE(A.shape[1]); opt = torch.optim.Adam(m.parameters(), 1e-3); g = torch.Generator().manual_seed(seed)
    for _ in range(epochs):
        m.train(); perm = torch.randperm(len(A), generator=g)
        for i in range(0, len(A), 32):
            xb = A[perm[i:i + 32]]; loss = ((m(xb) - xb) ** 2).mean(); opt.zero_grad(); loss.backward(); opt.step()
    m.eval()
    with torch.no_grad(): return [((m(B) - B) ** 2).mean(1).numpy() for B in (torch.tensor(sc.transform(X), dtype=torch.float32) for X in Xev)]
def det_if(Xtr, Xev, seed):
    m = IsolationForest(n_estimators=200, random_state=seed).fit(Xtr); return [-m.score_samples(X) for X in Xev]
def det_knn(Xtr, Xev, seed, k=5):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6; nn_ = NearestNeighbors(n_neighbors=k).fit((Xtr - mu) / sd)
    return [nn_.kneighbors((X - mu) / sd)[0].mean(1) for X in Xev]
DETS = {"knn": det_knn, "if": det_if, "ae": det_ae}
def rf_imp(X, y, seed):
    return RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=seed, n_jobs=2).fit(X, y).feature_importances_
def prot_F(y, rng):
    ni, ai = np.where(y == 0)[0], np.where(y == 1)[0]; ni = rng.permutation(ni); ai = rng.permutation(ai); h = len(ai) // 2
    return dict(train=ni[2 * h + (len(ai) - 2 * h):], sel=np.r_[ni[h:len(ai)], ai[h:]], test=np.r_[ni[:h], ai[:h]])
def prot_tez(y, rng):
    ni = rng.permutation(np.where(y == 0)[0]); k = int(round(len(ni) * 0.2)); return dict(train=ni[k:], test=np.r_[ni[:k], np.where(y == 1)[0]])
def log(**r):
    new = not OUT.exists()
    with open(OUT, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["snr", "id", "seed", "protocol", "selector", "k", "detector", "sel_auc", "auc", "pauc"]); new and w.writeheader(); w.writerow(r)
for snr in snrs:
    D = {}
    for m in IDS:
        z = np.load(f"feat/lm_{snr}_{m}.npz"); X = z[FEAT]
        if DROP: X = X[:, [i for i, n in enumerate(z["hnames"]) if not str(n).startswith(SEVIYE)]]
        D[m] = {"y": z["y"], FEAT: X}
    for seed in seeds:
        for proto, pf in [(n, f) for n, f in (("F", prot_F), ("tez", prot_tez)) if n in PROTOS]:
            SP = {m: pf(D[m]["y"], np.random.RandomState(seed)) for m in IDS}
            # ID-XAI: tüm ID'lerin eğitim normalleri, bire karşı diğerleri
            Xn = np.concatenate([D[m][FEAT][SP[m]["train"]] for m in IDS]); idl = np.concatenate([[i] * len(SP[m]["train"]) for i, m in enumerate(IDS)])
            for i, m in enumerate(IDS):
                X, y, sp = D[m][FEAT], D[m]["y"], SP[m]
                imps = {"tum": None, "id_xai": rf_imp(Xn, (idl == i).astype(int), seed)}
                if proto == "F": imps["etiket_F"] = rf_imp(X[np.r_[sp["train"], sp["sel"]]], y[np.r_[sp["train"], sp["sel"]]], seed)
                else: imps["etiket_tez"] = rf_imp(X, y, seed)          # tezdeki gibi tüm etiketli veri (test dahil)
                for selname, imp in imps.items():
                    for k in ([X.shape[1]] if imp is None else KS):
                        cols = np.arange(X.shape[1]) if imp is None else np.argsort(-imp)[:k]
                        ev = [X[sp["test"]][:, cols]] + ([X[sp["sel"]][:, cols]] if "sel" in sp else [])
                        for dn, fn in DETS.items():
                            out = fn(X[sp["train"]][:, cols], ev, seed)
                            sa = auc2(y[sp["sel"]], out[1])[0] if "sel" in sp else ""
                            a, p = auc2(y[sp["test"]], out[0])
                            log(snr=snr, id=m, seed=seed, protocol=proto, selector=selname, k=k, detector=dn, sel_auc=sa, auc=a, pauc=p)
            print(snr, seed, proto, "tamam", flush=True)
