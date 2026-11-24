import numpy as np, librosa
from scipy import stats as sst, signal as ssig
import multiprocessing as mp

STAT_NAMES = ["mean", "var", "std", "skew", "kurt", "max", "mad", "acf1"]

def seq_stats(x):
    x = np.asarray(x, dtype=np.float64).ravel()
    x = x[np.isfinite(x)]
    sd = x.std()
    ok = sd > 1e-12 and x.size > 3
    return [x.mean(), x.var(), sd,
            sst.skew(x) if ok else 0.0,
            sst.kurtosis(x) if ok else 0.0,
            x.max(), sst.median_abs_deviation(x),
            np.corrcoef(x[:-1], x[1:])[0, 1] if ok else 0.0]

def extract_features_y(y, sr=16000):
    S = np.abs(librosa.stft(y, n_fft=1024, hop_length=512))
    P = S ** 2
    f = {}
    def add(name, seq):
        for sn, v in zip(STAT_NAMES, seq_stats(seq)):
            f[f"{name}_{sn}"] = v
    add("centroid", librosa.feature.spectral_centroid(S=S, sr=sr)[0])
    add("bandwidth", librosa.feature.spectral_bandwidth(S=S, sr=sr, p=1)[0])
    add("spread", librosa.feature.spectral_bandwidth(S=S, sr=sr, p=2)[0])
    add("rolloff", librosa.feature.spectral_rolloff(S=S, sr=sr)[0])
    add("flatness", librosa.feature.spectral_flatness(S=S)[0])
    for i, v in enumerate(librosa.feature.spectral_contrast(S=S, sr=sr, fmin=100, n_bands=6).mean(axis=1)):
        f[f"contrast{i}_mean"] = v
    _, psd = ssig.welch(y, fs=sr, nperseg=1024)
    add("psd", np.log10(psd + 1e-12))
    frames = librosa.util.frame(y, frame_length=1024, hop_length=512)
    add("envelope", np.abs(frames).max(axis=0))
    rms = librosa.feature.rms(S=S, frame_length=1024)[0]
    add("rms", rms)
    add("db", librosa.amplitude_to_db(rms + 1e-10))
    chroma = librosa.feature.chroma_stft(S=P, sr=sr, tuning=0.0)
    for i in range(12):
        f[f"chroma{i}_mean"] = chroma[i].mean()
        f[f"chroma{i}_max"] = chroma[i].max()
    C = np.abs(librosa.cqt(y, sr=sr, hop_length=512, n_bins=48, bins_per_octave=12, fmin=librosa.note_to_hz("C2")))
    add("cqt", librosa.amplitude_to_db(C.mean(axis=0) + 1e-10))
    add("hilbert", np.abs(ssig.hilbert(y))[::16])
    add("zcr", librosa.feature.zero_crossing_rate(y, frame_length=1024, hop_length=512)[0])
    low = librosa.fft_frequencies(sr=sr, n_fft=1024) < 1000
    add("bandratio", P[low].sum(axis=0) / (P.sum(axis=0) + 1e-12))
    add("magnitude", S.mean(axis=0))
    f["sig_skew"] = sst.skew(y)
    f["sig_kurt"] = sst.kurtosis(y)
    return {k: float(np.nan_to_num(v)) for k, v in f.items()}