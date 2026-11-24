"""Colab için: bir SNR'ın fan zip'ini bütün halde indirir, açmadan içinden okuyarak 4 ID için öznitelik dosyalarını (feat/lm_{snr}_{id}.npz) üretir, zip'i siler.
Kullanım: python prep_colab.py 6 [id_00,id_02,id_04,id_06]"""
import sys, io, os, zipfile, subprocess, numpy as np, soundfile as sf
from pathlib import Path
from multiprocessing import Pool
sys.path.insert(0, str(Path(__file__).parent)); import feats
snr = sys.argv[1]; ids = (sys.argv[2] if len(sys.argv) > 2 else "id_00,id_02,id_04,id_06").split(",")
FE = Path("feat"); FE.mkdir(exist_ok=True)
todo = [m for m in ids if not (FE / f"lm_{snr}_{m}.npz").exists()]
if not todo: print("hazır:", snr); sys.exit()
ZP = Path(f"/content/{snr}_dB_fan.zip")
subprocess.run(["wget", "-c", "-q", "--show-progress", "-O", str(ZP), f"https://zenodo.org/records/3384388/files/{snr}_dB_fan.zip?download=1"], check=True)
def one_member(n):
    with zipfile.ZipFile(ZP) as z: data = z.read(n)
    tmp = f"/dev/shm/{os.getpid()}.wav"; open(tmp, "wb").write(data)
    return feats.one(tmp)
with zipfile.ZipFile(ZP) as z: allnames = sorted(n for n in z.namelist() if n.endswith(".wav"))
for m in todo:
    names = [n for n in allnames if f"/{m}/" in n]
    with Pool(os.cpu_count()) as pool: R = pool.map(one_member, names, chunksize=8)
    ids_ = np.array([n.split("/")[-2] + "/" + n.split("/")[-1] for n in names]); y = np.array([n.split("/")[-2] == "abnormal" for n in names], int)
    np.savez(FE / f"lm_{snr}_{m}.npz", ids=ids_, y=y, ch1=np.stack([r[0] for r in R]), ort8=np.stack([r[1] for r in R]), gort8=np.stack([r[2] for r in R]),
             h_ch1=np.array([r[3] for r in R], np.float32), h_ort8=np.array([r[4] for r in R], np.float32), hnames=np.array(R[0][5]))
    print(snr, m, len(names), "normal", int((y == 0).sum()), "arızalı", int(y.sum()), flush=True)
ZP.unlink()
