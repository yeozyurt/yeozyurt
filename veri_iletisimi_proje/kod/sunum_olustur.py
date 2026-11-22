#!/usr/bin/env python3
"""Rapora dayalı PowerPoint sunumu (16:9). Başlıklar 28–32 pt, içerik 18–22 pt.
Her slayta konuşmacı notu eklenir."""
import json
import os
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Cm, Emu, Pt

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEK = os.path.join(KOK, "sekiller")
R = json.load(open(os.path.join(KOK, "analiz", "ek_analiz.json"), encoding="utf-8"))
CIKTI = sys.argv[1] if len(sys.argv) > 1 else os.path.join(KOK, "Rumeysa_Betul_Ozyurt_Veri_Iletisimi_Proje_Sunumu.pptx")

LACI = RGBColor(0x1F, 0x2A, 0x44)
YESIL = RGBColor(0x1B, 0x7F, 0x5A)
MAVI = RGBColor(0x4A, 0x78, 0xC2)
TURUNCU = RGBColor(0xC7, 0x5B, 0x39)
GRI = RGBColor(0x5F, 0x66, 0x70)
ACIK = RGBColor(0xF3, 0xF5, 0xF8)
BEYAZ = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Calibri"

prs = Presentation()
prs.slide_width, prs.slide_height = Cm(33.867), Cm(19.05)
W, H = prs.slide_width, prs.slide_height
BOS = prs.slide_layouts[6]
sayac = [0]


def metin_kutusu(sl, x, y, w, h, satirlar, boyut=20, renk=LACI, kalin=False, hiza=PP_ALIGN.LEFT,
                 dikey=MSO_ANCHOR.TOP, aralik=6):
    tb = sl.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = dikey
    tf.margin_left = tf.margin_right = Cm(0.2)
    if isinstance(satirlar, str):
        satirlar = [satirlar]
    for i, s in enumerate(satirlar):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = hiza
        p.space_after = Pt(aralik)
        madde = s.startswith("• ")
        parcalar = s.split("**")
        for k, parca in enumerate(parcalar):
            if not parca:
                continue
            r = p.add_run()
            r.text = parca
            r.font.size = Pt(boyut)
            r.font.name = FONT
            r.font.color.rgb = renk
            r.font.bold = kalin or (k % 2 == 1)
    return tb


def kutu(sl, x, y, w, h, dolgu=ACIK, kenar=None, sekil=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = sl.shapes.add_shape(sekil, x, y, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = dolgu
    if kenar:
        s.line.color.rgb = kenar; s.line.width = Pt(1.5)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    if sekil == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = 0.08
    return s


def slayt(baslik, notlar="", bolum=None):
    sayac[0] += 1
    sl = prs.slides.add_slide(BOS)
    bar = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Cm(0.6), H)
    bar.fill.solid(); bar.fill.fore_color.rgb = YESIL; bar.line.fill.background()
    metin_kutusu(sl, Cm(1.5), Cm(0.7), Cm(30), Cm(2.0), baslik, 30, LACI, True, dikey=MSO_ANCHOR.MIDDLE)
    if bolum:
        metin_kutusu(sl, Cm(1.5), Cm(0.15), Cm(20), Cm(0.8), bolum.upper(), 11, YESIL, True)
    metin_kutusu(sl, Cm(26), Cm(18.1), Cm(7.3), Cm(0.8), f"Kuantum Sonrası TLS · {sayac[0]}", 11, GRI,
                 hiza=PP_ALIGN.RIGHT)
    if notlar:
        sl.notes_slide.notes_text_frame.text = notlar
    return sl


def resim(sl, dosya, x, y, w=None, h=None):
    return sl.shapes.add_picture(os.path.join(SEK, dosya), x, y, w, h)


def tablo(sl, x, y, w, satirlar, boyut=16, sutun=None, yukseklik=Cm(1.0), vurgu_son=False):
    t = sl.shapes.add_table(len(satirlar), len(satirlar[0]), x, y, w, yukseklik * len(satirlar)).table
    if sutun:
        top = sum(sutun)
        for j, c in enumerate(sutun):
            t.columns[j].width = Emu(int(w * c / top))
    for i, satir in enumerate(satirlar):
        for j, deger in enumerate(satir):
            h = t.cell(i, j)
            h.text = str(deger)
            h.margin_left = h.margin_right = Cm(0.2)
            h.vertical_anchor = MSO_ANCHOR.MIDDLE
            for p in h.text_frame.paragraphs:
                p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
                for r in p.runs:
                    r.font.size = Pt(boyut); r.font.name = FONT
                    r.font.bold = i == 0 or (vurgu_son and i == len(satirlar) - 1)
                    r.font.color.rgb = BEYAZ if i == 0 else LACI
            h.fill.solid()
            h.fill.fore_color.rgb = LACI if i == 0 else (RGBColor(0xDF, 0xF0, 0xE8) if vurgu_son and i == len(satirlar) - 1
                                                         else (ACIK if i % 2 else BEYAZ))
    return t


def buyuk_sayi(sl, x, y, w, sayi, aciklama, renk=YESIL):
    kutu(sl, x, y, w, Cm(3.6))
    metin_kutusu(sl, x, y + Cm(0.2), w, Cm(1.9), sayi, 40, renk, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    metin_kutusu(sl, x + Cm(0.2), y + Cm(2.0), w - Cm(0.4), Cm(1.5), aciklama, 15, GRI, False, PP_ALIGN.CENTER)


def tr(x, b=1):
    return f"{x:.{b}f}".replace(".", ",")


s = {o["sektor"]: o for o in R["sektor"]}
ag = R["ag"]
sim = {(x["senaryo"], x["kayip"]): x for x in R["simulasyon"]["rtt20"]}

# 1 ---------------------------------------------------------------------------
sl = prs.slides.add_slide(BOS); sayac[0] += 1
bg = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H); bg.fill.solid(); bg.fill.fore_color.rgb = LACI
bg.line.fill.background()
bar = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(2), Cm(5.2), Cm(2.5), Cm(0.25)); bar.fill.solid()
bar.fill.fore_color.rgb = YESIL; bar.line.fill.background()
metin_kutusu(sl, Cm(2), Cm(2.3), Cm(30), Cm(2.6), "VERİ İLETİŞİMİ (BİL321) · DÖNEM PROJESİ", 16,
             RGBColor(0x9F, 0xD8, 0xC0), True)
metin_kutusu(sl, Cm(2), Cm(5.8), Cm(30), Cm(5), ["Türkiye'deki Kritik Sektör Web Sitelerinin",
                                                 "Kuantum Sonrası TLS Hazırlığı"], 40, BEYAZ, True, aralik=0)
metin_kutusu(sl, Cm(2), Cm(10.6), Cm(30), Cm(1.5), "Sektörel Ölçüm, Ağ Maliyeti ve Paket Kaybı Analizi", 24,
             RGBColor(0xC9, 0xD3, 0xE6))
metin_kutusu(sl, Cm(2), Cm(13.6), Cm(30), Cm(4), [
    "**Rümeysa Betül ÖZYURT** · Bilgisayar Mühendisliği Yüksek Lisans",
    "Öğretim Üyesi: Prof. Dr. Agah Tuğrul KORUCU",
    "İstanbul Ticaret Üniversitesi · 2026–2027 Güz"], 18, BEYAZ, aralik=4)
sl.notes_slide.notes_text_frame.text = (
    "Merhaba, projem Türkiye'deki kritik sektör web sitelerinin kuantum bilgisayar tehdidine karşı ne kadar hazır "
    "olduğunu ve bu geçişin ağ katmanına getirdiği maliyeti inceliyor. Hem gerçek ölçüm, hem paket yakalama, hem de "
    "simülasyon kullandım.")

# 2 ---------------------------------------------------------------------------
sl = slayt("Neden şimdi? \"Şimdi topla, sonra çöz\"", bolum="Konu ve önemi", notlar=(
    "HTTPS oturum anahtarı bugün X25519 gibi eliptik eğri yöntemleriyle kuruluyor. Shor algoritması bu yöntemleri "
    "kuantum bilgisayarda kırabiliyor. Saldırgan bugün trafiği kaydedip yıllar sonra çözebilir. Mosca eşitsizliği: "
    "verinin gizli kalma süresi x ile geçiş süresi y'nin toplamı, kuantum bilgisayarın gelişine kadar geçecek z "
    "süresinden büyükse risk bugünden başlamıştır. Bankacılık, sağlık ve kamu verileri bu yüzden şimdiden risk altında."))
for i, (baslik, alt, renk) in enumerate((("2026 · Bugün", "Saldırgan şifreli HTTPS\ntrafiğini kaydeder", MAVI),
                                         ("Gizli kalma süresi", "Banka, sağlık, kamu verisi\n10+ yıl gizli kalmalı", GRI),
                                         ("Kuantum bilgisayar", "Shor algoritması X25519 /\nECDH anahtarını çözer", TURUNCU))):
    x = Cm(1.8 + i * 10.6)
    k = kutu(sl, x, Cm(3.6), Cm(9.6), Cm(4.6), ACIK, renk)
    metin_kutusu(sl, x, Cm(3.9), Cm(9.6), Cm(1.2), baslik, 22, renk, True, PP_ALIGN.CENTER)
    metin_kutusu(sl, x, Cm(5.3), Cm(9.6), Cm(2.6), alt.split("\n"), 18, LACI, hiza=PP_ALIGN.CENTER, aralik=2)
    if i < 2:
        ok_ = sl.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x + Cm(9.7), Cm(5.4), Cm(0.8), Cm(1.0))
        ok_.fill.solid(); ok_.fill.fore_color.rgb = GRI; ok_.line.fill.background()
kutu(sl, Cm(1.8), Cm(9.3), Cm(30.4), Cm(2.2), RGBColor(0xFB, 0xEE, 0xE8), TURUNCU)
metin_kutusu(sl, Cm(1.8), Cm(9.3), Cm(30.4), Cm(2.2),
             "Mosca eşitsizliği:  gizli kalma süresi (x) + geçiş süresi (y) > tehdit süresi (z)  ⇒  risk bugün başlar",
             20, TURUNCU, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
metin_kutusu(sl, Cm(1.8), Cm(12.2), Cm(30.4), Cm(5.5), [
    "• **Çözüm:** NIST FIPS 203 ile standartlaşan **ML-KEM** + klasik X25519 → hibrit **X25519MLKEM768**",
    "• Chrome, Edge, Firefox bu grubu **varsayılan** olarak teklif ediyor → istemci tarafı hazır",
    "• Belirleyici soru: **Sunucular kabul ediyor mu?**"], 20)

# 3 ---------------------------------------------------------------------------
sl = slayt("Veri iletişimi problemi: güvenlik ile verimlilik arasında", bolum="Problem tanımı", notlar=(
    "Problem iki yönlü. Birincisi güvenlik: Türkiye'de hangi kurumlar bu korumayı sağlıyor, bilinmiyor. İkincisi "
    "iletim verimliliği: hibrit anahtar payları el sıkışmayı yaklaşık 2,3 kilobayt büyütüyor ve ilk mesaj artık tek "
    "TCP segmentine sığmıyor. Bu da bant genişliği, gecikme, kayba duyarlılık ve ara cihaz uyumluluğu açısından "
    "sonuç doğuruyor."))
for i, (b, a, r) in enumerate((("Güvenlik", "Uzun vadeli gizlilik:\nhangi sunucu PQ korumalı?", YESIL),
                               ("Bant genişliği", "El sıkışma başına\n+2,3 KB ek veri", MAVI),
                               ("Gecikme / kayıp", "ClientHello 2 segmente\nbölünür → kayba duyarlı", TURUNCU),
                               ("Güvenilirlik", "Tek segment varsayan\neski ara cihazlar", GRI))):
    x = Cm(1.8 + i * 7.65)
    kutu(sl, x, Cm(3.5), Cm(7.1), Cm(5.2), ACIK, r)
    metin_kutusu(sl, x, Cm(3.9), Cm(7.1), Cm(1.2), b, 22, r, True, PP_ALIGN.CENTER)
    metin_kutusu(sl, x, Cm(5.4), Cm(7.1), Cm(3), a.split("\n"), 17, LACI, hiza=PP_ALIGN.CENTER, aralik=2)
metin_kutusu(sl, Cm(1.8), Cm(9.8), Cm(30.4), Cm(1.2), "Mevcut durumun sınırlılıkları", 22, LACI, True)
metin_kutusu(sl, Cm(1.8), Cm(11.2), Cm(30.4), Cm(6.5), [
    "• Küresel ölçümler **Türkiye ve sektör kırılımı** sunmuyor",
    "• Çalışmalar yalnızca \"destek var mı?\" sorusuna bakıyor; **ağ maliyeti** aynı veride incelenmemiş",
    "• Kurumların kendi durumunu ölçebileceği **açık ve yerel bir araç** yok"], 20)

# 4 ---------------------------------------------------------------------------
sl = slayt("Amaç ve hedefler", bolum="Projenin amacı", notlar=(
    "Dört hedefim vardı: ölçüm sistemi kurmak, hazırlığın neye bağlı olduğunu istatistikle göstermek, ağ maliyetini "
    "bayt, segment ve gecikme düzeyinde ölçmek, ve bunu herkesin tekrarlayabileceği açık bir araçla yapmak."))
for i, (n, b, a) in enumerate((("1", "Ölçüm sistemi", "4 kritik sektörden 130 sitenin TLS ve PQ hazırlığını ölçen açık araç"),
                               ("2", "Belirleyiciler", "Hazırlığın sektöre mi, altyapıya (CDN) mı bağlı olduğunu istatistikle sınamak"),
                               ("3", "Ağ maliyeti", "Bayt, TCP segmenti ve paket kaybı altında gecikme (ölçüm + pcap + simülasyon)"),
                               ("4", "Tekrarlanabilirlik", "Python + OpenSSL + Docker; iki ölçüm turu ile tutarlılık"))):
    y = Cm(3.4 + i * 3.6)
    c = kutu(sl, Cm(1.8), y, Cm(2.6), Cm(2.8), YESIL, sekil=MSO_SHAPE.OVAL)
    metin_kutusu(sl, Cm(1.8), y, Cm(2.6), Cm(2.8), n, 32, BEYAZ, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    metin_kutusu(sl, Cm(5.2), y + Cm(0.1), Cm(26), Cm(1.2), b, 24, LACI, True)
    metin_kutusu(sl, Cm(5.2), y + Cm(1.35), Cm(27), Cm(1.4), a, 19, GRI)

# 5 ---------------------------------------------------------------------------
sl = slayt("Literatür ve mevcut çözümler", bolum="Literatür", notlar=(
    "Paquin ve arkadaşları laboratuvarda PQ TLS'in kayıp altındaki davranışını incelemişti. 2026'da küresel ölçümler "
    "var: F5 Labs ilk 1 milyon sitede yüzde 54 destek buldu ama Cloudflare dışında bu oran yüzde 22'ye düşüyor. "
    "İngiltere için sektörel bir çalışma da var. Benim çalışmam Türkiye'ye odaklanıyor ve hazırlık ölçümünü aynı veri "
    "seti üzerinde ağ maliyeti ve kayıp analiziyle birleştiriyor."))
tablo(sl, Cm(1.8), Cm(3.3), Cm(30.4), [
    ["Çalışma", "Kapsam", "Sektör", "Ağ maliyeti", "Kayıp analizi", "Türkiye"],
    ["Paquin vd. (2020)", "Laboratuvar", "–", "✓", "✓ (emülasyon)", "–"],
    ["Dubey & Varshney (2026)", "32 011 alan adı", "✓", "–", "–", "–"],
    ["F5 Labs (2026)", "İlk 1 milyon site", "kısmi", "–", "–", "–"],
    ["BK sektör çalışması (2026)", "Birleşik Krallık", "✓", "–", "–", "–"],
    ["Bu proje", "130 site · 4 sektör", "✓", "✓ ölçüm + pcap", "✓ simülasyon", "✓"],
], boyut=17, sutun=[6, 4.5, 2.3, 4.2, 4, 2.4], yukseklik=Cm(1.25), vurgu_son=True)
metin_kutusu(sl, Cm(1.8), Cm(11.6), Cm(30.4), Cm(6), [
    "• Küresel tablo: F5 Labs **%54** PQ destek → Cloudflare hariç **%22**; sitelerin **%10,5**'i TLS 1.3 bile yok",
    "• Hibrit X25519MLKEM768: istemci payı **1216 B**, sunucu payı **1120 B** (IETF ECDHE-MLKEM taslağı)",
    "• Parçalanmış ClientHello'yu reddeden eski TLS denetim cihazları bildirilmiş"], 19)

# 6 ---------------------------------------------------------------------------
sl = slayt("Önerilen sistemin genel yapısı", bolum="Sistem mimarisi", notlar=(
    "Gönderici tarafta Python betiği OpenSSL 4.0.3'ün s_client bileşenini çalıştırıyor. Kanal, Türkiye'de bir ev "
    "internet bağlantısı; MSS 1460 bayt. Alıcı tarafta iki tip sunucu var: TLS'in CDN uç sunucusunda sonlandığı 31 "
    "site ve kurumun kendi sunucusunda sonlandığı 98 site. CDN ile kaynak sunucu arası dışarıdan görünmediği için "
    "kapsam dışı. Wireshark ile paket düzeyinde doğrulama yaptım."))
resim(sl, "diyagram_sistem_mimarisi.png", Cm(2.2), Cm(3.0), w=Cm(29.5))

# 7 ---------------------------------------------------------------------------
sl = slayt("Kullanılan teknolojiler ve seçim gerekçeleri", bolum="Teknolojiler ve protokoller", notlar=(
    "OpenSSL s_client'ı seçtim çünkü hangi anahtar paylarının gönderileceğini kontrol edebiliyorum ve -msg ile her "
    "mesajın boyutunu görüyorum. Python'un kendi ssl modülü bunu vermiyor. İstatistikte Fisher kesin testini seçtim "
    "çünkü bankalarda sıfır değeri var ve ki-kare küçük frekanslarda güvenilmez."))
tablo(sl, Cm(1.8), Cm(3.2), Cm(30.4), [
    ["Bileşen", "Seçim", "Neden?", "Alternatif"],
    ["TLS istemcisi", "OpenSSL 4.0.3 s_client", "Pay kontrolü (-groups), mesaj boyutu (-msg)", "Python ssl, curl"],
    ["Dil", "Python 3 (standart kütüphane)", "Taşınabilir, ek paket yok", "Go crypto/tls"],
    ["Anahtar grubu", "X25519MLKEM768", "Tarayıcıların varsayılanı", "SecP256r1MLKEM768"],
    ["Taşıma", "TCP + TLS 1.3", "HTTPS'in ana yolu; PQ yalnız TLS 1.3'te", "QUIC (yalnız ilan)"],
    ["Paket analizi", "Wireshark 4.6.8", "Çerçeve/uzantı düzeyinde doğrulama", "tcpdump"],
    ["İstatistik", "Fisher, Wilson GA, permütasyon", "Küçük örneklem, sıfır hücre", "Ki-kare"],
    ["Ortam", "Docker (OpenSSL 3.5)", "Her işletim sisteminde aynı ortam", "Yerel kurulum"],
], boyut=16, sutun=[3.6, 6.5, 8.5, 4.2], yukseklik=Cm(1.6))

# 8 ---------------------------------------------------------------------------
sl = slayt("Gönderici–alıcı protokol akışı", bolum="Gönderici–alıcı mimarisi", notlar=(
    "TCP üçlü el sıkışması bir RTT. Sonra istemci ClientHello gönderiyor; içinde iki anahtar payı var: 1216 baytlık "
    "hibrit pay ve yedek olarak 32 baytlık X25519. Bu mesaj iki TCP segmentine bölünüyor. Sunucu 1210 baytlık "
    "ServerHello ile cevap veriyor. Hibrit grupla da el sıkışma 1 RTT'de bitiyor. Sağda: sunucu tarayıcının "
    "gönderdiği grupları desteklemezse HelloRetryRequest ile fazladan bir RTT harcanıyor; bir bankada bunu gördüm."))
resim(sl, "diyagram_tls13_sira.png", Cm(1.8), Cm(2.9), w=Cm(30.4))

# 9 ---------------------------------------------------------------------------
sl = slayt("Katmanlar arası etki: TLS değişir, TCP ve Ethernet hisseder", bolum="Protokol katmanları", notlar=(
    "Bu slayt projenin veri iletişimi açısından özünü gösteriyor. Değişiklik TLS katmanında yapılıyor ama etkisi "
    "taşıma katmanında segment sayısı ve yeniden iletim olarak, veri bağı katmanında da çerçeve boyutu olarak "
    "görülüyor. Sağ sütunda her katmanda neyi ölçtüğümü yazdım."))
resim(sl, "diyagram_katman_esleme.png", Cm(4.2), Cm(2.9), h=Cm(15.0))

# 10 --------------------------------------------------------------------------
sl = slayt("Paketleme: ClientHello artık tek segmente sığmıyor", bolum="Kodlama ve paketleme", notlar=(
    "Klasik ClientHello 232 bayt, tek segment. Tarayıcı benzeri hibrit ClientHello başlıklarla 1543 bayt. MSS 1460 "
    "olduğu için 83 bayt taşıyor ve ikinci bir segment gerekiyor. Mesajın yaklaşık yüzde 80'i tek bir uzantı, "
    "key_share."))
resim(sl, "diyagram_clienthello_segment.png", Cm(1.6), Cm(2.9), w=Cm(30.8))
buyuk_sayi(sl, Cm(1.8), Cm(15.0), Cm(9.5), "232 → 1534 B", "ClientHello (klasik → tarayıcı hibrit)", MAVI)
buyuk_sayi(sl, Cm(12.2), Cm(15.0), Cm(9.5), "1 → 2", "TCP segmenti (MSS 1460 B)", TURUNCU)
buyuk_sayi(sl, Cm(22.6), Cm(15.0), Cm(9.5), "+2272 B", "el sıkışma başına ek veri", YESIL)

# 11 --------------------------------------------------------------------------
sl = slayt("Veri akışı: site başına ölçüm algoritması", bolum="Sistem tasarımı ve veri akışı", notlar=(
    "Her site için alan adını bir kez çözüp hep aynı IP'yi kullanıyorum. Beş TCP bağlantısıyla medyan RTT ölçüyorum. "
    "Sonra beş senaryo: tarayıcı benzeri teklif, TLS 1.2 testi, yalnız hibrit, yalnız klasik ve HTTP başlıkları. "
    "Hibrit ve klasik testler beşer kez tekrarlanıyor. Siteler arasında 1,5 saniye bekliyorum; tarama yapmıyorum."))
resim(sl, "diyagram_olcum_akis.png", Cm(5.0), Cm(2.8), h=Cm(15.3))

# 12 --------------------------------------------------------------------------
sl = slayt("Uygulama ortamı ve test senaryoları", bolum="Uygulama ortamı", notlar=(
    "Veri seti 130 site: 27 banka, 33 kamu, 40 üniversite, 30 e-ticaret. Ölçümü iki tur yaptım, 7 ve 8 Ekim'de. "
    "Etik açıdan normal bir ziyaretçi gibi bağlandım, sonuçları kurum adı vermeden sektör bazında raporladım."))
tablo(sl, Cm(1.8), Cm(3.3), Cm(14.5), [
    ["Sektör", "Site"], ["Banka", "27"], ["Kamu", "33"], ["Üniversite", "40"], ["E-ticaret", "30"],
    ["Toplam", "130"]], boyut=18, sutun=[3, 1.4], yukseklik=Cm(1.2), vurgu_son=True)
metin_kutusu(sl, Cm(1.8), Cm(11.0), Cm(14.5), Cm(7), [
    "• Windows dizüstü, Türkiye'de ev interneti",
    "• OpenSSL 4.0.3, Python 3, Wireshark 4.6.8",
    "• **1. tur:** 7 Ekim 2026 22.40–23.07",
    "• **2. tur:** 8 Ekim 2026 00.26–00.52"], 18)
kutu(sl, Cm(17.3), Cm(3.3), Cm(14.9), Cm(14.4), ACIK)
metin_kutusu(sl, Cm(17.8), Cm(3.6), Cm(14), Cm(1.2), "Test senaryoları (site başına)", 21, LACI, True)
metin_kutusu(sl, Cm(17.8), Cm(5.0), Cm(14), Cm(12.5), [
    "**S1** Tarayıcı benzeri: *X25519MLKEM768 : *X25519 : P-256",
    "**S2** TLS 1.2 kabul testi",
    "**S3** Yalnız hibrit X25519MLKEM768 (×5)",
    "**S4** Yalnız klasik X25519 (×5)",
    "**S5** HTTPS GET → Alt-Svc (HTTP/3), CDN başlıkları",
    "**S6** Wireshark: klasik vs hibrit ClientHello",
    "**S7** Simülasyon: %0–10 segment kaybı"], 18, aralik=8)

# 13 --------------------------------------------------------------------------
sl = slayt("Performans ölçütleri", bolum="Performans ölçütleri", notlar=(
    "Bu projede kanal TCP ile güvenilir hale geldiği için fiziksel katmandaki bit hataları uygulamaya segment kaybı ve "
    "yeniden iletim olarak yansıyor. Bu yüzden BER yerine segment kayıp oranını kullandım."))
tablo(sl, Cm(1.8), Cm(3.2), Cm(30.4), [
    ["Ölçüt", "Karşılığı", "Yöntem", "Türü"],
    ["Hazırlık", "PQ destek, TLS sürümü, HRR, sertifika", "s_client senaryoları", "Ölçüm"],
    ["Veri miktarı", "CH / SH baytı, toplam okunan/yazılan", "-msg çıktısı, pcap", "Ölçüm"],
    ["Segment sayısı", "⌈(boyut + 9) / 1460⌉", "Hesap + Wireshark", "Ölçüm"],
    ["Gecikme", "TCP RTT, HRR ek RTT, süre farkı", "TCP connect ×5 medyan", "Ölçüm"],
    ["Paket kaybı etkisi", "El sıkışma süresi, yeniden iletim olasılığı", "Analitik + Monte Carlo", "Simülasyon"],
    ["Tutarlılık", "İki tur arasında aynı sonuç oranı", "Tur karşılaştırması", "Ölçüm"],
    ["Anlamlılık", "Fisher, Wilson GA, permütasyon testi", "SciPy", "İstatistik"],
], boyut=16, sutun=[4, 9.5, 6.5, 3.2], yukseklik=Cm(1.6))

# 14 --------------------------------------------------------------------------
sl = slayt("Bulgu 1: Sitelerin yalnızca dörtte biri hazır", bolum="Ölçülen sonuçlar", notlar=(
    "129 siteden 32'si, yani yüzde 24,8'i kuantum sonrası anahtar değişimini destekliyor. Yüzde 26,4'ü hâlâ yalnız "
    "TLS 1.2. E-ticarette yüzde 80, bankalarda sıfır. Bankaların yarısı TLS 1.3'e bile geçmemiş. Siyah çizgiler yüzde "
    "95 güven aralıkları."))
resim(sl, "sekil_sektor_hazirlik.png", Cm(1.5), Cm(3.0), w=Cm(20))
buyuk_sayi(sl, Cm(22.4), Cm(3.2), Cm(9.8), "%24,8", "PQ hazır (32/129)\n%95 GA: 18,2–32,9", YESIL)
buyuk_sayi(sl, Cm(22.4), Cm(7.3), Cm(9.8), "%26,4", "hâlâ yalnız TLS 1.2", TURUNCU)
buyuk_sayi(sl, Cm(22.4), Cm(11.4), Cm(9.8), "0 / 27", "banka PQ hazır\n(%51,9'u TLS 1.2)", TURUNCU)
metin_kutusu(sl, Cm(1.8), Cm(15.3), Cm(20), Cm(2.5),
             "Banka vs e-ticaret: Fisher kesin testi p ≈ 1,5×10⁻¹⁰  ·  1 banka HRR → her bağlantıda +1 RTT", 16, GRI)

# 15 --------------------------------------------------------------------------
sl = slayt("Bulgu 2: Belirleyici sektör değil, CDN", bolum="Ölçülen sonuçlar", notlar=(
    "CDN arkasındaki 31 sitenin 30'u hazır, kendi sunucusunu işleten 98 siteden sadece 2'si. Sonra şunu sordum: banka "
    "olmak mı önemli, altyapı mı? CDN kullanımını sabit tutup sektör etiketlerini 20 bin kez karıştırdım. Fark "
    "kayboldu, p 0,52. Yani aynı altyapıyı kullanan banka ile e-ticaret sitesi arasında fark yok."))
resim(sl, "sekil_cdn_etkisi.png", Cm(1.5), Cm(3.0), w=Cm(15.5))
ks, kc = R["katman_kendi_sunucu"], R["katman_cdn"]
tablo(sl, Cm(17.8), Cm(3.2), Cm(14.4), [
    ["Sektör", "Kendi sunucusu", "CDN"],
    *[[k, ks[k], kc[k] if kc[k] != "0/0" else "–"] for k in ("Banka", "Kamu", "Üniversite", "E-ticaret")],
    ["Toplam", "2/98", "30/31"]], boyut=17, sutun=[3.4, 3.5, 2.4], yukseklik=Cm(1.15), vurgu_son=True)
kutu(sl, Cm(17.8), Cm(10.8), Cm(14.4), Cm(6.9), RGBColor(0xDF, 0xF0, 0xE8), YESIL)
metin_kutusu(sl, Cm(18.2), Cm(11.1), Cm(13.6), Cm(6.5), [
    "**Katmansız:** sektör etkisi güçlü (χ² = 67,3; p < 10⁻¹³)",
    "**CDN'e göre katmanlı:** etki kaybolur (permütasyon p = 0,52)",
    "⇒ Geçiş kurumsal kararla değil, **altyapı sağlayıcısıyla** ilerliyor"], 18)
metin_kutusu(sl, Cm(1.8), Cm(15.6), Cm(15.5), Cm(2.2), "CDN: Cloudflare 21 · CloudFront 5 · Akamai 4 · Imperva 1",
             16, GRI)

# 16 --------------------------------------------------------------------------
sl = slayt("Bulgu 3: Ağ maliyeti (bayt, segment, paket)", bolum="Ölçülen sonuçlar", notlar=(
    "Hibrit el sıkışmada istemci 1184, sunucu 1088 bayt fazla gönderiyor. Bu, ML-KEM'in sabit boyutlu anahtar ve şifre "
    "metninden geliyor; ServerHello 32 sitenin hepsinde tam 1210 bayt. Tarayıcı benzeri ClientHello 129 sitenin "
    "hepsinde iki segment. Wireshark'ta aynı siteye klasik ClientHello 369 baytlık çerçeve, hibrit 1591 bayt. 1514'ü "
    "aşmasının nedeni TSO: paket ağ kartı bölmeden önce yakalanıyor."))
resim(sl, "sekil_mesaj_boyutlari.png", Cm(1.5), Cm(3.0), w=Cm(18.5))
tablo(sl, Cm(20.8), Cm(3.2), Cm(11.4), [
    ["Wireshark", "Klasik", "Hibrit"],
    ["CH çerçevesi", "369 B", "1591 B"],
    ["CH kaydı", "310 B", "1532 B"],
    ["SH kaydı", "122 B", "1210 B"]], boyut=17, sutun=[4, 2.6, 2.6], yukseklik=Cm(1.15))
metin_kutusu(sl, Cm(20.8), Cm(8.4), Cm(11.4), Cm(9.5), [
    "• +2272 B / el sıkışma ≈ 2 MB'lık sayfanın **%0,11**'i",
    "• 1 milyon el sıkışma/gün ≈ **2,27 GB**",
    "• İlk pencere (10 segment) içinde → kayıpsızda **ek RTT yok**",
    "• 1591 B > 1514 B: **TSO** öncesi yakalama"], 17)
metin_kutusu(sl, Cm(1.8), Cm(13.6), Cm(18.5), Cm(4),
             "Ölçülen süre farkı: +0,35 ms / −1,1 ms (Wilcoxon p = 0,63) → kayıpsız ağda ölçülebilir fark yok", 16, GRI)

# 17 --------------------------------------------------------------------------
sl = slayt("Bulgu 4: Kayıplı kanalda ikinci segmentin bedeli", bolum="Simülasyon sonuçları (ölçüm değildir)", notlar=(
    "Gerçek internette kaybı kontrol edemediğim için ölçülen boyutlarla beslenen bir Monte Carlo simülasyonu yaptım. "
    "Varsayımlar: bağımsız segment kaybı, RTO = RTT + 200 ms, SYN için 1 saniye. Analitik formül 1 eksi (1 eksi p) "
    "üzeri n, simülasyonla örtüşüyor. Yüzde 10 kayıpta ortalama süre yüzde 7 artıyor. Önemli nokta: tarayıcı, "
    "sunucu desteklemese de iki payı gönderiyor; yani hazır olmayan sunucuların kullanıcıları bu maliyeti korumasız "
    "ödüyor."))
resim(sl, "sekil_simulasyon_kayip.png", Cm(1.5), Cm(2.9), w=Cm(21.5))
k01 = (sim[("Klasik", 0.01)], sim[("Hibrit (tarayıcı)", 0.01)])
k10 = (sim[("Klasik", 0.10)], sim[("Hibrit (tarayıcı)", 0.10)])
tablo(sl, Cm(23.6), Cm(3.2), Cm(8.6), [
    ["p", "Klasik", "Hibrit"],
    ["%1", f"{tr(k01[0]['ortalama_ms'])} ms", f"{tr(k01[1]['ortalama_ms'])} ms"],
    ["%10", f"{tr(k10[0]['ortalama_ms'])} ms", f"{tr(k10[1]['ortalama_ms'])} ms"]], boyut=16, sutun=[1.4, 3, 3],
    yukseklik=Cm(1.1))
metin_kutusu(sl, Cm(23.6), Cm(7.0), Cm(8.8), Cm(6), [
    "**P = 1 − (1 − p)ⁿ**", "n: 7 → 8 segment", "%10 kayıpta ort. süre **+%6,8**"], 17)
kutu(sl, Cm(1.8), Cm(12.6), Cm(30.4), Cm(2.5), RGBColor(0xFB, 0xEE, 0xE8), TURUNCU)
metin_kutusu(sl, Cm(2.2), Cm(12.6), Cm(29.6), Cm(2.5),
             "Tarayıcı iki payı sunucu desteklemese de gönderir → hazır olmayan sunucuların kullanıcıları maliyeti "
             "korumasız öder", 18, TURUNCU, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
metin_kutusu(sl, Cm(1.8), Cm(15.5), Cm(30.4), Cm(2.5),
             "Varsayımlar: RTT 20 ms · bağımsız Bernoulli kaybı · RTO = SRTT + max(4·RTTVAR, 200 ms) · SYN RTO 1 s · "
             "her nokta 40 000 tekrar", 14, GRI)

# 18 --------------------------------------------------------------------------
sl = slayt("Tutarlılık ve küresel karşılaştırma", bolum="Alternatiflerle karşılaştırma", notlar=(
    "İki turda 129 sitenin hepsinde TLS sürümü, PQ desteği, seçilen grup ve sertifika birebir aynı çıktı. 16 sitenin IP "
    "adresi değişti ama sonuç değişmedi. Küresel olarak F5 yüzde 54 buluyor; bizdeki yüzde 24,8 daha düşük ama bizim "
    "örneklem finans ve kamu ağırlıklı. Dikkat çekici olan yalnız TLS 1.2 oranı: bizde yüzde 26,4, dünyada yüzde 10,5."))
tablo(sl, Cm(1.8), Cm(3.3), Cm(14.6), [
    ["Metrik", "1. tur", "2. tur"],
    ["PQ destek", "32", "32"], ["TLS 1.3", "95", "95"], ["CDN / destekli", "31 / 30", "31 / 30"],
    ["ServerHello (B)", "1210", "1210"], ["Medyan RTT (ms)", "19,2", "20,0"]], boyut=17, sutun=[5, 2.5, 2.5],
    yukseklik=Cm(1.15))
metin_kutusu(sl, Cm(1.8), Cm(10.8), Cm(14.6), Cm(6), [
    "• 129/129 sitede **birebir aynı** sonuç",
    "• 16 IP değişti (13'ü CDN) → sonuç değişmedi",
    "• RTT korelasyonu r = 0,85"], 18)
tablo(sl, Cm(17.6), Cm(3.3), Cm(14.6), [
    ["Gösterge", "Türkiye (bu proje)", "Küresel (F5, 2026)"],
    ["PQ destek", "%24,8", "%54"],
    ["CDN/Cloudflare hariç", "%2,0", "%22"],
    ["Yalnız TLS 1.2", "%26,4", "%10,5"]], boyut=17, sutun=[4.4, 3.6, 3.6], yukseklik=Cm(1.3))
metin_kutusu(sl, Cm(17.6), Cm(9.2), Cm(14.6), Cm(7), [
    "• Aynı örüntü: hazırlık **CDN'de yoğunlaşıyor**",
    "• Türkiye'de TLS 1.2 borcu küresel ortalamanın **2,5 katı**",
    "• Not: örneklem finans/kamu ağırlıklı"], 18)

# 19 --------------------------------------------------------------------------
sl = slayt("Projenin özgün mühendislik katkıları", bolum="Özgün katkılar", notlar=(
    "Dört katkı: Türkiye'ye özgü sektörel ölçüm, hazırlığın belirleyicisinin katmanlı istatistikle gösterilmesi, aynı "
    "veride katmanlar arası ağ maliyeti analizi ve açık araç. Bu çalışmayı bir bildiri olarak göndermeyi "
    "planlıyorum."))
for i, (b, a) in enumerate((("Türkiye'ye özgü ilk sektörel PQ-TLS ölçümü", "4 kritik sektör · 130 site · 2 tur"),
                            ("Belirleyicinin istatistikle ayrıştırılması", "CDN'e göre katmanlı permütasyon testi"),
                            ("Katmanlar arası ağ maliyeti", "TLS → TCP segmenti → Ethernet çerçevesi, ölçüm + pcap + simülasyon"),
                            ("Açık ve tekrarlanabilir araç", "Python + OpenSSL + Docker; kurumlar kendi durumunu ölçebilir"))):
    x = Cm(1.8 + (i % 2) * 15.4); y = Cm(3.4 + (i // 2) * 7.2)
    kutu(sl, x, y, Cm(14.8), Cm(6.4), ACIK, YESIL)
    metin_kutusu(sl, x + Cm(0.5), y + Cm(0.5), Cm(13.8), Cm(2.6), b, 22, YESIL, True)
    metin_kutusu(sl, x + Cm(0.5), y + Cm(3.2), Cm(13.8), Cm(3), a, 18, LACI)

# 20 --------------------------------------------------------------------------
sl = slayt("Sınırlılıklar ve geliştirme önerileri", bolum="Sınırlılıklar", notlar=(
    "Sınırlılıklar: tek ölçüm noktası, yalnız ana sayfa, süre ölçümünde süreç başlatma yükü ve simülasyon "
    "varsayımları. Simülasyonu doğrulamak için Linux'ta netem ile kontrollü bir deney planladım: yerel sunucu, MTU 1500, "
    "20 ms gecikme ve yüzde 0–10 kayıp, her koşulda 1000 el sıkışma."))
metin_kutusu(sl, Cm(1.8), Cm(3.2), Cm(14.6), Cm(1.2), "Sınırlılıklar", 22, TURUNCU, True)
metin_kutusu(sl, Cm(1.8), Cm(4.6), Cm(14.6), Cm(13), [
    "• Tek ölçüm noktası (ev interneti), 2 tur",
    "• Yalnız ana sayfa; internet bankacılığı alt alan adları yok",
    "• Süre ölçümünde ≈ 1 s süreç yükü → bayt/segment esas alındı",
    "• Simülasyon: bağımsız kayıp, ACK kaybı yok",
    "• CDN–kaynak sunucu bağlantısı görünmez"], 18)
metin_kutusu(sl, Cm(17.6), Cm(3.2), Cm(14.6), Cm(1.2), "Planlanan çalışmalar", 22, YESIL, True)
metin_kutusu(sl, Cm(17.6), Cm(4.6), Cm(14.6), Cm(13), [
    "• **netem deneyi:** yerel s_server, MTU 1500, 20 ms, %0–10 kayıp, 1000 el sıkışma",
    "• Ölçümü periyodik tekrarlayarak geçiş hızını izlemek",
    "• Alt alan adları (e-Devlet, internet bankacılığı)",
    "• Farklı ISS'ler ve mobil ağdan ölçüm",
    "• SMTP/STARTTLS ve QUIC'e uyarlama"], 18)

# 21 --------------------------------------------------------------------------
sl = slayt("Genel sonuç ve öneriler", bolum="Sonuç", notlar=(
    "Özetle: Türkiye'de kuantum sonrası geçiş, kurumların kararıyla değil CDN sağlayıcılarıyla ilerliyor. Kendi "
    "sunucusunu işleten bankalar ve kamu kurumları geride. Ağ maliyeti küçük ama yapısal. Önerilerim: önce TLS 1.3, "
    "sonra OpenSSL 3.5 ve üstü; finans için düzenleyici yol haritası; CDN–kaynak bağlantısı; ve eski ara cihazların "
    "güncellenmesi. Teşekkür ederim, sorularınızı alabilirim."))
kutu(sl, Cm(1.8), Cm(3.2), Cm(30.4), Cm(4.3), RGBColor(0xDF, 0xF0, 0xE8), YESIL)
metin_kutusu(sl, Cm(2.3), Cm(3.4), Cm(29.4), Cm(4.0), [
    "Türkiye'de kuantum sonrası geçiş **kurumsal kararla değil, CDN sağlayıcılarıyla** ilerliyor.",
    "Kendi sunucusunu işleten **bankalar ve kamu** geride; ağ maliyeti **küçük ama yapısal** (+2,3 KB, 2 segment)."],
             20, LACI, dikey=MSO_ANCHOR.MIDDLE)
for i, (b, a) in enumerate((("1", "Kendi sunucusu olanlar: önce TLS 1.3, sonra OpenSSL 3.5+ ile X25519MLKEM768"),
                            ("2", "Finans için düzenleyici yol haritası ve takvim"),
                            ("3", "CDN kullananlar: CDN–kaynak sunucu bağlantısını da PQ'ya taşımalı"),
                            ("4", "Ağ yöneticileri: parçalı ClientHello'yu işlemeyen ara cihazları güncellemeli"))):
    y = Cm(8.3 + i * 2.15)
    kutu(sl, Cm(1.8), y, Cm(1.6), Cm(1.6), YESIL, sekil=MSO_SHAPE.OVAL)
    metin_kutusu(sl, Cm(1.8), y, Cm(1.6), Cm(1.6), b, 20, BEYAZ, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    metin_kutusu(sl, Cm(4.0), y, Cm(28), Cm(1.6), a, 19, LACI, dikey=MSO_ANCHOR.MIDDLE)
metin_kutusu(sl, Cm(1.8), Cm(17.0), Cm(24), Cm(1), "Teşekkürler · Sorular?", 20, YESIL, True)

# 22 --------------------------------------------------------------------------
sl = slayt("Kaynakça (seçilmiş)", bolum="Kaynakça", notlar="Tam kaynakça APA 7 formatında raporda yer almaktadır.")
metin_kutusu(sl, Cm(1.8), Cm(3.0), Cm(30.4), Cm(15), [
    "Dubey, V. M., & Varshney, G. (2026). Measurement study of post-quantum readiness of Internet: 2026. arXiv:2606.16473.",
    "F5 Labs. (2026). 2026 state of PQC on the web. F5.",
    "Kwiatkowski, K., Kampanakis, P., Westerbaan, B. E., & Stebila, D. (2026). Post-quantum hybrid ECDHE-MLKEM key "
    "agreement for TLSv1.3 (draft-ietf-tls-ecdhe-mlkem-05). IETF.",
    "Mosca, M. (2018). Cybersecurity in an era with quantum computers: Will we be ready? IEEE Security & Privacy, 16(5), 38–41.",
    "National Institute of Standards and Technology. (2024). Module-lattice-based key-encapsulation mechanism standard (FIPS 203).",
    "Paquin, C., Stebila, D., & Tamvada, G. (2020). Benchmarking post-quantum cryptography in TLS. PQCrypto 2020, LNCS 12100, 72–91.",
    "Paxson, V., Allman, M., Chu, J., & Sargent, M. (2011). Computing TCP's retransmission timer (RFC 6298). IETF.",
    "Rescorla, E. (2018). The Transport Layer Security (TLS) protocol version 1.3 (RFC 8446). IETF.",
    "Shor, P. W. (1997). Polynomial-time algorithms for prime factorization and discrete logarithms on a quantum "
    "computer. SIAM Journal on Computing, 26(5), 1484–1509."], 13.5, LACI, aralik=5)

prs.core_properties.title = "Kuantum Sonrası TLS Hazırlığı"
prs.core_properties.author = "Rümeysa Betül Özyurt"
prs.save(CIKTI)
print("Kaydedildi:", CIKTI, "| slayt:", sayac[0])
