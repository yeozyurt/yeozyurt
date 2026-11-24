---
title: "Arıza Etiketi Olmadan Açıklanabilir Öznitelik Seçimi: Makine Kimliği Vekil Görevi ile Gürültülü Endüstriyel Seslerde Anomali Tespiti"
subtitle: "Makale taslağı (v0.1)"
author: "Rümeysa Betül Özyurt"
lang: tr
---

# Özet

Endüstriyel makinelerin seslerinden arıza tespitinde etiketli arıza örneği nadirdir, bu yüzden modeller yalnızca normal kayıtlarla eğitilir. Açıklanabilir yapay zekâ (XAI) ile öznitelik seçimi MIMII veri setinde çok yüksek başarı vermiştir. Ancak bu seçim arıza etiketlerine dayanır ve yalnızca en temiz gürültü düzeyinde (+6 dB) sınanmıştır. Bu çalışmada XAI seçiminin etiketini değiştiren bir yöntem (ID-XAI) önerilmektedir: öznitelik önemi, arıza etiketi yerine her kaydın zaten bilinen makine kimliğinden öğrenilir. Bir Random Forest yalnızca normal kayıtlarla "bu ses bu makineye mi ait?" sorusunu çözer. En önemli öznitelikler üzerinde k-en yakın komşu mesafesi anomali skoru olur. Öznitelik sayısı seçimi etiket gerektirdiği için birden fazla k değeri topluluk olarak birleştirilir. Ayrıca 8 mikrofonun ortalamasından çıkarılan öznitelikler de aday kümeye eklenir.

MIMII fan verisinde (4 makine kimliği, +6 / 0 / −6 dB, 3 tekrar) önerilen yöntem arıza etiketi kullanmadan 0,995 / 0,968 / 0,908 AUC vermiştir. Bu değerler, arıza etiketli XAI seçiminin aynı koşullardaki sonuçlarına (0,998 / 0,980 / 0,910) çok yakındır. Taranan literatürdeki etiketsiz sonuçlar ise 0,971 / 0,902 / 0,764'tür. Seçim yapılmayan aynı öznitelik kümesine göre iyileşme her gürültü düzeyinde istatistiksel olarak anlamlıdır (Wilcoxon, p < 0,001). Çalışma ayrıca 8 kanal dalga ortalamasının MIMII'de gürültüyü azaltmadığını, CNN tabanlı makine kimliği sınıflandırıcısının ise kimliğe çok bağlı sonuç verdiğini göstermektedir.

**Anahtar kelimeler:** anomali tespiti, makine sesi, açıklanabilir yapay zekâ, öznitelik seçimi, gürültüye dayanıklılık, MIMII

# Abstract (English)

Explainable-AI (XAI) feature selection has yielded near-perfect anomaly detection on the MIMII machine-sound dataset, but it relies on anomaly labels and has only been evaluated at the cleanest noise level (+6 dB SNR). We propose ID-XAI, which keeps the XAI selection pipeline but replaces anomaly labels with machine-identity labels. These labels are always available and require no faulty recordings. A one-vs-rest random forest is trained on normal recordings only. Its top-ranked features feed a k-nearest-neighbour detector, scores are ensembled over feature budgets, and features from the 8-microphone average are added to the candidate pool. On MIMII fans (4 machine IDs, +6/0/−6 dB, 3 repetitions), ID-XAI reaches 0.995/0.968/0.908 AUC without any anomaly label. This is close to anomaly-label-based selection (0.998/0.980/0.910) and above the best unsupervised results we found in the literature (0.971/0.902/0.764).

# 1. Giriş

- Kestirimci bakım için akustik izleme; arıza verisinin azlığı → denetimsiz (yalnızca normal veriyle) anomali tespiti.
- MIMII [1] ve DCASE 2020 Task 2 [4]: log-mel + autoencoder baseline'ı; gürültü arttıkça başarı keskin düşer (fan: 0,91 → 0,66, MIMII Tablo 3).
- XAI tabanlı öznitelik seçimi [5]: +6 dB'de fan ortalaması 0,995. İki açık soru:
  1. Seçim arıza etiketlerine dayanır. Gerçek tesiste arıza örneği olmadan uygulanabilir mi?
  2. Gürültülü düzeylerde (0, −6 dB) davranışı nedir?
- Katkılar:
  1. ID-XAI: XAI seçimini makine kimliği vekil görevine taşıyan, arıza etiketi gerektirmeyen yöntem.
  2. k seçimini gerektirmeyen ölçeklenmiş kNN topluluğu ve tek kanal + 8 kanal öznitelik birleşimi.
  3. MIMII fanın tamamında (4 ID × 3 SNR) etiketli ve etiketsiz seçimin karşılaştırması, ablasyonlar ve eşleştirilmiş istatistik testleri.
  4. Olumsuz bulgular: 8 kanal dalga ortalaması gürültüyü azaltmaz. Log-mel autoencoder'lar ve CNN kimlik sınıflandırıcısı kimliğe bağlı biçimde başarısız olabilir.

# 2. İlgili çalışmalar

- Yeniden üretme tabanlı: AE / VAE / GRLNet [1, 6]; LPC + bellekli NMF (MemNMF) [6]; modülasyon temsilleri [7].
- Sınıflandırma tabanlı (makine ID / outlier exposure): DCASE 2020 üst sıra sistemleri (MobileNetV2, ensemble, veri artırma) [7'deki karşılaştırma].
- Eğitim gerektirmeyen gömme + kNN yaklaşımları [8].
- XAI ile öznitelik seçimi: [5]. Bu çalışmanın farkı: seçim etiketi olarak arıza yerine kimlik, ve gürültü düzeylerinde sistematik değerlendirme.

# 3. Yöntem

## 3.1 Öznitelikler
Her 10 sn klipten 145 öznitelik çıkarılır: 14 zaman dizisi (spektral merkez, bant genişliği, rolloff, düzlük, PSD, zarf, RMS, dB, CQT, Hilbert, ZCR, bant oranı, büyüklük, spread) × 8 istatistik, spektral kontrast (7), kroma (12 × 2), sinyal çarpıklık / basıklık. Bunlar iki kaynaktan hesaplanır: (i) 1. mikrofon, (ii) 8 mikrofonun dalga ortalaması. Toplam 290 aday öznitelik vardır.

## 3.2 ID-XAI seçimi
Kimlik $m$ için, tüm kimliklerin normal eğitim kayıtları üzerinde $y = \mathbb{1}[\text{kimlik} = m]$ hedefli bir Random Forest (300 ağaç, dengeli sınıf ağırlığı) eğitilir. Ortalama safsızlık azalması önemine göre öznitelikler sıralanır, ilk $k$ öznitelik seçilir.

## 3.3 Skor ve topluluk
Seçilen öznitelikler eğitim normallerinin ortalaması ve standart sapmasıyla standartlaştırılır. Skor, en yakın 5 eğitim normaline ortalama Öklid uzaklığıdır. Bu uzaklık, eğitim normallerinin kendini dışlayan aynı uzaklıklarının medyanına bölünür. Son skor $k \in \{5, 10, 20, 33\}$ için bu ölçeklenmiş skorların ortalamasıdır.

## 3.4 Karşılaştırılan yöntemler
- Dense AE (log-mel, MIMII / DCASE baseline'ı).
- Seçimsiz 145 öznitelik + kNN.
- Log-mel bant istatistiği + kNN (1 kanal / 8 kanal güç ortalaması).
- CNN makine kimliği sınıflandırıcısı (SpecAugment, −log p(kimlik) skoru).
- Arıza etiketli XAI seçimi [5] (yarı gözetimli üst referans). Etiketler yalnızca ayrı bir seçim kümesinde kullanılır, k bu kümede seçilir.

# 4. Deney düzeni
- MIMII fan, ID 00 / 02 / 04 / 06, +6 / 0 / −6 dB, 8 kanal.
- Dengeli protokol: tüm arızalılar + aynı sayıda normal test edilir, kalan normaller eğitime ayrılır. 3 tohum, her tohumda bölünme değişir.
- Tezle kıyas için tez protokolü: normallerin %80'i eğitim; %20 normal + tüm arızalılar test.
- Ölçütler: AUC, pAUC (FPR ≤ 0,1). Eşleştirilmiş Wilcoxon testi kimlik × tohum çiftleri (n = 12) üzerinden yapılır.

# 5. Sonuçlar
(Tablo ve şekiller rapordaki Tablo 13.1, 14.1-14.5, 15.1 ve Şekil 8-10'dan alınacak.)

- Tablo 1: ana sonuçlar (AUC / pAUC, 3 SNR).
- Tablo 2: literatürle kıyas.
- Tablo 3: tez protokolünde +6 dB kimlik bazında kıyas.
- Şekil 1: AUC-SNR eğrisi; Şekil 2: k ablasyonu (etiketli ve ID-XAI).

Başlıca bulgular:

1. ID-XAI, seçimsiz özniteliklere göre AUC'yi +6 / 0 / −6 dB'de sırasıyla +0,034 / +0,075 / +0,118 artırmıştır (p < 0,001).
2. Etiketli seçimle fark −6 dB'de 0,002, 0 dB'de 0,012 AUC'dir.
3. Tez protokolünde 8 kanal ortalaması öznitelikleriyle ID-XAI +6 dB'de 0,997 vermiştir (tez, etiketli seçim: 0,995).
4. Gürültü arttıkça en iyi öznitelik sayısı küçülür.

# 6. Tartışma ve sınırlılıklar
- Seviye öznitelikleri: çıkarıldığında ID-XAI'nin kazancı azalır. Arızalı fanların ses seviyesi farkının fiziksel mi yoksa kayıt kaynaklı mı olduğu ayırt edilemez.
- Yöntem aynı türden birden fazla makinenin normal kaydını gerektirir.
- Yalnızca fan türü incelenmiştir. Pompa, kızak, vana ve DCASE 2020 Task 2 resmi bölünmesi gelecek çalışmadır.
- Literatür kıyası farklı bölünmelere dayanır.

# 7. Sonuç
Arıza etiketi yerine makine kimliğiyle yapılan XAI öznitelik seçimi, etiketli seçimin başarısının neredeyse tamamını, hiçbir arıza örneği kullanmadan sağlamaktadır. En büyük kazanç en gürültülü koşulda elde edilmiştir.

# Kaynaklar
[1] H. Purohit ve ark., "MIMII Dataset…", DCASE Workshop, 2019 (arXiv:1909.09347).
[4] Y. Koizumi ve ark., "Description and Discussion on DCASE2020 Challenge Task2", 2020.
[5] B. S. Çağlar, "Açıklanabilir Yapay Zeka ve Akustik Sinyaller Kullanılarak Endüstriyel Makinelerde Anomali Tespiti", YL Tezi, Sakarya Üniv., 2025.
[6] P. Saengthong, T. Shinozaki, "MemNMF…", arXiv:2607.22086, 2026.
[7] K. Li ve ark., "Machine Anomalous Sound Detection Using Spectral-temporal Modulation Representations…", arXiv:2409.05319, 2024.
[8] P. Saengthong, T. Shinozaki, "Sub-Band Spectral Matching with Localized Score Aggregation…", arXiv:2603.13749, 2026.
