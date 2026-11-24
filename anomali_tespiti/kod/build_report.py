import sys, json, docx, re
sys.path.insert(0, "code"); from docxlib import Writer
SRC = "/root/.claude/uploads/88eb64f0-d555-5d74-bce9-85ed419aefd1/f3e81f71-Anomali_Tespiti_Hafta1-8_Raporu.docx"
T = json.load(open("tablolar/tablolar.json"))
d = docx.Document(SRC); P = d.paragraphs
gen = next(p for p in P if p.text.startswith("13. Genel Değerlendirme"))
W = Writer(d, gen)
def tab(key, widths=None, rows_filter=None, cols=None):
    t = T[key]; rows = t["rows"] if rows_filter is None else [r for r in t["rows"] if rows_filter(r)]
    rows = [[c if "arXiv" in c else re.sub(r"(\d)\.(\d)", r"\1,\2", c) for c in r] for r in rows]
    W.table([cols or t["cols"]] + rows, widths)
def val(key, rowstart, col):
    r = next(r for r in T[key]["rows"] if r[0].startswith(rowstart)); return r[col].split(" ±")[0].replace(".", ",")
A = "Tablo A (AUC)"
p6, p0, pm6 = (val("Tablo B", "Ortalama", i) for i in (1, 2, 3))

# ===================================================================== HAFTA 9
W.h1("13. Hafta 9: Tüm Fan Kimlikleri, 8 Kanal ve Makine ID Sınıflandırıcısı")
W.h2("13.1 Amaç: önceki haftaların zayıf noktaları")
W.p("Hafta 1-8 sonunda çalışmanın beş zayıf noktası belirlenmiştir. Bu hafta ve Hafta 10 bunları gidermek için planlanmıştır.")
for lead, rest in [("Tek makine. ", "Tüm sonuçlar yalnızca fan id_00 içindi. Tez ve literatür dört fan kimliğini (00, 02, 04, 06) birlikte raporlar."),
                   ("Tek kanal. ", "MIMII kayıtları 8 mikrofonlu dizi ile alınmış olmasına rağmen yalnızca ilk kanal kullanılmıştı."),
                   ("Gürültülü düzeylerde etiketsiz başarı düşük. ", "Etiket kullanmayan yöntemler 0 dB'de en fazla 0,83, −6 dB'de en fazla 0,70 AUC veriyordu. pAUC ise 0,51 civarındaydı."),
                   ("Planlanan model eksik. ", "Proje planındaki makine ID sınıflandırıcısı ve veri artırma yapılmamıştı."),
                   ("Tezin %99,5 düzeyi yalnızca tek kimlikte ve etiketli seçimle gösterilmişti. ", "Tezde fan ortalaması 0,9954'tür. Bu düzeye dört kimlikte ulaşılıp ulaşılamayacağı, ayrıca arıza etiketi kullanmadan ulaşılıp ulaşılamayacağı bilinmiyordu.")]:
    W.bold_lead(lead, rest)
W.h2("13.2 Veri ve protokol")
W.table([["Ayar", "Değer"],
         ["Veri", "MIMII fan, id_00 / 02 / 04 / 06, +6 / 0 / −6 dB, 8 kanalın tamamı. SNR başına 5.550 klip, toplam 16.650 klip (yaklaşık 42 GB ham ses)"],
         ["Kanal modları", "ch1: ilk mikrofon (önceki haftalarla aynı). ort8: 8 kanalın dalga ortalaması. gort8: 8 kanalın güç spektrogramlarının ortalaması"],
         ["Dengeli protokol (ana)", "Her kimlikte tüm arızalılar + aynı sayıda normal test edilir, kalan normaller eğitime ayrılır. Tohum (42, 43, 44) artık bölünmeyi de değiştirir"],
         ["Protokol F", "Arızalıların yarısı seçim kümesi, yarısı test (Bölüm 11). Etiketli öznitelik seçiminin dürüst değerlendirmesi için"],
         ["Tez protokolü", "Normallerin %80'i eğitim, %20 normal + tüm arızalılar test (Bölüm 12). Yalnızca tezle doğrudan kıyas için"],
         ["Ölçütler", "AUC ve pAUC (FPR ≤ 0,1). Önce 4 kimliğin ortalaması alınır, sonra 3 tohum üzerinden ortalama ± standart sapma verilir"]], [2600, 7038])
W.p("Hat doğrulaması: id_00, −6 dB, tek kanal, tohum 42 için Dense AE bu hatta 0,534 AUC vermiştir. Bölüm 8'deki Colab sonucu 0,541'dir. Yeni hat önceki sonuçları yeniden üretmektedir.")
W.h2("13.3 Eklenen yöntemler")
for lead, rest in [("Makine ID sınıflandırıcısı (derin öğrenme). ", "Yalnızca normal kayıtlarla, 2 saniyelik (64 kare) log-mel pencerelerinin dört fan kimliğinden hangisine ait olduğunu öğrenen 4 bloklu bir CNN'dir. Frekans ekseni korunur, zaman üzerinde ortalama alınır. Eğitimde SpecAugment (frekans ve zaman maskeleme) ve OneCycle öğrenme oranı kullanılır. Anomali skoru, klip pencerelerinde −log p(doğru kimlik) değerinin ortalamasıdır. DCASE 2020 Task 2'de öne çıkan yaklaşımın bu projedeki karşılığıdır."),
                   ("Öznitelik + kNN. ", "Bölüm 11'deki 145 el yapımı öznitelik standartlaştırılır, test klibinin eğitim normallerine en yakın 5 komşusuna ortalama uzaklığı anomali skoru olarak kullanılır. Eğitim gerektirmez."),
                   ("Log-mel bant istatistiği + kNN. ", "Her mel bandının klip boyunca ortalaması ve standart sapması (256 boyut) üzerinde aynı kNN skoru hesaplanır."),
                   ("Dense AE. ", "Hafta 3-6'daki temel model, dört kimlikte referans olarak yeniden çalıştırılmıştır. CPU süresi nedeniyle yalnızca tek tohumla (42) çalıştırılmıştır, bu yüzden tablolarda standart sapması yoktur.")]:
    W.bold_lead(lead, rest)
W.h2("13.4 Sonuçlar")
tab(A, [4800, 1612, 1613, 1613]); W.cap("Tablo 13.1. Dengeli protokolde AUC (4 fan kimliği ortalaması; 3 tohum ortalaması ± std). Son iki satır arıza etiketi kullanan yarı gözetimli referanslardır (Protokol F, k seçim kümesiyle belirlenmiş).")
tab("Tablo A (PAUC)", [4800, 1612, 1613, 1613]); W.cap("Tablo 13.2. Aynı yöntemler için pAUC (FPR ≤ 0,1).")
W.img("sekil8_hafta9.png", 16.5); W.cap("Şekil 8. Gürültü düzeyine göre AUC (sol) ve pAUC (sağ), 4 fan kimliği ortalaması. Kesikli siyah çizgiler literatürdeki etiketsiz sonuçlardır (Bölüm 15). Hata çubukları tohumlar arası standart sapmadır.")
W.img("sekil9_hafta9.png", 16.5); W.cap("Şekil 9. Kimlik ve gürültü düzeyine göre AUC (3 tohum ortalaması).")
W.h2("13.5 Yorum")
for lead, rest in [("Kimlikler arası fark çok büyüktür. ", "id_06 her yöntemde ve her gürültüde neredeyse kusursuzdur. id_00 ise en zor kimliktir. Önceki haftalarda yalnızca id_00'a bakılması, gürültünün etkisini olduğundan büyük göstermiştir. Örneğin Dense AE dört kimlik ortalamasında id_00'dan belirgin yüksektir (Şekil 9)."),
                   ("Makine ID sınıflandırıcısı kimliğe bağlı çalışmaktadır. ", "id_02, id_04 ve id_06'da −6 dB'de bile yüksek AUC ve pAUC vermiştir. Önceki haftalarda pAUC bu gürültüde 0,51'deydi. id_00'da ise rastgele düzeye yakındır, bu da ortalamasını düşürmektedir. Olası açıklama şudur: id_00'ın arızaları kimliği ayırt eden spektral desenleri değiştirmeyen türdendir (Bölüm 11.4'teki seviye bulgusuyla uyumlu), bu yüzden sınıflandırıcı arızalı klibi de doğru kimliğe atamaktadır. Bu açıklama ayrıca sınanmamıştır."),
                   ("8 kanalın dalga ortalaması gürültüyü azaltmamıştır. ", "Kanallar arası korelasyon normal kayıtlarda 0,5-0,98'dir, yani fabrika gürültüsü mikrofonlar arasında uyumludur. Sinyali ortalamak gürültüyü de ortalamaya katar. Güç spektrogramı ortalaması (gort8) ise kNN'de −6 dB'de AUC'yi 0,733'ten 0,780'e çıkarmıştır. 8 kanal, el yapımı özniteliklerle birleştirildiğinde (Bölüm 14) belirgin katkı vermiştir."),
                   ("Basit kNN, eğitilmiş autoencoder'lardan iyidir. ", "Seçimsiz 145 öznitelik + kNN, Hafta 7'deki öznitelikli autoencoder'dan ve tüm log-mel autoencoder'lardan her düzeyde yüksektir. Bu, sorunun model kapasitesinden çok temsil (öznitelik) seçiminde olduğunu düşündürmüştür ve Hafta 10'un çıkış noktası olmuştur.")]:
    W.bold_lead(lead, rest)

# ===================================================================== HAFTA 10
W.h1("14. Hafta 10: Arıza Etiketi Kullanmadan XAI ile Öznitelik Seçimi (ID-XAI)")
W.h2("14.1 Fikir")
W.p("Tezde ve Bölüm 11-12'de öznitelik seçimi, arıza etiketli kayıtlarla eğitilen Random Forest / SHAP önem sıralamasından yapılmaktadır. Bu nedenle sonuçlar yarı gözetimlidir: sahada arıza örneği olmadan uygulanamaz. Bu hafta önerilen ID-XAI yönteminde aynı XAI hattı korunmuş, yalnızca etiketin kaynağı değiştirilmiştir. Seçim için gereken etiket arıza bilgisi değil, her kaydın zaten bilinen makine kimliğidir.")
for t in ["Her kimlik için, yalnızca normal eğitim kayıtları üzerinde 'bu kayıt bu kimliğe mi ait, yoksa diğer üç fandan birine mi?' (bire karşı diğerleri) sorusunu çözen bir Random Forest (300 ağaç) eğitilir.",
          "Random Forest öznitelik önemine göre ilk k öznitelik seçilir. Bir fanı diğerlerinden ayıran öznitelikler, o fanın normal çalışmasının imzasını taşıyan özniteliklerdir. Arıza bu imzayı bozduğunda kNN mesafesi büyür.",
          "Seçilen özniteliklerde kNN (k_komşu = 5) mesafesi hesaplanır. Mesafe, eğitim normallerinin kendi kNN mesafelerinin medyanına bölünerek ölçeklenir.",
          "k değerini seçmek etiket gerektirdiği için tek bir k seçilmez. k ∈ {5, 10, 20, 33} için ölçeklenmiş skorların ortalaması alınır (topluluk).",
          "Öznitelikler hem ilk kanaldan hem de 8 kanal ortalamasından çıkarılıp birleştirilir (2 × 145 = 290 aday öznitelik). Seçim bunların içinden yapılır.",
          "Hiçbir adımda arıza etiketi, test kaydı veya seçim kümesi kullanılmaz. Hiperparametreler önceden sabitlenmiştir."]:
    W.bullet(t)
W.h2("14.2 Sonuçlar")
W.p(f"Önerilen yöntem dengeli protokolde dört fan kimliği ortalamasında +6 dB'de {p6}, 0 dB'de {p0}, −6 dB'de {pm6} AUC vermiştir (Tablo 13.1). Kimlik bazında değerler Tablo 14.1'dedir.")
tab("Tablo B", [3238, 2133, 2133, 2134]); W.cap("Tablo 14.1. Önerilen yöntemin (ID-XAI + kNN topluluğu, 1. kanal + 8 kanal ortalaması) kimlik bazında AUC değerleri (dengeli protokol, 3 tohum ortalaması).")
tab("Tablo D", [3838, 1160, 1160, 1160, 1160, 1160]); W.cap("Tablo 14.2. +6 dB'de tezle doğrudan kıyas (tez protokolü; tez değerleri Tablo 4.6'dan). 'En iyi k' satırları tezdeki gibi test AUC'sine göre seçilmiştir ve iyimserdir. ETİKETSİZ satırlarda hiçbir seçim yapılmamıştır.")
W.img("sekil10_hafta10.png", 16.5); W.cap("Şekil 10. Seçilen öznitelik sayısına (k) göre AUC: arıza etiketli XAI seçimi (kırmızı) ve önerilen ID-XAI (yeşil). Turuncu kesikli çizgi seçim yapılmayan 145 öznitelikli kNN'dir (Protokol F, kNN detektör, 3 tohum).")
W.h2("14.3 Ablasyon ve kontroller")
tab("Tablo E", [4800, 1612, 1613, 1613], rows_filter=lambda r: r[0].endswith("KNN") or r[0].endswith("AE"))
W.cap("Tablo 14.3. ID-XAI'de öznitelik sayısı ve detektörün etkisi (Protokol F, tek kanal öznitelikleri, 3 tohum). Isolation Forest satırları sonuç dosyasında, burada gösterilmemiştir.")
if "Tablo F1" in T:
    tab("Tablo F1", [4800, 1612, 1613, 1613], rows_filter=lambda r: r[0].endswith("KNN"))
    W.cap("Tablo 14.4. Mutlak ses seviyesine bağlı öznitelikler (rms, db, envelope, hilbert, magnitude, psd, cqt) çıkarıldığında kNN sonuçları (89 öznitelik, Protokol F).")
tab("Tablo G", [3238, 2133, 2133, 2134]); W.cap("Tablo 14.5. Önerilen yöntemle diğer yöntemlerin AUC farkı (önerilen − yöntem). p: Wilcoxon işaretli sıra testi, eşleştirilmiş kimlik × tohum çiftleri üzerinden.")
W.h2("14.4 Yorum")
for lead, rest in [("Tezin düzeyine etiketsiz olarak ulaşılmıştır. ", "Tez protokolünde 8 kanal ortalaması öznitelikleriyle ID-XAI, +6 dB fan ortalamasında 0,997 AUC vermiştir (tez 0,995). Bunu arıza etiketi, test AUC'sine göre seçim veya k ayarı yapmadan sağlamıştır. Arıza etiketli seçimle (tezin yöntemi) ise aynı protokolde AE ve kNN 0,998 vermiştir (Tablo 14.2)."),
                   ("Asıl kazanç gürültülü düzeylerdedir. ", "Seçim yapılmadan 145 öznitelikle kNN −6 dB'de 0,79'dur. ID-XAI ile 0,90'ın üstüne çıkılmış ve etiketli seçimle aradaki fark birkaç binde birlere inmiştir (Şekil 10). Literatürde fan için bildirilen en iyi etiketsiz −6 dB sonuçları yaklaşık 0,76'dır (Bölüm 15)."),
                   ("Az öznitelik daha iyidir. ", "Her iki seçicide de gürültü arttıkça en iyi k küçülmektedir (−6 dB'de 5-10). Gürültü, öznitelik uzayının çoğunu bilgisiz hale getirir. Seçim, kNN mesafesini bu boyutların baskınlığından kurtarmaktadır."),
                   ("Seviye özniteliklerinin rolü. ", "Ses seviyesine bağlı öznitelikler çıkarıldığında ID-XAI'nin üstünlüğü azalmaktadır (Tablo 14.4). Seçilen özniteliklerin bir kısmı, kimlikleri birbirinden ayıran mutlak seviye özellikleridir ve arızalı fanların seviye değişimini de yakalamaktadır. MIMII'de arızalı kayıtların seviyesinin fiziksel bir arıza imzası mı yoksa kayıt farkı mı olduğu ayırt edilemediğinden (Bölüm 11.6), bu bulgu sınırlılık olarak raporlanmalıdır."),
                   ("Derin öğrenme modelinin katkısı en gürültülü düzeydedir. ", "CNN tabanlı ID sınıflandırıcısı tek başına önerilen yöntemin gerisindedir (+6 dB'de 0,877, −6 dB'de 0,839). Ancak −6 dB'de log-mel autoencoder'lardan ve seçimsiz özniteliklerden belirgin yüksektir. Önerilen yöntemle sıra ortalamasıyla birleştirildiğinde −6 dB'de 0,918 AUC vermiştir. Bu, bu çalışmadaki en yüksek etiketsiz −6 dB değeridir, ancak önerilen yöntemle farkı istatistiksel olarak anlamlı değildir (p = 0,52). +6 dB'de ise füzyon sonucu düşürmektedir. Çalışmanın derin öğrenme bulgusu şudur: yalnızca normal veriyle 'kimlik' gibi bir yardımcı görev çözdürmek, hem CNN'de hem de XAI seçiminde etiketsiz anomali tespiti için güçlü bir öğrenme sinyalidir.")]:
    W.bold_lead(lead, rest)
W.h2("14.5 Sınırlılıklar")
for t in ["Yöntem, aynı türden birden fazla makine kimliğinin normal kaydına ihtiyaç duyar. Tek makineli bir tesiste doğrudan uygulanamaz.",
          "Sonuçlar yalnızca fan türü içindir. Pompa, kızak ve vana henüz çalışılmamıştır.",
          "Literatürle kıyaslar farklı bölünmelerle yapılmış çalışmalara dayanır, yaklaşık kıyastır. DCASE 2020 Task 2 geliştirme/değerlendirme bölünmesinde ayrıca test edilmelidir.",
          "Makine ID sınıflandırıcısı CPU'da küçük genişlikle (w = 16, 30 epoch) eğitilmiştir. GPU'da tam genişlikle (Colab defteri) sonuçlar değişebilir.",
          "Seviye özniteliklerinin katkısı yukarıda tartışılmıştır."]:
    W.bullet(t)

# ===================================================================== LİTERATÜR
W.h1("15. Literatür Taraması ve Yayın için Konumlandırma")
W.p("MIMII fan verisinde gürültü düzeyine göre sonuç veren çalışmalar taranmış, dört fan kimliği ortalamasında etiketsiz yöntemlerin bildirdiği AUC değerleri Tablo 15.1'de derlenmiştir.")
tab("Tablo C", [4800, 1612, 1613, 1613]); W.cap("Tablo 15.1. Literatürle kıyas (fan; 00, 02, 04, 06 kimliklerinin ortalaması; etiketsiz yöntemler; AUC). Literatür değerleri: MIMII makalesi Tablo 3 [1], MemNMF Tablo III [6] (AE, VAE, GRLNet değerleri bu kaynağın yeniden hesaplamasıdır), Li vd. Tablo IV [7]. Bölünmeler aynı değildir.")
W.p("Taramadan çıkan, bu çalışmanın doldurduğu boşluklar:")
for lead, rest in [("Gürültüye dayanıklılık için XAI tabanlı seçim. ", "XAI ile öznitelik seçimi makine sesinde kullanılmıştır (tez [5] ve benzeri çalışmalar), ancak yalnızca +6 dB'de ve arıza etiketiyle. Gürültü düzeyine göre davranışı ve etiketsiz bir türevi bildirilmemiştir."),
                   ("Kimlik bilgisinin seçim için kullanılması. ", "Makine kimliği sınıflandırması DCASE'de derin ağların eğitim hedefi olarak yaygındır. Ancak açıklanabilir bir öznitelik seçicisinin etiketi olarak kullanımı taramada bulunamamıştır."),
                   ("Çok kanal. ", "Literatürde sistemlerin çoğu tek kanal kullanır. Bu çalışmada dalga ortalamasının MIMII'de gürültüyü azaltmadığı, buna karşın 8 kanal ortalamasından çıkarılan özniteliklerin tek kanallarla birleştirildiğinde katkı verdiği gösterilmiştir."),
                   ("Değerlendirme titizliği. ", "Etiket karıştırma, blok bölünme, seviyesiz öznitelik, üç protokol ve eşleştirilmiş istatistik testi birlikte raporlanmıştır.")]:
    W.bold_lead(lead, rest)
W.p("Önerilen başlık (taslak): 'Arıza Etiketi Olmadan Açıklanabilir Öznitelik Seçimi: Makine Kimliği Vekil Görevi ile Gürültülü Endüstriyel Seslerde Anomali Tespiti'. Hedef: ulusal bir konferans (örneğin SİU) veya bir dergi.")

# ===================================================================== GENEL DEĞERLENDİRME güncelle
gen.runs[0].text = "16. Genel Değerlendirme ve Sıradaki İşler"
for r in gen.runs[1:]: r.text = ""
P = d.paragraphs; gi = next(i for i, p in enumerate(P) if p.text.startswith("16. Genel"))
nxt = next(i for i in range(gi + 1, len(P)) if P[i].style is not None and P[i].style.name.startswith("Heading"))
W2 = Writer(d, P[nxt]); W2.T, W2.tbl = W.T, W.tbl
for t in [f"Hafta 9-10 sonunda fan türünün dört kimliğinde, etiket kullanmadan +6 / 0 / −6 dB'de {p6} / {p0} / {pm6} AUC elde edilmiştir. Bu değerler taranan literatürdeki etiketsiz sonuçların her gürültü düzeyinde üstündedir.",
          "Tezin %99,5 düzeyine +6 dB'de hem tezin yöntemiyle (etiketli seçim, 0,998) hem de etiketsiz ID-XAI ile (0,997) ulaşılmıştır. Tez 0 dB ve −6 dB'de çalışmamıştır. Bu çalışma bu düzeyleri ekleyerek etiketli seçimin −6 dB'de 0,91-0,93, etiketsiz seçimin 0,90-0,91 AUC verdiğini göstermiştir."]:
    W2.num(t)
sq = next(i for i, p in enumerate(d.paragraphs) if p.text == "Sıradaki işler")
P = d.paragraphs; j = sq + 1
while j < len(P) and P[j].style is not None and P[j].style.name == "List Paragraph":
    P[j]._p.getparent().remove(P[j]._p); P = d.paragraphs
W3 = Writer(d, d.paragraphs[sq + 1]); W3.T, W3.tbl = W.T, W.tbl
for t in ["Yöntemi pompa, kızak ve vana türlerine ve DCASE 2020 Task 2 bölünmesine genişletmek.",
          "Seviye özniteliklerinin rolünü ayırmak için seviye normalleştirmesi yapılmış bir ID-XAI sürümü.",
          "ID sınıflandırıcısını GPU'da tam boyutta eğitip (Colab defteri) önerilen yöntemle füzyonunu yeniden değerlendirmek.",
          "Makale metnini (Bölüm 15'teki konumlandırmayla) tamamlamak."]:
    W3.bullet(t)
# kaynaklar
kp = [p for p in d.paragraphs if p.style is not None and p.style.name == "List Paragraph"][-1]
for t in ["P. Saengthong, T. Shinozaki, \"MemNMF: Memory-Augmented NMF on LPC Spectra for Anomalous Sound Detection,\" arXiv:2607.22086, 2026.",
          "K. Li, K. Zaman, X. Li, M. Akagi, M. Unoki, \"Machine Anomalous Sound Detection Using Spectral-temporal Modulation Representations Derived from Machine-specific Filterbanks,\" arXiv:2409.05319, 2024.",
          "P. Saengthong, T. Shinozaki, \"Sub-Band Spectral Matching with Localized Score Aggregation for Robust Anomalous Sound Detection,\" arXiv:2603.13749, 2026.",
          "D. S. Park ve ark., \"SpecAugment: A Simple Data Augmentation Method for Automatic Speech Recognition,\" Interspeech, 2019."]:
    import copy
    el = copy.deepcopy(kp._p); kp._p.addnext(el); np_ = docx.text.paragraph.Paragraph(el, kp._parent)
    for r in np_.runs[1:]: r._r.getparent().remove(r._r)
    np_.runs[0].text = t; kp = np_
# kapak
for t in d.tables[:1]:
    for row in t.rows:
        if row.cells[0].text.strip() == "Kapsam":
            c = row.cells[1].paragraphs[0]; c.runs[-1].text += ". Hafta 9: tüm fan kimlikleri, 8 kanal, makine ID sınıflandırıcısı. Hafta 10: etiketsiz XAI öznitelik seçimi (ID-XAI), tez ve literatürle kıyas."
        if row.cells[0].text.strip() == "Rapor tarihi":
            row.cells[1].paragraphs[0].runs[0].text = "24 Kasım 2026"; [setattr(r, "text", "") for r in row.cells[1].paragraphs[0].runs[1:]]
for p in d.paragraphs[:8]:
    if "Hafta 1-8" in p.text:
        for r in p.runs: r.text = r.text.replace("Hafta 1-8", "Hafta 1-10")
out = sys.argv[1]; d.save(out); print("kaydedildi", out)
