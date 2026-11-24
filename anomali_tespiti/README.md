# Gürültülü Endüstriyel Fan Seslerinde Etiketsiz Anomali Tespiti (Hafta 1-10)

Derin Öğrenme ve Uygulamaları dersi projesi. Veri: MIMII fan (id_00, 02, 04, 06), +6 / 0 / −6 dB, 8 kanal.

## Ana sonuç (AUC, 4 fan kimliği ortalaması, 3 tohum, dengeli protokol)

| Yöntem | Arıza etiketi | +6 dB | 0 dB | −6 dB |
|---|---|---|---|---|
| MIMII baseline AE (literatür) | yok | 0.913 | 0.795 | 0.663 |
| Literatürdeki en iyi etiketsiz (Li 2024 / MemNMF 2026) | yok | 0.971 | 0.902 | 0.764 |
| Dense AE, log-mel (Hafta 3-6) | yok | 0.960 | 0.865 | 0.710 |
| Makine ID sınıflandırıcısı (CNN) | yok | 0.877 | 0.845 | 0.839 |
| **ID-XAI + kNN topluluğu (önerilen)** | **yok** | **0.995** | **0.968** | **0.908** |
| Füzyon: CNN + önerilen | yok | 0.972 | 0.959 | 0.918 |
| Arıza etiketli XAI seçimi (tezin yöntemi, dürüst protokol) | var | 0.998 | 0.980 | 0.910 |

Tez protokolünde +6 dB: tez 0.995. Bu çalışmada etiketli seçimle 0.998, etiketsiz ID-XAI (8 kanal ortalaması) ile 0.997.

## Klasörler
- `Hafta9_10.ipynb`: Colab defteri. Veriyi indirir, tüm deneyleri Drive'a kaldığı yerden devam edecek şekilde çalıştırır, tabloları ve şekilleri üretir.
- `kod/`: tüm betikler (defter bunları `%%writefile` ile içerir).
- `sonuclar/`: ham sonuç dosyaları (`results*.csv`, `sel_*.csv`) ve özet tablolar (`tablolar.md`).
- `sekiller/`: Şekil 8-10.
- `rapor/`: güncellenmiş rapor (Hafta 1-10, docx + pdf) ve makale taslağı.
- `literatur/`: literatür taraması notları.

## Yeniden üretme (yerel)
```bash
python kod/dl.py -6 id_00,id_02,id_04,id_06 data      # remotezip ile indir (6, 0 için de)
python kod/feats.py data -6 id_00 feat                 # her SNR × ID için
python kod/run.py -6 id_00,id_02,id_04,id_06 knn,hand,idxai ch1,ort8,both 42,43,44
IDC_W=16 IDC_EP=30 python kod/run.py -6 id_00,id_02,id_04,id_06 idc ch1 42,43,44
python kod/sel.py 6,0,-6 42,43,44 h_ch1
python kod/analyze.py denge; python kod/analyze.py tez; python kod/final_tables.py; python kod/plots.py
```
