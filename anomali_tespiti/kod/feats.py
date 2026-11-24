"""8 kanallı MIMII kayıtlarından üç modda log-mel çıkarır: ch1 (ilk kanal), ort8 (8 kanal dalga ortalaması), gort8 (8 kanal güç spektrogramı ortalaması)."""
import sys, numpy as np, soundfile as sf, librosa
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent)); import hand
from pathlib import Path
from multiprocessing import Pool
SR, NFFT, HOP, NMELS = 16000, 1024, 512, 128
MEL = librosa.filters.mel(sr=SR, n_fft=NFFT, n_mels=NMELS)
def pw(y): return np.abs(librosa.stft(y, n_fft=NFFT, hop_length=HOP)) ** 2
def db(P): return librosa.power_to_db(MEL @ P, ref=1.0).astype(np.float16)
def one(p):
    x, _ = sf.read(p, dtype="float32")
    P = np.stack([pw(x[:, c]) for c in range(x.shape[1])])
    m = x.mean(1); h1 = hand.extract_features_y(x[:, 0]); h8 = hand.extract_features_y(m)
    return db(P[0]), db(pw(m)), db(P.mean(0)), list(h1.values()), list(h8.values()), list(h1.keys())
if __name__ == "__main__":
    root, snr, mid, out = Path(sys.argv[1]), sys.argv[2], sys.argv[3], Path(sys.argv[4])
    d = root / f"{snr}_dB_fan" / "fan" / mid
    files = sorted(d.glob("*/*.wav"))
    with Pool(4) as pool: R = pool.map(one, files, chunksize=8)
    ids = np.array([f.parent.name + "/" + f.name for f in files]); y = np.array([f.parent.name == "abnormal" for f in files], int)
    out.mkdir(parents=True, exist_ok=True)
    np.savez(out / f"lm_{snr}_{mid}.npz", ids=ids, y=y, ch1=np.stack([r[0] for r in R]), ort8=np.stack([r[1] for r in R]), gort8=np.stack([r[2] for r in R]),
             h_ch1=np.array([r[3] for r in R], np.float32), h_ort8=np.array([r[4] for r in R], np.float32), hnames=np.array(R[0][5]))
    print(snr, mid, len(files), "normal", int((y == 0).sum()), "abnormal", int(y.sum()))
