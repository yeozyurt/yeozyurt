import sys, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from remotezip import RemoteZip
snr = sys.argv[1]; ids = sys.argv[2].split(","); out = Path(sys.argv[3]) / f"{snr}_dB_fan"
url = f"https://zenodo.org/records/3384388/files/{snr}_dB_fan.zip?download=1"
with RemoteZip(url) as z:
    allnames = [n for n in z.namelist() if n.endswith(".wav")]
for mid in ids:
    names = [n for n in allnames if f"/{mid}/" in n]
    def work(chunk):
        z = None
        for n in chunk:
            dst = out / n
            if dst.exists(): continue
            for a in range(8):
                try:
                    if z is None: z = RemoteZip(url)
                    b = z.read(n); dst.parent.mkdir(parents=True, exist_ok=True)
                    tmp = dst.with_suffix(".tmp"); tmp.write_bytes(b); tmp.rename(dst); break
                except Exception as e:
                    z = None; time.sleep(2 * (a + 1))
    t0 = time.time(); k = 12
    with ThreadPoolExecutor(k) as ex: list(ex.map(work, [names[i::k] for i in range(k)]))
    got = sum(1 for n in names if (out / n).exists())
    print(snr, mid, got, "/", len(names), int(time.time() - t0), "s", flush=True)
