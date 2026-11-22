#!/usr/bin/env python3
"""Kullanıcının düzenlediği sunuma:
  1) 'Bu proje neden bir veri iletişimi problemi?' slaytını (4. sıra) ekler,
  2) tüm slaytların konuşmacı notlarını genişletir,
  3) aynı notları yazdırılabilir bir Word konuşma metni olarak üretir.
Slaytların görsel içeriğine dokunmaz (yeni slayt hariç)."""
import copy
import json
import os
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor as DRGB
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Cm as PCm, Pt as PPt

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GIRDI = sys.argv[1]
CIKTI = os.path.join(KOK, "Rumeysa_Betul_Ozyurt_Veri_Iletisimi_Proje_Sunumu.pptx")
METIN = os.path.join(KOK, "Rumeysa_Betul_Ozyurt_Sunum_Konusma_Metni.docx")
R = json.load(open(os.path.join(KOK, "analiz", "ek_analiz.json"), encoding="utf-8"))


def tr(x, b=1):
    return f"{x:.{b}f}".replace(".", ",")


S = {o["sektor"]: o for o in R["sektor"]}
T, B, E, K, U = S["TÜMÜ"], S["Banka"], S["E-ticaret"], S["Kamu"], S["Üniversite"]
cdn_k, cdn_n = map(int, R["cdn_fisher"]["cdn"].split("/"))
oz_k, oz_n = map(int, R["cdn_fisher"]["kendi"].split("/"))
AG, Z = R["ag"], R["zaman"]
SIM = {(x["senaryo"], x["kayip"]): x for x in R["simulasyon"]["rtt20"]}
k01 = (SIM[("Klasik", 0.01)], SIM[("Hibrit (tarayıcı)", 0.01)])
k10 = (SIM[("Klasik", 0.10)], SIM[("Hibrit (tarayıcı)", 0.10)])
art10 = 100 * (k10[1]["ortalama_ms"] / k10[0]["ortalama_ms"] - 1)
sfk, sfh = R["simulasyon"]["sf_klasik_seg"], R["simulasyon"]["sf_hibrit_seg"]
ks = R["katman_kendi_sunucu"]
uni_kaz = sum(1 for d in Z["degisimler"] if d["sektor"] == "Üniversite" and d["yeni_pq"] and not d["eski_pq"])

# ---------------------------------------------------------------------------------
# Notlar: (başlık, süre, söylenecekler, veri iletişimi bağlantısı, olası soru, cevap, geçiş)
# ---------------------------------------------------------------------------------
N = [
 ("Kapak", "30 sn",
  "Merhaba, ben Rümeysa Betül Özyurt. Projemin adı: Türkiye'deki kritik sektör web sitelerinin kuantum sonrası TLS "
  "hazırlığı. Kısaca şunu ölçtüm: Bankalar, kamu kurumları, üniversiteler, e-ticaret siteleri gibi önemli kurumların "
  "web siteleri, gelecekte kuantum bilgisayarların kırabileceği şifrelemeye karşı yeni korumayı kullanıyor mu? Ve bu "
  "yeni koruma internet trafiğine, yani paketlere, baytlara ve gecikmeye ne kadar yük getiriyor? Arka plandaki nokta "
  "deseni, yeni şifreleme standardının dayandığı 'kafes' (lattice) matematiğine bir gönderme.",
  "Proje, veri iletiminin güvenliğini (TLS) ve bu güvenliğin iletim maliyetini (bayt, paket, gecikme) birlikte ele "
  "alıyor; yani hem 'güvenli veri iletimi' hem 'iletim performansı' konularına giriyor.",
  None, None,
  "Önce bu konunun neden şimdi önemli olduğunu anlatayım."),
 ("Neden şimdi?", "1 dk",
  "Bugün bir web sitesine bağlandığımızda tarayıcı ile sunucu, TLS protokolüyle ortak bir gizli anahtar oluşturur. "
  "Bu anahtar X25519 gibi eliptik eğri yöntemleriyle üretiliyor. Shor algoritması, yeterince büyük bir kuantum "
  "bilgisayarda bu yöntemleri kırabiliyor. Ekrandaki üç adım tehdidi özetliyor: 1) Saldırgan bugün şifreli trafiği "
  "kaydeder, 2) bekler, 3) kuantum bilgisayar çıktığında çözer. Buna 'şimdi topla, sonra çöz' deniyor. Mosca "
  "eşitsizliği de şunu söylüyor: verinin gizli kalması gereken süre artı geçiş süresi, kuantum bilgisayarın gelişine "
  "kalan süreden büyükse risk bugünden başlamıştır. Banka ve sağlık verisi 10 yıldan fazla gizli kalmalı; bu yüzden "
  "risk bugün. İyi haber: çözüm hazır. NIST 2024'te ML-KEM'i standartlaştırdı. Klasik X25519 ile ML-KEM birleştirilerek "
  "'hibrit' bir yöntem oluşturuldu: X25519MLKEM768. Chrome, Edge ve Firefox bunu zaten kullanıyor. Yani istemci "
  "tarafı hazır; asıl soru sunucuların kabul edip etmediği.",
  "Saldırının kendisi bir veri iletişimi olayıdır: iletim kanalından geçen paketlerin dinlenip kaydedilmesi "
  "(pasif dinleme). Korunmak istediğimiz şey, kanaldan geçen verinin gizliliğidir.",
  "Kuantum bilgisayar henüz yokken bu neden acil?",
  "Çünkü bugün kaydedilen trafik yıllar sonra çözülebilir. Verinin gizlilik süresi uzunsa, geçişi bugünden yapmak "
  "gerekiyor; bu, Mosca eşitsizliğinin söylediği şey.",
  "Peki bunun veri iletişimi açısından problemi ne? Bir sonraki slayt bunu gösteriyor."),
 ("Problem", "1 dk",
  "Problemin iki tarafı var. Birincisi güvenlik: Türkiye'de hangi kurumların bu yeni korumayı kullandığını bilmiyoruz; "
  "bu konuda Türkiye'ye özel bir ölçüm yok. İkincisi iletim verimliliği: yeni yöntemin anahtarları çok daha büyük. "
  f"El sıkışma başına yaklaşık {tr((AG['yazilan_fark'] + AG['okunan_fark']) / 1000)} kilobayt ek veri gönderiliyor. "
  "Ekrandaki dört kart bunun etkilerini gösteriyor: gizlilik, bant genişliği, gecikme ve kayıp, güvenilirlik. En "
  "önemlisi: tarayıcının gönderdiği ilk mesaj artık tek bir TCP paketine sığmıyor, ikiye bölünüyor. Paket sayısı "
  "artınca kayıplı ağlarda gecikme artıyor; ayrıca ilk mesajın tek paket olduğunu varsayan eski güvenlik duvarları "
  "bağlantıyı bozabiliyor. Alt kısımdaki üç madde de mevcut çalışmaların eksiklerini özetliyor: Türkiye verisi yok, "
  "ağ maliyeti aynı veriyle incelenmemiş, kurumların kendini ölçebileceği açık bir araç yok.",
  "Bant genişliği, gecikme, paket kaybı ve bağlantı güvenilirliği, ödev yönergesinde sayılan veri iletişimi "
  "problemlerinin ta kendisi. Bu projede güvenlik değişikliğinin bu dört parametreyi nasıl etkilediğini ölçüyorum.",
  "2,3 KB çok küçük değil mi, neden önemli?",
  "Bayt olarak küçük; asıl önemli olan nitelik değişikliği: ilk mesaj tek paketten iki pakete çıkıyor. Paket sayısı "
  "artınca kayıp olasılığı ve yeniden iletim gecikmesi artıyor; bunu ileride simülasyonla göstereceğim.",
  "Bu noktada şu soruyu cevaplamak istiyorum: bu konu neden bir veri iletişimi konusu?"),
 ("Veri iletişimiyle ilişkisi", "1 dk",
  "Bu slayt projenin ders içindeki yerini gösteriyor. Soldaki sütun, ödev yönergesinde geçen veri iletişimi konuları; "
  "sağdaki sütun bu projede her birinin karşılığı. TLS ve güvenli haberleşme: ölçtüğüm şey doğrudan TLS 1.3 el "
  "sıkışması. TCP/IP modeli ve katmanlar: değişiklik TLS katmanında oluyor ama etkisi TCP ve Ethernet'te görülüyor. "
  "Paketleme ve çerçeveleme: MTU 1500, MSS 1460 bayt; mesajın kaç segmente bölündüğünü hesapladım ve Wireshark'ta "
  "çerçeve boyutlarını gördüm. Gecikme ve paket kaybı: RTT ölçtüm, kayıplı kanalda yeniden iletim maliyetini "
  "simüle ettim. Bant genişliği: el sıkışma başına ek baytı ölçtüm. Ağ trafiğinin izlenmesi: Wireshark ile paket "
  "yakalama yaptım. Kısaca: kriptografi işin bahanesi; ölçtüğüm şey veri iletiminin kendisi.",
  "Bu slaytın tamamı bu sorunun cevabı. Hocanın yönergesindeki 1.2 (ağ protokolleri, TCP, paket anahtarlama, trafik "
  "izleme) ve 1.5 (TLS, güvenli iletim, paket bütünlüğü) başlıklarına doğrudan giriyor.",
  "Bu bir kriptografi projesi değil mi?",
  "Kriptografik algoritmayı ben tasarlamadım; mevcut standardın ağda nasıl davrandığını ölçtüm. Sorduğum sorular "
  "'kaç bayt, kaç paket, kaç milisaniye, hangi katman' soruları; bunlar veri iletişimi soruları.",
  "Bu çerçevede projenin amacını iki soru ve dört hedefle tanımladım."),
 ("Amaç", "45 sn",
  "İki araştırma sorum var. Birincisi: Türkiye'deki kritik sektör siteleri kuantum sonrası TLS'e hazır mı ve "
  "hazırlığı ne belirliyor? İkincisi: bu geçiş ağa ne maliyet getiriyor: bayt, TCP segmenti ve gecikme olarak? Bunun "
  f"için dört hedef koydum: {R['liste_boyutu']} siteyi ölçen açık bir sistem kurmak; hazırlığın sektöre mi altyapıya "
  "mı bağlı olduğunu istatistikle sınamak; ağ maliyetini ölçüm, Wireshark ve simülasyonla göstermek; ve her şeyi "
  "başkalarının tekrarlayabileceği şekilde yapmak.",
  "İkinci soru tamamen bir iletim performansı sorusu: ek yük, segmentasyon ve gecikme.",
  None, None,
  "Önce literatürde bu konuda ne yapılmış, ona bakalım."),
 ("Literatür", "1 dk",
  "Tablo mevcut çalışmaları karşılaştırıyor. Paquin ve arkadaşları 2020'de laboratuvarda kuantum sonrası TLS'in ağ "
  "maliyetini ve kayıp altındaki davranışını incelemiş; ama gerçek sitelerde ölçüm yapmamış. 2026'da internet "
  "ölçekli çalışmalar var: Dubey ve Varshney 32 bin alan adında ölçmüş, F5 Labs en popüler 1 milyon sitede ölçmüş. "
  "F5'e göre sitelerin yüzde 54'ü hazır; ama Cloudflare dışındaki sitelerde bu oran yüzde 22'ye düşüyor ve sitelerin "
  "yüzde 10,5'i TLS 1.3'ü bile desteklemiyor. İngiltere için sektörel bir çalışma da var. Benim projemin farkı son "
  "satırda: Türkiye'ye odaklanıyor, sektör kırılımı veriyor ve aynı veri üzerinde ağ maliyetini ve kayıp analizini "
  "de yapıyor.",
  "Literatürdeki boşluk tam olarak veri iletişimi kısmında: hazırlık ölçülmüş ama bunun iletim maliyeti aynı veride "
  "ölçülmemiş.",
  "Yeşil tik ne demek, turuncu ne demek?",
  "Yeşil o çalışmada bu analizin var olduğunu, turuncu kısmen yapıldığını, gri nokta hiç yapılmadığını gösteriyor.",
  "Şimdi kurduğum sistemin mimarisine geçiyorum."),
 ("Sistem mimarisi", "1 dk",
  "Mimariyi klasik haberleşme modeliyle anlattım: gönderici, kanal, alıcı. Gönderici tarafı benim bilgisayarım: site "
  "listesini okuyan Python programı, OpenSSL 4.0.3'ü çalıştırıyor; OpenSSL yeni hibrit anahtar grubunu destekliyor. "
  "Sonuçlar CSV dosyasına yazılıyor, Wireshark da paketleri yakalıyor. İletim kanalı Türkiye'deki ev internetim: "
  "Wi-Fi, modem, internet servis sağlayıcısı; TCP/IP üzerinden, paket başına en fazla 1460 bayt veri (MSS), ortalama "
  f"gidiş-dönüş süresi yaklaşık 20 milisaniye. Alıcı tarafında iki tür sunucu var: {cdn_n} site bir içerik dağıtım ağı, "
  f"yani CDN arkasında, örneğin Cloudflare; {oz_n} site ise kurumun kendi sunucusunda. CDN ile kurumun asıl sunucusu "
  "arasındaki bağlantı dışarıdan görünmediği için ölçemiyorum; bu bir sınırlılık.",
  "Gönderici–kanal–alıcı modeli, Shannon'ın haberleşme modeli ve dersin temel çerçevesi. Kanal parametreleri (MSS, "
  "RTT) de veri iletişimi kavramları.",
  "CDN nedir?",
  "İçerik dağıtım ağı: siteyi kullanıcıya yakın sunuculardan sunan şirketler (Cloudflare, Akamai gibi). Kullanıcının "
  "TLS bağlantısı aslında CDN sunucusunda sonlanıyor; bu yüzden şifreleme ayarlarını da büyük ölçüde CDN belirliyor.",
  "Bu sistemi kurarken hangi teknolojileri neden seçtiğimi göstereyim."),
 ("Teknolojiler", "45 sn",
  "Her kartta bir bileşen, rolü, neden seçildiği ve alternatifi var. En önemli seçim OpenSSL'in s_client aracı: hangi "
  "anahtar paylarının gönderileceğini kontrol edebiliyorum ve her mesajın kaç bayt olduğunu görebiliyorum. Python'un "
  "kendi SSL modülü bunları vermiyor. Taşıma olarak TCP ve TLS 1.3 seçtim çünkü kuantum sonrası destek sadece TLS "
  "1.3'te var. Paket analizi için Wireshark, istatistik için Fisher kesin testi kullandım; çünkü bankalarda sıfır "
  "değeri var ve küçük sayılarda ki-kare testi güvenilir değil. Kayıp analizi için Monte Carlo simülasyonu kullandım, "
  "çünkü gerçek internette paket kaybını kontrol edemiyorum.",
  "Protokol seçimi (TCP vs QUIC) ve ölçüm aracı seçimi, ödevde istenen 'protokol seçimlerinin gerekçelendirilmesi' "
  "kısmı.",
  "Neden QUIC/HTTP3 ölçmedin?",
  "HTTPS trafiğinin çoğu hâlâ TCP üzerinden. HTTP/3 desteğini sadece ilan olarak kaydettim; QUIC'e uyarlamak gelecek "
  "çalışma.",
  "Şimdi bağlantı sırasında hangi mesajların gidip geldiğine bakalım."),
 ("Protokol akışı", "1,5 dk",
  "Soldaki diyagram bir hibrit TLS 1.3 bağlantısını adım adım gösteriyor. Önce TCP'nin üçlü el sıkışması var: SYN, "
  "SYN-ACK, ACK; bu bir gidiş-dönüş süresi, yani 1 RTT. Sonra istemci ClientHello gönderiyor. İçinde iki anahtar payı "
  "var: 1216 baytlık hibrit pay ve sunucu desteklemezse diye 32 baytlık klasik X25519 payı. Toplam yaklaşık 1535 bayt; "
  "bu yüzden iki TCP segmentine bölünüyor. Sunucu 1210 baytlık ServerHello ile cevap veriyor, içinde ML-KEM şifre "
  "metni var; arkasından şifreli sertifika ve Finished mesajları geliyor. Bu da 1 RTT. Yani hibrit yöntemle de el "
  "sıkışma toplam 2 RTT'de bitiyor, ekstra gidiş-dönüş yok. Sağdaki panel kötü durumu gösteriyor: sunucu istemcinin "
  "gönderdiği grupları desteklemezse HelloRetryRequest gönderiyor ve istemci ikinci bir ClientHello yolluyor. Bu "
  f"fazladan bir RTT, yani yaklaşık 20 milisaniye demek. Ölçümde {len(R['hrr'])} site her bağlantıda bunu yaşatıyor.",
  "Bu bir protokol mesajlaşma (sıra) diyagramı: el sıkışma, RTT, segmentasyon ve yeniden deneme mekanizmaları "
  "doğrudan veri iletişimi konuları.",
  "1 RTT ne demek?",
  "Bir paketin karşıya gidip cevabının geri gelmesi için geçen süre. Bizim ölçümümüzde ortalama yaklaşık 20 ms.",
  "Bu değişikliğin hangi katmanda olduğunu ve etkisinin nerede görüldüğünü bir sonraki slayt gösteriyor."),
 ("Katmanlar", "1 dk",
  "Bu slayt projenin veri iletişimi açısından özü. TCP/IP modelinin beş katmanını alt alta yazdım. Değişiklik ikinci "
  "satırda, güvenlik katmanında yani TLS'te yapılıyor: yeni anahtar grubu. Ama etkisi alt katmanlarda görülüyor: "
  "taşıma katmanında, yani TCP'de, mesaj daha fazla segmente bölünüyor ve kayıpta yeniden iletim gerekiyor. Ağ erişim "
  "katmanında, yani Ethernet ve Wi-Fi'de, çerçeve boyutu büyüyor; bunu Wireshark'ta 369 bayttan 1591 bayta çıkan "
  "çerçevede gördüm. Sağ sütun her katmanda neyi ölçtüğümü gösteriyor. Renkli satırlar etkinin görüldüğü katmanlar.",
  "Katmanlı mimari ve katmanlar arası etkileşim, dersin temel konusu. Üst katmandaki bir değişikliğin alt katmanlarda "
  "paket ve çerçeve düzeyinde ölçülebilir sonuçları var.",
  "OSI modeline göre TLS hangi katmanda?",
  "TLS, OSI'de genellikle sunum ve oturum katmanlarına karşılık gelir; TCP/IP modelinde uygulama ile taşıma "
  "katmanı arasında durur.",
  "Şimdi paketin içine bayt bayt bakalım."),
 ("Paketleme", "1 dk",
  "Üstteki çubuk klasik ClientHello: başlıklarla 241 bayt, tek segmente rahatça sığıyor. Alttaki çubuk tarayıcının "
  "gönderdiği hibrit ClientHello: 1543 bayt. Yeşil kısım, yani hibrit anahtar payı, mesajın neredeyse yüzde 80'i. "
  "Kırmızı kesikli çizgi 1460 baytlık MSS sınırı: bir TCP segmentinin taşıyabileceği en fazla veri. Ethernet'in MTU'su "
  "1500 bayt; 20 bayt IP, 20 bayt TCP başlığı çıkınca 1460 kalıyor. Mesaj bunu 83 bayt aşıyor, bu yüzden ikinci bir "
  f"segment gerekiyor. Ölçtüğüm {T['n']} sitenin tamamında tarayıcı benzeri ilk mesaj iki segmente bölündü. Alttaki "
  f"kutular özet: ilk mesaj 232'den yaklaşık {int(AG['tarayici_ch_medyan'])} bayta çıkıyor, segment sayısı 1'den 2'ye "
  "çıkıyor, toplam ek veri 2272 bayt.",
  "MTU, MSS, başlık (header), segmentasyon ve çerçeveleme; ödevdeki 'paket ve çerçeve yapıları' başlığının doğrudan "
  "karşılığı.",
  "MSS neden 1460?",
  "Ethernet MTU'su 1500 bayt. Bunun 20 baytı IPv4 başlığı, 20 baytı TCP başlığı; geriye 1460 bayt veri kalıyor.",
  "Bu ölçümleri yapan programın nasıl çalıştığını kısaca göstereyim."),
 ("Ölçüm algoritması", "1 dk",
  "Üstteki ok dizisi her site için yapılan adımlar. Önce alan adını DNS ile bir kez çözüyorum ve tüm testlerde aynı "
  "IP'yi kullanıyorum. Sonra beş kez TCP bağlantısı açıp ortalama gidiş-dönüş süresini ölçüyorum. Ardından beş "
  "senaryo: tarayıcı gibi bağlanmak, TLS 1.2 kabul ediliyor mu diye denemek, sadece yeni hibrit yöntemle bağlanmak, "
  "sadece eski yöntemle bağlanmak ve son olarak bir HTTP isteğiyle CDN bilgisini almak. Sadece hibrit yöntemle "
  "bağlantı kurulabiliyorsa o site 'hazır' sayılıyor. Altta kodun özeti var. Sağdaki kartlar önemli: etik olarak "
  "tarama yapmıyorum, siteler arasında bekliyorum; hatalar kayıt altına alınıyor ve program kaldığı yerden devam "
  "edebiliyor; 500 site için farklı siteleri aynı anda ölçen paralel mod ekledim, tek bir siteye binen yük artmıyor.",
  "DNS çözümleme, TCP bağlantı kurma ve RTT ölçümü ağ ölçümünün temel adımları; ödevdeki 'ağ trafiğinin izlenmesi ve "
  "analizi' başlığına giriyor.",
  "Bir site 'hazır' sayılmak için ne gerekiyor?",
  "Sadece X25519MLKEM768 grubu teklif edildiğinde sunucunun bağlantıyı bu grupla kurması.",
  "Ölçümleri hangi ortamda yaptığıma bakalım."),
 ("Uygulama ortamı", "45 sn",
  f"Halka grafik veri setinin sektörlere dağılımı: toplam {R['liste_boyutu']} site, {len(S) - 1} sektör. Bunlardan "
  f"{T['n']}'i başarıyla ölçüldü; 6 siteye ulaşılamadı. Ölçümleri kendi dizüstü bilgisayarımdan, ev internetimle "
  "yaptım. Yazılım olarak Python, OpenSSL 4.0.3 ve Wireshark kullandım. Üç ölçüm turu var: 7 ve 8 Ekim'de 130 "
  "siteyle iki tur, 22 Kasım'da 500 siteyle üçüncü tur. Kasım ölçümü 28 dakika sürdü. Hibrit ve klasik bağlantıları "
  "beşer kez tekrarlayıp ortanca değeri aldım. Tam ölçümden önce 20 sitelik bir pilot yaptım ve listeyi DNS'te "
  "kontrol ettim.",
  "Tekrarlı ölçüm ve ortanca kullanımı, ağ ölçümlerindeki gürültüyü azaltmanın standart yolu.",
  "Neden tek bir bilgisayardan ölçtün?",
  "Proje kapsamı için yeterli; ama CDN'ler konuma göre farklı sunucuya yönlendirebildiği için farklı ağlardan ölçüm "
  "gelecek çalışma olarak planlandı.",
  "Başarıyı hangi ölçütlerle değerlendirdiğimi göstereyim."),
 ("Performans ölçütleri", "45 sn",
  "Her kartta bir ölçüt, neyi temsil ettiği, nasıl ölçüldüğü ve altında bir etiket var: ölçüm mü, simülasyon mu, "
  "istatistik mi. Bunu özellikle ayırdım, çünkü gerçek ölçüm ile simülasyonu karıştırmamak gerekiyor. Burada bir "
  "noktaya dikkat çekmek istiyorum: ödevde bit hata oranı (BER) da geçiyor. Ama TCP, hatalı paketleri zaten yeniden "
  "gönderdiği için fiziksel katmandaki bit hataları uygulamaya 'paket kaybı ve yeniden iletim' olarak yansıyor. Bu "
  "yüzden BER yerine segment kayıp oranını kullandım.",
  "BER ile paket kaybı arasındaki ilişki: TCP'nin güvenilir iletim mekanizması bit hatalarını segment kaybına "
  "dönüştürür. Bu, dersin hata kontrolü ve güvenilir iletim konusu.",
  "Neden BER ölçmedin?",
  "Uygulama katmanından BER doğrudan görülmez; TCP sağlama toplamı hatalı segmenti atar ve yeniden gönderir. "
  "Bu yüzden kullanıcıya etkisi segment kaybı ve gecikme olarak ortaya çıkar.",
  "Şimdi sonuçlara geçiyorum."),
 ("Bulgu 1: genel hazırlık", "1 dk",
  f"Ölçülen {T['n']} sitenin yalnızca yüzde {tr(T['pq'])}'i, yani {T['pq_k']} site, kuantum sonrası anahtar değişimini "
  f"destekliyor. Yüzde {tr(T['tls12'])}'si hâlâ sadece TLS 1.2 kullanıyor; bunların önce TLS 1.3'e geçmesi gerekiyor, "
  "çünkü yeni yöntem sadece TLS 1.3'te var. Çubuk grafikte yeşil hazır olanlar, mavi sadece klasik TLS 1.3, turuncu "
  f"hâlâ TLS 1.2. Sektörler arasında çok büyük fark var: e-ticarette yüzde {tr(E['pq'])}, bankalarda "
  f"{B['n']} bankadan sadece {B['pq_k']}. Kamuda da yüzde {tr(K['pq'])}. Bankaların yarısı TLS 1.3'e bile geçmemiş.",
  "TLS sürümü bir protokol sürümü sorunu: TLS 1.2'de kalan sunucular yeni anahtar değişimini taşıyamıyor; protokol "
  "yükseltmesi ön koşul.",
  "Yüzde 95 güven aralığı ne demek?",
  f"Gerçek oranın yüzde 95 olasılıkla {tr(T['pq_ci'][0])} ile {tr(T['pq_ci'][1])} arasında olduğu anlamına gelir; "
  "örneklemden kaynaklanan belirsizliği gösterir.",
  "Peki bu farkı ne açıklıyor? En önemli bulgum bir sonraki slaytta."),
 ("Bulgu 2: CDN", "1,5 dk",
  f"Bir sitenin hazır olup olmamasını en çok belirleyen şey CDN kullanıp kullanmaması. CDN arkasındaki {cdn_n} sitenin "
  f"{cdn_k}'si, yani yüzde {tr(100 * cdn_k / cdn_n)}'i hazır. Kendi sunucusunu işleten {oz_n} sitede ise oran yüzde "
  f"{tr(100 * oz_k / oz_n)}. Bu fark istatistiksel olarak çok güçlü. Sonra şunu sordum: banka olmak mı önemli, altyapı "
  "mı? CDN kullanımını sabit tutup sektör etiketlerini 20 bin kez rastgele karıştırdım. Fark büyük ölçüde azaldı ama "
  f"tamamen kaybolmadı. Sağdaki tablo bunu gösteriyor: kendi sunucusunu işletenler arasında üniversiteler "
  f"{ks['Üniversite']} ile öne çıkıyor, bankalar {ks['Banka']}. Bir de ilginç bir sonuç: yerli CDN Medianova arkasındaki "
  f"sitelerin hiçbiri ({R['cdn_pq'].get('Medianova', '0/0')}) hazır değil. Yani belirleyici olan sadece CDN kullanmak "
  "değil; sağlayıcının bu özelliği varsayılan olarak açıp açmadığı.",
  "TLS bağlantısının nerede sonlandığı (CDN uç sunucusu mu, kurumun sunucusu mu) bir ağ mimarisi meselesi; "
  "şifreleme ayarlarını mimari belirliyor.",
  "Permütasyon testi ne yapıyor?",
  "CDN kullanan ve kullanmayan grupların içinde sektör etiketlerini rastgele karıştırıp, gözlenen farkın tesadüfen "
  "ortaya çıkma olasılığını hesaplıyor. p = 0,01 çıktı; yani fark tesadüf değil ama CDN'e göre çok daha küçük.",
  "Şimdi projenin veri iletişimi tarafına, ağ maliyetine geçiyorum."),
 ("Bulgu 3: ağ maliyeti", "1 dk",
  "Grafik klasik ve hibrit el sıkışmadaki mesaj boyutlarını karşılaştırıyor. ClientHello 232 bayttan 1416 bayta, "
  "ServerHello 122 bayttan 1210 bayta çıkıyor. Toplam ek veri her bağlantıda 2272 bayt. Bu, ML-KEM'in sabit boyutlu "
  "anahtarından geliyor; bu yüzden ServerHello hazır olan tüm sitelerde tam 1210 bayt çıktı. 2272 bayt, 2 megabaytlık "
  "bir web sayfasının binde biri kadar; bant genişliği açısından küçük. Ama günde bir milyon bağlantı yapan bir sunucu "
  "için günde yaklaşık 2,3 gigabayt ek trafik demek. Sağda Wireshark doğrulaması var: aynı siteye klasik ilk mesaj "
  "369 baytlık çerçeve, hibrit 1591 bayt. 1591, Ethernet'in 1514 baytlık sınırından büyük; çünkü paket, ağ kartı "
  "bölmeden önce yakalanıyor, buna TSO deniyor. Kayıpsız ev internetinde süre farkı ölçülemeyecek kadar küçük çıktı. "
  f"Bir de sunucunun gönderdiği yanıt da {sfk} segmentten {sfh} segmente çıkıyor.",
  "Bant genişliği kullanımı, ek yük (overhead) hesabı ve paket yakalamayla doğrulama; ödevdeki 'throughput / veri "
  "miktarı / Wireshark' beklentilerinin karşılığı.",
  "1591 bayt nasıl 1514'ten büyük olabiliyor?",
  "Wireshark paketi gönderen bilgisayarda, ağ kartı TCP Segmentation Offload ile bölmeden önce görüyor. Kabloya "
  "çıkarken iki segmente bölünüyor.",
  "Kayıpsız ağda fark yok dedim; peki paket kaybı olursa ne olur?"),
 ("Bulgu 4: simülasyon", "1,5 dk",
  "Bu slayttaki sonuçlar ölçüm değil, simülasyon; köşede de bunu yazdım. Gerçek internette paket kaybını kontrol "
  "edemediğim için, ölçtüğüm paket sayılarıyla bir Monte Carlo simülasyonu yaptım: her paket belli bir olasılıkla "
  "kayboluyor, kaybolursa TCP bir zaman aşımı sonra yeniden gönderiyor. Bunu her kayıp oranı için 40 bin kez "
  f"tekrarladım. Grafik gösteriyor ki kayıp arttıkça yeni yöntem daha yavaş kalıyor: yüzde 10 kayıpta ortalama el "
  f"sıkışma süresi yaklaşık yüzde {tr(art10)} artıyor. Yüzde 1 kayıpta bile, bağlantıda en az bir paketin yeniden "
  f"gönderilme olasılığı yüzde {tr(100 * k01[0]['gecikme_olasiligi'])}'den yüzde {tr(100 * k01[1]['gecikme_olasiligi'])}'ye "
  "çıkıyor. Formül basit: en az bir kayıp olasılığı 1 eksi (1 eksi p) üzeri paket sayısı; paket sayısı arttıkça bu "
  "olasılık artıyor. Kritik nokta sağ altta: tarayıcı, sunucu desteklemese bile büyük mesajı gönderiyor. Yani hazır "
  "olmayan sitelerin kullanıcıları bu bedeli koruma almadan ödüyor.",
  "Paket kaybı, yeniden iletim zaman aşımı (RTO) ve gecikme; dersin 'iletişim kanallarında veri kaybı' ve 'gecikme "
  "analizi' konuları. Simülasyon, kanal modelinin (Bernoulli kayıp) kullanılmasına bir örnek.",
  "Simülasyonun varsayımları neler, ne kadar gerçekçi?",
  "Paketlerin bağımsız kaybolduğunu ve zaman aşımının RTT + 200 ms olduğunu varsaydım. Gerçek ağlarda kayıplar "
  "art arda gelebilir; bu yüzden bunu Linux netem aracıyla gerçek bir deneyle doğrulamayı planladım.",
  "Sonuçlar zaman içinde değişiyor mu ve dünyayla karşılaştırınca nerede duruyoruz?"),
 ("Zaman içinde değişim", "1 dk",
  "Sol tarafta zaman içindeki değişim var. Ekim'de iki kez ölçtüm, iki turda da sonuçlar birebir aynıydı; yani ölçüm "
  f"kararlı. Kasım'da aynı siteleri tekrar ölçtüm: altı haftada hazır site sayısı {Z['pq_ekim']}'den {Z['pq_kasim']}'e "
  f"çıktı. Geçen {Z['pq_kazanan']} kurumun hepsi kendi sunucusunu güncellemiş, {uni_kaz}'sı üniversite. Bir kurum ise CDN'den "
  "ayrılınca desteği kaybetti. Bu da geçişin ikinci yolunun, yani sunucu yazılımını güncellemenin, şu anda işlediğini "
  f"gösteriyor. Sağda dünya ile karşılaştırma: Türkiye'de hazır oranı yüzde {tr(T['pq'])}, dünyada yüzde 54. CDN dışındaki "
  f"sitelerde Türkiye yüzde {tr(100 * oz_k / oz_n)}, dünya yüzde 22. En dikkat çekici olan: Türkiye'de hâlâ TLS 1.2 kullanan "
  f"site oranı yüzde {tr(T['tls12'])}, dünya ortalamasının yaklaşık 2,6 katı.",
  "Tekrarlı ölçümlerle ağ davranışının kararlılığını sınamak ve zaman içinde izlemek, ağ trafiği izleme konusunun bir "
  "parçası.",
  "Türkiye örneklemi dünyayla karşılaştırılabilir mi?",
  "Tam değil; benim örneklemim kamu ve finans ağırlıklı, F5'inki en popüler siteler. Bu yüzden karşılaştırmayı "
  "dikkatli yorumluyorum.",
  "Bütün bunlardan projenin özgün katkılarını özetleyeyim."),
 ("Özgün katkılar", "45 sn",
  "Dört katkı var. Bir: Türkiye'ye özgü, yedi sektörü kapsayan ilk kuantum sonrası TLS ölçümü ve altı haftalık takip. "
  "İki: geçişin iki ayrı yoldan ilerlediğini istatistikle ayırmak: CDN'in varsayılan ayarı ve kurumun kendi sunucusunu "
  "güncellemesi. Üç: aynı veride, bir güvenlik değişikliğinin katmanlar boyunca maliyetini göstermek: TLS'ten TCP "
  "segmentine, oradan Ethernet çerçevesine. Dört: kurumların kendi durumunu ölçebileceği açık bir araç. Bu çalışmayı "
  "bir bildiriye dönüştürmeyi planlıyorum.",
  "Üçüncü katkı doğrudan veri iletişimi katkısı: katmanlar arası maliyet analizi.",
  None, None,
  "Son olarak sonuç ve önerilerim."),
 ("Sonuç ve öneriler", "1 dk",
  "Özetle: Türkiye'de kuantum sonrası geçiş başladı. Bu geçiş çoğunlukla CDN'ler sayesinde oluyor ama son haftalarda "
  f"kurumlar kendi sunucularında da geçiş yapıyor. Siteler yüzde {tr(T['pq'])} hazır; bankalarda bu sayı {B['pq_k']}/"
  f"{B['n']}. Ağ maliyeti küçük ama yapısal: her bağlantıda 2,3 kilobayt ve iki yönde birer paket fazladan. Dört önerim "
  "var. Kendi sunucusu olan kurumlar önce TLS 1.3'e, sonra OpenSSL 3.5 ve üstüne geçmeli. Finans sektörü için "
  "düzenleyici bir takvim gerekli. CDN kullananlar, sağlayıcılarının bu özelliği açtığından emin olmalı ve CDN ile kendi "
  "sunucuları arasını da korumalı. Ağ yöneticileri de iki pakete bölünen ilk mesajı işleyemeyen eski cihazları "
  "güncellemeli. Sınırlılıklarım: tek ölçüm noktası, sadece ana sayfalar ve simülasyon varsayımları; bunları rapora "
  "yazdım. Teşekkür ederim, sorularınızı alabilirim.",
  "Son öneri doğrudan ağ yönetimi önerisi: ara cihazlar (middlebox) ve parçalanmış mesajlar.",
  "Sınırlılıkların neler?",
  "Tek bir ev bağlantısından ölçtüm; sadece ana sayfaları ölçtüm, internet bankacılığı gibi alt alan adlarını "
  "değil; kayıp analizi simülasyon. Gelecekte netem ile gerçek kayıp deneyi ve farklı ağlardan ölçüm planlıyorum.",
  None),
 ("Kaynakça", "—",
  "Bu slaytta durmanıza gerek yok; sadece kaynakların listesi. Tam kaynakça raporda APA 7 formatında var. Soru gelirse "
  "en çok başvurduğum kaynaklar: NIST FIPS 203 standardı, TLS 1.3 için RFC 8446 ve F5 Labs 2026 ölçümü.",
  None, None, None, None),
]


# ---------------------------------------------------------------------------------
# SÖZLÜK: kısaltmalar ve terimler, hiç bilmeyen birine anlatır gibi
# ---------------------------------------------------------------------------------
SOZLUK = {
 "TLS": ("Transport Layer Security", "Taşıma Katmanı Güvenliği",
         "Tarayıcının adres çubuğundaki kilit simgesinin arkasındaki protokol. Bilgisayarınla site arasında giden veriyi "
         "şifreler; böylece yoldaki biri okuyamaz. Mektubu açık zarf yerine kilitli kutuda göndermek gibi."),
 "HTTPS": ("Hypertext Transfer Protocol Secure", "Güvenli HTTP",
           "Web sayfalarının TLS ile şifrelenmiş hâlde taşınması. Adresi 'https://' ile başlayan her site bunu kullanır."),
 "HTTP": ("Hypertext Transfer Protocol", "Köprü Metni Aktarım Protokolü",
          "Tarayıcının siteden sayfa istediği ve sitenin sayfayı gönderdiği dil."),
 "TCP": ("Transmission Control Protocol", "İletim Kontrol Protokolü",
         "Veriyi küçük parçalara (segment) bölüp karşıya sırayla ve eksiksiz ulaştıran protokol. Bir parça kaybolursa "
         "fark eder ve yeniden gönderir. Takipli kargo gibi: eksik koli varsa tekrar yollar."),
 "IP": ("Internet Protocol", "İnternet Protokolü",
        "Her paketin üstüne 'gönderen' ve 'alıcı' adresini yazan, paketi doğru bilgisayara yönlendiren protokol. "
        "Zarftaki adres gibi."),
 "TCP/IP": ("Transmission Control Protocol / Internet Protocol", "İnternetin katman modeli",
            "İnternetin çalışma düzenini 4–5 katmana ayıran model: uygulama, taşıma (TCP), internet (IP), ağ erişimi "
            "(Ethernet/Wi-Fi). Her katman bir işi yapar, bir üsttekine hizmet eder."),
 "OSI": ("Open Systems Interconnection", "Açık Sistemler Bağlantısı modeli",
         "Ağ iletişimini 7 katmana ayıran öğretici model (fiziksel, veri bağı, ağ, taşıma, oturum, sunum, uygulama)."),
 "ML-KEM": ("Module-Lattice-Based Key-Encapsulation Mechanism", "Modül-kafes tabanlı anahtar kapsülleme mekanizması",
            "Kuantum bilgisayarların da kıramayacağı düşünülen yeni anahtar paylaşma yöntemi. 'Kafes' denen çok boyutlu "
            "nokta ızgaralarıyla ilgili zor bir matematik problemine dayanır. NIST 2024'te standart yaptı."),
 "KEM": ("Key Encapsulation Mechanism", "Anahtar kapsülleme",
         "Gizli bir anahtarı karşı tarafın açık anahtarıyla 'kapsülleyip' güvenle göndermek. Kasaya koyup sadece "
         "karşı tarafın açabileceği şekilde kilitlemek gibi."),
 "X25519": ("Curve25519 üzerinde Diffie–Hellman", "Eliptik eğri anahtar değişimi",
            "Bugün sitelerin çoğunun kullandığı anahtar paylaşma yöntemi. Hızlı ve güvenli; ama kuantum bilgisayar "
            "Shor algoritmasıyla kırabilir."),
 "X25519MLKEM768": ("X25519 + ML-KEM-768", "Hibrit anahtar değişimi",
                    "Eski (X25519) ve yeni (ML-KEM) yöntemin aynı anda kullanılması. İkisinin sonucu birleştirilir; biri "
                    "kırılsa bile diğeri korur. Kapıya iki farklı kilit takmak gibi. '768' güvenlik seviyesini belirten "
                    "parametre."),
 "Hibrit": ("Hybrid", "Melez",
            "Klasik ve kuantum sonrası yöntemin birlikte kullanılması (iki kilit)."),
 "Diffie–Hellman": ("Diffie–Hellman key exchange", "Diffie–Hellman anahtar değişimi",
                    "İki tarafın herkesin duyabildiği bir kanalda konuşarak, sadece ikisinin bildiği ortak bir sır "
                    "üretmesi. İki kişinin herkesin önünde boya karıştırıp sonunda sadece kendilerinin bildiği rengi "
                    "elde etmesine benzetilir."),
 "ECDH": ("Elliptic Curve Diffie–Hellman", "Eliptik eğri Diffie–Hellman",
          "Diffie–Hellman'ın eliptik eğri matematiğiyle yapılan, bugün yaygın sürümü (X25519, P-256)."),
 "P-256": ("NIST P-256 / prime256v1", "Bir eliptik eğri",
           "X25519'a alternatif, daha eski bir eliptik eğri. Bazı sunucular sadece bunu destekliyor."),
 "PQ": ("Post-Quantum", "Kuantum sonrası",
        "Kuantum bilgisayarların da kıramayacağı düşünülen kriptografi. Sunumda 'PQ hazır' = site yeni hibrit yöntemi "
        "destekliyor."),
 "Shor": ("Shor algoritması", "Kuantum algoritması",
          "Peter Shor'un 1994'te bulduğu, büyük bir kuantum bilgisayarda RSA ve eliptik eğri şifrelerini hızla kırabilen "
          "algoritma. Bütün telaşın kaynağı."),
 "NIST": ("National Institute of Standards and Technology", "ABD Ulusal Standartlar ve Teknoloji Enstitüsü",
          "Şifreleme standartlarını belirleyen ve dünyanın büyük kısmının takip ettiği ABD kurumu."),
 "FIPS 203": ("Federal Information Processing Standard 203", "NIST'in ML-KEM standardı",
              "ML-KEM'i resmî standart yapan 2024 tarihli belge."),
 "IETF": ("Internet Engineering Task Force", "İnternet Mühendisliği Görev Gücü",
          "İnternet protokollerini (TCP, TLS, HTTP...) standartlaştıran uluslararası topluluk."),
 "RFC": ("Request for Comments", "Yorum talebi (internet standardı belgesi)",
         "IETF'in standart belgeleri. Örneğin TLS 1.3'ün tanımı RFC 8446'da."),
 "CDN": ("Content Delivery Network", "İçerik dağıtım ağı",
         "Bir sitenin içeriğini dünyanın her yerindeki sunuculara kopyalayıp kullanıcıya en yakından sunan şirketler "
         "(Cloudflare, Akamai, Amazon CloudFront). Sen siteye bağlandığında aslında CDN'in sunucusuyla konuşursun; "
         "şifreleme ayarlarını da büyük ölçüde CDN belirler. Mağazanın her mahallede şubesi olması gibi."),
 "Origin": ("Origin server", "Kaynak sunucu",
            "Sitenin asıl sahibi olan kurumun sunucusu. CDN arkasındaki sitelerde CDN ile bu sunucu arasındaki bağlantı "
            "dışarıdan görünmez."),
 "Medianova": ("Medianova", "Yerli CDN sağlayıcısı",
               "Türkiye merkezli bir içerik dağıtım ağı şirketi. Ölçümde arkasındaki sitelerin hiçbiri PQ hazır değildi."),
 "DNS": ("Domain Name System", "Alan adı sistemi",
         "www.ornek.com gibi isimleri bilgisayarın anladığı IP adresine çeviren sistem. İnternetin telefon rehberi."),
 "RTT": ("Round-Trip Time", "Gidiş-dönüş süresi",
         "Bir paketin karşıya gidip cevabının geri gelmesi için geçen süre. Ölçümde ortalama ≈ 20 milisaniye. "
         "Bir soru sorup cevabını duyana kadar geçen süre gibi."),
 "ms": ("millisecond", "milisaniye", "Saniyenin binde biri."),
 "MTU": ("Maximum Transmission Unit", "En büyük iletim birimi",
         "Ağda tek seferde gönderilebilecek en büyük paket boyutu. Ethernet'te 1500 bayt. Kargo kutusunun en büyük "
         "boyutu gibi."),
 "MSS": ("Maximum Segment Size", "En büyük segment boyutu",
         "Bir TCP segmentinin taşıyabileceği en fazla veri: 1500 (MTU) − 20 (IP başlığı) − 20 (TCP başlığı) = 1460 bayt. "
         "Kutunun içine sığan eşya miktarı."),
 "Segment / paket / çerçeve": ("Segment / Packet / Frame", "Veri parçalarının katmanlara göre adı",
                               "Aynı verinin farklı katmanlardaki adı: TCP'de 'segment', IP'de 'paket', Ethernet'te "
                               "'çerçeve'. Her katman kendi başlık bilgisini ekler, zarf içinde zarf gibi."),
 "Bayt": ("Byte", "Bayt", "8 bitlik veri birimi; yaklaşık bir harf. 1 KB ≈ 1000 bayt, 1 GB ≈ 1 milyar bayt."),
 "El sıkışma": ("Handshake", "El sıkışma",
                "Şifreli konuşmaya başlamadan önce tarayıcı ile sunucunun yöntem ve anahtar üzerinde anlaştığı ilk mesaj "
                "alışverişi. Tanışıp ortak dil belirlemek gibi."),
 "ClientHello": ("Client Hello", "İstemcinin 'merhaba' mesajı",
                 "Tarayıcının sunucuya gönderdiği ilk TLS mesajı: 'Şu yöntemleri biliyorum, işte anahtar payım.' Hibrit "
                 "yöntemde büyüdüğü için iki pakete bölünüyor."),
 "ServerHello": ("Server Hello", "Sunucunun cevap mesajı",
                 "Sunucunun 'Şu yöntemi seçtim, işte benim payım' diye cevap verdiği mesaj. Hibritte 122'den 1210 bayta çıkıyor."),
 "key_share": ("Key share", "Anahtar payı",
               "ClientHello içindeki, anahtar değişimi için gönderilen açık değer. Hibrit payı 1216 bayt."),
 "HRR": ("HelloRetryRequest", "'Tekrar dener misin' isteği",
         "Sunucu tarayıcının teklif ettiği yöntemi desteklemiyorsa 'başka yöntemle tekrar gönder' der. Fazladan bir "
         "gidiş-dönüş (≈ 20 ms) kaybettirir."),
 "SYN / ACK": ("Synchronize / Acknowledge", "TCP bağlantı açma mesajları",
               "TCP bağlantısı üç mesajla açılır: SYN ('konuşalım mı?'), SYN-ACK ('olur'), ACK ('tamam'). Buna üçlü el "
               "sıkışma denir."),
 "RTO": ("Retransmission Timeout", "Yeniden iletim zaman aşımı",
         "TCP'nin kaybolan paketi yeniden göndermeden önce beklediği süre (en az ≈ 200 ms). Kargo gelmeyince belli bir "
         "süre bekleyip yeniden göndermek gibi."),
 "Paket kaybı": ("Packet loss", "Paket kaybı",
                 "Ağda bir paketin yolda kaybolması (zayıf Wi-Fi, yoğun hat). TCP fark edip yeniden gönderir ama bu zaman "
                 "kaybettirir."),
 "TSO": ("TCP Segmentation Offload", "TCP bölme işinin ağ kartına devri",
         "Büyük veriyi segmentlere bölme işini işlemci yerine ağ kartının yapması. Wireshark paketi bölünmeden önce "
         "gördüğü için 1591 baytlık 'dev' çerçeve görünüyor."),
 "BER": ("Bit Error Rate", "Bit hata oranı",
         "İletilen bitlerin ne kadarının bozulduğu. TCP bozuk segmenti atıp yeniden gönderdiği için kullanıcı bunu "
         "'paket kaybı' olarak hisseder; bu yüzden projede kayıp oranı kullanıldı."),
 "Ethernet / Wi-Fi": ("Ethernet / Wireless Fidelity", "Kablolu / kablosuz yerel ağ",
                      "Verinin bilgisayardan modeme fiziksel olarak taşındığı alt katman teknolojileri."),
 "OpenSSL": ("OpenSSL", "Açık kaynak TLS kütüphanesi",
             "Sunucuların ve programların TLS'i çalıştırmak için kullandığı yazılım. 3.5 sürümünden itibaren hibrit "
             "yöntem varsayılan olarak açık."),
 "s_client": ("OpenSSL s_client", "OpenSSL'in test istemcisi",
              "Bir siteye komut satırından TLS bağlantısı açıp her mesajı ve boyutunu gösteren araç. Ölçümün kalbi."),
 "Wireshark": ("Wireshark", "Paket yakalama programı",
               "Bilgisayarın ağ kartından geçen her paketi yakalayıp içini gösteren program. Ağın 'röntgeni'."),
 "pcap": ("Packet capture", "Paket yakalama dosyası", "Wireshark'ın yakaladığı paketleri kaydettiği dosya (.pcapng)."),
 "HTTP/3 · QUIC": ("HTTP/3 · Quick UDP Internet Connections", "Yeni nesil web protokolü",
                   "TCP yerine UDP üzerinde çalışan yeni web protokolü. Projede sadece sitenin bunu ilan edip etmediği "
                   "kaydedildi."),
 "Alt-Svc": ("Alternative Service", "Alternatif hizmet başlığı", "Sitenin 'beni HTTP/3 ile de bulabilirsin' dediği HTTP başlığı."),
 "Sertifika · RSA · ECDSA": ("Certificate · Rivest–Shamir–Adleman · Elliptic Curve DSA", "Kimlik belgesi ve imza türleri",
                             "Sertifika sitenin 'kimlik kartı'dır; RSA ve ECDSA bu kartı imzalamak için kullanılan yöntemler. "
                             "Kuantum sonrası imzalı sertifikaya henüz rastlanmadı."),
 "Middlebox": ("Middlebox / TLS inspection", "Ara cihaz (güvenlik duvarı, TLS denetim cihazı)",
               "Kurumların ağında trafiği inceleyen cihazlar. Bazı eski cihazlar ilk mesajın tek paket olduğunu varsayar; "
               "iki pakete bölünen ClientHello'yu bozabilir."),
 "Monte Carlo": ("Monte Carlo simulation", "Monte Carlo simülasyonu",
                 "Rastgele olayı (paket kaybı) bilgisayarda binlerce kez deneyip ortalama sonucu bulma yöntemi. Zarı "
                 "40 bin kez atıp ortalamaya bakmak gibi."),
 "p değeri": ("p-value", "p değeri",
              "Görülen farkın tesadüfen ortaya çıkma olasılığı. 0,05'ten küçükse fark 'anlamlı' kabul edilir; 10⁻⁷³ gibi "
              "bir değer, farkın tesadüf olma ihtimalinin sıfıra çok yakın olduğu anlamına gelir."),
 "Fisher kesin testi": ("Fisher's exact test", "Fisher kesin testi",
                        "İki grubun oranlarını (ör. CDN'li ve CDN'siz sitelerde hazır olma) karşılaştıran, küçük sayılarda "
                        "da güvenilir istatistik testi."),
 "Ki-kare (χ²)": ("Chi-square test", "Ki-kare testi", "Birden fazla grubun oranları arasında fark olup olmadığını sınayan test."),
 "Permütasyon testi": ("Permutation test", "Permütasyon (karıştırma) testi",
                       "Etiketleri (ör. sektör adlarını) rastgele karıştırıp binlerce kez tekrar ederek, gerçek farkın "
                       "tesadüfle açıklanıp açıklanamayacağını bulan test."),
 "GA (güven aralığı)": ("Confidence Interval (CI) · Wilson", "Güven aralığı",
                        "Gerçek oranın %95 olasılıkla bulunduğu aralık. Örneklem küçükse aralık geniş olur."),
 "Medyan": ("Median", "Ortanca", "Sıralanmış değerlerin tam ortasındaki değer; uç değerlerden etkilenmez."),
 "F5 Labs": ("F5 Labs", "F5 şirketinin araştırma birimi",
             "2026'da en popüler 1 milyon sitede PQ hazırlığını ölçen ve karşılaştırma için kullandığım rapor."),
 "Mosca eşitsizliği": ("Mosca's inequality", "Mosca eşitsizliği",
                       "x + y > z: Verinin gizli kalma süresi (x) ile geçiş süresi (y) toplamı, kuantum bilgisayarın "
                       "gelmesine kalan süreden (z) büyükse risk bugün başlamıştır."),
 "Docker": ("Docker", "Konteyner yazılımı", "Programı tüm ayarlarıyla paketleyip her bilgisayarda aynı şekilde çalıştırmayı sağlar."),
}
TERIMLER = [
 ["TLS", "PQ", "Hibrit"],
 ["Shor", "X25519", "Diffie–Hellman", "Mosca eşitsizliği", "NIST", "ML-KEM", "X25519MLKEM768"],
 ["TCP", "Bayt", "Middlebox", "Paket kaybı"],
 ["TLS", "OSI", "TCP/IP", "MTU", "MSS", "RTT", "Paket kaybı", "Wireshark"],
 ["CDN", "TCP", "Segment / paket / çerçeve"],
 ["F5 Labs", "TLS", "RFC", "IETF"],
 ["OpenSSL", "s_client", "MSS", "RTT", "CDN", "Origin"],
 ["s_client", "TCP", "HTTP/3 · QUIC", "Wireshark", "Fisher kesin testi", "Ki-kare (χ²)", "Monte Carlo", "Docker"],
 ["SYN / ACK", "RTT", "El sıkışma", "ClientHello", "key_share", "ServerHello", "HRR", "P-256"],
 ["TCP/IP", "OSI", "HTTP", "Ethernet / Wi-Fi", "TSO"],
 ["MTU", "MSS", "Segment / paket / çerçeve", "Bayt"],
 ["DNS", "IP", "RTT", "HTTP/3 · QUIC", "Alt-Svc"],
 ["Medyan", "Wireshark", "DNS"],
 ["BER", "Paket kaybı", "RTO", "Monte Carlo", "p değeri"],
 ["GA (güven aralığı)", "TLS"],
 ["CDN", "Origin", "Medianova", "Fisher kesin testi", "Permütasyon testi", "p değeri"],
 ["ClientHello", "ServerHello", "TSO", "pcap", "Bayt"],
 ["Monte Carlo", "Paket kaybı", "RTO", "RTT"],
 ["F5 Labs", "CDN", "TLS"],
 ["CDN", "Segment / paket / çerçeve"],
 ["OpenSSL", "Middlebox", "CDN"],
 ["NIST", "FIPS 203", "RFC"],
]
OZ = [
 "Kurumların web siteleri gelecekteki kuantum tehdidine karşı yeni şifrelemeyi kullanıyor mu, bunun internete maliyeti ne?",
 "Bugün kaydedilen şifreli trafik yarın çözülebilir; çözüm hazır, soru sitelerin bunu kullanıp kullanmadığı.",
 "Sorun iki yönlü: hangi kurumlar korumalı bilinmiyor ve yeni yöntem paketleri büyütüyor.",
 "Ölçtüğüm şey veri iletiminin kendisi: bayt, paket, katman, gecikme ve kayıp.",
 "İki soru: Türkiye hazır mı ve bunun ağa maliyeti ne?",
 "Dünyada ölçümler var ama Türkiye yok ve ağ maliyeti aynı veride ölçülmemiş.",
 "Benim bilgisayarım (gönderici) → ev interneti (kanal) → siteler (alıcı).",
 "Her aracı neden seçtiğimin özeti.",
 "Tarayıcı ile site arasındaki mesajlaşma: yeni yöntem ekstra bekleme getirmiyor ama ilk mesaj iki pakete bölünüyor.",
 "Değişiklik şifreleme katmanında, etkisi alttaki taşıma ve fiziksel katmanlarda görülüyor.",
 "İlk mesaj 1460 baytlık paket sınırını aşıyor, iki pakete bölünüyor.",
 "Programım her siteye aynı 5 testi uyguluyor.",
 "Ne kadar siteyi, hangi ortamda, kaç kez ölçtüm.",
 "Başarıyı neyle ölçtüm; neyin ölçüm neyin simülasyon olduğu.",
 "Sitelerin sadece dörtte biri hazır; bankalar en geride.",
 "Hazır olmayı en çok belirleyen şey CDN kullanmak.",
 "Yeni yöntem her bağlantıda 2,3 KB ekliyor; küçük ama paket sayısını artırıyor.",
 "Paket kaybı olan ağlarda yeni yöntem daha yavaş kalıyor (simülasyon).",
 "6 haftada 7 kurum geçti; Türkiye dünyanın gerisinde.",
 "Projenin yeni olan dört yanı.",
 "Geçiş başladı ama bankalar ve kamu geride; dört öneri.",
 "Kaynaklar.",
]


def not_metni(n, i=None):
    bas, sure, soz, vi, soru, cevap, gecis = n
    p = [f"[{bas} · yaklaşık {sure}]", "", f"BU SLAYTIN ÖZÜ: {OZ[i]}", "", "NE SÖYLEYECEĞİM:", soz]
    if vi:
        p += ["", "VERİ İLETİŞİMİYLE BAĞLANTISI:", vi]
    if soru:
        p += ["", f"OLASI SORU: {soru}", f"CEVAP: {cevap}"]
    if gecis:
        p += ["", f"GEÇİŞ: \"{gecis}\""]
    p += ["", "BU SLAYTTAKİ TERİMLER:"]
    for t in TERIMLER[i]:
        ac, tr_, an = SOZLUK[t]
        p.append(f"• {t} ({ac} = {tr_}): {an}")
    return "\n".join(p)


# ---------------------------------------------------------------------------------
# Sunum: yeni slayt + notlar
# ---------------------------------------------------------------------------------
prs = Presentation(GIRDI)
LACI, YESIL, GRI = RGBColor(0x14, 0x21, 0x3D), RGBColor(0x12, 0x8C, 0x6A), RGBColor(0x5E, 0x67, 0x74)
YESIL_A, CIZGI, ZEMIN, BEYAZ = RGBColor(0xE2, 0xF3, 0xEC), RGBColor(0xD5, 0xDB, 0xE3), RGBColor(0xF7, 0xF9, 0xFC), RGBColor(0xFF, 0xFF, 0xFF)
MAVI_A = RGBColor(0xE4, 0xEC, 0xF8)
FG, FB = "Segoe UI", "Segoe UI Semibold"


def yazi(sl, x, y, w, h, m, b, r, kalin=False, hiza=PP_ALIGN.LEFT, dikey=MSO_ANCHOR.TOP):
    tf = sl.shapes.add_textbox(x, y, w, h).text_frame
    tf.word_wrap = True; tf.vertical_anchor = dikey
    p = tf.paragraphs[0]; p.alignment = hiza
    ru = p.add_run(); ru.text = m; ru.font.size = PPt(b); ru.font.color.rgb = r; ru.font.name = FB if kalin else FG


def kutu(sl, x, y, w, h, dolgu, cizgi=None):
    s = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = dolgu
    if cizgi:
        s.line.color.rgb = cizgi; s.line.width = PPt(1)
    else:
        s.line.fill.background()
    s.shadow.inherit = False; s.adjustments[0] = 0.12


sl = prs.slides.add_slide(prs.slide_layouts[6])
sl.background.fill.solid(); sl.background.fill.fore_color.rgb = ZEMIN
yazi(sl, PCm(1.6), PCm(0.75), PCm(20), PCm(0.8), "DERSLE İLİŞKİSİ", 11, YESIL, True)
yazi(sl, PCm(1.6), PCm(1.35), PCm(30.5), PCm(1.7), "Bu proje neden bir veri iletişimi problemi?", 28, LACI, True,
     dikey=MSO_ANCHOR.MIDDLE)
k = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, PCm(1.65), PCm(3.0), PCm(1.6), PCm(0.09))
k.fill.solid(); k.fill.fore_color.rgb = YESIL; k.line.fill.background()
yazi(sl, PCm(1.6), PCm(3.5), PCm(9.5), PCm(0.8), "DERS KONUSU (ÖDEV YÖNERGESİ)", 11, GRI, True)
yazi(sl, PCm(11.8), PCm(3.5), PCm(20), PCm(0.8), "BU PROJEDEKİ KARŞILIĞI", 11, GRI, True)
eslesme = [("TLS ve güvenli haberleşme", "TLS 1.3 el sıkışması ve hibrit anahtar değişimi ölçüldü"),
           ("OSI ve TCP/IP katmanları", "TLS'teki değişikliğin TCP ve Ethernet'teki etkisi izlendi"),
           ("Paket ve çerçeve yapısı · MTU/MSS", "ClientHello 1 → 2 TCP segmenti; çerçeve 369 → 1591 B (Wireshark)"),
           ("Gecikme (RTT) analizi", f"TCP RTT ölçümü; HelloRetryRequest ile +1 RTT ({len(R['hrr'])} site)"),
           ("Paket kaybı ve yeniden iletim", f"Kayıplı kanal simülasyonu: %10 kayıpta +%{tr(art10)} el sıkışma süresi"),
           ("Bant genişliği kullanımı", "El sıkışma başına +2272 B; 1 milyon bağlantıda ≈ 2,3 GB/gün"),
           ("Ağ trafiğinin izlenmesi", f"{R['liste_boyutu']} siteye 3 ölçüm turu + Wireshark paket yakalama")]
for i, (a, b) in enumerate(eslesme):
    y = PCm(4.4 + i * 1.82)
    kutu(sl, PCm(1.6), y, PCm(9.6), PCm(1.55), MAVI_A)
    yazi(sl, PCm(1.9), y, PCm(9.2), PCm(1.55), a, 15, LACI, True, dikey=MSO_ANCHOR.MIDDLE)
    ar = sl.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, PCm(11.35), y + PCm(0.45), PCm(0.7), PCm(0.65))
    ar.fill.solid(); ar.fill.fore_color.rgb = YESIL; ar.line.fill.background()
    kutu(sl, PCm(12.2), y, PCm(20.0), PCm(1.55), BEYAZ, CIZGI)
    yazi(sl, PCm(12.6), y, PCm(19.4), PCm(1.55), b, 15, LACI, dikey=MSO_ANCHOR.MIDDLE)
alt = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, prs.slide_height - PCm(0.9), prs.slide_width, PCm(0.9))
alt.fill.solid(); alt.fill.fore_color.rgb = BEYAZ; alt.line.fill.background()
yazi(sl, PCm(1.6), prs.slide_height - PCm(0.82), PCm(22), PCm(0.75), "Kuantum Sonrası TLS Hazırlığı  ·  Veri İletişimi (BİL321)",
     10, GRI, dikey=MSO_ANCHOR.MIDDLE)
# 4. sıraya taşı
lst = prs.slides._sldIdLst
yeni = lst[-1]; lst.remove(yeni); lst.insert(3, yeni)

# Sayfa numaralarını güncelle (alt bilgideki iki haneli numaralar)
for i, s in enumerate(prs.slides, 1):
    for sh in s.shapes:
        if (sh.has_text_frame and sh.text_frame.text.strip().isdigit() and len(sh.text_frame.text.strip()) == 2
                and sh.top > prs.slide_height - PCm(1.2)):   # yalnızca alt bilgideki sayfa numarası
            r_ = sh.text_frame.paragraphs[0].runs
            if r_:
                r_[0].text = f"{i:02d}"
                for extra in r_[1:]:
                    extra.text = ""
    if i == 4:
        yazi(s, prs.slide_width - PCm(3.6), prs.slide_height - PCm(0.82), PCm(2.0), PCm(0.75), "04", 10, YESIL, True,
             PP_ALIGN.RIGHT, MSO_ANCHOR.MIDDLE)

assert len(prs.slides) == len(N), (len(prs.slides), len(N))
assert len(TERIMLER) == len(OZ) == len(N)
ornek_ph = next(x.notes_slide.notes_placeholder for x in prs.slides
                if x.has_notes_slide and x.notes_slide.notes_placeholder is not None)
for i, (s, n) in enumerate(zip(prs.slides, N)):
    ns = s.notes_slide
    if ns.notes_placeholder is None:   # not alanı olmayan slayta, başka slayttan not alanı kopyala
        ns.shapes._spTree.append(copy.deepcopy(ornek_ph._element))
    ns.notes_text_frame.text = not_metni(n, i)
prs.save(CIKTI)
print("Sunum:", CIKTI, len(prs.slides), "slayt")

# ---------------------------------------------------------------------------------
# Yazdırılabilir konuşma metni (Word)
# ---------------------------------------------------------------------------------
d = Document()
st = d.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(11.5)
for sec in d.sections:
    sec.top_margin = sec.bottom_margin = Cm(2); sec.left_margin = sec.right_margin = Cm(2.2)
h = d.add_paragraph(); r = h.add_run("Sunum Konuşma Metni"); r.bold = True; r.font.size = Pt(20)
d.add_paragraph("Kuantum Sonrası TLS Hazırlığı · Veri İletişimi (BİL321) · Rümeysa Betül Özyurt").runs[0].font.color.rgb = DRGB(0x5E, 0x67, 0x74)
kutu_ = d.add_paragraph()
kutu_.add_run("Tek cümlelik özet (soru gelirse): ").bold = True
kutu_.add_run("Türkiye'deki 500 kritik sitenin kuantum bilgisayarlara karşı yeni şifrelemeyi ne kadar kullandığını ölçtüm "
              "ve bu yeni şifrelemenin internet trafiğine — bayt, paket ve gecikme olarak — maliyetini analiz ettim.")
kutu2 = d.add_paragraph()
kutu2.add_run("\"Bunun veri iletişimiyle ilgisi ne?\" sorusunun kısa cevabı: ").bold = True
kutu2.add_run("Ölçtüğüm şey veri iletiminin kendisi: TLS el sıkışmasındaki mesajların kaç bayt olduğu, kaç TCP segmentine "
              "bölündüğü (MTU/MSS), Ethernet çerçevesinin boyutu, RTT ve paket kaybı altında gecikme. Kriptografi işin "
              "nedeni; ölçülen ve analiz edilen şey protokol katmanları boyunca iletim maliyeti.")
toplam = 0
for i, n in enumerate(N, 1):
    bas, sure, soz, vi, soru, cevap, gecis = n
    p = d.add_paragraph(); p.paragraph_format.space_before = Pt(12)
    r = p.add_run(f"Slayt {i} · {bas}"); r.bold = True; r.font.size = Pt(14); r.font.color.rgb = DRGB(0x12, 0x8C, 0x6A)
    r2 = p.add_run(f"   ({sure})"); r2.font.color.rgb = DRGB(0x5E, 0x67, 0x74)
    q = d.add_paragraph(); q.add_run("Bu slaytın özü: ").bold = True; q.add_run(OZ[i - 1]).italic = True
    d.add_paragraph(soz)
    if vi:
        q = d.add_paragraph(); q.add_run("Veri iletişimi bağlantısı: ").bold = True; q.add_run(vi)
    if soru:
        q = d.add_paragraph(); q.add_run(f"Olası soru: {soru} ").bold = True; q.add_run(f"→ {cevap}")
    if gecis:
        q = d.add_paragraph(); rr = q.add_run(f"Geçiş: \"{gecis}\""); rr.italic = True
    q = d.add_paragraph(); q.add_run("Bu slayttaki terimler: ").bold = True; q.add_run(", ".join(TERIMLER[i - 1]))
d.add_page_break()
h = d.add_paragraph(); r = h.add_run("Sözlük: Kısaltmalar ve Terimler"); r.bold = True; r.font.size = Pt(18)
d.add_paragraph("Her terim için: İngilizce açılımı · Türkçe karşılığı · basit açıklama.")
for t in sorted(SOZLUK, key=lambda x: x.lower().replace("ç", "c").replace("ş", "s").replace("ı", "i").replace("ö", "o").replace("ü", "u").replace("ğ", "g")):
    ac, tr_, an = SOZLUK[t]
    q = d.add_paragraph(); q.paragraph_format.space_after = Pt(4)
    r = q.add_run(t); r.bold = True; r.font.color.rgb = DRGB(0x12, 0x8C, 0x6A)
    q.add_run(f"  ({ac} · {tr_})").italic = True
    q.add_run(f"\n{an}")
d.save(METIN)
print("Konuşma metni:", METIN)
