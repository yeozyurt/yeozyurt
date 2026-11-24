import numpy as np, torch, torch.nn as nn, random, time
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import NearestNeighbors
torch.set_num_threads(4)
dev = "cuda" if torch.cuda.is_available() else "cpu"
IDS = ["id_00", "id_02", "id_04", "id_06"]

def auc2(y, s): return roc_auc_score(y, s), roc_auc_score(y, s, max_fpr=0.1)

def split(y, seed):
    """Arızalıların tamamı + aynı sayıda normal test, kalan normaller eğitim. Tohum bölünmeyi değiştirir."""
    rng = np.random.RandomState(seed)
    ni = np.where(y == 0)[0].copy(); rng.shuffle(ni); ai = np.where(y == 1)[0]
    if __import__("os").environ.get("PROTO") == "tez":      # tez protokolü: normallerin %80'i eğitim, %20 normal + tüm arızalı test
        k = int(round(len(ni) * 0.2)); return ni[k:], np.r_[ni[:k], ai]
    return ni[len(ai):], np.r_[ni[:len(ai)], ai]

def seed_all(s): random.seed(s); np.random.seed(s); torch.manual_seed(s)

# ---------------- Dense AE (Hafta 3-6 temel modeli)
def frames(S, n=5):
    T = S.shape[1] - n + 1
    return np.concatenate([S[:, i:i + T] for i in range(n)], 0).T
class DenseAE(nn.Module):
    def __init__(s, d=640, h=128, z=8):
        super().__init__()
        b = lambda i, o: [nn.Linear(i, o), nn.BatchNorm1d(o), nn.ReLU()]
        s.enc = nn.Sequential(*b(d, h), *b(h, h), *b(h, h), *b(h, h), *b(h, z))
        s.dec = nn.Sequential(*b(z, h), *b(h, h), *b(h, h), *b(h, h), nn.Linear(h, d))
    def forward(s, x): return s.dec(s.enc(x))
def dense_ae(Str, Ste, seed, epochs=30, bs=512):
    seed_all(seed)
    X = np.concatenate([frames(S) for S in Str]).astype(np.float32); mu, sd = X.mean(), X.std()
    X = torch.from_numpy((X - mu) / sd).to(dev); m = DenseAE().to(dev); opt = torch.optim.Adam(m.parameters(), 1e-3)
    for _ in range(epochs):
        m.train(); perm = torch.randperm(len(X), device=dev)
        for i in range(0, len(X), bs):
            xb = X[perm[i:i + bs]]; loss = ((m(xb) - xb) ** 2).mean(); opt.zero_grad(); loss.backward(); opt.step()
    m.eval()
    with torch.no_grad():
        return np.array([((m(x) - x) ** 2).mean().item() for x in (torch.from_numpy((frames(S).astype(np.float32) - mu) / sd).to(dev) for S in Ste)])

# ---------------- Bant istatistiği + kNN (etiketsiz, eğitimsiz)
def bandstats(S): S = S.astype(np.float32); return np.r_[S.mean(1), S.std(1)]
def knn_score(Ftr, Fte, k=5):
    mu, sd = Ftr.mean(0), Ftr.std(0) + 1e-6
    nn_ = NearestNeighbors(n_neighbors=k).fit((Ftr - mu) / sd)
    return nn_.kneighbors((Fte - mu) / sd)[0].mean(1)

# ---------------- Makine ID sınıflandırıcısı (öz-denetimli)
class IDNet(nn.Module):
    def __init__(s, n_cls, emb=128, w=32):
        super().__init__()
        def blk(i, o, p): return [nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(), nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(), nn.MaxPool2d(p)]
        s.f = nn.Sequential(*blk(1, w, 2), *blk(w, 2 * w, 2), *blk(2 * w, 4 * w, 2), *blk(4 * w, 4 * w, (2, 1)))
        s.emb = nn.Sequential(nn.Linear(4 * w * 8, emb), nn.BatchNorm1d(emb), nn.ReLU()); s.out = nn.Linear(emb, n_cls)
    def embed(s, x):                       # x: B x 128 mel x T
        h = s.f(x.unsqueeze(1))            # B x 128 x 8 x T/8
        return s.emb(h.mean(3).flatten(1))  # zaman üzerinde ortalama, frekans bilgisi korunur
    def forward(s, x): return s.out(s.embed(x))

def specaug(x, F=16, T=12):
    x = x.clone()
    for b in range(x.size(0)):
        f0 = np.random.randint(0, x.size(1) - F); t0 = np.random.randint(0, x.size(2) - T)
        x[b, f0:f0 + np.random.randint(0, F), :] = 0; x[b, :, t0:t0 + np.random.randint(0, T)] = 0
    return x

def id_classifier(train_sets, test_sets, seed, win=64, epochs=40, bs=64, aug=True, w=32):
    """train_sets/test_sets: {sınıf_no: [S,...]}. Döner: {sınıf: (logp_skor, emb_eğitim, emb_test)}"""
    seed_all(seed)
    allS = [S for v in train_sets.values() for S in v]
    mu = np.mean([S.astype(np.float32).mean(1) for S in allS], 0)[:, None]; sd = np.std(np.concatenate([S.astype(np.float32) for S in allS], 1), 1)[:, None] + 1e-6
    norm = lambda S: (S.astype(np.float32) - mu) / sd
    Xtr = [(torch.from_numpy(norm(S)), c) for c, v in train_sets.items() for S in v]
    m = IDNet(len(train_sets), w=w).to(dev); opt = torch.optim.AdamW(m.parameters(), 1e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, 2e-3, total_steps=epochs * ((len(Xtr) + bs - 1) // bs))
    ce = nn.CrossEntropyLoss()
    for ep in range(epochs):
        m.train(); order = np.random.permutation(len(Xtr))
        for i in range(0, len(order), bs):
            idx = order[i:i + bs]; T = Xtr[0][0].shape[1]
            st = np.random.randint(0, T - win, len(idx))
            xb = torch.stack([Xtr[j][0][:, s:s + win] for j, s in zip(idx, st)]).to(dev)
            yb = torch.tensor([Xtr[j][1] for j in idx], device=dev)
            if aug: xb = specaug(xb)
            loss = ce(m(xb), yb); opt.zero_grad(); loss.backward(); opt.step(); sched.step()
    m.eval()
    def clip(S):   # klibi örtüşen pencerelere böl
        x = torch.from_numpy(norm(S)); T = x.shape[1]
        return torch.stack([x[:, s:s + win] for s in range(0, T - win + 1, win // 2)]).to(dev)
    out = {}
    with torch.no_grad():
        for c in test_sets:
            sc, et = [], []
            for S in test_sets[c]:
                xw = clip(S); e = m.embed(xw); lp = torch.log_softmax(m.out(e), 1)[:, c]
                sc.append(-lp.mean().item()); et.append(e.mean(0).cpu().numpy())
            etr = np.array([m.embed(clip(S)).mean(0).cpu().numpy() for S in train_sets[c]])
            out[c] = (np.array(sc), etr, np.array(et))
    return out

# ---------------- ID-XAI: arıza etiketi kullanmadan öznitelik seçimi (önerilen)
def knn_norm(Ftr, Fte, k=5):
    """kNN mesafesi, eğitim normallerinin kendi (kendini dışlayan) kNN mesafesinin medyanına bölünür -> farklı k'lar birleştirilebilir."""
    mu, sd = Ftr.mean(0), Ftr.std(0) + 1e-6; A, B = (Ftr - mu) / sd, (Fte - mu) / sd
    nn_ = NearestNeighbors(n_neighbors=k + 1).fit(A)
    ref = np.median(nn_.kneighbors(A)[0][:, 1:].mean(1))
    return nn_.kneighbors(B, n_neighbors=k)[0].mean(1) / ref
def idxai_scores(H_by_id, tr_by_id, te_by_id, seed, ks=(5, 10, 20, 33)):
    from sklearn.ensemble import RandomForestClassifier
    ids = list(H_by_id); Xn = np.concatenate([H_by_id[m][tr_by_id[m]] for m in ids])
    lab = np.concatenate([[i] * len(tr_by_id[m]) for i, m in enumerate(ids)]); out = {}
    for i, m in enumerate(ids):
        imp = RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=seed, n_jobs=-1).fit(Xn, (lab == i).astype(int)).feature_importances_
        o = np.argsort(-imp); H = H_by_id[m]; r = {}
        for k in ks:
            c = o[:k]; r[f"k{k}"] = knn_norm(H[tr_by_id[m]][:, c], H[te_by_id[m]][:, c])
        r["ens"] = np.mean([r[f"k{k}"] for k in ks], 0); out[m] = (r, o)
    return out
