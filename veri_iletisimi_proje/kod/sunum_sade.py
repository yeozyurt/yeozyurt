#!/usr/bin/env python3
"""Sadeleştirilmiş sunum: her slaytta tek mesaj, az metin, büyük sayılar, yerel (düzenlenebilir)
grafikler. Tüm sayılar analiz/ek_analiz.json'dan okunur; yeni veriyle yeniden üretilebilir."""
import json
import os
import sys

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Cm, Pt

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
R = json.load(open(os.path.join(KOK, "analiz", "ek_analiz.json"), encoding="utf-8"))
CIKTI = sys.argv[1] if len(sys.argv) > 1 else os.path.join(KOK, "Rumeysa_Betul_Ozyurt_Veri_Iletisimi_Proje_Sunumu.pptx")

LACI, YESIL, MAVI = RGBColor(0x1F, 0x2A, 0x44), RGBColor(0x1B, 0x7F, 0x5A), RGBColor(0x4A, 0x78, 0xC2)
TURUNCU, GRI, ACIK = RGBColor(0xC7, 0x5B, 0x39), RGBColor(0x6B, 0x72, 0x7C), RGBColor(0xF2, 0xF4, 0xF7)
BEYAZ, ACIKYESIL = RGBColor(0xFF, 0xFF, 0xFF), RGBColor(0xE3, 0xF2, 0xEB)
FONT = "Calibri"

prs = Presentation()
prs.slide_width, prs.slide_height = Cm(33.867), Cm(19.05)
W, H = prs.slide_width, prs.slide_height
no = [0]


def tr(x, b=1):
    return f"{x:.{b}f}".replace(".", ",")


def yazi(sl, x, y, w, h, metin, boyut=24, renk=LACI, kalin=False, hiza=PP_ALIGN.LEFT, dikey=MSO_ANCHOR.TOP):
    tf = sl.shapes.add_textbox(x, y, w, h).text_frame
    tf.word_wrap = True; tf.vertical_anchor = dikey
    for i, satir in enumerate(metin if isinstance(metin, list) else [metin]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = hiza; p.space_after = Pt(10)
        for k, parca in enumerate(satir.split("**")):
            if parca:
                r = p.add_run(); r.text = parca
                r.font.size, r.font.name, r.font.color.rgb = Pt(boyut), FONT, renk
                r.font.bold = kalin or k % 2 == 1
    return tf


def sekil(sl, tur, x, y, w, h, renk, cizgi=None):
    s = sl.shapes.add_shape(tur, x, y, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = renk
    if cizgi:
        s.line.color.rgb = cizgi; s.line.width = Pt(2)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    return s


def slayt(baslik, notlar, koyu=False):
    no[0] += 1
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    if koyu:
        sekil(sl, MSO_SHAPE.RECTANGLE, 0, 0, W, H, LACI)
    else:
        sekil(sl, MSO_SHAPE.RECTANGLE, 0, 0, Cm(0.5), H, YESIL)
        yazi(sl, Cm(1.6), Cm(0.9), Cm(31), Cm(2.2), baslik, 34, LACI, True, dikey=MSO_ANCHOR.MIDDLE)
        yazi(sl, Cm(30), Cm(17.9), Cm(3.3), Cm(0.9), str(no[0]), 12, GRI, hiza=PP_ALIGN.RIGHT)
    sl.notes_slide.notes_text_frame.text = notlar
    return sl


def buyuk(sl, x, y, w, sayi, aciklama, renk=YESIL, boyut=66):
    yazi(sl, x, y, w, Cm(3.2), sayi, boyut, renk, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    yazi(sl, x, y + Cm(3.2), w, Cm(2.2), aciklama, 22, GRI, hiza=PP_ALIGN.CENTER)


def kutu_metin(sl, x, y, w, h, metin, renk, zemin, boyut=24):
    sekil(sl, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, zemin, renk).adjustments[0] = 0.12
    yazi(sl, x + Cm(0.3), y, w - Cm(0.6), h, metin, boyut, renk, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)


def ok(sl, x, y, w=Cm(1.6), h=Cm(1.4)):
    sekil(sl, MSO_SHAPE.RIGHT_ARROW, x, y, w, h, GRI)


def kaynak_notu(sl, metin):
    yazi(sl, Cm(1.6), Cm(17.6), Cm(27), Cm(1), metin, 13, GRI)


S = {o["sektor"]: o for o in R["sektor"]}
T = S["TÜMÜ"]
sektorler = [o for o in R["sektor"] if o["sektor"] != "TÜMÜ"]
cdn_k, cdn_n = map(int, R["cdn_fisher"]["cdn"].split("/"))
oz_k, oz_n = map(int, R["cdn_fisher"]["kendi"].split("/"))
ag = R["ag"]
sim = {(x["senaryo"], x["kayip"]): x for x in R["simulasyon"]["rtt20"]}
n_site = T["n"]

# 1 Başlık ----------------------------------------------------------------------
sl = slayt("", "Merhaba. Projem, Türkiye'deki önemli web sitelerinin kuantum bilgisayar tehdidine karşı ne kadar "
              "hazır olduğunu ve bu geçişin internet trafiğine maliyetini ölçüyor.", koyu=True)
yazi(sl, Cm(2.2), Cm(2.6), Cm(30), Cm(1.2), "VERİ İLETİŞİMİ · DÖNEM PROJESİ", 18, RGBColor(0x9F, 0xD8, 0xC0), True)
yazi(sl, Cm(2.2), Cm(4.6), Cm(30), Cm(5.5), ["Türk web siteleri", "kuantum bilgisayarlara hazır mı?"], 50,
     BEYAZ, True)
yazi(sl, Cm(2.2), Cm(10.4), Cm(30), Cm(1.5), "Kuantum sonrası TLS: sektörel ölçüm ve ağ maliyeti", 24,
     RGBColor(0xC9, 0xD3, 0xE6))
yazi(sl, Cm(2.2), Cm(14.2), Cm(30), Cm(3), ["**Rümeysa Betül Özyurt**",
                                            "Prof. Dr. Agah Tuğrul Korucu · İstanbul Ticaret Üniversitesi"], 20, BEYAZ)

# 2 Problem ---------------------------------------------------------------------
sl = slayt("Problem: Bugün kaydedilen trafik, yarın çözülebilir",
           "HTTPS bağlantılarının anahtarı bugün eliptik eğri yöntemleriyle kuruluyor. Saldırgan bu trafiği bugün "
           "kaydedip, yeterince güçlü bir kuantum bilgisayar çıktığında çözebilir. Buna 'şimdi topla, sonra çöz' "
           "deniyor. Banka ve sağlık verisi yıllarca gizli kalmalı, bu yüzden risk bugünden başlıyor.")
for i, (b, a, r) in enumerate((("1. Kaydet", "Saldırgan şifreli\ntrafiği bugün saklar", MAVI),
                               ("2. Bekle", "Banka, sağlık verisi\nyıllarca değerli", GRI),
                               ("3. Çöz", "Kuantum bilgisayar\nanahtarı kırar", TURUNCU))):
    x = Cm(1.8 + i * 10.6)
    sekil(sl, MSO_SHAPE.ROUNDED_RECTANGLE, x, Cm(4.2), Cm(8.8), Cm(6.2), ACIK, r).adjustments[0] = 0.1
    yazi(sl, x, Cm(4.6), Cm(8.8), Cm(1.6), b, 32, r, True, PP_ALIGN.CENTER)
    yazi(sl, x, Cm(6.6), Cm(8.8), Cm(3.5), a.split("\n"), 22, LACI, hiza=PP_ALIGN.CENTER)
    if i < 2:
        ok(sl, x + Cm(9.0), Cm(6.6))
kutu_metin(sl, Cm(1.8), Cm(12.2), Cm(30.2), Cm(3.4),
           "Çözüm hazır: NIST standardı ML-KEM ile hibrit anahtar değişimi (X25519MLKEM768)", YESIL, ACIKYESIL, 26)
kaynak_notu(sl, "Shor (1997) · Mosca (2018) · NIST FIPS 203 (2024)")

# 3 Sorular ---------------------------------------------------------------------
sl = slayt("İki araştırma sorusu",
           "Tarayıcılar yeni yöntemi zaten kullanıyor; asıl soru sunucuların kabul edip etmediği. İkinci soru veri "
           "iletişimi tarafı: daha büyük anahtarlar ağda neye mal oluyor?")
for i, (n, s_, a) in enumerate((("1", "Türkiye'deki siteler hazır mı?", "Hangi sektör, neden geride?"),
                                ("2", "Ağa maliyeti ne?", "Bayt, TCP paketi ve gecikme"))):
    y = Cm(4.0 + i * 6.4)
    sekil(sl, MSO_SHAPE.OVAL, Cm(2.0), y, Cm(4.2), Cm(4.2), YESIL)
    yazi(sl, Cm(2.0), y, Cm(4.2), Cm(4.2), n, 54, BEYAZ, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    yazi(sl, Cm(7.6), y + Cm(0.4), Cm(24), Cm(2), s_, 36, LACI, True)
    yazi(sl, Cm(7.6), y + Cm(2.4), Cm(24), Cm(1.6), a, 26, GRI)

# 4 Yöntem ----------------------------------------------------------------------
sl = slayt("Nasıl ölçtüm?",
           f"Kendi dizüstü bilgisayarımdan, ev internetimle, {n_site} siteye normal bir ziyaretçi gibi bağlandım. "
           "Python ile yazdığım araç OpenSSL'i çalıştırıp her siteye beş farklı bağlantı deniyor: tarayıcı gibi, "
           "sadece eski yöntemle, sadece yeni yöntemle, TLS 1.2 ile ve bir HTTP isteği. Wireshark ile paketleri "
           "yakalayıp sonuçları doğruladım. Ölçümü iki kez tekrarladım, sonuçlar birebir aynı çıktı.")
for i, (b, a, r) in enumerate((("Dizüstü bilgisayar", "Python + OpenSSL\nWireshark", MAVI),
                               ("Ev interneti", "TCP / IP\nRTT ≈ 20 ms", GRI),
                               (f"{n_site} web sitesi", "CDN arkasında\nveya kendi sunucusu", YESIL))):
    x = Cm(1.8 + i * 10.6)
    sekil(sl, MSO_SHAPE.ROUNDED_RECTANGLE, x, Cm(4.0), Cm(8.8), Cm(5.4), ACIK, r).adjustments[0] = 0.1
    yazi(sl, x, Cm(4.4), Cm(8.8), Cm(1.6), b, 28, r, True, PP_ALIGN.CENTER)
    yazi(sl, x, Cm(6.2), Cm(8.8), Cm(3), a.split("\n"), 22, LACI, hiza=PP_ALIGN.CENTER)
    if i < 2:
        ok(sl, x + Cm(9.0), Cm(6.0))
yazi(sl, Cm(1.8), Cm(10.6), Cm(30), Cm(6.5), [
    "• Her siteye **5 bağlantı**: tarayıcı gibi · yalnız klasik · yalnız hibrit · TLS 1.2 · HTTP",
    "• Paket yakalama ile doğrulama (**Wireshark**)",
    "• **İki tur** ölçüm, etik: tarama yok, siteler arası bekleme"], 24)

# 5 Ne değişiyor ----------------------------------------------------------------
sl = slayt("Yeni anahtar, ilk mesajı iki pakete böler",
           "TLS bağlantısındaki ilk mesaj ClientHello. Eski yöntemde 232 bayt ve tek pakete sığıyor. Tarayıcı yeni "
           "ve eski anahtarı birlikte gönderdiği için mesaj 1534 bayta çıkıyor. Bir TCP paketi en fazla 1460 bayt "
           "taşıyabildiği için mesaj iki pakete bölünüyor. Bu veri iletişimi açısından önemli bir değişiklik.")
olcek = Cm(19) / 1600
for i, (ad, b, r) in enumerate((("Eski (klasik)", 232, MAVI), ("Yeni (hibrit, tarayıcı)", int(ag["tarayici_ch_medyan"]), YESIL))):
    y = Cm(4.6 + i * 4.6)
    yazi(sl, Cm(1.8), y, Cm(8), Cm(2.4), ad, 24, LACI, True, dikey=MSO_ANCHOR.MIDDLE)
    sekil(sl, MSO_SHAPE.RECTANGLE, Cm(10.2), y + Cm(0.3), int(olcek * b), Cm(1.8), r)
    yazi(sl, Cm(10.4) + int(olcek * b), y, Cm(5), Cm(2.4), f"{b} B", 26, r, True, dikey=MSO_ANCHOR.MIDDLE)
sinir_x = Cm(10.2) + int(olcek * 1460)
cz = sl.shapes.add_connector(1, sinir_x, Cm(4.0), sinir_x, Cm(11.6))
cz.line.color.rgb = TURUNCU; cz.line.width = Pt(3); cz.line.dash_style = 4
yazi(sl, sinir_x - Cm(4), Cm(11.6), Cm(8), Cm(1.2), "1 TCP paketi sınırı (1460 B)", 18, TURUNCU, True, PP_ALIGN.CENTER)
for i, (s_, a, r) in enumerate((("1 → 2", "TCP paketi", TURUNCU), (f"+{tr((ag['yazilan_fark'] + ag['okunan_fark']) / 1000)} KB",
                                                                 "her bağlantıda ek veri", YESIL))):
    buyuk(sl, Cm(4 + i * 14), Cm(13.0), Cm(12), s_, a, r, 44)

# 6 Bulgu: genel + sektör grafiği -------------------------------------------------
sl = slayt(f"Sitelerin sadece %{tr(T['pq'])}'i hazır",
           f"Ölçülen {n_site} sitenin %{tr(T['pq'])}'i yeni yöntemi destekliyor. Sektörler arasında çok büyük fark var: "
           "e-ticaret önde, bankalar en geride.")
cd = CategoryChartData()
cd.categories = [o["sektor"] for o in sektorler]
cd.add_series("Kuantum sonrası hazır (%)", [o["pq"] for o in sektorler])
gf = sl.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Cm(1.6), Cm(3.4), Cm(20), Cm(14), cd).chart
gf.has_legend = False
pl = gf.plots[0]; pl.gap_width = 60; pl.has_data_labels = True
pl.data_labels.number_format = '0"%"'; pl.data_labels.number_format_is_linked = False
pl.data_labels.font.size = Pt(20); pl.data_labels.font.bold = True; pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
pl.series[0].format.fill.solid(); pl.series[0].format.fill.fore_color.rgb = YESIL
gf.category_axis.tick_labels.font.size = Pt(20); gf.category_axis.reverse_order = True
gf.value_axis.maximum_scale = 100; gf.value_axis.visible = False; gf.value_axis.has_major_gridlines = False
buyuk(sl, Cm(22.5), Cm(4.5), Cm(10), f"%{tr(T['pq'])}", f"hazır ({T['pq_k']}/{T['n']} site)", YESIL, 60)
buyuk(sl, Cm(22.5), Cm(10.5), Cm(10), f"%{tr(T['tls12'])}", "hâlâ eski TLS 1.2", TURUNCU, 60)

# 7 Bulgu: CDN ----------------------------------------------------------------
sl = slayt("Asıl fark: sitenin CDN kullanıp kullanmaması",
           f"En önemli bulgu bu. Cloudflare gibi bir içerik dağıtım ağı, yani CDN arkasındaki {cdn_n} sitenin {cdn_k}'u "
           f"hazır; kendi sunucusunu işleten {oz_n} siteden sadece {oz_k}'si hazır. CDN kullanımını sabit tuttuğumda "
           "sektörler arasındaki fark kayboluyor. Yani bankalar banka oldukları için değil, kendi sunucularını "
           "kullandıkları için geride. Geçiş kurumların kararıyla değil, altyapı sağlayıcıları sayesinde ilerliyor.")
buyuk(sl, Cm(2), Cm(4.6), Cm(13.5), f"%{tr(100 * cdn_k / cdn_n)}", f"CDN arkasındaki siteler ({cdn_k}/{cdn_n})", YESIL, 88)
yazi(sl, Cm(15.5), Cm(5.4), Cm(3), Cm(3), "vs", 36, GRI, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
buyuk(sl, Cm(18.5), Cm(4.6), Cm(13.5), f"%{tr(100 * oz_k / oz_n)}", f"kendi sunucusu olanlar ({oz_k}/{oz_n})", TURUNCU, 88)
kutu_metin(sl, Cm(1.8), Cm(12.4), Cm(30.2), Cm(3.6),
           "CDN sabit tutulunca sektör farkı kayboluyor → belirleyici olan altyapı", LACI, ACIK, 26)
kaynak_notu(sl, f"Fisher kesin testi p < 10⁻²⁵ · CDN'e göre katmanlı permütasyon testi p = "
                f"{tr(R['sektor_permutasyon_cdn_katmanli']['p'], 2)}")

# 8 Bankalar --------------------------------------------------------------------
B = S["Banka"]
sl = slayt("En hassas veri, en geride: bankalar",
           "Şimdi topla sonra çöz tehdidine en çok maruz kalan veri finansal veri. Ama bankaların hiçbiri hazır değil "
           "ve yarısından fazlası daha bir önceki adım olan TLS 1.3'e bile geçmemiş.")
buyuk(sl, Cm(2), Cm(5.0), Cm(14), f"{B['pq_k']} / {B['n']}", "banka hazır", TURUNCU, 96)
buyuk(sl, Cm(17.5), Cm(5.0), Cm(14), f"%{tr(B['tls12'])}", "hâlâ yalnız TLS 1.2", TURUNCU, 96)
kutu_metin(sl, Cm(1.8), Cm(13.0), Cm(30.2), Cm(3.0), "Önce TLS 1.3, sonra kuantum sonrası geçiş gerekiyor",
           TURUNCU, RGBColor(0xFB, 0xEE, 0xE8), 26)

# 9 Ağ maliyeti -----------------------------------------------------------------
sl = slayt("Ağ maliyeti: küçük ama yapısal",
           "Yeni yöntem her bağlantıda yaklaşık 2,3 kilobayt ek veri getiriyor. Bu bir web sayfasının binde biri "
           "kadar. Normal ev internetinde ölçtüğüm sürelerde anlamlı bir fark çıkmadı. Ama ilk mesaj artık iki "
           "pakete bölünüyor; bu kayıplı ağlarda önemli, bir sonraki slayt bunu gösteriyor.")
for i, (s_, a, r) in enumerate((("+2,3 KB", "her bağlantıda\nek veri", YESIL),
                                ("%0,1", "2 MB'lık bir web\nsayfasına oranı", MAVI),
                                ("≈ 0 ms", "kayıpsız ağda\nölçülen gecikme farkı", GRI))):
    x = Cm(1.8 + i * 10.4)
    sekil(sl, MSO_SHAPE.ROUNDED_RECTANGLE, x, Cm(4.2), Cm(9.6), Cm(8.2), ACIK).adjustments[0] = 0.08
    buyuk(sl, x, Cm(5.0), Cm(9.6), s_, a.split("\n"), r, 54)
kaynak_notu(sl, f"Ölçüm: {ag['n']} hazır sitede klasik ve hibrit el sıkışma karşılaştırması · Wireshark ile doğrulandı "
                "(369 B → 1591 B)")

# 10 Simülasyon -----------------------------------------------------------------
sl = slayt("Kayıplı ağda ikinci paketin bedeli",
           "Gerçek internette paket kaybını kontrol edemediğim için ölçtüğüm paket boyutlarıyla bir simülasyon "
           "yaptım. Bu bir ölçüm değil, simülasyon. Paket kaybı arttıkça yeni yöntem biraz daha yavaş kalıyor: yüzde "
           "10 kayıpta ortalama yüzde 7 kadar. Önemli nokta: tarayıcı, site desteklemese bile büyük mesajı gönderiyor. "
           "Yani hazır olmayan sitelerin kullanıcıları bu bedeli koruma almadan ödüyor.")
kayiplar = [0.0, 0.01, 0.02, 0.05, 0.10]
cd = CategoryChartData()
cd.categories = [f"%{int(100 * k)}" for k in kayiplar]
cd.add_series("Eski (klasik)", [sim[("Klasik", k)]["ortalama_ms"] for k in kayiplar])
cd.add_series("Yeni (hibrit)", [sim[("Hibrit (tarayıcı)", k)]["ortalama_ms"] for k in kayiplar])
gf = sl.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Cm(1.6), Cm(3.4), Cm(19), Cm(13.6), cd).chart
gf.has_legend = True; gf.legend.position = XL_LEGEND_POSITION.TOP; gf.legend.include_in_layout = False
gf.legend.font.size = Pt(18)
for s_, r in zip(gf.plots[0].series, (MAVI, YESIL)):
    s_.format.line.color.rgb = r; s_.format.line.width = Pt(3.5); s_.smooth = False
    s_.marker.format.fill.solid(); s_.marker.format.fill.fore_color.rgb = r
gf.category_axis.tick_labels.font.size = Pt(16); gf.value_axis.tick_labels.font.size = Pt(16)
gf.category_axis.has_title = True; gf.category_axis.axis_title.text_frame.text = "Paket kaybı"
gf.category_axis.axis_title.text_frame.paragraphs[0].runs[0].font.size = Pt(16)
gf.value_axis.has_title = True; gf.value_axis.axis_title.text_frame.text = "Ortalama süre (ms)"
gf.value_axis.axis_title.text_frame.paragraphs[0].runs[0].font.size = Pt(16)
k10 = (sim[("Klasik", 0.10)]["ortalama_ms"], sim[("Hibrit (tarayıcı)", 0.10)]["ortalama_ms"])
buyuk(sl, Cm(21.5), Cm(4.0), Cm(11), f"+%{tr(100 * (k10[1] / k10[0] - 1), 0)}", "%10 kayıpta\nortalama süre".split("\n"),
      YESIL, 60)
kutu_metin(sl, Cm(21.5), Cm(11.0), Cm(10.8), Cm(4.2), "Hazır olmayan sitenin kullanıcısı da bu bedeli öder",
           TURUNCU, RGBColor(0xFB, 0xEE, 0xE8), 20)
sekil(sl, MSO_SHAPE.ROUNDED_RECTANGLE, Cm(24.5), Cm(1.2), Cm(7.8), Cm(1.4), TURUNCU)
yazi(sl, Cm(24.5), Cm(1.2), Cm(7.8), Cm(1.4), "SİMÜLASYON", 18, BEYAZ, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)

# 11 Dünya ile karşılaştırma ----------------------------------------------------
sl = slayt("Dünyada durum ne?",
           "F5 Labs'in 2026'da en popüler 1 milyon sitede yaptığı ölçümde oran yüzde 54. Ama Cloudflare dışındaki "
           "sitelerde yüzde 22'ye düşüyor; yani dünyada da aynı örüntü var. Türkiye'de dikkat çeken, hâlâ TLS 1.2 "
           "kullanan site oranının dünya ortalamasının yaklaşık 2,5 katı olması.")
for i, (b, tr_, dn) in enumerate((("Hazır siteler", f"%{tr(T['pq'])}", "%54"),
                                  ("Yalnız TLS 1.2", f"%{tr(T['tls12'])}", "%10,5"))):
    y = Cm(4.2 + i * 6.2)
    yazi(sl, Cm(1.8), y, Cm(9), Cm(4), b, 28, LACI, True, dikey=MSO_ANCHOR.MIDDLE)
    buyuk(sl, Cm(11), y - Cm(0.6), Cm(10), tr_, "Türkiye (bu proje)", TURUNCU if i else YESIL, 56)
    buyuk(sl, Cm(21.8), y - Cm(0.6), Cm(10), dn, "Dünya (F5 Labs, 2026)", GRI, 56)
kaynak_notu(sl, "F5 Labs (2026): ilk 1 milyon site; Cloudflare hariç hazırlık %22")

# 12 Öneriler -------------------------------------------------------------------
sl = slayt("Ne yapılmalı?",
           "Dört öneri: kendi sunucusu olanlar önce TLS 1.3'e, sonra OpenSSL 3.5 ve üstüne geçmeli. Finans için "
           "düzenleyici bir takvim gerekli. CDN kullananlar CDN ile kendi sunucuları arasını da korumalı. Ağ "
           "yöneticileri iki pakete bölünen ilk mesajı işleyemeyen eski cihazları güncellemeli.")
for i, (b, a) in enumerate((("Kurumlar", "Önce TLS 1.3, sonra OpenSSL 3.5+"),
                            ("Düzenleyiciler", "Finans için geçiş takvimi"),
                            ("CDN kullananlar", "CDN–sunucu arasını da koru"),
                            ("Ağ yöneticileri", "Eski güvenlik cihazlarını güncelle"))):
    x = Cm(1.8 + (i % 2) * 15.3); y = Cm(4.0 + (i // 2) * 6.6)
    sekil(sl, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Cm(14.8), Cm(5.8), ACIK, YESIL).adjustments[0] = 0.08
    yazi(sl, x, y + Cm(0.7), Cm(14.8), Cm(1.8), b, 30, YESIL, True, PP_ALIGN.CENTER)
    yazi(sl, x, y + Cm(2.8), Cm(14.8), Cm(2.4), a, 24, LACI, hiza=PP_ALIGN.CENTER)

# 13 Sonuç ----------------------------------------------------------------------
sl = slayt("", "Özetle: Türkiye'de geçiş başladı ama kurumların kararıyla değil, altyapı sağlayıcıları sayesinde. "
               "Bankalar ve kamu geride. Ağ maliyeti küçük ama yapısal. Teşekkür ederim, sorularınızı alabilirim.",
           koyu=True)
yazi(sl, Cm(2.2), Cm(2.4), Cm(29), Cm(1.4), "SONUÇ", 20, RGBColor(0x9F, 0xD8, 0xC0), True)
yazi(sl, Cm(2.2), Cm(4.2), Cm(29.5), Cm(9), [
    "Geçiş başladı, ama **kurumların kararıyla değil, CDN'ler sayesinde**.",
    "**Bankalar ve kamu** en hassas veriye sahip, ama en geride.",
    "Ağ maliyeti **küçük ama yapısal**: +2,3 KB, ilk mesaj 2 paket."], 30, BEYAZ)
yazi(sl, Cm(2.2), Cm(14.6), Cm(29), Cm(2), "Teşekkürler · Sorular?", 36, RGBColor(0x9F, 0xD8, 0xC0), True)

# 14 Kaynakça -------------------------------------------------------------------
sl = slayt("Kaynakça", "Tam kaynakça raporda APA 7 formatında yer almaktadır.")
yazi(sl, Cm(1.8), Cm(3.6), Cm(30.4), Cm(14), [
    "Dubey, V. M., & Varshney, G. (2026). Measurement study of post-quantum readiness of Internet: 2026. arXiv:2606.16473.",
    "F5 Labs. (2026). 2026 state of PQC on the web.",
    "Kwiatkowski, K., Kampanakis, P., Westerbaan, B. E., & Stebila, D. (2026). Post-quantum hybrid ECDHE-MLKEM key "
    "agreement for TLSv1.3. IETF Internet-Draft.",
    "Mosca, M. (2018). Cybersecurity in an era with quantum computers. IEEE Security & Privacy, 16(5), 38–41.",
    "NIST. (2024). Module-lattice-based key-encapsulation mechanism standard (FIPS 203).",
    "Paquin, C., Stebila, D., & Tamvada, G. (2020). Benchmarking post-quantum cryptography in TLS. PQCrypto 2020.",
    "Rescorla, E. (2018). The TLS protocol version 1.3 (RFC 8446). IETF.",
    "Shor, P. W. (1997). Polynomial-time algorithms for prime factorization and discrete logarithms on a quantum "
    "computer. SIAM Journal on Computing, 26(5), 1484–1509."], 16)

prs.core_properties.title = "Kuantum Sonrası TLS Hazırlığı"
prs.core_properties.author = "Rümeysa Betül Özyurt"
prs.save(CIKTI)
print("Kaydedildi:", CIKTI, "| slayt:", no[0])
