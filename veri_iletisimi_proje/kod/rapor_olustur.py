#!/usr/bin/env python3
"""Ders yönergesine uygun akademik proje raporunu (.docx) üretir.
Biçim: A4, Times New Roman 12, başlıklar 14 kalın, alt başlıklar 12 kalın, 1,5 satır,
iki yana yaslı, 2,5 cm kenar, paragraf önce 0 / sonra 6 nk, kapak hariç sayfa numarası."""
import json
import os
import re
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEK = os.path.join(KOK, "sekiller")
R = json.load(open(os.path.join(KOK, "analiz", "ek_analiz.json"), encoding="utf-8"))
CIKTI = sys.argv[1] if len(sys.argv) > 1 else os.path.join(KOK, "Rumeysa_Betul_Ozyurt_Veri_Iletisimi_Proje_Raporu.docx")

ogrenci = dict(ad="Rümeysa Betül ÖZYURT", no="[Öğrenci numarası]", donem="2026–2027 Güz Dönemi")

doc = Document()
st = doc.styles["Normal"]
st.font.name = "Times New Roman"
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.font.size = Pt(12)
pf = st.paragraph_format
pf.line_spacing = 1.5
pf.space_before = Pt(0)
pf.space_after = Pt(6)
pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

for s in doc.sections:
    s.page_height, s.page_width = Cm(29.7), Cm(21.0)
    s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Cm(2.5)

sekil_no = [0]
tablo_no = [0]


def calistir(p, metin, boyut=None, kalin=None, italik=None):
    """**kalın** ve *italik* işaretlerini destekleyen basit satır içi biçimlendirme."""
    for parca in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", metin):
        if not parca:
            continue
        if parca.startswith("**"):
            r = p.add_run(parca[2:-2]); r.bold = True
        elif parca.startswith("*"):
            r = p.add_run(parca[1:-1]); r.italic = True
        else:
            r = p.add_run(parca)
        r.font.name = "Times New Roman"
        if boyut:
            r.font.size = Pt(boyut)
        if kalin is not None and not parca.startswith("**"):
            r.bold = kalin
        if italik:
            r.italic = True
    return p


def P(metin, hiza=None, boyut=None, kalin=None, italik=None, sonra=None, girinti=None):
    p = doc.add_paragraph()
    if hiza is not None:
        p.alignment = hiza
    if sonra is not None:
        p.paragraph_format.space_after = Pt(sonra)
    if girinti is not None:
        p.paragraph_format.left_indent = Cm(girinti)
    return calistir(p, metin, boyut, kalin, italik)


def H1(metin):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(metin); r.bold = True; r.font.size = Pt(14); r.font.name = "Times New Roman"
    return p


def H2(metin):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(metin); r.bold = True; r.font.size = Pt(12); r.font.name = "Times New Roman"
    return p


def madde(metinler, numarali=False):
    for i, m in enumerate(metinler, 1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.9)
        p.paragraph_format.first_line_indent = Cm(-0.5)
        p.paragraph_format.space_after = Pt(3)
        calistir(p, (f"{i}) " if numarali else "• ") + m)


def sekil(dosya, baslik, genislik=15.5):
    sekil_no[0] += 1
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.line_spacing = 1.0
    p.add_run().add_picture(os.path.join(SEK, dosya), width=Cm(genislik))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.line_spacing = 1.0
    c.paragraph_format.space_after = Pt(10)
    calistir(c, f"**Şekil {sekil_no[0]}.** {baslik}", boyut=10)
    return sekil_no[0]


def hucre_golge(hucre, renk):
    tcPr = hucre._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), renk)
    tcPr.append(shd)


def tablo(baslik, satirlar, genislikler=None, boyut=10, not_=None):
    tablo_no[0] += 1
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.LEFT
    c.paragraph_format.keep_with_next = True
    c.paragraph_format.line_spacing = 1.0
    c.paragraph_format.space_before = Pt(6)
    calistir(c, f"**Tablo {tablo_no[0]}.** {baslik}", boyut=10)
    t = doc.add_table(rows=len(satirlar), cols=len(satirlar[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, satir in enumerate(satirlar):
        for j, deger in enumerate(satir):
            h = t.cell(i, j)
            h.text = ""
            p = h.paragraphs[0]
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(0)
            p.alignment = (WD_ALIGN_PARAGRAPH.CENTER if (i == 0 or (j > 0 and len(str(deger)) <= 26))
                           else WD_ALIGN_PARAGRAPH.LEFT)
            calistir(p, str(deger), boyut=boyut, kalin=(i == 0))
            if i == 0:
                hucre_golge(h, "D9E2F3")
            if genislikler:
                h.width = Cm(genislikler[j])
    if genislikler:
        t.autofit = False
        tblPr = t._tbl.tblPr
        lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
        grid = t._tbl.tblGrid
        for j, gc in enumerate(grid.findall(qn("w:gridCol"))):
            gc.set(qn("w:w"), str(int(genislikler[j] * 567)))
        for j, col in enumerate(t.columns):
            col.width = Cm(genislikler[j])
    if not_:
        n = doc.add_paragraph()
        n.paragraph_format.line_spacing = 1.0
        calistir(n, not_, boyut=9, italik=True)
    else:
        doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return tablo_no[0]


def sayfa_sonu():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def tr(x, b=1):
    return f"{x:.{b}f}".replace(".", ",")


# ---------------------------------------------------------------------------
# KAPAK
# ---------------------------------------------------------------------------
for t, b in (("T.C.", 14), ("İSTANBUL TİCARET ÜNİVERSİTESİ", 14), ("MÜHENDİSLİK FAKÜLTESİ", 13),
             ("İNGİLİZCE BİLGİSAYAR MÜHENDİSLİĞİ BÖLÜMÜ", 13)):
    P(f"**{t}**", WD_ALIGN_PARAGRAPH.CENTER, b, sonra=2)
P("", sonra=30)
P("**VERİ İLETİŞİMİ (BİL321)**", WD_ALIGN_PARAGRAPH.CENTER, 13)
P("Dönem Projesi – Akademik Proje Raporu", WD_ALIGN_PARAGRAPH.CENTER, 12)
P("", sonra=30)
P("**TÜRKİYE'DEKİ KRİTİK SEKTÖR WEB SİTELERİNİN KUANTUM SONRASI TLS HAZIRLIĞI: SEKTÖREL BİR ÖLÇÜM, "
  "AĞ MALİYETİ VE PAKET KAYBI ANALİZİ**", WD_ALIGN_PARAGRAPH.CENTER, 15)
P("", sonra=50)
for k, v in (("Hazırlayan", ogrenci["ad"]), ("Öğrenci Numarası", ogrenci["no"]),
             ("Program", "Bilgisayar Mühendisliği Yüksek Lisans (Bilimsel Hazırlık)"),
             ("Öğretim Üyesi", "Prof. Dr. Agah Tuğrul KORUCU"), ("Akademik Dönem", ogrenci["donem"])):
    p = P(f"**{k}:** {v}", WD_ALIGN_PARAGRAPH.CENTER, 12, sonra=2)
P("", sonra=60)
P("İstanbul, Kasım 2026", WD_ALIGN_PARAGRAPH.CENTER, 12)

# kapak ayrı bölüm: sayfa numarası yok; sonraki bölüm 1'den başlar
yeni = doc.add_section(WD_SECTION.NEW_PAGE)
yeni.top_margin = yeni.bottom_margin = yeni.left_margin = yeni.right_margin = Cm(2.5)
yeni.footer.is_linked_to_previous = False
pgNum = OxmlElement("w:pgNumType"); pgNum.set(qn("w:start"), "1")
yeni._sectPr.append(pgNum)
fp = yeni.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = fp.add_run()
for tip, metin in (("begin", None), (None, "PAGE"), ("end", None)):
    if tip:
        e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), tip); r._r.append(e)
    else:
        e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = metin; r._r.append(e)
r.font.name = "Times New Roman"; r.font.size = Pt(11)

s = {o["sektor"]: o for o in R["sektor"]}
T = s["TÜMÜ"]
ag = R["ag"]
sim = {(x["senaryo"], x["kayip"]): x for x in R["simulasyon"]["rtt20"]}
sim65 = {(x["senaryo"], x["kayip"]): x for x in R["simulasyon"]["rtt65"]}

# ---------------------------------------------------------------------------
# ÖZET
# ---------------------------------------------------------------------------
H1("ÖZET")
P("Yeterince güçlü kuantum bilgisayarlar, bugün HTTPS trafiğini koruyan eliptik eğri tabanlı anahtar değişimini "
  "kırabilecektir; \"şimdi topla, sonra çöz\" tehdidi nedeniyle bu risk bugünden başlamaktadır. Bu projede "
  "Türkiye'de bankacılık, kamu, üniversite ve e-ticaret sektörlerine ait 130 web sitesinin, NIST FIPS 203 ile "
  "standartlaştırılan ML-KEM'e dayalı hibrit X25519MLKEM768 anahtar değişimine hazırlığı, Python ve OpenSSL 4.0.3 "
  "ile geliştirilen açık bir ölçüm aracıyla iki tur hâlinde ölçülmüş; bulgular Wireshark paket yakalamasıyla "
  f"doğrulanmıştır. Başarıyla ölçülen 129 sitenin %{tr(T['pq'])}'i kuantum sonrası anahtar değişimini "
  f"desteklemekte, %{tr(T['tls12'])}'i ise hâlâ yalnızca TLS 1.2 kullanmaktadır. E-ticaret sitelerinin "
  f"%{tr(s['E-ticaret']['pq'])}'i hazırken bankaların hiçbiri hazır değildir. Hazırlığın belirleyicisi içerik "
  f"dağıtım ağı (CDN) kullanımıdır: CDN arkasındaki sitelerin %96,8'i, kendi sunucusunu işletenlerin %2,0'ı hazırdır "
  f"(Fisher kesin testi, p < 10⁻²⁵); CDN kullanımı sabit tutulduğunda sektörler arasındaki fark ortadan kalkmaktadır "
  f"(katmanlı permütasyon testi, p = {tr(R['sektor_permutasyon_cdn_katmanli']['p'], 2)}). Hibrit el sıkışma, "
  "ServerHello mesajını 122 bayttan 1210 bayta çıkarmakta, el sıkışma başına yaklaşık 2,3 KB ek veri getirmekte ve "
  "tarayıcı benzeri ClientHello'yu (medyan 1534 bayt) 1460 baytlık TCP MSS sınırının ötesine taşıyarak iki "
  "segmente bölmektedir. Ölçülen verilerle beslenen Monte Carlo simülasyonu, %1–10 segment kaybında bu ek "
  "segmentin ortalama el sıkışma süresini %1,5–7 artırdığını göstermektedir. Sonuçlar, Türkiye'de kuantum sonrası "
  "geçişin kurumsal kararlardan çok altyapı sağlayıcıları üzerinden ilerlediğini ortaya koymaktadır.")
P("**Anahtar Kelimeler:** kuantum sonrası kriptografi, TLS 1.3, ML-KEM, hibrit anahtar değişimi, ağ ölçümü, "
  "TCP segmentasyonu, CDN")

H1("ABSTRACT")
P("Cryptographically relevant quantum computers would break the elliptic-curve key exchange that protects today's "
  "HTTPS traffic, and the \"harvest now, decrypt later\" threat makes this a present-day risk. This project measures "
  "the readiness of 130 Turkish websites in the banking, public, university and e-commerce sectors for the hybrid "
  "X25519MLKEM768 key exchange using an open Python/OpenSSL 4.0.3 measurement tool in two runs, validated by "
  "packet capture. Of 129 sites measured, 24.8% support post-quantum key exchange and 26.4% still offer only "
  "TLS 1.2; 80% of e-commerce sites are ready while no bank is. CDN use is the determinant: 96.8% of CDN-fronted "
  "sites are ready versus 2.0% of self-hosted ones (Fisher's exact test, p < 10⁻²⁵), and the sector effect "
  "disappears once CDN use is controlled for. The hybrid handshake grows the ServerHello from 122 to 1210 bytes, adds "
  "about 2.3 KB per handshake and splits the browser-like ClientHello (median 1534 bytes) into two TCP segments. "
  "A Monte Carlo simulation fed with the measured sizes shows that the extra segment increases mean handshake time "
  "by 1.5–7% at 1–10% segment loss.")
P("**Keywords:** post-quantum cryptography, TLS 1.3, ML-KEM, hybrid key exchange, network measurement, TCP "
  "segmentation, CDN")
sayfa_sonu()

# ---------------------------------------------------------------------------
# İÇİNDEKİLER (statik)
# ---------------------------------------------------------------------------
H1("İÇİNDEKİLER")
for satir in ["Özet / Abstract", "1. Giriş", "2. Problem Tanımı ve İhtiyaç Analizi",
              "3. Literatür Araştırması ve Mevcut Sistemlerin İncelenmesi",
              "4. Sistem Gereksinimleri ve Haberleşme Analizi", "5. Sistem Tasarımı ve Haberleşme Mimarisi",
              "6. Kullanılan Teknolojiler, Protokoller ve Geliştirme Yöntemi",
              "7. Uygulama ve Simülasyon Süreci", "8. Bulgular, Performans Testleri ve Değerlendirme",
              "9. Sınırlılıklar", "10. Sonuç ve Öneriler", "Yapay Zekâ Araçlarının Kullanımına İlişkin Beyan",
              "Kaynakça", "Ek A. Teknik Dosyalar ve Tekrarlanabilirlik"]:
    P(satir, WD_ALIGN_PARAGRAPH.LEFT, sonra=0)
P("")
H2("Kısaltmalar")
tablo("Raporda kullanılan kısaltmalar", [
    ["Kısaltma", "Açıklama"],
    ["CDN", "Content Delivery Network – İçerik dağıtım ağı"],
    ["CH / SH", "ClientHello / ServerHello (TLS el sıkışma mesajları)"],
    ["HRR", "HelloRetryRequest – sunucunun farklı anahtar grubu istemesi (+1 RTT)"],
    ["ML-KEM", "Module-Lattice-Based Key-Encapsulation Mechanism (NIST FIPS 203)"],
    ["MSS / MTU", "Maximum Segment Size (1460 B) / Maximum Transmission Unit (1500 B)"],
    ["PQ", "Post-quantum – kuantum sonrası"],
    ["RTO / RTT", "Retransmission Timeout / Round-Trip Time"],
    ["TSO", "TCP Segmentation Offload – segmentasyonun ağ kartında yapılması"],
], genislikler=[3, 12.5])
sayfa_sonu()

# ---------------------------------------------------------------------------
# 1. GİRİŞ
# ---------------------------------------------------------------------------
H1("1. GİRİŞ")
P("Günümüzde web trafiğinin büyük bölümü TCP üzerinde çalışan TLS (Transport Layer Security) protokolüyle "
  "korunmaktadır. TLS 1.3, istemci ile sunucu arasındaki oturum anahtarını X25519 veya P-256 gibi eliptik eğri "
  "tabanlı Diffie–Hellman yöntemleriyle tek gidiş-dönüş süresinde (1-RTT) oluşturur (Rescorla, 2018). Bu "
  "yöntemlerin güvenliği ayrık logaritma probleminin klasik bilgisayarlarla çözülememesine dayanır; ancak Shor "
  "algoritması yeterince büyük bir kuantum bilgisayarda bu problemi polinom zamanda çözebilmektedir (Shor, 1997; "
  "Bernstein ve Lange, 2017).")
P("Kuantum bilgisayarların henüz bu ölçekte olmaması riski ortadan kaldırmaz. \"Şimdi topla, sonra çöz\" "
  "(harvest now, decrypt later) senaryosunda bir saldırgan bugün kaydettiği şifreli trafiği gelecekte "
  "çözebilir. Mosca'nın (2018) ifade ettiği gibi, verinin gizli kalması gereken süre ile geçiş süresinin toplamı "
  "kuantum bilgisayarın ortaya çıkış süresini aşıyorsa risk bugünden başlamıştır. Bankacılık, sağlık ve kamu "
  "yazışmaları gibi uzun yıllar gizli kalması gereken veriler bu nedenle şimdiden tehdit altındadır.")
P("Bu tehdide karşı NIST, Ağustos 2024'te kafes (lattice) tabanlı ML-KEM anahtar kapsülleme mekanizmasını "
  "FIPS 203 olarak standartlaştırmıştır (National Institute of Standards and Technology [NIST], 2024). TLS 1.3 "
  "ekosistemi, klasik X25519 ile ML-KEM-768'i birlikte çalıştıran hibrit X25519MLKEM768 grubunda birleşmiştir "
  "(Kwiatkowski vd., 2026; Westerbaan ve Sardar, 2026). Chrome, Edge ve Firefox bu grubu varsayılan olarak "
  "teklif ettiğinden geçişin istemci tarafı büyük ölçüde tamamlanmıştır; belirleyici olan sunucuların bu grubu "
  "kabul edip etmediğidir.")
P("Veri iletişimi açısından bu geçiş yalnızca bir kriptografi değişikliği değildir. Hibrit anahtar payları el "
  "sıkışma mesajlarını yaklaşık 1,2 KB büyütür; bu da ilk mesajın tek bir TCP segmentine sığıp sığmamasını, "
  "kayıplı kanallarda yeniden iletim olasılığını ve ara cihazların davranışını etkiler. Dolayısıyla soru iki "
  "yönlüdür: (i) Türkiye'deki kritik sektör sunucuları bu geçişe ne kadar hazırdır, (ii) geçiş ağ katmanına ne "
  "maliyet getirmektedir?")
P("**Projenin amacı ve kapsamı.** Bu proje; dört kritik sektörden 130 web sitesinin TLS ve kuantum sonrası "
  "hazırlığını ölçen, açık ve tekrarlanabilir bir ölçüm sistemi tasarlamayı, hazırlığın belirleyicilerini "
  "istatistiksel olarak ortaya koymayı ve hibrit anahtar değişiminin bayt, segment ve gecikme düzeyindeki ağ "
  "maliyetini ölçüm, paket yakalama ve simülasyonla değerlendirmeyi amaçlamaktadır. Kapsam, sunucuların "
  "dışarıdan gözlemlenebilen TLS el sıkışma davranışıyla sınırlıdır; CDN ile kaynak sunucu arasındaki bağlantı "
  "ve sertifika imzalarının kuantum sonrası geçişi kapsam dışıdır.")
P("Projenin katkıları şunlardır:")
madde(["Türkiye'de dört kritik sektörden 130 web sitesinin TLS sürümü, kuantum sonrası anahtar değişimi desteği, "
       "seçilen anahtar grubu, HelloRetryRequest davranışı, sertifika türü ve HTTP/3 desteği iki tur hâlinde "
       "ölçülmüştür.",
       "Hazırlığın kurumun kendi çabasından çok CDN kullanımına bağlı olduğu gösterilmiş; CDN'e göre katmanlanmış "
       "analizle sektörler arası farkın büyük ölçüde altyapı farkından kaynaklandığı istatistiksel olarak "
       "ortaya konmuştur.",
       "Hibrit anahtar değişiminin mesaj boyutlarına ve TCP segmentasyonuna etkisi hem ölçüm verisiyle hem de "
       "Wireshark paket yakalamasıyla doğrulanmış; ek segmentin paket kaybı altındaki gecikme maliyeti analitik "
       "model ve Monte Carlo simülasyonuyla nicelleştirilmiştir.",
       "Ölçümü tekrarlanabilir kılan açık kaynaklı bir Python aracı ve Docker ortamı geliştirilmiştir."],
      numarali=True)

# ---------------------------------------------------------------------------
# 2. PROBLEM
# ---------------------------------------------------------------------------
H1("2. PROBLEM TANIMI VE İHTİYAÇ ANALİZİ")
H2("2.1. Problem Tanımı")
P("Projenin ele aldığı veri iletişimi problemi, **iletilen verinin uzun vadeli gizliliğinin** (haberleşme "
  "güvenliği) ve bu gizliliği sağlamak için yapılan protokol değişikliğinin **iletim verimliliğine etkisinin** "
  "birlikte değerlendirilmesidir. Bugün klasik anahtar değişimiyle kurulan her HTTPS oturumu, kaydedilmesi "
  "hâlinde gelecekte çözülebilir durumdadır. Hibrit anahtar değişimi bu riski giderir; ancak el sıkışmaya "
  "eklediği yaklaşık 2,3 KB'lık veri, tek pakette taşınan ilk mesajı iki pakete böler. Bu değişiklik:")
madde(["**bant genişliği** kullanımını (el sıkışma başına ek bayt),",
       "**gecikmeyi** (sunucu desteklemediğinde fazladan RTT, kayıp durumunda yeniden iletim),",
       "**paket kaybına duyarlılığı** (iletilmesi gereken segment sayısının artması) ve",
       "**bağlantı güvenilirliğini** (tek segmentlik ClientHello varsayan eski ara cihazlar)"])
P("doğrudan etkilemektedir. Türkiye özelinde ise hangi kurumların bu korumayı sağladığı, hangilerinin geride "
  "kaldığı ve bunun nedeni bilinmemektedir.")
H2("2.2. Mevcut Durumun Sınırlılıkları")
madde(["Küresel ölçümler (Dubey ve Varshney, 2026; F5 Labs, 2026) ülke ve sektör kırılımında Türkiye'ye ilişkin "
       "veri sunmamaktadır.",
       "Mevcut çalışmalar çoğunlukla desteğin var olup olmadığına odaklanmakta, geçişin ağ katmanına getirdiği "
       "maliyeti (bayt, segment, kayıp altında gecikme) aynı veri seti üzerinde incelememektedir.",
       "Kurumların kendi sunucularının kuantum sonrası durumunu kolayca ölçebileceği açık ve yerel bir araç "
       "bulunmamaktadır."])
H2("2.3. İhtiyaç Analizi ve Paydaşlar")
tablo("Paydaşlar ve projenin karşıladığı ihtiyaçlar", [
    ["Paydaş", "İhtiyaç", "Projenin karşılığı"],
    ["Kurum BT/ağ ekipleri", "Kendi sunucusunun PQ durumunu bilmek", "Açık ölçüm aracı (olcum.py, Docker)"],
    ["Düzenleyiciler (BDDK, BTK, USOM vb.)", "Sektörel risk tablosu", "Sektör bazında hazırlık oranları ve güven aralıkları"],
    ["Ağ yöneticileri", "Büyüyen el sıkışmanın ağ etkisini öngörmek", "Bayt/segment ölçümü, kayıp altında gecikme modeli"],
    ["Son kullanıcılar", "Verilerinin uzun vadeli gizliliği", "Hangi sektörlerde riskin sürdüğünün görünür kılınması"],
], genislikler=[4, 5.5, 6])

# ---------------------------------------------------------------------------
# 3. LİTERATÜR
# ---------------------------------------------------------------------------
H1("3. LİTERATÜR ARAŞTIRMASI VE MEVCUT SİSTEMLERİN İNCELENMESİ")
H2("3.1. TLS 1.3 El Sıkışması")
P("TCP/IP modelinde TLS, taşıma katmanı (TCP) ile uygulama katmanı (HTTP) arasında yer alır; HTTPS, TCP "
  "üzerinde TLS ve onun üzerinde HTTP'den oluşur. TLS 1.3 el sıkışmasında istemci, ilk mesaj olan ClientHello'da "
  "desteklediği anahtar değişimi gruplarını (supported_groups) ve bunların bir kısmı için hazır anahtar paylarını "
  "(key_share) gönderir. Sunucu ServerHello mesajında bu gruplardan birini seçer ve kendi payını ekler; böylece "
  "anahtar değişimi tek gidiş-dönüşte tamamlanır. Sunucu, istemcinin pay gönderdiği grupların hiçbirini "
  "desteklemiyorsa HelloRetryRequest (HRR) ile farklı bir grup ister; bu el sıkışmaya fazladan bir RTT ekler "
  "(Rescorla, 2018). Kuantum sonrası geçiş TLS 1.3'e özgüdür; TLS 1.2 kullanan bir sunucunun önce sürüm "
  "yükseltmesi gerekir.")
H2("3.2. ML-KEM ve Hibrit Anahtar Değişimi")
P("ML-KEM, modül kafes problemlerine dayanan ve bilinen kuantum algoritmalarına karşı dayanıklı kabul edilen bir "
  "anahtar kapsülleme mekanizmasıdır (NIST, 2024). Yeni algoritmalara henüz tam güvenilmediği geçiş döneminde "
  "klasik ve kuantum sonrası algoritmaların birlikte kullanıldığı hibrit yapılar tercih edilmektedir (Driscoll "
  "vd., 2025). X25519MLKEM768 grubunda istemci payı, 1184 baytlık ML-KEM-768 kapsülleme anahtarı ile 32 baytlık "
  "X25519 payının birleşimidir (1216 B); sunucu payı 1088 baytlık ML-KEM şifre metni ile 32 baytlık X25519 "
  "payından oluşur (1120 B). İki yöntemin ürettiği gizli değerler birleştirilerek anahtar türetimine verilir; biri "
  "kırılsa bile diğeri oturumu korumaya devam eder (Kwiatkowski vd., 2026). IETF'te bu grubun \"önerilen\" olarak "
  "işaretlenmesi de gündemdedir (Westerbaan ve Sardar, 2026).")
P("Kuantum sonrası algoritmaların TLS performansına etkisi deneysel olarak da incelenmiştir. Paquin vd. (2020), "
  "ağ emülasyonuyla farklı gecikme ve kayıp oranlarında kuantum sonrası TLS el sıkışmalarını karşılaştırmış ve "
  "mesaj boyutunun TCP'nin ilk tıkanıklık penceresini aşmasının belirgin gecikmeye yol açtığını göstermiştir. "
  "Sikeridis vd. (2020) ise kuantum sonrası imzaların sertifika zincirini büyüterek el sıkışma süresini "
  "artırdığını raporlamıştır. ML-KEM-768'in boyutu ilk pencere içinde kaldığından asıl etki ClientHello'nun "
  "tek segment sınırını aşmasıdır; parçalanmış ClientHello mesajını reddeden eski TLS denetim cihazları da "
  "bildirilmiştir (UnveilScan, 2026).")
H2("3.3. İlgili Ölçüm Çalışmaları")
P("Cloudflare verilerine göre 2025 sonunda ağına gelen insan kaynaklı TLS trafiğinin çoğunluğu hibrit anahtar "
  "değişimi kullanmaktadır (Cloudflare, 2025); bu oran istemci desteğinin ve CDN tarafındaki varsayılan "
  "etkinleştirmenin sonucudur. Kaynak (origin) sunucularda ise destek çok daha düşüktür; OpenSSL 3.5 gibi "
  "sunucu kütüphanelerinin varsayılan olarak hibrit grubu açmasıyla artmaya başlamıştır (Cloudflare, 2026; "
  "Jacar, 2026). F5 Labs'in (2026) en popüler bir milyon sitedeki ölçümü, sitelerin %54'ünün kuantum sonrası "
  "anahtar değişimini desteklediğini, ancak Cloudflare arkasındaki siteler çıkarıldığında oranın %22'ye "
  "düştüğünü ve sitelerin %10,5'inin TLS 1.3'ü bile desteklemediğini raporlamıştır. Dubey ve Varshney (2026), "
  "32 011 alan adında yaptıkları ölçümde alan adlarının yaklaşık yarısında hibrit destek bulmuş, kuantum sonrası "
  "imzalı sertifikaya rastlamamıştır. Sektör odaklı en yakın çalışma Birleşik Krallık'taki kuruluşları "
  "inceleyen ölçümdür (\"Measuring Post-Quantum TLS Deployment\", 2026); bu çalışma da dağıtımın az sayıda "
  "altyapı sağlayıcısında yoğunlaştığını bulmuştur.")
H2("3.4. Mevcut Çalışmaların Karşılaştırılması ve Projenin Farkı")
tablo("İlgili çalışmalar ile bu projenin karşılaştırılması", [
    ["Çalışma", "Kapsam", "Sektör kırılımı", "Ağ maliyeti (bayt/segment)", "Kayıp altında gecikme", "Türkiye"],
    ["Paquin vd. (2020)", "Laboratuvar", "–", "Var", "Var (emülasyon)", "–"],
    ["Dubey ve Varshney (2026)", "32 011 alan adı", "Var", "–", "–", "–"],
    ["F5 Labs (2026)", "İlk 1 milyon site", "Kısmi", "–", "–", "–"],
    ["UK sektör çalışması (2026)", "BK, 10 sektör", "Var", "–", "–", "–"],
    ["**Bu proje**", "130 site, 4 sektör", "**Var**", "**Var (ölçüm + pcap)**", "**Var (simülasyon)**", "**Var**"],
], genislikler=[3.6, 2.8, 2.0, 2.8, 2.6, 1.6], boyut=9)
P("Tablo 3'te görüldüğü gibi bu proje, Türkiye'nin kritik sektörlerine odaklanması ve hazırlık ölçümünü aynı "
  "veri seti üzerinde ağ maliyeti ve kayıp altında gecikme analiziyle birleştirmesiyle mevcut çalışmalardan "
  "ayrılmaktadır.")

# ---------------------------------------------------------------------------
# 4. GEREKSİNİMLER
# ---------------------------------------------------------------------------
H1("4. SİSTEM GEREKSİNİMLERİ VE HABERLEŞME ANALİZİ")
H2("4.1. İşlevsel Gereksinimler")
tablo("Ölçüm sisteminin işlevsel gereksinimleri", [
    ["Kod", "Gereksinim"],
    ["İG-1", "Bir alan adı listesini (sektör, alan adı) okuyup her siteyi sırayla ölçebilmeli."],
    ["İG-2", "Sunucunun TLS 1.3 / TLS 1.2 desteğini ve tarayıcı benzeri teklifte seçtiği grubu belirleyebilmeli."],
    ["İG-3", "Yalnız X25519MLKEM768 sunulduğunda bağlantı kurulup kurulmadığını (PQ desteği) belirleyebilmeli."],
    ["İG-4", "ClientHello/ServerHello boyutunu, okunan/yazılan toplam baytı ve segment sayısını kaydetmeli."],
    ["İG-5", "HelloRetryRequest durumunu ve sertifika anahtar türü/uzunluğunu tespit etmeli."],
    ["İG-6", "HTTP yanıt başlıklarından HTTP/3 ilanını ve CDN kullanımını belirlemeli."],
    ["İG-7", "Sonuçları makine tarafından okunabilir CSV biçiminde yazmalı ve yarıda kalan ölçüme devam edebilmeli."],
], genislikler=[1.6, 13.9])
H2("4.2. İşlevsel Olmayan Gereksinimler")
tablo("İşlevsel olmayan gereksinimler", [
    ["Kod", "Gereksinim", "Karşılama yöntemi"],
    ["İOG-1 Etik", "Sunuculara yük bindirmemeli, tarama/saldırı yapmamalı", "Normal ziyaretçi bağlantısı, siteler arası 1,5 s bekleme"],
    ["İOG-2 Tekrarlanabilirlik", "Başka araştırmacılar aynı ölçümü yapabilmeli", "Açık kod, Docker ortamı, sabit site listesi"],
    ["İOG-3 Tutarlılık", "Anlık değil kararlı yapılandırmayı yansıtmalı", "İki ölçüm turu, 5 tekrar ve medyan"],
    ["İOG-4 Taşınabilirlik", "Windows, Linux ve macOS'ta çalışmalı", "Yalnız standart Python kütüphanesi + OpenSSL"],
    ["İOG-5 Gizlilik", "Kurumları teşhir etmemeli", "Sonuçların sektör bazında raporlanması"],
], genislikler=[3.4, 6, 6.1], boyut=9.5)
H2("4.3. Haberleşme Parametrelerinin Analizi")
P("Yönergede önerilen parametrelerin bu projedeki karşılıkları Tablo 6'da verilmiştir. Bu projede iletişim "
  "kanalı TCP ile güvenilir hâle getirildiğinden, fiziksel katmandaki bit hataları (BER) uygulamaya "
  "segment kaybı ve yeniden iletim olarak yansır. Bu nedenle BER yerine **segment kayıp oranı** temel "
  "güvenilirlik parametresi olarak kullanılmıştır.")
tablo("Haberleşme parametreleri, ölçüm yöntemleri ve elde edilen değerler", [
    ["Parametre", "Bu projedeki karşılığı", "Yöntem", "Değer / aralık"],
    ["Veri miktarı (bayt)", "El sıkışmada gönderilen/alınan bayt", "s_client -msg, Wireshark", "+1184 / +1088 B (ölçüm)"],
    ["Bant genişliği kullanımı", "Ek bayt × el sıkışma sayısı", "Hesaplama", "1 milyon el sıkışma/gün ≈ 2,27 GB"],
    ["Segment sayısı", "ClientHello'nun MSS=1460 B'a bölünmesi", "⌈(boyut+9)/1460⌉, pcap", "Klasik 1, hibrit tarayıcı 2"],
    ["Gecikme (ms)", "TCP RTT, HRR ek RTT, el sıkışma süresi", "TCP connect ×5 medyanı", "Medyan RTT 19,2–20,0 ms"],
    ["Paket (segment) kaybı", "Kayıp altında el sıkışma süresi", "Analitik model + Monte Carlo", "p = %0–10 (simülasyon)"],
    ["Güvenilirlik", "Bağlantı başarısı, turlar arası tutarlılık", "İki tur karşılaştırması", "129/129 aynı sonuç"],
    ["Güvenlik", "PQ anahtar değişimi, TLS sürümü, sertifika", "Yalnız-PQ el sıkışma testi", "%24,8 PQ hazır"],
    ["Ölçeklenebilirlik", "Site sayısının artırılabilmesi", "CSV tabanlı liste, kaldığı yerden devam", "≈ 25–30 dk / 130 site"],
], genislikler=[3.2, 4.4, 3.8, 4.1], boyut=9)

# ---------------------------------------------------------------------------
# 5. MİMARİ
# ---------------------------------------------------------------------------
H1("5. SİSTEM TASARIMI VE HABERLEŞME MİMARİSİ")
H2("5.1. Gönderici–Kanal–Alıcı Mimarisi")
n_mim = sekil("diyagram_sistem_mimarisi.png", "Ölçüm sisteminin gönderici–kanal–alıcı blok diyagramı.")
P(f"Şekil {n_mim}'de sistemin genel mimarisi gösterilmektedir. **Gönderici (istemci)** tarafında Python ile "
  "yazılan ölçüm betiği, X25519MLKEM768 destekli OpenSSL 4.0.3 s_client bileşenini alt süreç olarak "
  "çalıştırmakta ve çıktısını ayrıştırmaktadır. **İletim kanalı**, Türkiye'deki bir ev internet bağlantısıdır "
  "(Wi-Fi → modem → ISS → İnternet); kanal IP/TCP ile modellenmiş, MSS değeri Ethernet MTU'sundan (1500 B) "
  "IP (20 B) ve TCP (20 B) başlıkları çıkarılarak 1460 B kabul edilmiştir. **Alıcı (sunucu)** tarafında iki "
  "farklı yapı bulunmaktadır: TLS bağlantısının bir CDN uç sunucusunda sonlandığı siteler (31) ve kurumun kendi "
  "web sunucusunun TLS'i sonlandırdığı siteler (98). CDN uç sunucusu ile kurumun kaynak sunucusu arasındaki "
  "bağlantı dışarıdan gözlemlenemediği için ölçüm kapsamı dışındadır. Wireshark, gönderici bilgisayardaki ağ "
  "arayüzünü dinleyerek paket düzeyinde doğrulama sağlamaktadır.")
H2("5.2. Protokol Katmanları")
n_kat = sekil("diyagram_katman_esleme.png", "OSI ve TCP/IP katmanlarının, ilgili protokol mekanizmalarının ve "
                                             "bu projede ölçülen değişkenlerin eşlenmesi.")
P(f"Şekil {n_kat}, ölçülen her değişkenin hangi protokol katmanına ait olduğunu göstermektedir. Kuantum sonrası "
  "geçiş, OSI'nin sunum/oturum katmanlarına karşılık gelen TLS'te gerçekleşmekte; ancak etkisi taşıma "
  "katmanında (segment sayısı, yeniden iletim) ve veri bağı katmanında (çerçeve boyutu) gözlenmektedir. Bu "
  "katmanlar arası etki, projenin veri iletişimi açısından odak noktasıdır.")
H2("5.3. Protokol Mesajlaşma ve Zamanlama")
n_sira = sekil("diyagram_tls13_sira.png", "TCP ve TLS 1.3 el sıkışmasının sıra diyagramı: (a) hibrit "
                                           "X25519MLKEM768 ile 1-RTT el sıkışma, (b) HelloRetryRequest durumu.",
               16)
P(f"Şekil {n_sira}a'da tarayıcı benzeri bir istemcinin hibrit el sıkışması gösterilmektedir. TCP üçlü el "
  "sıkışması 1 RTT sürer; ardından istemci, iki anahtar payı (X25519MLKEM768 için 1216 B ve yedek olarak "
  "X25519 için 32 B) içeren ve iki TCP segmentine bölünen ClientHello'yu gönderir. Sunucu, ML-KEM şifre metnini "
  "içeren 1210 baytlık ServerHello ile birlikte şifreli el sıkışma mesajlarını tek uçuşta (flight) gönderir. "
  "İstemci Finished mesajıyla birlikte uygulama verisini (HTTP GET) gönderebilir; yani TLS 1.3 el sıkışması "
  f"hibrit grupla da 1-RTT'de tamamlanır. Şekil {n_sira}b'de ise sunucunun yalnızca P-256'yı desteklediği ve "
  "HelloRetryRequest gönderdiği durum görülmektedir; bu durumda el sıkışmaya fazladan bir RTT eklenir.")
H2("5.4. Paket ve Çerçeve Yapısı")
n_ch = sekil("diyagram_clienthello_segment.png", "ClientHello mesajının yapısı ve TCP segmentlerine bölünmesi: "
                                                 "(a) klasik, (b) tarayıcı benzeri hibrit.", 16)
P(f"Şekil {n_ch}, ClientHello mesajının bayt düzeyindeki bileşimini göstermektedir. Her TLS el sıkışma mesajı "
  "5 baytlık TLS kayıt başlığı ve 4 baytlık el sıkışma başlığıyla taşınır. Klasik ClientHello 232 B olup tek "
  "segmente rahatlıkla sığarken, tarayıcı benzeri hibrit ClientHello'nun neredeyse %80'ini oluşturan key_share "
  "uzantısı mesajı 1543 bayta (başlıklarla) çıkarır. Bu değer 1460 baytlık MSS'i 83 bayt aştığından mesaj iki "
  "TCP segmentiyle iletilmek zorundadır. Bir Ethernet çerçevesi bu durumda 14 B Ethernet + 20 B IP + 20 B TCP "
  "başlığı ile en fazla 1514 B olur.")
H2("5.5. Veri Akışı ve Ölçüm Algoritması")
n_akis = sekil("diyagram_olcum_akis.png", "Ölçüm aracının site başına veri akışı ve karar yapısı.", 15)
P(f"Şekil {n_akis}'te her site için uygulanan ölçüm algoritması verilmiştir. Alan adı bir kez çözülür ve tüm "
  "testlerde aynı IP adresi kullanılır; böylece CDN'lerin farklı uç sunuculara yönlendirmesi tek bir ölçüm içinde "
  "sonucu etkilemez. TCP bağlantı kurma süresi beş kez ölçülerek medyan RTT hesaplanır. Ardından beş bağlantı "
  "senaryosu sırayla uygulanır: (1) tarayıcı benzeri teklif, (2) TLS 1.2 kabul testi, (3) yalnız hibrit grup, "
  "(4) yalnız klasik grup ve (5) HTTP başlık sorgusu. Üçüncü ve dördüncü senaryolar yalnızca TLS 1.3 "
  "destekleyen sunucularda ve beşer kez tekrarlanır. Sözde kod aşağıda verilmiştir:")
kod = ("for (sektör, alan_adı) in siteler:\n"
       "    ip  ← DNS(alan_adı)                          # bir kez\n"
       "    rtt ← medyan(TCP_connect(ip) × 5)\n"
       "    v   ← s_client(ip, groups=\"*X25519MLKEM768:*X25519:P-256\")\n"
       "    kaydet(v.sürüm, v.grup, v.hrr, v.sertifika, |v.ClientHello|)\n"
       "    tls12 ← s_client(ip, -tls1_2).başarılı\n"
       "    if v.sürüm = TLS1.3:\n"
       "        pq ← s_client(ip, -tls1_3, groups=X25519MLKEM768) × 5\n"
       "        kl ← s_client(ip, -tls1_3, groups=X25519) × 5\n"
       "        pq_destek ← pq.başarılı ∧ pq.grup = X25519MLKEM768\n"
       "    http ← HTTPS_GET(\"/\") → Alt-Svc, CDN başlıkları\n"
       "    CSV'ye_yaz(satır); bekle(1,5 s)")
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
p.paragraph_format.line_spacing = 1.0
p.paragraph_format.left_indent = Cm(0.8)
r = p.add_run(kod); r.font.name = "Consolas"; r.font.size = Pt(9.5)
H2("5.6. Hata Kontrol Mekanizmaları")
P("Ölçüm sisteminde hata kontrolü üç düzeyde sağlanmaktadır. Taşıma düzeyinde TCP'nin sağlama toplamı ve "
  "yeniden iletim mekanizması veri bütünlüğünü korur; TLS düzeyinde her kayıt AEAD şifrelemesiyle (ör. "
  "AES-GCM) bütünlük doğrulamasına tabidir ve el sıkışma Finished mesajlarındaki HMAC ile doğrulanır. Uygulama "
  "düzeyinde ise ölçüm aracı her siteyi dns_hatasi, ulasilamadi, tls_hatasi ve zaman_asimi (10 s) durumlarıyla "
  "sınıflandırır; bir sitedeki beklenmeyen hata tüm ölçümü durdurmaz ve araç kesintiden sonra kaldığı yerden "
  "devam eder.")

# ---------------------------------------------------------------------------
# 6. TEKNOLOJİLER
# ---------------------------------------------------------------------------
H1("6. KULLANILAN TEKNOLOJİLER, PROTOKOLLER VE GELİŞTİRME YÖNTEMİ")
P("Kullanılan teknolojiler, seçim gerekçeleri ve değerlendirilen alternatifler Tablo 7'de özetlenmiştir.")
tablo("Teknoloji seçimleri, gerekçeleri ve alternatifler", [
    ["Bileşen", "Seçim", "Gerekçe", "Alternatif ve neden seçilmedi"],
    ["TLS istemcisi", "OpenSSL 4.0.3 s_client",
     "X25519MLKEM768 desteği; -groups ile pay kontrolü; -msg ile mesaj boyutları",
     "Python ssl: grup seçimi ve mesaj boyutu vermiyor; curl: el sıkışma ayrıntısı sınırlı"],
    ["Programlama dili", "Python 3 (yalnız standart kütüphane)",
     "Taşınabilirlik, kolay ayrıştırma, ek paket gerektirmemesi", "Go crypto/tls: daha hızlı ama ham mesaj boyutlarına erişim zor"],
    ["Anahtar grubu", "X25519MLKEM768", "Tarayıcıların varsayılanı, IETF'te önerilen grup",
     "SecP256r1MLKEM768: tarayıcılar varsayılan olarak teklif etmiyor"],
    ["Taşıma", "TCP (TLS 1.3)", "HTTPS trafiğinin büyük çoğunluğu", "QUIC/HTTP3: yalnızca ilan (Alt-Svc) olarak kaydedildi"],
    ["Paket analizi", "Wireshark 4.6.8", "Çerçeve ve uzantı düzeyinde doğrulama", "tcpdump: görsel analiz için daha zahmetli"],
    ["İstatistik", "Fisher kesin testi, Wilson aralığı, permütasyon testi",
     "Küçük örneklem ve sıfır hücreli tablolar için doğru sonuç", "Ki-kare: beklenen frekans < 5 olduğunda güvenilmez"],
    ["Gecikme analizi", "Analitik model + Monte Carlo", "Kayıp oranını kontrollü değiştirme imkânı",
     "Gerçek ağda kayıp kontrol edilemez; netem deneyi Bölüm 10'da planlandı"],
    ["Ortam", "Docker (Alpine 3.22, OpenSSL 3.5)", "Her işletim sisteminde aynı ortam", "Yerel kurulum: Ubuntu 24.04'te OpenSSL 3.0 (PQ yok)"],
], genislikler=[2.6, 3.4, 4.8, 4.7], boyut=9)
P("Ölçüm aracı yalnızca Python'un standart kütüphanesini kullandığından ek paket gerektirmez. Analiz betikleri "
  "(analiz.py ve analiz_ek.py) matplotlib ve SciPy kullanır. Tüm kodlar Ek A'da listelenen ZIP dosyasında "
  "teslim edilmiştir.")

# ---------------------------------------------------------------------------
# 7. UYGULAMA
# ---------------------------------------------------------------------------
H1("7. UYGULAMA VE SİMÜLASYON SÜRECİ")
H2("7.1. Veri Seti")
P("Ölçüm, Türkiye'de yüksek değerli kişisel ve kurumsal veri işleyen dört sektörden seçilen 130 web sitesini "
  "kapsamaktadır (Tablo 8). Her site için kurumun ana sayfasının alan adı (www önekli) kullanılmıştır.")
tablo("Veri setinin sektörel dağılımı", [
    ["Sektör", "Kapsam", "Site"],
    ["Banka", "Kamu, özel ve katılım bankaları, merkez bankası", "27"],
    ["Kamu", "Cumhurbaşkanlığı, TBMM, bakanlıklar, kamu kurumları, büyükşehir belediyeleri", "33"],
    ["Üniversite", "Devlet ve vakıf üniversiteleri", "40"],
    ["E-ticaret", "Pazar yerleri, perakende ve elektronik zincirleri", "30"],
    ["Toplam", "", "130"],
], genislikler=[3, 10.5, 2])
H2("7.2. Kurulum ve Test Ortamı")
madde(["**Donanım/işletim sistemi:** Windows işletim sistemli dizüstü bilgisayar, Türkiye'de ev internet "
       "bağlantısı (Wi-Fi).",
       "**Yazılım:** Python 3, OpenSSL 4.0.3 (X25519MLKEM768 destekli), Wireshark 4.6.8. Alternatif olarak "
       "Dockerfile ile Alpine 3.22 + OpenSSL 3.5 ortamı.",
       "**Doğrulama:** Araç başlangıçta openssl list -tls-groups çıktısında X25519MLKEM768 bulunduğunu kontrol "
       "eder; bulunmazsa ölçümü başlatmaz.",
       "**Pilot ölçüm:** Tam ölçümden önce 5 sitelik pilot (pilot.csv) ile ayrıştırma doğrulanmıştır.",
       "**Ölçüm turları:** 1. tur 7 Ekim 2026 22.40–23.07, 2. tur 8 Ekim 2026 00.26–00.52 (aynı ağ, aynı araç)."])
H2("7.3. Ölçüm Etiği")
P("Her siteye normal bir ziyaretçinin kuracağı türden bağlantılar kurulmuş; port taraması veya güvenlik açığı "
  "testi yapılmamıştır. Siteler arasında 1,5 saniye beklenerek sunuculara yük bindirilmesi önlenmiş, yalnızca "
  "herkese açık el sıkışma bilgisi kaydedilmiş ve sonuçlar sektör bazında raporlanmıştır. HTTP isteğinde "
  "kullanıcı aracısı başlığı ölçümün akademik amaçlı olduğunu belirtmektedir.")
H2("7.4. Paket Yakalama Senaryosu")
P("Ölçüm verisini bağımsız bir yöntemle doğrulamak için Wireshark ile, hibrit anahtar değişimini destekleyen "
  "bir e-ticaret sitesine (CDN arkasında) art arda kurulan klasik ve hibrit bağlantılar yakalanmıştır "
  "(trendyol_klasik_hibrit.pcapng, 1185 paket). Yakalama dosyası ayrıca bu raporun hazırlanması sırasında "
  "Python/Scapy ile yeniden ayrıştırılarak ClientHello ve ServerHello kayıt uzunlukları çıkarılmıştır.")
H2("7.5. Simülasyon Modeli: Paket Kaybı Altında El Sıkışma Süresi")
P("Gerçek İnternet üzerinde kayıp oranı kontrol edilemediğinden, ClientHello'nun ikinci segmentinin kayıplı "
  "kanallardaki etkisi ölçülen değerlerle beslenen bir model üzerinden incelenmiştir. **Bu bölümdeki sonuçlar "
  "ölçüm değil simülasyondur.** Model varsayımları şunlardır:")
madde(["Her segment, yönünden bağımsız olarak p olasılığıyla kaybolur (Bernoulli kayıp modeli).",
       "Kayıpsız el sıkışma süresi 2 RTT'dir (TCP 1 RTT + TLS 1.3 1 RTT). RTT = 20 ms (ölçülen medyan) ve "
       "65 ms (yurt dışı uç sunucular) için çalıştırılmıştır.",
       "SYN veya SYN/ACK kaybında ilk RTO 1 s'dir ve her denemede iki katına çıkar (Paxson vd., 2011).",
       "Veri segmentlerinde RTO = SRTT + max(4·RTTVAR, 200 ms) alınmıştır (Linux'taki 200 ms alt sınırı); "
       "kaybolan segmentler bir RTO sonra yeniden gönderilir ve tekrar kayıpta RTO iki katına çıkar.",
       "Segment sayıları ölçümden alınmıştır: klasik ClientHello 1, tarayıcı benzeri hibrit ClientHello 2 segment; "
       f"sunucu uçuşu (ServerHello + sertifika vb.) klasikte {tr(ag['okunan_klasik'], 0)} B, hibritte "
       f"{tr(ag['okunan_hibrit'], 0)} B olup her ikisi de 4 segmenttir.",
       "ACK kayıpları, hızlı yeniden iletim ve kuyruk kaybı yoklaması (TLP) modellenmemiştir; bu nedenle model "
       "kuyruk gecikmesini bir miktar abartabilir ancak senaryolar arası karşılaştırma için tutarlıdır."])
P("Bu varsayımlar altında el sıkışmanın en az bir yeniden iletim içerme olasılığı analitik olarak "
  "**P = 1 − (1 − p)^n** şeklinde yazılabilir; burada n, kritik yoldaki toplam segment sayısıdır (klasikte "
  "2 + 1 + 4 = 7, hibritte 2 + 2 + 4 = 8). Üç senaryo karşılaştırılmıştır: (i) klasik istemci → klasik sunucu, "
  "(ii) tarayıcı → hibrit destekli sunucu ve (iii) tarayıcı → hibrit desteklemeyen sunucu. Üçüncü senaryo, "
  "tarayıcının iki anahtar payını sunucu desteklemese de gönderdiği durumu temsil eder. Her kayıp oranı için "
  "40 000 tekrar yapılmıştır.")

# ---------------------------------------------------------------------------
# 8. BULGULAR
# ---------------------------------------------------------------------------
H1("8. BULGULAR, PERFORMANS TESTLERİ VE DEĞERLENDİRME")
P("130 sitenin 129'u başarıyla ölçülmüştür; bir üniversite sitesiyle TLS bağlantısı kurulamamış ve analiz dışında "
  "bırakılmıştır. Aksi belirtilmedikçe değerler ölçülmüş değerlerdir; Bölüm 8.5 simülasyon sonuçlarını içerir.")
H2("8.1. Sektörel Hazırlık (Ölçüm)")
tsek = tablo("Sektöre göre TLS ve kuantum sonrası hazırlık (%, n = 129)",
             [["Sektör", "n", "TLS 1.3", "Yalnız TLS 1.2", "PQ hazır", "PQ %95 GA", "CDN arkasında", "HTTP/3"]] +
             [[o["sektor"], o["n"], tr(o["tls13"]), tr(o["tls12"]), tr(o["pq"]),
               f"{tr(o['pq_ci'][0])}–{tr(o['pq_ci'][1])}", tr(o["cdn"]), tr(o["http3"])] for o in R["sektor"]],
             genislikler=[2.6, 1, 1.7, 2.2, 1.7, 2.4, 2.2, 1.7], boyut=9.5,
             not_="GA: Wilson yöntemiyle hesaplanan %95 güven aralığı (Wilson, 1927).")
n_s1 = sekil("sekil_sektor_hazirlik.png", "Sektöre göre sitelerin hazırlık durumu ve kuantum sonrası destek "
                                          "oranının %95 güven aralığı.", 14.5)
P(f"Ölçülen sitelerin %{tr(T['pq'])}'i (32/129; %95 GA: %{tr(T['pq_ci'][0])}–%{tr(T['pq_ci'][1])}) kuantum "
  f"sonrası anahtar değişimini desteklemektedir. Yalnızca TLS 1.3 destekleyen siteler dikkate alındığında bu "
  f"oran %33,7'dir (32/95). Sitelerin %{tr(T['tls12'])}'i ise hâlâ yalnızca TLS 1.2 kullanmaktadır ve kuantum "
  f"sonrası geçiş için önce sürüm yükseltmesine ihtiyaç duymaktadır (Tablo {tsek}, Şekil {n_s1}). Sektörler arası "
  "fark belirgindir: bankaların hiçbiri kuantum sonrası anahtar değişimini desteklemezken e-ticaret sitelerinin "
  f"%80'i desteklemektedir (Fisher kesin testi, p = {R['banka_eticaret_fisher']['p']:.1e}). Bankaların yarısından "
  "fazlası (%51,9) TLS 1.3'e bile geçmemiştir. Kamu sitelerinde destek tek bir siteyle sınırlıdır ve bu site bir "
  "CDN arkasındadır.")
P("Tarayıcı benzeri teklifte kuantum sonrası grubu seçmeyen 63 TLS 1.3 sunucusunun 62'si X25519'u seçmiştir. "
  "Bir banka sitesi ise X25519'u desteklemediği için P-256 istemiş ve HelloRetryRequest göndermiştir; bu site "
  "güncel tarayıcılarla her bağlantıda fazladan bir RTT (ölçüm ortamında ≈ 20 ms) harcamaktadır. Sertifika "
  "tarafında sitelerin %91,5'i RSA (107'si 2048, 9'u 4096, 2'si 3072 bit), %8,5'i 256 bitlik ECDSA anahtarı "
  "kullanmaktadır; kuantum sonrası imzalı sertifikaya rastlanmamıştır. Bu bulgu küresel ölçümlerle uyumludur "
  "(Dubey ve Varshney, 2026).")
H2("8.2. CDN Etkisi ve Katmanlı Analiz (Ölçüm)")
n_cdn = sekil("sekil_cdn_etkisi.png", "CDN arkasındaki ve kendi sunucusunu işleten sitelerde kuantum sonrası "
                                      "destek oranı (%95 Wilson güven aralığıyla).", 11)
P(f"Hazırlığın en güçlü belirleyicisi CDN kullanımıdır (Şekil {n_cdn}). CDN arkasındaki 31 sitenin 30'u (%96,8; "
  "%95 GA: %83,8–%99,4) kuantum sonrası anahtar değişimini desteklerken kendi sunucusunu işleten 98 sitenin "
  f"yalnızca 2'si (%2,0; %95 GA: %0,6–%7,1) desteklemektedir (Fisher kesin testi, p = "
  f"{R['cdn_fisher']['p']:.1e}). CDN arkasındaki sitelerin 21'i Cloudflare, 5'i Amazon CloudFront, 4'ü Akamai "
  "ve 1'i Imperva kullanmaktadır. Bu sınıflandırmada 29 site HTTP yanıt başlıklarıyla, 2 site ise IP adresinin "
  "bilinen CDN adres bloklarına ait olmasıyla belirlenmiştir.")
P("Sektör farkının CDN kullanımından mı yoksa sektörün kendisinden mi kaynaklandığını sınamak için analiz CDN "
  "kullanımına göre katmanlandırılmıştır (Tablo 10). Katmansız analizde sektör ile kuantum sonrası destek "
  f"arasında güçlü bir ilişki vardır (χ² = {tr(R['sektor_kikare_katmansiz']['chi2'], 2)}, p < 10⁻¹³). Ancak CDN "
  "katmanları içinde sektör etiketleri 20 000 kez rastgele karıştırılarak yapılan permütasyon testinde bu ilişki "
  f"kaybolmaktadır (p = {tr(R['sektor_permutasyon_cdn_katmanli']['p'], 2)}). Başka bir deyişle, aynı altyapıyı "
  "kullanan bir banka ile bir e-ticaret sitesi arasında anlamlı bir fark yoktur; sektörel farkı altyapı tercihi "
  "açıklamaktadır.")
ks, kc = R["katman_kendi_sunucu"], R["katman_cdn"]
tablo("CDN kullanımına göre katmanlanmış kuantum sonrası destek (destekleyen / toplam)", [
    ["Sektör", "Kendi sunucusu", "CDN arkasında"],
    *[[k, ks[k], kc[k] if kc[k] != "0/0" else "–"] for k in ("Banka", "Kamu", "Üniversite", "E-ticaret")],
    ["Toplam", "2/98", "30/31"]], genislikler=[4, 4, 4])
P("CDN arkasında olup destek vermeyen tek site, CDN'nin TLS 1.3'ü desteklediği bilinmesine rağmen yalnızca "
  "TLS 1.2 sunmaktadır; bu durum kurum tarafındaki bir yapılandırma tercihinin CDN'nin sağladığı korumayı devre "
  "dışı bırakabildiğini göstermektedir. CDN kullanmadan destek veren iki site ise iki üniversiteye aittir ve kendi "
  "sunucularında güncel bir TLS kütüphanesi kullanmaktadır; bu örnekler geçişin kendi sunucusunu işleten "
  "kurumlar için de teknik olarak mümkün olduğunu göstermektedir.")
H2("8.3. Ağ Maliyeti: Bayt ve Segment Analizi (Ölçüm)")
tablo("Klasik ve hibrit el sıkışmanın mesaj boyutları (medyan, n = 32)", [
    ["Metrik", "Klasik (X25519)", "Hibrit (X25519MLKEM768)", "Artış"],
    ["ClientHello (bayt)", "232", "1416", "6,1 kat (+1184)"],
    ["ServerHello (bayt)", "122", "1210", "9,9 kat (+1088)"],
    ["İstemcinin gönderdiği toplam", "—", "—", "+1184 B"],
    ["İstemcinin aldığı toplam", f"{tr(ag['okunan_klasik'], 0)}", f"{tr(ag['okunan_hibrit'], 0)}", "+1088 B"],
    ["Tarayıcı benzeri ClientHello (n = 129)", "—", "1529–1543 (medyan 1534)", "2 TCP segmenti"],
], genislikler=[5.5, 3, 4, 3])
n_boy = sekil("sekil_mesaj_boyutlari.png", "Klasik ve hibrit el sıkışmada mesaj boyutları. Kesikli çizgi, "
                                           "TLS başlıklarıyla birlikte tek bir TCP segmentine sığabilecek azami "
                                           "mesaj boyutunu (1451 B) göstermektedir.", 14)
P(f"Hibrit anahtar değişimi her el sıkışmada 1184 + 1088 = 2272 bayt (≈ 2,3 KB) ek veri aktarımına yol "
  f"açmaktadır (Şekil {n_boy}). Bu artış ML-KEM-768'in sabit boyutlu kapsülleme anahtarından (1184 B) ve şifre "
  "metninden (1088 B) kaynaklandığından ServerHello boyutu destek veren 32 sitenin tamamında 1210 bayt olarak sabit "
  "çıkmıştır. Güncel tarayıcılar sunucunun hangi grubu desteklediğini bilmediğinden hem hibrit hem klasik anahtar "
  "payını birlikte gönderir; tarayıcı benzeri ClientHello 129 sitenin tamamında MSS'i aşarak iki TCP "
  "segmentine bölünmüştür.")
P("**Bant genişliği değerlendirmesi.** 2272 baytlık ek, ortalama 2 MB'lık bir web sayfasının yaklaşık %0,11'i "
  "kadardır ve TCP'nin ilk tıkanıklık penceresi olan 10 segmentin (Chu vd., 2013) içinde kaldığından normal "
  "koşullarda ek bir RTT gerektirmez. Ölçek açısından ise günde bir milyon yeni el sıkışma yapan bir sunucu için "
  "yaklaşık 2,27 GB/gün ek trafik anlamına gelir. Asıl nitel değişiklik, ilk mesajın artık tek pakette "
  "taşınamamasıdır.")
H2("8.4. Paket Düzeyinde Doğrulama (Wireshark)")
tablo("Paket yakalamadan elde edilen ClientHello/ServerHello değerleri (aynı e-ticaret sitesi)", [
    ["Mesaj", "Çerçeve boyutu (B)", "TLS kayıt uzunluğu (B)", "El sıkışma uzunluğu (B)"],
    ["Klasik ClientHello", "369", "310", "306"],
    ["Hibrit ClientHello", "1591", "1532", "1528"],
    ["Klasik ServerHello kaydı", "—", "122", "118"],
    ["Hibrit ServerHello kaydı", "—", "1210", "1206"],
], genislikler=[4.5, 3.5, 3.8, 3.7])
P("Klasik ClientHello 369 baytlık tek bir çerçevede taşınırken hibrit ClientHello 1591 baytlık bir çerçeve olarak "
  "görünmektedir. Bu değer Ethernet'in 1514 baytlık azami çerçeve boyutunu aşmaktadır; bunun nedeni paketin "
  "gönderen bilgisayar üzerinde, ağ kartının TCP Segmentation Offload (TSO) ile bölmesinden önce yakalanmasıdır. "
  "Ağ üzerinde bu veri iki segment olarak iletilmektedir. Bu yakalamada istemci TLS 1.2 şifre takımlarını da "
  "teklif ettiğinden klasik ClientHello, Tablo 11'deki yalnız TLS 1.3 değerinden biraz büyüktür. Hibrit "
  "ClientHello'nun key_share uzantısında 1216 baytlık X25519MLKEM768 payı ve 32 baytlık yedek X25519 payı "
  "görülmektedir; toplam 1258 baytlık bu uzantı iki mesaj arasındaki boyut farkının neredeyse tamamını "
  "açıklamaktadır. Ölçüm aracının raporladığı 1210 baytlık ServerHello değeri de pakette birebir doğrulanmıştır. "
  "Aynı yakalama dosyasında bilgisayardaki başka bir istemci uygulamasına ait 2120–2122 baytlık ClientHello "
  "mesajları da görülmüştür; gerçek tarayıcı mesajlarının ek uzantılar nedeniyle ölçüm aracınınkinden de büyük "
  "olabildiği, dolayısıyla iki segment bulgusunun alt sınır niteliğinde olduğu anlaşılmaktadır.")
H2("8.5. Gecikme ve Paket Kaybı Analizi (Ölçüm + Simülasyon)")
P("**Ölçülen el sıkışma süresi.** Hibrit ile klasik el sıkışma arasındaki medyan süre farkı birinci turda "
  f"+{tr(ag['sure_farki_medyan_tur1'], 2)} ms, ikinci turda {tr(ag['sure_farki_medyan_tur2'], 1)} ms "
  f"bulunmuştur (n = 32). Farkın işaret değiştirmesi ve Wilcoxon işaretli sıra testinin anlamsız çıkması "
  f"(p = {tr(ag['sure_wilcoxon_p'], 2)}), düşük kayıplı bir ev bağlantısında hibrit el sıkışmanın ölçülebilir bir "
  "süre maliyeti olmadığını göstermektedir. ML-KEM işlemlerinin hesaplama süresi mikrosaniyeler düzeyinde "
  "olduğundan bu sonuç beklenen bir sonuçtur. Süre ölçümü ayrıca s_client sürecinin başlatma yükünü (≈ 1 s) "
  "içerdiğinden mutlak değerler yerine farklar yorumlanmıştır.")
P("**Kayıplı kanal simülasyonu.** Sürenin kayıpsız ortamda değişmemesi, ek segmentin kayıplı kanallarda maliyetsiz "
  "olduğu anlamına gelmez. Simülasyon sonuçları Tablo 13 ve Şekil 9'da verilmiştir.")
satirlar = [["Kayıp p", "Ort. süre klasik (ms)", "Ort. süre hibrit (ms)", "Ek süre", "Yeniden iletim olas. klasik",
             "Yeniden iletim olas. hibrit"]]
for pk in (0.005, 0.01, 0.02, 0.05, 0.10):
    a_, b_ = sim[("Klasik", pk)], sim[("Hibrit (tarayıcı)", pk)]
    satirlar.append([f"%{tr(100 * pk)}", tr(a_["ortalama_ms"]), tr(b_["ortalama_ms"]),
                     f"+{tr(b_['ortalama_ms'] - a_['ortalama_ms'])} ms (%{tr(100 * (b_['ortalama_ms'] / a_['ortalama_ms'] - 1))})",
                     f"%{tr(100 * a_['gecikme_olasiligi'])}", f"%{tr(100 * b_['gecikme_olasiligi'])}"])
tsim = tablo("Paket kaybı altında el sıkışma süresi – SİMÜLASYON (RTT = 20 ms, 40 000 tekrar)", satirlar,
             genislikler=[1.7, 2.6, 2.6, 3.2, 2.7, 2.7], boyut=9,
             not_="Değerler simülasyon sonucudur, ölçüm değildir. Model varsayımları Bölüm 7.5'tedir.")
n_sim = sekil("sekil_simulasyon_kayip.png", "Simülasyon: segment kayıp oranına göre ortalama el sıkışma süresi ve "
                                            "en az bir yeniden iletim olasılığı (noktalar: Monte Carlo, çizgiler: "
                                            "analitik model).", 16)
k10 = (sim[("Klasik", 0.10)], sim[("Hibrit (tarayıcı)", 0.10)])
k01 = (sim[("Klasik", 0.01)], sim[("Hibrit (tarayıcı)", 0.01)])
P(f"Simülasyonda yeniden iletim olasılığı analitik modelle neredeyse birebir örtüşmektedir (Şekil {n_sim}). "
  f"ClientHello'nun ikinci segmenti, %1 kayıpta yeniden iletim olasılığını %{tr(100 * k01[0]['gecikme_olasiligi'])}'den "
  f"%{tr(100 * k01[1]['gecikme_olasiligi'])}'e, %10 kayıpta %{tr(100 * k10[0]['gecikme_olasiligi'])}'den "
  f"%{tr(100 * k10[1]['gecikme_olasiligi'])}'e çıkarmaktadır. Bir yeniden iletim en az RTO (≈ 220 ms) kadar "
  f"bekleme getirdiğinden ortalama süre %10 kayıpta {tr(k10[0]['ortalama_ms'])} ms'den "
  f"{tr(k10[1]['ortalama_ms'])} ms'ye (+%{tr(100 * (k10[1]['ortalama_ms'] / k10[0]['ortalama_ms'] - 1))}) "
  f"yükselmektedir. RTT = 65 ms'de (yurt dışındaki uç sunucular) aynı karşılaştırma "
  f"{tr(sim65[('Klasik', 0.10)]['ortalama_ms'])} ms'ye karşı {tr(sim65[('Hibrit (tarayıcı)', 0.10)]['ortalama_ms'])} "
  "ms vermektedir. Etki, kayıpsız kablolu ağlarda ihmal edilebilir; ancak kayıplı mobil, kırsal veya uydu "
  "bağlantılarında ve kuyruk gecikmesine duyarlı uygulamalarda dikkate alınmalıdır.")
P("Önemli bir sonuç da üçüncü senaryodan çıkmaktadır: tarayıcı, sunucunun hibrit grubu desteklemediğini "
  "bilmediğinden iki anahtar payını yine gönderir. Bu nedenle **hibrit desteklemeyen sunuculara bağlanan "
  "kullanıcılar ek segmentin gecikme maliyetini koruma elde etmeden ödemektedir** (Tablo 13'teki hibrit sütunu "
  "ile neredeyse aynı değerler). Sunucuların geçişi geciktirmesi bu maliyeti karşılıksız bırakmaktadır.")
H2("8.6. Ölçümlerin Tutarlılığı")
tablo("İki ölçüm turunun karşılaştırılması (n = 129)", [
    ["Metrik", "1. tur", "2. tur"],
    ["Kuantum sonrası destek", "32 (%24,8)", "32 (%24,8)"],
    ["TLS 1.3 desteği", "95 (%73,6)", "95 (%73,6)"],
    ["CDN arkasında / destekli", "31 / 30", "31 / 30"],
    ["HTTP/3 ilanı", "15", "15"],
    ["Hibrit ServerHello (bayt)", "1210", "1210"],
    ["Medyan TCP RTT (ms)", tr(ag["rtt_medyan_tur1"]), tr(ag["rtt_medyan_tur2"])],
    ["Medyan süre farkı hibrit − klasik (ms)", f"+{tr(ag['sure_farki_medyan_tur1'], 2)}",
     tr(ag["sure_farki_medyan_tur2"])],
], genislikler=[7, 4, 4])
n_rtt = sekil("sekil_rtt_turlar.png", "İki ölçüm turunda site bazında TCP RTT değerleri.", 9.5)
P("129 sitenin tamamında TLS sürümü, kuantum sonrası destek, seçilen anahtar değişim grubu, HelloRetryRequest "
  "davranışı, TLS 1.2 kabulü ve sertifika anahtar türü ile uzunluğu iki turda birebir aynı çıkmıştır. 16 sitenin "
  "IP adresi turlar arasında değişmiştir; bunların 13'ü CDN arkasındadır ve değişim CDN'nin kullanıcıyı farklı uç "
  "sunuculara yönlendirmesinden kaynaklanmaktadır. Bu sitelerin hiçbirinde sonuç değişmemiştir. Ağ gecikmesi "
  f"turlar arasında doğal olarak dalgalanmış, site bazındaki RTT değerleri arasındaki korelasyon "
  f"{tr(R['tutarlilik']['rtt_pearson'], 2)}, ortalama mutlak fark {tr(R['tutarlilik']['rtt_ort_mutlak_fark'])} ms "
  f"olmuştur (Şekil {n_rtt}).")
H2("8.7. Tartışma ve Küresel Karşılaştırma")
P("**Hazırlık kurumsal bir karardan çok altyapı tercihinin sonucudur.** Katmanlı analiz, Türkiye'deki kuantum "
  "sonrası geçişin kurumların bilinçli kararından çok CDN sağlayıcılarının özelliği varsayılan olarak "
  "etkinleştirmesiyle ilerlediğini göstermektedir. Bu bulgu, Cloudflare dışındaki sitelerde hazırlığın %54'ten "
  "%22'ye düştüğünü raporlayan F5 Labs (2026) ölçümüyle ve dağıtımın az sayıda sağlayıcıda yoğunlaştığını bulan BK "
  "çalışmasıyla tutarlıdır. Bunun iki sonucu vardır: CDN kullanan kurumlar korumayı ayrı bir çaba harcamadan elde "
  "etmekte, ancak bu koruma yalnızca kullanıcı ile CDN arasındaki bağlantıyı kapsamaktadır.")
P("**Bankacılık paradoksu.** \"Şimdi topla, sonra çöz\" tehdidine en fazla maruz kalan veriler finansal "
  "verilerdir; ancak bankacılık ölçülen sektörler arasında en geride kalan sektördür. Bankaların kendi "
  "altyapılarını işletme eğilimi ve geçişlerin uzun test ve onay süreçlerine tabi olması bu durumu "
  "açıklayabilecek olası nedenlerdir. Bankaların yarısından fazlasının TLS 1.3'e bile geçmemiş olması, kuantum "
  "sonrası geçişin önünde önce bir protokol sürümü yükseltmesi bulunduğunu göstermektedir.")
P("**Küresel karşılaştırma.** Örneklemdeki %24,8'lik destek oranı, en popüler bir milyon sitede %54 "
  "(F5 Labs, 2026) ve alan adlarının yaklaşık yarısında hibrit destek bulan küresel ölçümlerin (Dubey ve "
  "Varshney, 2026) altındadır. Ancak örneklem kendi altyapısını işletme eğilimi yüksek finans ve kamu sitelerine "
  "ağırlık verdiğinden karşılaştırma örneklem farkları göz önünde bulundurularak yorumlanmalıdır. Türkiye'deki "
  "yalnız TLS 1.2 oranı (%26,4), F5 Labs'in küresel olarak raporladığı %10,5'in belirgin biçimde üzerindedir.")

# ---------------------------------------------------------------------------
# 9. SINIRLILIKLAR
# ---------------------------------------------------------------------------
H1("9. SINIRLILIKLAR")
madde(["**Örneklem:** Veri seti 130 siteden oluşmaktadır ve sektörlerin tamamını temsil etmemektedir; özellikle "
       "kamu ve üniversite sektörlerinde site sayısının artırılması genellenebilirliği güçlendirecektir.",
       "**Tek ölçüm noktası ve kısa zaman aralığı:** Ölçümler tek bir ev bağlantısından ve 1,5–3 saat arayla "
       "yapılmıştır; tutarlılık sınaması kısa vadeli kararlılığı göstermektedir. CDN'ler kullanıcıyı konuma göre "
       "farklı sunuculara yönlendirebildiğinden farklı ağlardan farklı sonuçlar alınabilir.",
       "**Yalnız ana sayfa:** İnternet bankacılığı veya ödeme sayfaları gibi alt alan adları farklı bir altyapıda "
       "çalışıyor olabilir.",
       "**Süre ölçümünün hassasiyeti:** El sıkışma süreleri s_client sürecinin duvar saati süresiyle ölçülmüştür ve "
       "Windows'ta yaklaşık 1 s sabit yük içermektedir; bu nedenle ağ maliyeti bayt ve segment düzeyinde, kayıp "
       "etkisi ise simülasyonla değerlendirilmiştir.",
       "**Simülasyon varsayımları:** Bağımsız Bernoulli kaybı, ACK kayıplarının ve hızlı yeniden iletimin "
       "modellenmemesi gerçek ağlardaki ardışık (burst) kayıpları tam yansıtmayabilir. Simülasyon sonuçları "
       "kontrollü bir ağ emülasyonu deneyiyle doğrulanmalıdır (Bölüm 10).",
       "**CDN tespiti:** Başlık ve adres bloğuna dayalı yöntemin tanımadığı yerel CDN veya ters vekil sunucular "
       "\"kendi sunucusu\" olarak sınıflandırılmış olabilir.",
       "**Kaynak sunucu bağlantısı:** CDN ile kurumun kaynak sunucusu arasındaki bağlantı dışarıdan "
       "gözlemlenemediğinden ölçülememiştir."])

# ---------------------------------------------------------------------------
# 10. SONUÇ
# ---------------------------------------------------------------------------
H1("10. SONUÇ VE ÖNERİLER")
P("Bu projede Türkiye'de dört kritik sektöre ait 129 web sitesinin kuantum sonrası TLS hazırlığı açık bir ölçüm "
  "sistemiyle iki tur hâlinde ölçülmüş, geçişin ağ maliyeti ölçüm, paket yakalama ve simülasyonla incelenmiştir. "
  "Sitelerin dörtte biri hibrit X25519MLKEM768 anahtar değişimini desteklemekte, ancak bu destek neredeyse "
  "tamamen CDN arkasındaki sitelerden gelmektedir. CDN kullanımı sabit tutulduğunda sektörler arasındaki fark "
  "ortadan kalkmaktadır. Kendi sunucusunu işleten bankalar ve kamu kurumları belirgin biçimde geridedir; "
  "bankaların hiçbiri hazır değildir ve yarısı hâlâ TLS 1.2 kullanmaktadır. Ağ düzeyinde hibrit anahtar "
  "değişimi el sıkışma başına yaklaşık 2,3 KB ek veri getirmekte ve tarayıcı ClientHello mesajını iki TCP "
  "segmentine bölmektedir. Bu ek segment kayıpsız ortamda ölçülebilir bir gecikme yaratmazken, %1–10 kayıplı "
  "kanallarda ortalama el sıkışma süresini simülasyona göre %1,5–7 artırmaktadır.")
P("**Mühendislik katkısı ve özgün yönler:** (i) Türkiye'ye özgü ilk sektörel kuantum sonrası TLS ölçümü, "
  "(ii) hazırlığın belirleyicisinin katmanlı istatistikle ortaya konması, (iii) hazırlık ölçümü ile katmanlar "
  "arası ağ maliyetinin (TLS → TCP segmenti → Ethernet çerçevesi) aynı veri setinde birleştirilmesi ve "
  "(iv) kurumların kendi durumunu ölçebileceği açık, Docker ile taşınabilir bir araç.")
P("Bulgular ışığında şu öneriler sunulmaktadır:")
madde(["Kendi sunucusunu işleten kurumlar öncelikle TLS 1.3'e geçmeli, ardından TLS kütüphanelerini "
       "X25519MLKEM768'i varsayılan olarak destekleyen sürümlere (ör. OpenSSL 3.5 ve sonrası) güncellemelidir. "
       "Ölçülen iki üniversite bunun CDN olmadan da mümkün olduğunu göstermektedir.",
       "Finans sektörü için düzenleyici kurumların kuantum sonrası geçişe yönelik bir yol haritası ve takvim "
       "belirlemesi, sektördeki gecikmeyi azaltabilir.",
       "CDN kullanan kurumlar, CDN ile kendi kaynak sunucuları arasındaki bağlantının da kuantum sonrası korumaya "
       "kavuşturulmasını gündemlerine almalıdır.",
       "Ağ yöneticileri, büyüyen ve parçalanan ClientHello mesajlarını doğru işlemeyen eski güvenlik duvarı ve TLS "
       "denetim cihazlarını güncellemeli; yüksek kayıplı erişim ağlarında ek segmentin kuyruk gecikmesine etkisini "
       "izlemelidir."], numarali=True)
H2("Gelecek Çalışmalar ve Planlanan Doğrulama Deneyi")
P("Simülasyon sonuçlarını doğrulamak için şu deney planlanmıştır: Linux üzerinde OpenSSL 3.5+ ile yerel bir TLS "
  "sunucusu (openssl s_server) kurulacak, istemci ile sunucu arasındaki arayüzün MTU değeri 1500 B'a ayarlanacak "
  "ve tc qdisc add dev <arayüz> root netem delay 10ms loss p% komutuyla 20 ms RTT ve %0–10 kayıp oranları "
  "uygulanacaktır. Her koşulda klasik, hibrit ve tarayıcı benzeri teklifle 1000'er el sıkışma yapılarak süre "
  "dağılımı, ortalama ve 95. yüzdelik değerler Tablo 13'teki beklenen değerlerle karşılaştırılacaktır. Bunun "
  "yanında ölçümün düzenli aralıklarla tekrarlanarak Türkiye'deki geçiş hızının izlenmesi, örneklemin internet "
  "bankacılığı ve e-Devlet hizmetleri gibi alt alan adlarını kapsayacak şekilde genişletilmesi ve farklı ISS'lerden "
  "ölçüm yapılması planlanmaktadır. Sistem, aynı mimariyle SMTP (STARTTLS) ve QUIC/HTTP3 gibi farklı haberleşme "
  "protokollerine de uyarlanabilir.")

# ---------------------------------------------------------------------------
# YZ BEYANI
# ---------------------------------------------------------------------------
H1("YAPAY ZEKÂ ARAÇLARININ KULLANIMINA İLİŞKİN BEYAN")
P("Bu projede üretken yapay zekâ aracı olarak Claude (Anthropic) kullanılmıştır. Araç; ölçüm ve analiz "
  "betiklerinin geliştirilmesinde, ek istatistiksel analizlerin (Wilson güven aralığı, katmanlı permütasyon "
  "testi) ve paket kaybı simülasyonunun kodlanmasında, teknik diyagramların ve grafiklerin üretilmesinde, "
  "paket yakalama dosyasının programla yeniden ayrıştırılmasında, kaynakların varlığının ve künyelerinin "
  "kontrolünde ve raporun ders yönergesine göre yapılandırılıp yazılmasında destek amacıyla kullanılmıştır.")
P("Ölçümler öğrenci tarafından kendi bilgisayarında ve ağında gerçekleştirilmiştir. Raporda verilen tüm sayısal "
  "sonuçlar ham ölçüm dosyalarından (sonuclar_1.csv, sonuclar_2.csv, trendyol_klasik_hibrit.pcapng) teslim edilen "
  "kodlarla yeniden hesaplanabilmektedir. Simülasyon sonuçları ölçüm sonuçlarından açıkça ayrılmış ve "
  "varsayımları belirtilmiştir. Kodların, hesaplamaların ve kaynakların doğruluğu öğrenci tarafından kontrol "
  "edilmiştir; projenin bilimsel ve akademik sorumluluğu öğrenciye aittir.")

# ---------------------------------------------------------------------------
# KAYNAKÇA (APA 7)
# ---------------------------------------------------------------------------
H1("KAYNAKÇA")
kaynaklar = [
    "Bernstein, D. J., & Lange, T. (2017). Post-quantum cryptography. *Nature, 549*(7671), 188–194. "
    "https://doi.org/10.1038/nature23461",
    "Chu, J., Dukkipati, N., Cheng, Y., & Mathis, M. (2013). *Increasing TCP's initial window* (RFC 6928). "
    "Internet Engineering Task Force. https://doi.org/10.17487/RFC6928",
    "Cloudflare. (2025). *State of the post-quantum Internet in 2025* [Blog yazısı]. "
    "https://blog.cloudflare.com/pq-2025",
    "Cloudflare. (2026, 27 Şubat). *Post-quantum encryption and key transparency on Cloudflare Radar* "
    "[Değişiklik günlüğü]. https://developers.cloudflare.com/changelog/post/2026-02-27-radar-pq-key-transparency/",
    "Driscoll, F., Parsons, M., & Hale, B. (2025). *Terminology for post-quantum traditional hybrid schemes* "
    "(RFC 9794). Internet Engineering Task Force. https://doi.org/10.17487/RFC9794",
    "Dubey, V. M., & Varshney, G. (2026). *Measurement study of post-quantum readiness of Internet: 2026* "
    "(arXiv:2606.16473). arXiv. https://arxiv.org/abs/2606.16473",
    "F5 Labs. (2026). *2026 state of PQC on the web*. F5. "
    "https://www.f5.com/labs/articles/2026-state-of-pqc-on-the-web",
    "Jacar. (2026, Temmuz). *Post-quantum cryptography in TLS: Real-world adoption*. "
    "https://jacar.es/en/post-quantum-cryptography-in-tls-real-world-adoption/",
    "Kwiatkowski, K., Kampanakis, P., Westerbaan, B. E., & Stebila, D. (2026). *Post-quantum hybrid ECDHE-MLKEM "
    "key agreement for TLSv1.3* (Internet-Draft draft-ietf-tls-ecdhe-mlkem-05; çalışma aşamasında). Internet "
    "Engineering Task Force. https://datatracker.ietf.org/doc/draft-ietf-tls-ecdhe-mlkem/",
    "*Measuring post-quantum TLS deployment across UK Internet sectors*. (2026). (arXiv:2608.02147). arXiv. "
    "https://arxiv.org/abs/2608.02147",
    "Mosca, M. (2018). Cybersecurity in an era with quantum computers: Will we be ready? *IEEE Security & Privacy, "
    "16*(5), 38–41. https://doi.org/10.1109/MSP.2018.3761723",
    "National Institute of Standards and Technology. (2024). *Module-lattice-based key-encapsulation mechanism "
    "standard* (FIPS 203). U.S. Department of Commerce. https://doi.org/10.6028/NIST.FIPS.203",
    "Paquin, C., Stebila, D., & Tamvada, G. (2020). Benchmarking post-quantum cryptography in TLS. In J. Ding & "
    "J.-P. Tillich (Eds.), *Post-Quantum Cryptography: PQCrypto 2020* (LNCS Vol. 12100, pp. 72–91). Springer. "
    "https://doi.org/10.1007/978-3-030-44223-1_5",
    "Paxson, V., Allman, M., Chu, J., & Sargent, M. (2011). *Computing TCP's retransmission timer* (RFC 6298). "
    "Internet Engineering Task Force. https://doi.org/10.17487/RFC6298",
    "Rescorla, E. (2018). *The Transport Layer Security (TLS) protocol version 1.3* (RFC 8446). Internet "
    "Engineering Task Force. https://doi.org/10.17487/RFC8446",
    "Shor, P. W. (1997). Polynomial-time algorithms for prime factorization and discrete logarithms on a quantum "
    "computer. *SIAM Journal on Computing, 26*(5), 1484–1509. https://doi.org/10.1137/S0097539795293172",
    "Sikeridis, D., Kampanakis, P., & Devetsikiotis, M. (2020). Post-quantum authentication in TLS 1.3: A "
    "performance study. In *Proceedings of the Network and Distributed System Security Symposium (NDSS 2020)*. "
    "Internet Society. https://doi.org/10.14722/ndss.2020.24203",
    "UnveilScan. (2026). *Post-quantum TLS: What's actually shipping in 2026*. "
    "https://unveilscan.unveiltech.com/blog/post-quantum-tls.html",
    "Westerbaan, B., & Sardar, M. U. (2026). *Updated recommendations for TLS keyshares* (Internet-Draft "
    "draft-westerbaan-tls-keyshare-recommendations-02; çalışma aşamasında). Internet Engineering Task Force. "
    "https://datatracker.ietf.org/doc/draft-westerbaan-tls-keyshare-recommendations/",
    "Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. *Journal of the "
    "American Statistical Association, 22*(158), 209–212. https://doi.org/10.1080/01621459.1927.10502953",
]
for k in kaynaklar:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.left_indent = Cm(1.27)
    p.paragraph_format.first_line_indent = Cm(-1.27)
    calistir(p, k, boyut=11)

# ---------------------------------------------------------------------------
# EK A
# ---------------------------------------------------------------------------
H1("EK A. TEKNİK DOSYALAR VE TEKRARLANABİLİRLİK")
P("Teknik dosyalar Rumeysa_Betul_Ozyurt_Veri_Iletisimi_Uygulama.zip dosyasında teslim edilmiştir.")
tablo("Teslim edilen teknik dosyalar", [
    ["Dosya", "İçerik"],
    ["kod/olcum.py", "Ölçüm aracı (OpenSSL s_client tabanlı, 34 sütunlu CSV üretir)"],
    ["kod/analiz.py", "Sektör bazında özet tablolar ve temel grafikler"],
    ["kod/analiz_ek.py", "Güven aralıkları, Fisher/permütasyon testleri, ağ maliyeti, kayıp simülasyonu"],
    ["kod/diyagramlar.py", "Mimari, sıra, katman, paket yapısı ve akış diyagramları"],
    ["kod/Dockerfile, README.md", "OpenSSL 3.5 hazır ortam ve kullanım kılavuzu"],
    ["veri/siteler.csv", "130 sitelik ölçüm listesi"],
    ["veri/sonuclar_1.csv, sonuclar_2.csv, pilot.csv", "Ham ölçüm sonuçları (iki tur ve pilot)"],
    ["veri/trendyol_klasik_hibrit.pcapng", "Wireshark paket yakalama dosyası"],
    ["analiz/ek_analiz.json, simulasyon.csv", "Ek analiz ve simülasyon çıktıları"],
    ["sekiller/*.png", "Rapor ve sunumdaki tüm şekiller"],
], genislikler=[6, 9.5], boyut=9.5)
P("Analizleri yeniden üretmek için: python3 analiz_ek.py --veri ../veri --cikti ../analiz --sekiller ../sekiller "
  "ve python3 diyagramlar.py ../sekiller. Ölçümü tekrarlamak için: "
  "docker build -t pqtls . && docker run --rm -v \"$PWD/veri:/veri\" pqtls.", WD_ALIGN_PARAGRAPH.LEFT)

doc.core_properties.title = "Türkiye'deki Kritik Sektör Web Sitelerinin Kuantum Sonrası TLS Hazırlığı"
doc.core_properties.author = "Rümeysa Betül Özyurt"
doc.save(CIKTI)
print("Kaydedildi:", CIKTI, "| şekil:", sekil_no[0], "| tablo:", tablo_no[0])
