#!/usr/bin/env python3
"""Seslendirmeli proje videosu üretimi.
1) Sahne metinlerini Piper (tr_TR-dfki-medium) ile seslendirir
2) Sahne sürelerini seslendirmeye göre ayarlar (zaman.json)
3) Müzik + geçiş sesleri + seslendirmeyi karıştırır (ses.wav)
4) Animasyonu kare kare kaydeder ve sesle birleştirir (MP4)

Kullanım: python3 video_ses.py [--model /opt/piper/tr_TR-dfki-medium.onnx]"""
import argparse
import json
import math
import os
import subprocess
import wave

import numpy as np

BURADA = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(BURADA)
SR = 44100

R = json.load(open(os.path.join(KOK, "analiz", "ek_analiz.json"), encoding="utf-8"))
S = {o["sektor"]: o for o in R["sektor"]}
T = S["TÜMÜ"]
cdn_k, cdn_n = map(int, R["cdn_fisher"]["cdn"].split("/"))
oz_k, oz_n = map(int, R["cdn_fisher"]["kendi"].split("/"))
Z = R["zaman"]

BIRLER = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
ONLAR = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]


def oku(n):
    """0–9999 arası tam sayıyı Türkçe okur."""
    n = int(n)
    if n == 0:
        return "sıfır"
    p = []
    if n >= 1000:
        p.append(("" if n // 1000 == 1 else oku(n // 1000) + " ") + "bin"); n %= 1000
    if n >= 100:
        p.append(("" if n // 100 == 1 else BIRLER[n // 100] + " ") + "yüz"); n %= 100
    if n >= 10:
        p.append(ONLAR[n // 10]); n %= 10
    if n:
        p.append(BIRLER[n])
    return " ".join(p)


yuzde = lambda x: oku(round(x))
B = S["Banka"]; E = S["E-ticaret"]
oz_y = 100 * oz_k / oz_n
oz_soz = "yüzde " + (oku(math.floor(oz_y)) + " buçuk" if abs(oz_y - math.floor(oz_y) - .5) < .25 else oku(round(oz_y)))
oz_alt = f"%{oz_y:.1f}".replace(".", ",")

# (konuşulan metin, altyazı cümleleri)
SAHNE = [
    ("Bugün şifrelenen internet trafiği, yarın bir kuantum bilgisayarla çözülebilir. Türk web siteleri buna hazır mı?",
     ["Bugün şifrelenen internet trafiği, yarın bir kuantum bilgisayarla çözülebilir.",
      "Türk web siteleri buna hazır mı?"]),
    ("Saldırganlar şifreli trafiği bugün kaydedip, yarın çözebilir. Şimdi topla, sonra çöz.",
     ["Saldırganlar şifreli trafiği bugün kaydedip yarın çözebilir:", "\"Şimdi topla, sonra çöz.\""]),
    ("Çözüm hazır. Klasik anahtar, kuantuma dayanıklı em el kem ile birleşiyor. Biri kırılsa da, diğeri korur.",
     ["Çözüm hazır: klasik anahtar, kuantuma dayanıklı ML-KEM ile birleşiyor.", "Biri kırılsa da diğeri korur."]),
    (f"{oku(len(S) - 1).capitalize()} kritik sektörden, {oku(R['liste_boyutu'])} siteyi, geliştirdiğim araçla ölçtüm.",
     [f"{oku(len(S) - 1).capitalize()} kritik sektörden {R['liste_boyutu']} siteyi geliştirdiğim araçla ölçtüm."]),
    (f"Hazır site oranı, yalnızca yüzde {yuzde(T['pq'])}. {oku(B['n']).capitalize()} bankadan ise, sadece "
     f"{oku(B['pq_k'])} tanesi hazır.",
     [f"Hazır site oranı yalnızca %{round(T['pq'])}.", f"{B['n']} bankadan ise sadece {B['pq_k']} tanesi hazır."]),
    (f"Belirleyici olan altyapı. İçerik dağıtım ağı kullanan sitelerde oran yüzde {yuzde(100 * cdn_k / cdn_n)}, "
     f"kendi sunucusu olanlarda ise {oz_soz}.",
     ["Belirleyici olan altyapı:", f"CDN kullanan sitelerde oran %{round(100 * cdn_k / cdn_n)},",
      f"kendi sunucusu olanlarda ise {oz_alt}."]),
    ("Bedeli de var. Tarayıcının ilk mesajı tek bir paketi aşıyor ve ikiye bölünüyor. Kayıplı ağlarda, bağlantı yavaşlıyor.",
     ["Bedeli de var: tarayıcının ilk mesajı tek bir paketi aşıyor ve ikiye bölünüyor.",
      "Kayıplı ağlarda bağlantı yavaşlıyor."]),
    ("Geçiş başladı. Ama bankalar ve kamu, hâlâ geride. Rümeysa Betül Özyurt, Veri İletişimi.",
     ["Geçiş başladı; ama bankalar ve kamu hâlâ geride.", "Rümeysa Betül Özyurt · Veri İletişimi"]),
]
EN_AZ = [5.0, 6.5, 6.0, 5.5, 6.0, 7.0, 7.5, 5.0]   # animasyonun ihtiyaç duyduğu en kısa sahne süreleri


def wav_oku(yol):
    with wave.open(yol) as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
    if sr != SR:   # doğrusal yeniden örnekleme
        t = np.arange(int(len(x) * SR / sr)) * sr / SR
        x = np.interp(t, np.arange(len(x)), x).astype(np.float32)
    return x


def seslendir(model, klasor):
    os.makedirs(klasor, exist_ok=True)
    sesler = []
    for i, (soz, _) in enumerate(SAHNE):
        yol = os.path.join(klasor, f"sahne_{i + 1}.wav")
        subprocess.run(["python3", "-m", "piper", "-m", model, "-f", yol, "--length-scale", "0.88",
                        "--sentence-silence", "0.18"], input=soz.encode("utf-8"), check=True, capture_output=True)
        x = wav_oku(yol)
        # baş/son sessizliği kırp
        e = np.where(np.abs(x) > 0.01)[0]
        x = x[max(0, e[0] - 400): e[-1] + 2000] if len(e) else x
        sesler.append(x)
    return sesler


def zaman_cizelgesi(sesler):
    t, sahneler = 0.0, []
    for i, x in enumerate(sesler):
        d = len(x) / SR
        bas = t
        k_bas = bas + (0.9 if i == 0 else 0.55)
        son = max(bas + EN_AZ[i], k_bas + d + 0.55)
        sahneler.append(dict(bas=round(bas, 3), son=round(son, 3), konusma_bas=round(k_bas, 3),
                             konusma_son=round(k_bas + d, 3), cumleler=SAHNE[i][1]))
        t = son
    sahneler[-1]["son"] = round(sahneler[-1]["son"] + 1.2, 3)
    return sahneler


def muzik(sure):
    """Yumuşak ambient fon: Am–F–C–G akorları (sinüs pad) + hafif arpej."""
    n = int(sure * SR); t = np.arange(n) / SR
    akor = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [130.81, 196.0, 261.63], [196.0, 246.94, 293.66]]
    L = 4.0; m = np.zeros(n, np.float32)
    for k in range(int(sure / L) + 1):
        a = akor[k % 4]; s0 = int(k * L * SR); s1 = min(n, int((k + 1) * L * SR + SR))
        if s0 >= n:
            break
        tt = t[s0:s1] - k * L
        env = np.minimum(1, tt / 1.2) * np.minimum(1, np.maximum(0, (L + 1 - tt) / 1.5))
        for f in a:
            m[s0:s1] += (0.5 * np.sin(2 * np.pi * f * tt) + 0.2 * np.sin(2 * np.pi * f * 2 * tt + 1)) * env
        for j, f in enumerate(a + [a[1] * 2]):        # arpej
            q0 = s0 + int(j * L / 4 * SR); q1 = min(n, q0 + int(0.9 * SR))
            if q0 < n:
                tq = t[q0:q1] - t[q0]
                m[q0:q1] += 0.25 * np.sin(2 * np.pi * f * 2 * tq) * np.exp(-tq * 4)
    m /= np.max(np.abs(m)) + 1e-9
    giris = np.minimum(1, t / 2.0); cikis = np.minimum(1, (sure - t) / 2.5)
    return (m * giris * cikis).astype(np.float32)


def vuus(n_ornek):
    """Geçiş sesi: gürültü süpürmesi."""
    rng = np.random.default_rng(3)
    g = rng.standard_normal(n_ornek).astype(np.float32)
    k = np.ones(40) / 40; g = np.convolve(g, k, "same")
    t = np.linspace(0, 1, n_ornek)
    return (g * np.sin(np.pi * t) ** 2 * 0.9).astype(np.float32)


def karistir(sesler, sahneler, yol):
    sure = sahneler[-1]["son"]
    n = int(sure * SR) + SR
    ses = np.zeros(n, np.float32)
    for x, s in zip(sesler, sahneler):
        i = int(s["konusma_bas"] * SR); ses[i:i + len(x)] += x[: n - i]
    ses /= np.max(np.abs(ses)) + 1e-9; ses *= 0.92
    m = muzik(n / SR)[:n]
    m = np.pad(m, (0, n - len(m)))
    # sesin olduğu yerlerde müziği kıs (ducking)
    zarf = np.convolve(np.abs(ses), np.ones(int(0.25 * SR)) / int(0.25 * SR), "same")
    duck = 1 - 0.55 * np.minimum(1, zarf / 0.05)
    toplam = ses + 0.16 * m * duck
    for s in sahneler[1:]:
        i = int((s["bas"] - 0.3) * SR); v = vuus(int(0.6 * SR)); toplam[i:i + len(v)] += 0.10 * v[: n - i]
    toplam /= max(1.0, np.max(np.abs(toplam)) / 0.97)
    with wave.open(yol, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((toplam * 32767).astype(np.int16).tobytes())
    return sure


def dis_ses_bol(yol, klasor, n=8):
    """Clipchamp/ElevenLabs'ten gelen tek dosyayı (veya sahne_1..8 dosyalarını) sahnelere böler.
    Tek dosyada sahneler arasındaki en uzun n-1 sessizlikten bölünür."""
    os.makedirs(klasor, exist_ok=True)
    if os.path.isdir(yol):
        dosyalar = sorted((f for f in os.listdir(yol) if f.lower().startswith("sahne")),
                          key=lambda f: int("".join(c for c in f if c.isdigit()) or 0))
        kaynaklar = [os.path.join(yol, f) for f in dosyalar]
    else:
        kaynaklar = [yol]
    parcalar = []
    for k in kaynaklar:
        w = os.path.join(klasor, "_donusum.wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", k, "-ac", "1", "-ar", str(SR), w], check=True)
        parcalar.append(wav_oku(w))
    if len(parcalar) == n:
        sesler = parcalar
    else:
        x = parcalar[0]
        pen = int(0.05 * SR)
        enerji = np.sqrt(np.convolve(x ** 2, np.ones(pen) / pen, "same"))
        sessiz = enerji < 0.01
        # sessiz aralıkları bul
        araliklar, i = [], 0
        while i < len(x):
            if sessiz[i]:
                j = i
                while j < len(x) and sessiz[j]:
                    j += 1
                araliklar.append((i, j)); i = j
            else:
                i += 1
        ic = [a for a in araliklar if a[0] > 0 and a[1] < len(x)]
        kesim = sorted(sorted(ic, key=lambda a: a[1] - a[0], reverse=True)[: n - 1])
        if len(kesim) < n - 1:
            raise SystemExit(f"Yalnızca {len(kesim) + 1} parça bulundu; sahneler arasında 1–2 sn boşluk bırakın.")
        sinir = [0] + [(a + b) // 2 for a, b in kesim] + [len(x)]
        sesler = [x[sinir[k]: sinir[k + 1]] for k in range(n)]
    sonuc = []
    for x in sesler:   # baş/son sessizliği kırp, ses seviyesini eşitle
        e = np.where(np.abs(x) > 0.02)[0]
        x = x[max(0, e[0] - 800): e[-1] + 3000] if len(e) else x
        sonuc.append((x / (np.max(np.abs(x)) + 1e-9) * 0.9).astype(np.float32))
    return sonuc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="/opt/piper/tr_TR-dfki-medium.onnx")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--yalniz-ses", action="store_true")
    ap.add_argument("--dis-ses", help="Clipchamp/ElevenLabs ses dosyası veya sahne_1..8 dosyalarının klasörü")
    a = ap.parse_args()
    gecici = os.path.join(BURADA, "_ses")
    sesler = dis_ses_bol(a.dis_ses, gecici) if a.dis_ses else seslendir(a.model, gecici)
    sahneler = zaman_cizelgesi(sesler)
    json.dump(sahneler, open(os.path.join(BURADA, "zaman.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ses_yolu = os.path.join(gecici, "ses.wav")
    sure = karistir(sesler, sahneler, ses_yolu)
    print(f"Toplam süre: {sure:.1f} s")
    for i, s in enumerate(sahneler):
        print(i + 1, s["bas"], s["son"], round(s["konusma_son"] - s["konusma_bas"], 2))
    if a.yalniz_ses:
        return
    sessiz = os.path.join(gecici, "sessiz.mp4")
    subprocess.run(["node", os.path.join(BURADA, "video_olustur.js"), str(a.fps), sessiz], check=True)
    cikti = os.path.join(KOK, "Rumeysa_Betul_Ozyurt_Proje_Videosu.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", sessiz, "-i", ses_yolu, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", cikti], check=True)
    print("Video:", cikti)


if __name__ == "__main__":
    main()
