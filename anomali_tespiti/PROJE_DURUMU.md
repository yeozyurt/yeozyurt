# Proje durumu (kaldığımız yer) — 24 Kasım 2026

Yeni bir oturumda devam etmek için bu dosyayı okut: "anomali_tespiti/PROJE_DURUMU.md'den devam edelim".

## Proje
Derin Öğrenme dersi: MIMII fan seslerinde farklı gürültü düzeylerinde (+6 / 0 / −6 dB) denetimsiz anomali tespiti.
Karşılaştırma tezi: B. S. Çağlar (Sakarya Üniv., 2025), XAI ile öznitelik seçimi; fan ortalaması +6 dB'de 0,9954 (etiketli seçim).

## Yapılanlar
- Hafta 1-8 (önceki Colab defteri): yalnız fan id_00, ilk kanal; Dense/LSTM/Conv AE, karışık gürültü eğitimi, 145 el yapımı öznitelik + XAI (RF/SHAP/LASSO), sızıntı kontrolleri, tez protokolü.
- Hafta 9: fan id_00/02/04/06 × 3 SNR × 8 kanal indirildi; kanal modları ch1 / ort8 / gort8; CNN makine ID sınıflandırıcısı (SpecAugment); kNN yöntemleri; dengeli protokolde 3 tohum (tohum bölünmeyi de değiştirir).
- Hafta 10: **ID-XAI (önerilen, arıza etiketi yok)**. RF yalnız normal kayıtlarla "bu ses bu makine kimliğine mi ait?" (bire karşı diğerleri) öğrenir. İlk k öznitelik + ölçeklenmiş kNN, k ∈ {5,10,20,33} topluluğu. Öznitelikler: 1. kanal + 8 kanal ortalaması (290 aday).
- Literatür taraması: `literatur/literatur_notlari.md`.

## Ana sonuçlar (AUC, 4 fan ID ort., 3 tohum)
| Yöntem | +6 | 0 | −6 |
|---|---|---|---|
| Literatür en iyi etiketsiz | 0,971 | 0,902 | 0,764 |
| Dense AE (1 tohum) | 0,960 | 0,865 | 0,710 |
| CNN ID sınıflandırıcısı | 0,877 | 0,845 | 0,839 |
| **ID-XAI (etiketsiz)** | **0,995** | **0,968** | **0,908** |
| Füzyon CNN + ID-XAI | 0,972 | 0,959 | 0,918 |
| Etiketli XAI seçimi (Protokol F) | 0,998 | 0,980 | 0,910 |
Tez protokolü +6 dB: etiketli seçim 0,998; etiketsiz ID-XAI (ort8) 0,997; tez 0,995.
Wilcoxon: ID-XAI vs seçimsiz öznitelik kNN, her SNR'da p < 0,001.

## Dürüst bulgular / sınırlılıklar
- Seviye öznitelikleri çıkarılınca ID-XAI −6 dB'de 0,743'e düşüyor (seviye farkı fiziksel mi, kayıt mı belirsiz).
- 8 kanal dalga ortalaması gürültüyü azaltmadı (gürültü kanallar arası korelasyonlu).
- CNN id_00'da başarısız (~0,55). CPU'da küçük boyutla eğitildi (w=16, 30 epoch).
- Yalnız fan türü.

## Sıradaki işler (yayın için)
1. Pompa, kızak, vana türlerine genişletme; DCASE 2020 Task 2 resmi bölünmesi.
2. Seviye normalleştirilmiş ID-XAI sürümü.
3. CNN'i Colab GPU'da tam boyutta (w=32, 40 epoch) yeniden eğitip füzyonu tekrar değerlendirme.
4. Makale metnini tamamlama (`rapor/makale_taslak.md`); hedef SİU veya dergi.

## Dosyalar
- `rapor/Anomali_Tespiti_Hafta1-10_Raporu.docx/.pdf`: güncel rapor (bölüm 13-16 yeni).
- `rapor/Makale_Taslagi.docx`, `rapor/makale_taslak.md`.
- `Hafta9_10.ipynb`: Colab defteri (Drive `mimii/hafta9`, kaldığı yerden devam eder).
- `kod/`, `sonuclar/` (ham csv + `tablolar.md`), `sekiller/`.
- Ham ses ve öznitelik dosyaları (feat/*.npz, ~4 GB) depoda yok; `kod/dl.py` + `kod/feats.py` veya defterdeki `prep_colab.py` ile yeniden üretilir.

Etiketler: #anomali-tespiti #MIMII #fan #XAI #ID-XAI #gurultu #derin-ogrenme #makale
