#!/usr/bin/env python3
"""Yüksek kaliteli proje sunumu (16:9, .pptx).
- Diyagramlar PowerPoint şekilleriyle çizilir (net, düzenlenebilir); grafikler yerel PowerPoint grafikleridir.
- Tüm sayılar analiz/ek_analiz.json'dan okunur → yeni ölçümle yeniden üretilebilir.
- Her slaytta konuşmacı notu bulunur."""
import json
import os
import sys

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Cm, Emu, Pt
from lxml import etree

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
R = json.load(open(os.path.join(KOK, "analiz", "ek_analiz.json"), encoding="utf-8"))
CIKTI = sys.argv[1] if len(sys.argv) > 1 else os.path.join(KOK, "Rumeysa_Betul_Ozyurt_Veri_Iletisimi_Proje_Sunumu.pptx")

# --- Tasarım dili -------------------------------------------------------------------
LACI = RGBColor(0x14, 0x21, 0x3D)      # ana koyu
LACI2 = RGBColor(0x22, 0x33, 0x5A)
YESIL = RGBColor(0x12, 0x8C, 0x6A)     # kuantum sonrası / olumlu
YESIL_A = RGBColor(0xE2, 0xF3, 0xEC)
MAVI = RGBColor(0x3A, 0x6E, 0xC4)      # klasik
MAVI_A = RGBColor(0xE4, 0xEC, 0xF8)
MERCAN = RGBColor(0xD9, 0x5D, 0x39)    # risk / TLS 1.2
MERCAN_A = RGBColor(0xFB, 0xE9, 0xE2)
AMBER = RGBColor(0xE8, 0xA3, 0x3D)     # vurgu
AMBER_A = RGBColor(0xFD, 0xF3, 0xE1)
GRI = RGBColor(0x5E, 0x67, 0x74)
GRI_A = RGBColor(0xEE, 0xF1, 0xF5)
CIZGI = RGBColor(0xD5, 0xDB, 0xE3)
ZEMIN = RGBColor(0xF7, 0xF9, 0xFC)
BEYAZ = RGBColor(0xFF, 0xFF, 0xFF)
NANE = RGBColor(0x9F, 0xE0, 0xC8)
F_GOVDE, F_BASLIK = "Segoe UI", "Segoe UI Semibold"

prs = Presentation()
prs.slide_width, prs.slide_height = Cm(33.867), Cm(19.05)
W, H = prs.slide_width, prs.slide_height
no = [0]


def tr(x, b=1):
    return f"{x:.{b}f}".replace(".", ",")


# --- Temel çizim yardımcıları ----------------------------------------------------------
def yazi(sl, x, y, w, h, metin, boyut=18, renk=LACI, kalin=False, hiza=PP_ALIGN.LEFT, dikey=MSO_ANCHOR.TOP,
         font=None, aralik=6, satir=1.0):
    tb = sl.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = dikey
    tf.margin_left = tf.margin_right = Cm(0.1)
    tf.margin_top = tf.margin_bottom = Cm(0.05)
    for i, s in enumerate(metin if isinstance(metin, list) else [metin]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = hiza
        p.space_after = Pt(aralik)
        p.line_spacing = satir
        for k, parca in enumerate(s.split("**")):
            if not parca:
                continue
            r = p.add_run()
            r.text = parca
            r.font.size = Pt(boyut)
            r.font.color.rgb = renk
            kal = kalin or k % 2 == 1
            r.font.name = font or (F_BASLIK if kal else F_GOVDE)
            r.font.bold = kal and font is None and False
    return tb


def sekil(sl, tur, x, y, w, h, dolgu=BEYAZ, cizgi=None, kalinlik=1.0, yuvarlak=0.12):
    s = sl.shapes.add_shape(tur, x, y, w, h)
    if dolgu is None:
        s.fill.background()
    else:
        s.fill.solid(); s.fill.fore_color.rgb = dolgu
    if cizgi is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = cizgi; s.line.width = Pt(kalinlik)
    s.shadow.inherit = False
    if tur == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = yuvarlak
    return s


def kart(sl, x, y, w, h, dolgu=BEYAZ, cizgi=CIZGI, yuvarlak=0.06, kalinlik=1.0):
    return sekil(sl, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, dolgu, cizgi, kalinlik, yuvarlak)


def ok(sl, x1, y1, x2, y2, renk=GRI, kalinlik=2.0, kesikli=False, iki_yon=False, uc=True):
    c = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    c.line.color.rgb = renk
    c.line.width = Pt(kalinlik)
    ln = c.line._get_or_add_ln()
    if kesikli:
        d = etree.SubElement(ln, qn("a:prstDash")); d.set("val", "dash")
    if uc:
        t = etree.SubElement(ln, qn("a:tailEnd")); t.set("type", "triangle"); t.set("w", "med"); t.set("len", "med")
    if iki_yon:
        h_ = etree.SubElement(ln, qn("a:headEnd")); h_.set("type", "triangle"); h_.set("w", "med"); h_.set("len", "med")
    return c


def rozet(sl, x, y, metin, renk, zemin=None, boyut=12, w=None):
    w = w or Cm(0.32 * len(metin) + 0.9)
    s = sekil(sl, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, Cm(0.85), zemin or renk, None, yuvarlak=0.5)
    yazi(sl, x, y, w, Cm(0.85), metin, boyut, BEYAZ if zemin is None else renk, True, PP_ALIGN.CENTER,
         MSO_ANCHOR.MIDDLE)
    return w


def ikon(sl, x, y, d, renk, sembol, boyut=None, zemin=None):
    sekil(sl, MSO_SHAPE.OVAL, x, y, d, d, zemin or renk)
    yazi(sl, x, y, d, d, sembol, boyut or int(d / Cm(1) * 11), BEYAZ if zemin is None else renk, True,
         PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)


def buyuk_sayi(sl, x, y, w, sayi, aciklama, renk=YESIL, boyut=48, kart_=True, h=Cm(4.2)):
    if kart_:
        kart(sl, x, y, w, h)
        sekil(sl, MSO_SHAPE.RECTANGLE, x, y + Cm(0.5), Cm(0.18), h - Cm(1.0), renk)
    yazi(sl, x + Cm(0.5), y + Cm(0.35), w - Cm(0.8), Cm(2.3), sayi, boyut, renk, True, dikey=MSO_ANCHOR.MIDDLE)
    yazi(sl, x + Cm(0.55), y + Cm(2.6), w - Cm(0.8), h - Cm(2.7), aciklama, 14, GRI, satir=0.95)


def slayt(baslik, notlar, bolum="", alt=None, zemin=ZEMIN):
    no[0] += 1
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    bg = sl.background.fill; bg.solid(); bg.fore_color.rgb = zemin
    if bolum:
        yazi(sl, Cm(1.6), Cm(0.75), Cm(20), Cm(0.8), bolum.upper(), 11, YESIL, True, font=F_BASLIK)
    yazi(sl, Cm(1.6), Cm(1.35), Cm(30.5), Cm(1.7), baslik, 28, LACI, True, dikey=MSO_ANCHOR.MIDDLE)
    if alt:
        yazi(sl, Cm(1.6), Cm(3.0), Cm(30.5), Cm(1.0), alt, 15, GRI)
    sekil(sl, MSO_SHAPE.RECTANGLE, Cm(1.65), Cm(3.0) if not alt else Cm(4.0), Cm(1.6), Cm(0.09), YESIL)
    # alt bilgi
    sekil(sl, MSO_SHAPE.RECTANGLE, 0, H - Cm(0.9), W, Cm(0.9), BEYAZ)
    yazi(sl, Cm(1.6), H - Cm(0.82), Cm(22), Cm(0.75), "Kuantum Sonrası TLS Hazırlığı  ·  Veri İletişimi (BİL321)",
         10, GRI, dikey=MSO_ANCHOR.MIDDLE)
    yazi(sl, W - Cm(3.6), H - Cm(0.82), Cm(2.0), Cm(0.75), f"{no[0]:02d}", 10, YESIL, True, PP_ALIGN.RIGHT,
         MSO_ANCHOR.MIDDLE)
    sl.notes_slide.notes_text_frame.text = notlar
    return sl


def kafes_deseni(sl, x0, y0, sutun, satir, ad, renk, nokta=Cm(0.16)):
    """Kafes (lattice) motifi: ML-KEM'in dayandığı modül kafeslerine görsel gönderme."""
    for i in range(sutun):
        for j in range(satir):
            sekil(sl, MSO_SHAPE.OVAL, x0 + i * ad, y0 + j * ad, nokta, nokta, renk)


def stil_grafik(gf, eksen_boyut=14):
    gf.font.name = F_GOVDE
    gf.font.size = Pt(eksen_boyut)
    gf.font.color.rgb = GRI


# --- Veriler -------------------------------------------------------------------------
S = {o["sektor"]: o for o in R["sektor"]}
T = S["TÜMÜ"]
SEKT = [o for o in R["sektor"] if o["sektor"] != "TÜMÜ"]
cdn_k, cdn_n = map(int, R["cdn_fisher"]["cdn"].split("/"))
oz_k, oz_n = map(int, R["cdn_fisher"]["kendi"].split("/"))
AG = R["ag"]
SIM = {(x["senaryo"], x["kayip"]): x for x in R["simulasyon"]["rtt20"]}
N_SITE = T["n"]
N_LISTE = R.get("liste_boyutu", N_SITE + 1)
TUT = R["tutarlilik"]
B = S.get("Banka")
ETK = S.get("E-ticaret")
ek_bayt = AG["yazilan_fark"] + AG["okunan_fark"]
k01 = (SIM[("Klasik", 0.01)], SIM[("Hibrit (tarayıcı)", 0.01)])
k10 = (SIM[("Klasik", 0.10)], SIM[("Hibrit (tarayıcı)", 0.10)])
artis10 = 100 * (k10[1]["ortalama_ms"] / k10[0]["ortalama_ms"] - 1)

# =====================================================================================
# 1. KAPAK
# =====================================================================================
no[0] += 1
sl = prs.slides.add_slide(prs.slide_layouts[6])
bg = sl.background.fill; bg.solid(); bg.fore_color.rgb = LACI
kafes_deseni(sl, Cm(21.5), Cm(1.2), 12, 16, Cm(1.0), LACI2, Cm(0.18))
for (i, j) in ((3, 4), (5, 4), (7, 6), (4, 9), (8, 10), (10, 3), (6, 12), (9, 14), (2, 13)):
    sekil(sl, MSO_SHAPE.OVAL, Cm(21.5) + i * Cm(1.0) - Cm(0.05), Cm(1.2) + j * Cm(1.0) - Cm(0.05), Cm(0.28),
          Cm(0.28), YESIL)
rozet(sl, Cm(2.2), Cm(2.2), "VERİ İLETİŞİMİ · BİL321 · DÖNEM PROJESİ", NANE, LACI2, 12, Cm(9.6))
yazi(sl, Cm(2.2), Cm(4.0), Cm(20.5), Cm(6.4), ["Türkiye'deki Kritik Sektör", "Web Sitelerinin", "**Kuantum Sonrası TLS** Hazırlığı"], 34, BEYAZ, font=F_BASLIK, aralik=0, satir=1.0)
yazi(sl, Cm(2.2), Cm(10.6), Cm(19), Cm(1.6), "Sektörel ölçüm · ağ maliyeti · paket kaybı analizi", 20, NANE)
sekil(sl, MSO_SHAPE.RECTANGLE, Cm(2.2), Cm(13.2), Cm(1.6), Cm(0.09), YESIL)
yazi(sl, Cm(2.2), Cm(13.6), Cm(19), Cm(3.6), ["**Rümeysa Betül Özyurt**",
                                              "Bilgisayar Mühendisliği Yüksek Lisans",
                                              "Öğretim Üyesi: Prof. Dr. Agah Tuğrul Korucu",
                                              "İstanbul Ticaret Üniversitesi · 2026–2027 Güz"], 15,
     RGBColor(0xC9, 0xD3, 0xE6), aralik=2)
sl.notes_slide.notes_text_frame.text = (
    "Merhaba. Projem, Türkiye'deki kritik sektörlere ait web sitelerinin kuantum bilgisayar tehdidine karşı ne kadar "
    "hazır olduğunu ve bu geçişin veri iletişimine, yani bayt, paket ve gecikme düzeyinde getirdiği maliyeti "
    "inceliyor. Arka plandaki nokta deseni, yeni standardın dayandığı kafes (lattice) matematiğine bir gönderme.")

# =====================================================================================
# 2. NEDEN ŞİMDİ
# =====================================================================================
sl = slayt("Neden şimdi? \"Şimdi topla, sonra çöz\" tehdidi", bolum="Konu ve önemi", notlar=(
    "HTTPS oturum anahtarı bugün X25519 gibi eliptik eğri yöntemleriyle kuruluyor. Shor algoritması bu yöntemleri "
    "yeterince büyük bir kuantum bilgisayarda kırabiliyor. Saldırgan bugün trafiği kaydedip yıllar sonra çözebilir. "
    "Mosca eşitsizliği şunu söyler: verinin gizli kalma süresi ile geçiş süresinin toplamı, kuantum bilgisayarın "
    "gelişine kadar geçecek süreyi aşıyorsa risk bugünden başlamıştır. Çözüm hazır: NIST'in ML-KEM standardı ve "
    "tarayıcıların varsayılan olarak kullandığı hibrit X25519MLKEM768 grubu."))
# zaman çizelgesi
y0 = Cm(5.6)
sekil(sl, MSO_SHAPE.RECTANGLE, Cm(3.0), y0 + Cm(1.05), Cm(27.8), Cm(0.12), CIZGI)
adimlar = (("2026 · BUGÜN", "Kaydet", "Saldırgan şifreli HTTPS trafiğini depolar", MAVI, "1"),
           ("YILLAR BOYU", "Bekle", "Banka, sağlık, kamu verisi 10+ yıl gizli kalmalı", GRI, "2"),
           ("KUANTUM BİLGİSAYAR", "Çöz", "Shor algoritması ECDH / X25519 anahtarını kırar", MERCAN, "3"))
for i, (ust, bas, acik, r, n) in enumerate(adimlar):
    x = Cm(2.0 + i * 10.3)
    ikon(sl, x + Cm(3.7), y0, Cm(2.3), r, n, 26)
    yazi(sl, x, y0 + Cm(2.6), Cm(9.7), Cm(0.8), ust, 11, r, True, PP_ALIGN.CENTER)
    yazi(sl, x, y0 + Cm(3.3), Cm(9.7), Cm(1.2), bas, 26, LACI, True, PP_ALIGN.CENTER)
    yazi(sl, x + Cm(0.8), y0 + Cm(4.6), Cm(8.1), Cm(1.8), acik, 15, GRI, hiza=PP_ALIGN.CENTER)
# Mosca + çözüm
kart(sl, Cm(1.6), Cm(13.0), Cm(15.2), Cm(4.4), MERCAN_A, None)
yazi(sl, Cm(2.2), Cm(13.3), Cm(14.2), Cm(0.9), "MOSCA EŞİTSİZLİĞİ", 11, MERCAN, True)
yazi(sl, Cm(2.2), Cm(14.1), Cm(14.2), Cm(1.5), "x + y > z  ⇒  risk bugün başlar", 26, MERCAN, True)
yazi(sl, Cm(2.2), Cm(15.7), Cm(14.2), Cm(1.4), "x: gizli kalma süresi · y: geçiş süresi · z: tehdide kalan süre",
     13, GRI)
kart(sl, Cm(17.4), Cm(13.0), Cm(14.8), Cm(4.4), YESIL_A, None)
yazi(sl, Cm(18.0), Cm(13.3), Cm(14), Cm(0.9), "ÇÖZÜM HAZIR", 11, YESIL, True)
yazi(sl, Cm(18.0), Cm(14.1), Cm(14), Cm(1.5), "ML-KEM + X25519 = hibrit", 26, YESIL, True)
yazi(sl, Cm(18.0), Cm(15.7), Cm(14), Cm(1.4), "NIST FIPS 203 (2024) · Chrome, Edge, Firefox'ta varsayılan", 13, GRI)

# =====================================================================================
# 3. PROBLEM
# =====================================================================================
sl = slayt("Problem: güvenlik ve iletim verimliliği aynı anda", bolum="Problem tanımı", notlar=(
    "Problem iki yönlü. Güvenlik tarafında Türkiye'de hangi kurumların bu korumayı sağladığı bilinmiyor. Veri "
    "iletişimi tarafında ise hibrit anahtar payları el sıkışmayı yaklaşık 2,3 kilobayt büyütüyor ve ilk mesaj artık "
    "tek TCP segmentine sığmıyor. Bu da bant genişliği, gecikme, kayba duyarlılık ve ara cihaz uyumluluğunu "
    "etkiliyor."))
kartlar = (("Gizlilik", "Hangi sunucu kuantum sonrası korumalı? Türkiye için veri yok.", YESIL, YESIL_A, "◆"),
           ("Bant genişliği", f"El sıkışma başına +{tr(ek_bayt / 1000)} KB ek veri", MAVI, MAVI_A, "⇄"),
           ("Gecikme ve kayıp", "ClientHello 2 segmente bölünür, kayba daha duyarlı", MERCAN, MERCAN_A, "◷"),
           ("Güvenilirlik", "Tek paket varsayan eski ara cihazlar bağlantıyı bozabilir", AMBER, AMBER_A, "!"))
for i, (b, a, r, z, s_) in enumerate(kartlar):
    x = Cm(1.6 + i * 7.75)
    kart(sl, x, Cm(4.0), Cm(7.25), Cm(7.6))
    ikon(sl, x + Cm(0.7), Cm(4.7), Cm(1.8), r, s_, 20, z)
    yazi(sl, x + Cm(0.7), Cm(7.0), Cm(6.2), Cm(1.2), b, 20, LACI, True)
    yazi(sl, x + Cm(0.7), Cm(8.3), Cm(6.1), Cm(3.0), a, 15, GRI, satir=0.95)
kart(sl, Cm(1.6), Cm(12.3), Cm(30.6), Cm(5.1), BEYAZ)
yazi(sl, Cm(2.3), Cm(12.7), Cm(29), Cm(0.9), "MEVCUT DURUMUN SINIRLILIKLARI", 11, MERCAN, True)
for i, m in enumerate(("Küresel ölçümler **Türkiye ve sektör kırılımı** sunmuyor",
                       "\"Destek var mı?\" sorusu ile **ağ maliyeti** aynı veride incelenmemiş",
                       "Kurumların kendini ölçebileceği **açık ve yerel bir araç** yok")):
    y = Cm(13.7 + i * 1.15)
    sekil(sl, MSO_SHAPE.OVAL, Cm(2.4), y + Cm(0.25), Cm(0.35), Cm(0.35), MERCAN)
    yazi(sl, Cm(3.1), y, Cm(28), Cm(1.0), m, 17, LACI)

# =====================================================================================
# 4. AMAÇ
# =====================================================================================
sl = slayt("Amaç: iki soru, dört hedef", bolum="Projenin amacı", notlar=(
    "İki araştırma sorum var: Türkiye'deki siteler hazır mı, ve bu geçişin ağa maliyeti ne. Bunlara cevap vermek "
    "için dört hedef koydum: açık bir ölçüm sistemi, hazırlığın belirleyicisini istatistikle bulmak, ağ maliyetini "
    "bayt-segment-gecikme düzeyinde ölçmek ve her şeyi tekrarlanabilir yapmak."))
for i, (s_, a, r) in enumerate((("S1", "Türkiye'deki kritik sektör siteleri kuantum sonrası TLS'e hazır mı? "
                                       "Hazırlığı ne belirliyor?", YESIL),
                                ("S2", "Hibrit anahtar değişimi ağa ne maliyet getiriyor: bayt, TCP segmenti, "
                                       "gecikme?", MAVI))):
    y = Cm(4.0 + i * 3.1)
    kart(sl, Cm(1.6), y, Cm(30.6), Cm(2.6))
    ikon(sl, Cm(2.2), y + Cm(0.4), Cm(1.8), r, s_, 16)
    yazi(sl, Cm(4.6), y, Cm(27), Cm(2.6), a, 19, LACI, dikey=MSO_ANCHOR.MIDDLE)
hedefler = (("Ölçüm sistemi", f"{N_LISTE} site, açık Python + OpenSSL aracı"),
            ("Belirleyiciler", "Sektör mü, altyapı (CDN) mı? İstatistiksel sınama"),
            ("Ağ maliyeti", "Ölçüm + Wireshark + kayıp simülasyonu"),
            ("Tekrarlanabilirlik", "Docker, tekrarlı turlar, açık veri"))
for i, (b, a) in enumerate(hedefler):
    x = Cm(1.6 + i * 7.75)
    kart(sl, x, Cm(10.6), Cm(7.25), Cm(6.8), BEYAZ)
    yazi(sl, x + Cm(0.6), Cm(11.0), Cm(2.5), Cm(1.6), f"0{i + 1}", 30, YESIL, True)
    yazi(sl, x + Cm(0.6), Cm(12.9), Cm(6.3), Cm(1.2), b, 19, LACI, True)
    yazi(sl, x + Cm(0.6), Cm(14.2), Cm(6.2), Cm(3), a, 15, GRI, satir=0.95)

# =====================================================================================
# 5. LİTERATÜR
# =====================================================================================
sl = slayt("Literatür: küresel tablo var, Türkiye ve ağ maliyeti yok", bolum="Literatür ve mevcut çözümler", notlar=(
    "Paquin ve arkadaşları laboratuvarda PQ TLS'in kayıp altındaki davranışını incelemişti. 2026'da küresel ölçümler "
    "var: F5 Labs ilk 1 milyon sitede yüzde 54 destek buldu; Cloudflare dışında bu oran yüzde 22. İngiltere için de "
    "sektörel bir çalışma var. Benim çalışmam Türkiye'ye odaklanıyor ve hazırlık ölçümünü aynı veride ağ maliyeti ve "
    "kayıp analiziyle birleştiriyor."))
kolon = ["Kapsam", "Sektör", "Ağ maliyeti", "Kayıp analizi", "Türkiye"]
satirlar = (("Paquin vd. (2020)", "Laboratuvar", [0, 1, 1, 0]),
            ("Dubey & Varshney (2026)", "32 011 alan adı", [1, 0, 0, 0]),
            ("F5 Labs (2026)", "İlk 1 milyon site", [0.5, 0, 0, 0]),
            ("BK sektör çalışması (2026)", "Birleşik Krallık", [1, 0, 0, 0]),
            ("Bu proje", f"{N_LISTE} site", [1, 1, 1, 1]))
x0, y0, sw, rh = Cm(1.6), Cm(4.0), [Cm(8.0), Cm(5.6), Cm(4.2), Cm(4.2), Cm(4.2), Cm(4.2)], Cm(1.55)
kart(sl, x0, y0, sum(sw, Emu(0)), rh * 6 + Cm(0.2))
xs = [x0]
for w in sw[:-1]:
    xs.append(xs[-1] + w)
for j, k in enumerate(["Çalışma"] + kolon):
    yazi(sl, xs[j] + Cm(0.4), y0 + Cm(0.15), sw[j] - Cm(0.5), rh, k.upper(), 11, GRI, True,
         PP_ALIGN.LEFT if j < 2 else PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
for i, (ad, kapsam, deg) in enumerate(satirlar):
    y = y0 + rh * (i + 1) + Cm(0.1)
    son = i == len(satirlar) - 1
    if son:
        sekil(sl, MSO_SHAPE.ROUNDED_RECTANGLE, x0 + Cm(0.15), y, sum(sw, Emu(0)) - Cm(0.3), rh - Cm(0.1), YESIL_A,
              None, yuvarlak=0.2)
    else:
        sekil(sl, MSO_SHAPE.RECTANGLE, x0 + Cm(0.4), y, sum(sw, Emu(0)) - Cm(0.8), Cm(0.02), CIZGI)
    yazi(sl, xs[0] + Cm(0.4), y, sw[0], rh, ad, 16, YESIL if son else LACI, son, dikey=MSO_ANCHOR.MIDDLE)
    yazi(sl, xs[1] + Cm(0.4), y, sw[1], rh, kapsam, 15, LACI if son else GRI, son, dikey=MSO_ANCHOR.MIDDLE)
    for j, v in enumerate(deg):
        cx = xs[j + 2] + sw[j + 2] / 2 - Cm(0.45)
        cy = y + rh / 2 - Cm(0.45)
        if v == 1:
            ikon(sl, cx, cy, Cm(0.9), YESIL, "✓", 13)
        elif v == 0.5:
            ikon(sl, cx, cy, Cm(0.9), AMBER, "~", 13)
        else:
            sekil(sl, MSO_SHAPE.OVAL, cx + Cm(0.3), cy + Cm(0.3), Cm(0.3), Cm(0.3), CIZGI)
for i, (s_, a, r) in enumerate((("%54", "F5 Labs: ilk 1 milyon sitede PQ destek", YESIL),
                                ("%22", "aynı ölçüm, Cloudflare hariç", AMBER),
                                ("%10,5", "TLS 1.3'ü bile desteklemeyen siteler", MERCAN))):
    buyuk_sayi(sl, Cm(1.6 + i * 10.3), Cm(13.6), Cm(9.8), s_, a, r, 32, h=Cm(3.8))

# =====================================================================================
# 6. SİSTEM MİMARİSİ (yerel diyagram)
# =====================================================================================
sl = slayt("Sistem mimarisi: gönderici → kanal → alıcı", bolum="Önerilen sistemin genel yapısı", notlar=(
    "Gönderici tarafta Python betiği, X25519MLKEM768 destekli OpenSSL 4.0.3'ün s_client bileşenini çalıştırıyor. "
    "Kanal, Türkiye'de bir ev internet bağlantısı; MSS 1460 bayt. Alıcı tarafta iki tip sunucu var: TLS'in CDN uç "
    "sunucusunda sonlandığı siteler ve kurumun kendi sunucusunda sonlandığı siteler. CDN ile kaynak sunucu arası "
    "dışarıdan görünmediği için kapsam dışı. Wireshark ile paket düzeyinde doğrulama yaptım."))
for x, w, b, r in ((Cm(1.6), Cm(10.2), "GÖNDERİCİ · ÖLÇÜM İSTEMCİSİ", MAVI), (Cm(12.4), Cm(6.6), "İLETİM KANALI", GRI),
                   (Cm(19.6), Cm(12.6), "ALICI · SUNUCULAR", YESIL)):
    kart(sl, x, Cm(3.8), w, Cm(12.2), BEYAZ)
    sekil(sl, MSO_SHAPE.RECTANGLE, x, Cm(3.8), w, Cm(0.15), r)
    yazi(sl, x + Cm(0.5), Cm(4.15), w, Cm(0.8), b, 11, r, True)


def dugum(sl, x, y, w, h, bas, alt, r, z):
    kart(sl, x, y, w, h, z, None, 0.1)
    yazi(sl, x + Cm(0.3), y + Cm(0.2), w - Cm(0.6), Cm(0.9), bas, 15, r, True, PP_ALIGN.CENTER)
    yazi(sl, x + Cm(0.3), y + Cm(1.05), w - Cm(0.6), h - Cm(1.1), alt, 12, GRI, hiza=PP_ALIGN.CENTER, satir=0.95)


dugum(sl, Cm(2.2), Cm(5.2), Cm(4.4), Cm(2.4), "siteler.csv", f"{N_LISTE} alan adı", AMBER, AMBER_A)
dugum(sl, Cm(7.0), Cm(5.2), Cm(4.4), Cm(2.4), "Wireshark", "paket yakalama", GRI, GRI_A)
dugum(sl, Cm(2.2), Cm(8.6), Cm(4.4), Cm(3.4), "olcum.py", "DNS → RTT →\n5 bağlantı senaryosu", MAVI, MAVI_A)
dugum(sl, Cm(7.0), Cm(8.6), Cm(4.4), Cm(3.4), "OpenSSL", "4.0.3 · s_client\nhibrit PQ\ndestekli", YESIL, YESIL_A)
dugum(sl, Cm(2.2), Cm(13.0), Cm(9.2), Cm(2.4), "sonuclar.csv → analiz", "34 sütun/site · istatistik · grafik",
      AMBER, AMBER_A)
ok(sl, Cm(4.4), Cm(7.6), Cm(4.4), Cm(8.6))
ok(sl, Cm(6.6), Cm(10.3), Cm(7.0), Cm(10.3), iki_yon=True)
ok(sl, Cm(4.4), Cm(12.0), Cm(4.4), Cm(13.0))
ok(sl, Cm(9.2), Cm(7.6), Cm(9.2), Cm(8.6), kesikli=True, uc=False)
dugum(sl, Cm(13.0), Cm(7.4), Cm(5.4), Cm(5.4), "Ev interneti (TR)",
      "Wi-Fi → modem → ISS\n\nIP / TCP\nMSS = 1460 B\nmedyan RTT ≈ 20 ms", GRI, GRI_A)
ok(sl, Cm(11.4), Cm(10.3), Cm(13.0), Cm(10.3), iki_yon=True, renk=LACI)
cdn_say = R["cdn_saglayicilar"]
cdn_metin = " · ".join(f"{k} {v}" for k, v in sorted(cdn_say.items(), key=lambda x: -x[1]))
dugum(sl, Cm(20.4), Cm(5.2), Cm(6.6), Cm(3.6), f"CDN uç sunucusu ({cdn_n})", cdn_metin, YESIL, YESIL_A)
dugum(sl, Cm(27.8), Cm(5.2), Cm(3.8), Cm(3.6), "Origin", "kaynak sunucu\n(görünmez)", GRI, GRI_A)
ok(sl, Cm(27.0), Cm(7.0), Cm(27.8), Cm(7.0), kesikli=True)
dugum(sl, Cm(20.4), Cm(10.6), Cm(11.2), Cm(3.0), f"Kendi sunucusunu işleten kurum ({oz_n})",
      "TLS kurumun kendi web sunucusunda sonlanır (Apache, nginx, IIS, BIG-IP)", MAVI, MAVI_A)
ok(sl, Cm(18.4), Cm(9.4), Cm(20.4), Cm(7.0), renk=YESIL)
ok(sl, Cm(18.4), Cm(11.0), Cm(20.4), Cm(12.1), renk=MAVI)
yazi(sl, Cm(20.4), Cm(14.1), Cm(11.4), Cm(1.8), "Ölçülen: TLS sürümü · seçilen grup · HRR · sertifika · "
                                                  "CH/SH baytı · segment · RTT · Alt-Svc", 12, GRI)

# =====================================================================================
# 7. TEKNOLOJİLER
# =====================================================================================
sl = slayt("Teknolojiler ve seçim gerekçeleri", bolum="Kullanılan teknolojiler ve protokoller", notlar=(
    "OpenSSL s_client'ı seçtim çünkü hangi anahtar paylarının gönderileceğini kontrol edebiliyorum ve -msg ile her "
    "mesajın boyutunu görüyorum; Python'un ssl modülü bunu vermiyor. İstatistikte Fisher kesin testini seçtim çünkü "
    "bankalarda sıfır hücre var ve ki-kare küçük frekanslarda güvenilmez."))
tek = (("OpenSSL 4.0.3", "TLS istemcisi", "Pay kontrolü (-groups), mesaj boyutu (-msg)", "Python ssl, curl", YESIL),
       ("Python 3", "Ölçüm aracı", "Taşınabilir, yalnız standart kütüphane", "Go crypto/tls", MAVI),
       ("X25519MLKEM768", "Anahtar grubu", "Tarayıcıların varsayılanı, IETF önerisi", "SecP256r1MLKEM768", YESIL),
       ("TCP + TLS 1.3", "Taşıma", "HTTPS'in ana yolu; PQ yalnız TLS 1.3'te", "QUIC (yalnız ilan)", MAVI),
       ("Wireshark 4.6.8", "Paket analizi", "Çerçeve ve uzantı düzeyinde doğrulama", "tcpdump", GRI),
       ("Fisher · Wilson", "İstatistik", "Küçük örneklem, sıfır hücre", "Ki-kare", AMBER),
       ("Monte Carlo", "Kayıp analizi", "Kayıp oranını kontrollü değiştirme", "Gerçek ağda kontrol yok", MERCAN),
       ("Docker", "Ortam", "Her işletim sisteminde aynı OpenSSL", "Yerel kurulum", GRI))
for i, (ad, rol, neden, alt, r) in enumerate(tek):
    x = Cm(1.6 + (i % 4) * 7.75); y = Cm(3.8 + (i // 4) * 6.9)
    kart(sl, x, y, Cm(7.25), Cm(6.4))
    sekil(sl, MSO_SHAPE.RECTANGLE, x, y, Cm(7.25), Cm(0.15), r)
    yazi(sl, x + Cm(0.5), y + Cm(0.45), Cm(6.5), Cm(0.7), rol.upper(), 10, r, True)
    yazi(sl, x + Cm(0.5), y + Cm(1.1), Cm(6.5), Cm(1.1), ad, 19, LACI, True)
    yazi(sl, x + Cm(0.5), y + Cm(2.4), Cm(6.4), Cm(2.2), neden, 14, LACI, satir=0.95)
    yazi(sl, x + Cm(0.5), y + Cm(5.0), Cm(6.4), Cm(1.0), f"Alternatif: {alt}", 11, GRI)

# =====================================================================================
# 8. TLS 1.3 SIRA DİYAGRAMI (yerel)
# =====================================================================================
sl = slayt("Protokol akışı: hibrit TLS 1.3 el sıkışması", bolum="Gönderici–alıcı mimarisi", notlar=(
    "TCP üçlü el sıkışması bir RTT sürüyor. Sonra istemci ClientHello gönderiyor; içinde iki anahtar payı var: "
    "1216 baytlık hibrit pay ve 32 baytlık yedek X25519. Bu mesaj iki TCP segmentine bölünüyor. Sunucu 1210 "
    "baytlık ServerHello ile cevap veriyor. Hibrit grupla da el sıkışma 1 RTT'de bitiyor. Sağda: sunucu tarayıcının "
    "gönderdiği grupları desteklemezse HelloRetryRequest ile fazladan bir RTT harcanıyor; bir bankada bunu gördüm."))
kart(sl, Cm(1.6), Cm(3.8), Cm(19.6), Cm(13.6))
kart(sl, Cm(21.8), Cm(3.8), Cm(10.4), Cm(13.6))
xi, xs_ = Cm(4.6), Cm(17.6)
for x, ad in ((xi, "İstemci"), (xs_, "Sunucu")):
    kart(sl, x - Cm(1.9), Cm(4.3), Cm(3.8), Cm(1.1), LACI, None, 0.25)
    yazi(sl, x - Cm(1.9), Cm(4.3), Cm(3.8), Cm(1.1), ad, 15, BEYAZ, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    ok(sl, x, Cm(5.4), x, Cm(16.9), CIZGI, 1.5, kesikli=True, uc=False)
mesajlar = ((6.0, True, "TCP SYN", GRI, 13), (6.9, False, "SYN / ACK", GRI, 13), (7.8, True, "ACK", GRI, 13),
            (9.1, True, "ClientHello · 1534 B · 2 segment", YESIL, 15),
            (10.9, False, "ServerHello · 1210 B  +  {EE, Cert, CV, Fin}", YESIL, 15),
            (12.7, True, "{Finished} + HTTP GET", MAVI, 14), (13.6, False, "HTTP yanıtı", MAVI, 14))
for y, sag, m, r, b in mesajlar:
    y1, y2 = Cm(y), Cm(y + 0.55)
    ok(sl, xi if sag else xs_, y1, xs_ if sag else xi, y2, r, 2.2)
    yazi(sl, Cm(5.2), Cm(y - 0.75), Cm(11.8), Cm(0.8), m, b, r, b >= 15, PP_ALIGN.CENTER)
kart(sl, Cm(5.0), Cm(9.85), Cm(12.2), Cm(0.75), YESIL_A, None, 0.4)
yazi(sl, Cm(5.0), Cm(9.85), Cm(12.2), Cm(0.75), "key_share: X25519MLKEM768 (1216 B) + X25519 (32 B)", 12, YESIL,
     hiza=PP_ALIGN.CENTER, dikey=MSO_ANCHOR.MIDDLE)
for y1, y2, t, r in ((5.9, 8.4, "1 RTT\nTCP", GRI), (8.9, 11.6, "1 RTT\nTLS", YESIL)):
    sekil(sl, MSO_SHAPE.RIGHT_BRACE, Cm(18.3), Cm(y1), Cm(0.5), Cm(y2 - y1), None, r, 1.5)
    yazi(sl, Cm(18.9), Cm((y1 + y2) / 2 - 0.7), Cm(2.2), Cm(1.4), t, 12, r, True)
yazi(sl, Cm(2.2), Cm(15.2), Cm(18.5), Cm(2), "Gizli değer = X25519 sırrı ‖ ML-KEM sırrı → biri kırılsa bile "
                                              "diğeri oturumu korur", 13, GRI)
# HRR paneli
yazi(sl, Cm(22.4), Cm(4.2), Cm(9.4), Cm(0.8), "HELLORETRYREQUEST (+1 RTT)", 11, MERCAN, True)
xi2, xs2 = Cm(23.6), Cm(30.4)
for x in (xi2, xs2):
    ok(sl, x, Cm(5.3), x, Cm(12.6), CIZGI, 1.5, kesikli=True, uc=False)
yazi(sl, xi2 - Cm(1.2), Cm(4.9), Cm(2.4), Cm(0.6), "İstemci", 11, GRI, True, PP_ALIGN.CENTER)
yazi(sl, xs2 - Cm(1.2), Cm(4.9), Cm(2.4), Cm(0.6), "Sunucu", 11, GRI, True, PP_ALIGN.CENTER)
for y, sag, m, r in ((6.4, True, "ClientHello [hibrit, X25519]", YESIL), (7.9, False, "HRR [P-256 iste]", MERCAN),
                     (9.4, True, "ClientHello (2.) [P-256]", MAVI), (10.9, False, "ServerHello …", MAVI)):
    ok(sl, xi2 if sag else xs2, Cm(y), xs2 if sag else xi2, Cm(y + 0.5), r, 2.0)
    yazi(sl, Cm(22.4), Cm(y - 0.7), Cm(9.4), Cm(0.7), m, 12, r, True, PP_ALIGN.CENTER)
hrr_say = len(R["hrr"])
kart(sl, Cm(22.4), Cm(13.4), Cm(9.2), Cm(3.4), MERCAN_A, None)
yazi(sl, Cm(22.8), Cm(13.6), Cm(8.6), Cm(3.0), [f"**{hrr_say} site** bu davranışı gösterdi",
                                               "Her bağlantıda +1 RTT ≈ +20 ms"], 14, MERCAN)

# =====================================================================================
# 9. KATMANLAR
# =====================================================================================
sl = slayt("Katmanlar arası etki: TLS değişir, TCP ve Ethernet hisseder", bolum="Protokol katmanları", notlar=(
    "Bu slayt projenin veri iletişimi açısından özünü gösteriyor. Değişiklik TLS katmanında yapılıyor, ama etkisi "
    "taşıma katmanında segment sayısı ve yeniden iletim olarak, veri bağı katmanında çerçeve boyutu olarak "
    "görülüyor. Sağ sütun her katmanda neyi ölçtüğümü gösteriyor."))
katmanlar = (("Uygulama", "HTTP/1.1 · HTTP/2 · Alt-Svc (h3)", "http3_ilani · CDN başlıkları", GRI_A, GRI, False),
             ("Güvenlik (TLS 1.3)", "El sıkışma · X25519MLKEM768 · sertifika", "PQ destek · grup · HRR · CH/SH baytı",
              YESIL_A, YESIL, True),
             ("Taşıma (TCP)", "3'lü el sıkışma · MSS 1460 B · RTO", "RTT · segment sayısı · kayıp etkisi", MAVI_A, MAVI,
              True),
             ("İnternet (IP)", "IPv4/IPv6 · DNS · CDN anycast", "IP · CDN adres bloğu", GRI_A, GRI, False),
             ("Ağ erişimi", "Ethernet / Wi-Fi · MTU 1500 B · TSO", "Wireshark: 369 / 1591 B çerçeve", AMBER_A, AMBER,
              True))
for j, k in enumerate(("TCP/IP KATMANI", "MEKANİZMA", "BU ÇALIŞMADA ÖLÇÜLEN")):
    yazi(sl, [Cm(1.6), Cm(9.6), Cm(21.0)][j], Cm(3.7), Cm(10), Cm(0.7), k, 11, GRI, True)
for i, (ad, mek, olc, z, r, etki) in enumerate(katmanlar):
    y = Cm(4.6 + i * 2.5)
    kart(sl, Cm(1.6), y, Cm(30.6), Cm(2.2), z if etki else BEYAZ, None if etki else CIZGI, 0.15)
    sekil(sl, MSO_SHAPE.RECTANGLE, Cm(1.6), y + Cm(0.3), Cm(0.2), Cm(1.6), r)
    yazi(sl, Cm(2.3), y, Cm(7.2), Cm(2.2), ad, 17, LACI, True, dikey=MSO_ANCHOR.MIDDLE)
    yazi(sl, Cm(9.6), y, Cm(11.2), Cm(2.2), mek, 15, LACI, dikey=MSO_ANCHOR.MIDDLE)
    yazi(sl, Cm(21.0), y, Cm(10.9), Cm(2.2), olc, 14, r if etki else GRI, etki, dikey=MSO_ANCHOR.MIDDLE)
yazi(sl, Cm(1.6), Cm(17.2), Cm(30), Cm(0.8), "Renkli satırlar: hibrit anahtar değişiminin etkisinin görüldüğü katmanlar",
     11, GRI)

# =====================================================================================
# 10. PAKETLEME
# =====================================================================================
sl = slayt("Paketleme: ClientHello artık tek segmente sığmıyor", bolum="Kodlama ve paketleme", notlar=(
    "Klasik ClientHello 232 bayt, tek segment. Tarayıcı benzeri hibrit ClientHello başlıklarla 1543 bayt. MSS 1460 "
    "olduğu için 83 bayt taşıyor ve ikinci bir segment gerekiyor. Mesajın yaklaşık yüzde 80'i tek bir uzantı: "
    "key_share."))
kart(sl, Cm(1.6), Cm(3.8), Cm(30.6), Cm(8.6))
olcek = Cm(27.0) / 1600
x0 = Cm(3.2)
for i, (bas, parcalar) in enumerate((("Klasik ClientHello · 241 B · 1 segment", [(9, GRI_A, ""), (196, MAVI_A, "ortak alanlar"),
                                                                                (36, MAVI, "")]),
                                     ("Tarayıcı benzeri hibrit ClientHello · 1543 B · 2 segment",
                                      [(9, GRI_A, ""), (278, MAVI_A, "ortak alanlar"),
                                       (1220, YESIL_A, "X25519MLKEM768 payı: 1184 B ML-KEM-768 anahtarı + 32 B X25519"),
                                       (36, MAVI, "")]))):
    y = Cm(4.3 + i * 3.6)
    yazi(sl, Cm(2.2), y, Cm(26), Cm(0.8), bas, 15, LACI, True)
    x = x0
    for b_, z, et in parcalar:
        w = int(olcek * b_)
        sekil(sl, MSO_SHAPE.RECTANGLE, x, y + Cm(1.0), w, Cm(1.5), z, BEYAZ, 1.0)
        if et:
            yazi(sl, x, y + Cm(1.0), w, Cm(1.5), et, 12, LACI, hiza=PP_ALIGN.CENTER, dikey=MSO_ANCHOR.MIDDLE)
        x += w
sinir = x0 + int(olcek * 1460)
ok(sl, sinir, Cm(4.6), sinir, Cm(11.6), MERCAN, 2.5, kesikli=True, uc=False)
yazi(sl, sinir - Cm(3.5), Cm(11.55), Cm(7), Cm(0.7), "MSS = 1460 B · 1. segmentin sonu", 12, MERCAN, True,
     PP_ALIGN.CENTER)
for i, (s_, a, r) in enumerate(((f"232 → {int(AG['tarayici_ch_medyan'])} B", "ClientHello: klasik → tarayıcı hibrit", MAVI),
                                ("1 → 2", "TCP segmenti (ölçülen sitelerin tamamında)", MERCAN),
                                (f"+{int(ek_bayt)} B", "el sıkışma başına ek veri (+1184 / +1088)", YESIL))):
    buyuk_sayi(sl, Cm(1.6 + i * 10.3), Cm(13.1), Cm(9.8), s_, a, r, 32, h=Cm(4.3))

# =====================================================================================
# 11. ÖLÇÜM ALGORİTMASI
# =====================================================================================
sl = slayt("Veri akışı: site başına ölçüm algoritması", bolum="Sistem tasarımı ve veri akışı", notlar=(
    "Her site için alan adını bir kez çözüp hep aynı IP'yi kullanıyorum. Beş TCP bağlantısıyla medyan RTT ölçüyorum. "
    "Sonra beş senaryo: tarayıcı benzeri teklif, TLS 1.2 testi, yalnız hibrit, yalnız klasik ve HTTP başlıkları. "
    "Hibrit ve klasik testler beşer kez tekrarlanıyor. Siteler arasında bekleme var; tarama yapmıyorum."))
adim = (("DNS", "Bir kez çöz\nsabit IP"), ("RTT", "TCP bağlantısı\n×5 → medyan"),
        ("S1 Tarayıcı", "*MLKEM:*X25519:P-256\nsürüm · grup · HRR"), ("S2 TLS 1.2", "kabul ediliyor mu?"),
        ("S3 Hibrit", "yalnız X25519MLKEM768\n×5 → PQ destek"), ("S4 Klasik", "yalnız X25519\n×5 → karşılaştırma"),
        ("S5 HTTP", "Alt-Svc (h3)\nCDN başlıkları"))
renkler = (GRI, GRI, YESIL, MAVI, YESIL, MAVI, AMBER)
for i, ((b, a), r) in enumerate(zip(adim, renkler)):
    x = Cm(1.6 + i * 4.43)
    s = sekil(sl, MSO_SHAPE.CHEVRON if i else MSO_SHAPE.PENTAGON, x, Cm(4.2), Cm(4.6), Cm(2.0), r)
    yazi(sl, x + Cm(0.6), Cm(4.2), Cm(3.4), Cm(2.0), b, 13, BEYAZ, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    yazi(sl, x + Cm(0.1), Cm(6.5), Cm(4.2), Cm(2.2), a.split("\n"), 12, LACI, hiza=PP_ALIGN.CENTER, aralik=1)
kart(sl, Cm(1.6), Cm(9.4), Cm(18.8), Cm(8.0), BEYAZ)
yazi(sl, Cm(2.2), Cm(9.7), Cm(18), Cm(0.8), "SÖZDE KOD", 11, GRI, True)
kod = ["for (sektör, alan_adı) in siteler:",
       "    ip  ← DNS(alan_adı)",
       "    rtt ← medyan(TCP_connect(ip) × 5)",
       "    v   ← s_client(ip, groups=\"*X25519MLKEM768:*X25519:P-256\")",
       "    if v.sürüm = TLS1.3:",
       "        pq ← s_client(ip, groups=X25519MLKEM768) × 5",
       "        kl ← s_client(ip, groups=X25519) × 5",
       "    http ← HTTPS_GET(\"/\")  → Alt-Svc, CDN",
       "    CSV'ye_yaz(satır); bekle(1,5 s)"]
yazi(sl, Cm(2.2), Cm(10.5), Cm(18), Cm(6.8), kod, 12, LACI, font="Consolas", aralik=1)
for i, (b, a, r) in enumerate((("Etik", "Tarama yok · siteler arası bekleme · sektör bazında raporlama", YESIL),
                               ("Hata yönetimi", "dns_hatasi · tls_hatasi · zaman_asimi (10 s) · kaldığı yerden devam",
                                MERCAN),
                               ("Paralel mod", "Farklı siteler eşzamanlı (4 iş parçacığı); siteye yük artmaz", MAVI))):
    y = Cm(9.4 + i * 2.75)
    kart(sl, Cm(21.0), y, Cm(11.2), Cm(2.45))
    sekil(sl, MSO_SHAPE.RECTANGLE, Cm(21.0), y + Cm(0.3), Cm(0.18), Cm(1.85), r)
    yazi(sl, Cm(21.6), y + Cm(0.2), Cm(10.4), Cm(0.8), b, 15, r, True)
    yazi(sl, Cm(21.6), y + Cm(1.0), Cm(10.4), Cm(1.4), a, 12, GRI, satir=0.95)

# =====================================================================================
# 12. UYGULAMA ORTAMI / VERİ SETİ
# =====================================================================================
sl = slayt("Uygulama ortamı ve veri seti", bolum="Uygulama ortamı", notlar=(
    "Veri seti sektörlere göre şöyle dağılıyor. Ölçümleri kendi dizüstü bilgisayarımdan, ev internetimle yaptım. "
    "Etik açıdan normal bir ziyaretçi gibi bağlandım, sonuçları kurum adı vermeden sektör bazında raporladım."))
cd = CategoryChartData()
cd.categories = [o["sektor"] for o in SEKT]
cd.add_series("Site", [o["n"] for o in SEKT])
gf = sl.shapes.add_chart(XL_CHART_TYPE.DOUGHNUT, Cm(1.6), Cm(4.6), Cm(14), Cm(12.8), cd).chart
stil_grafik(gf, 13)
gf.has_legend = True; gf.legend.position = XL_LEGEND_POSITION.RIGHT; gf.legend.include_in_layout = False
gf.legend.font.size = Pt(13)
pal = [MERCAN, MAVI, AMBER, YESIL, LACI2, GRI, NANE, RGBColor(0x8E, 0x6C, 0xC4)]
for i, pt in enumerate(gf.plots[0].series[0].points):
    pt.format.fill.solid(); pt.format.fill.fore_color.rgb = pal[i % len(pal)]
gf.plots[0].has_data_labels = True
gf.plots[0].data_labels.font.size = Pt(14); gf.plots[0].data_labels.font.color.rgb = BEYAZ
gf.plots[0].data_labels.font.bold = True
yazi(sl, Cm(2.2), Cm(3.6), Cm(13), Cm(1.0), f"Ölçülen site sayısı: {N_SITE}", 15, LACI, True)
ortam = (("Donanım", "Windows dizüstü · ev interneti (TR) · Wi-Fi"),
         ("Yazılım", "Python 3 · OpenSSL 4.0.3 · Wireshark 4.6.8"),
         ("Ölçüm turları", R.get("tur_bilgisi", "1. tur 7 Eki 2026 · 2. tur 8 Eki 2026")),
         ("Tekrar", "Hibrit ve klasik el sıkışma ×5, medyan"),
         ("Doğrulama", "Pilot ölçüm + Wireshark paket yakalama"))
for i, (b, a) in enumerate(ortam):
    y = Cm(3.9 + i * 2.7)
    kart(sl, Cm(16.8), y, Cm(15.4), Cm(2.35))
    yazi(sl, Cm(17.4), y, Cm(4.2), Cm(2.35), b, 15, YESIL, True, dikey=MSO_ANCHOR.MIDDLE)
    yazi(sl, Cm(21.6), y, Cm(10.4), Cm(2.35), a, 14, LACI, dikey=MSO_ANCHOR.MIDDLE)

# =====================================================================================
# 13. PERFORMANS ÖLÇÜTLERİ
# =====================================================================================
sl = slayt("Performans ölçütleri", bolum="Performans ölçütleri", notlar=(
    "Kanal TCP ile güvenilir hale geldiği için fiziksel katmandaki bit hataları uygulamaya segment kaybı ve yeniden "
    "iletim olarak yansıyor. Bu yüzden BER yerine segment kayıp oranını kullandım. Her ölçütün yanında ölçüm mü "
    "simülasyon mu olduğu yazıyor."))
olc = (("Hazırlık", "PQ destek · TLS sürümü · HRR", "s_client senaryoları", "ÖLÇÜM", YESIL),
       ("Veri miktarı", "CH / SH baytı · okunan/yazılan", "-msg çıktısı, pcap", "ÖLÇÜM", YESIL),
       ("Segment", "⌈(boyut + 9) / 1460⌉", "Hesap + Wireshark", "ÖLÇÜM", YESIL),
       ("Gecikme", "RTT · HRR ek RTT · süre farkı", "TCP connect ×5", "ÖLÇÜM", YESIL),
       ("Kayıp etkisi", "El sıkışma süresi · yeniden iletim", "Analitik + Monte Carlo", "SİMÜLASYON", MERCAN),
       ("Tutarlılık", "Turlar arası aynı sonuç oranı", "Tur karşılaştırması", "ÖLÇÜM", YESIL),
       ("Anlamlılık", "Fisher · Wilson GA · permütasyon", "SciPy", "İSTATİSTİK", MAVI),
       ("Ölçek", "Ek bayt × el sıkışma sayısı", "Hesaplama", "HESAP", AMBER))
for i, (b, a, y_, t, r) in enumerate(olc):
    x = Cm(1.6 + (i % 4) * 7.75); y = Cm(3.8 + (i // 4) * 6.9)
    kart(sl, x, y, Cm(7.25), Cm(6.4))
    yazi(sl, x + Cm(0.5), y + Cm(0.5), Cm(6.5), Cm(1.1), b, 19, LACI, True)
    yazi(sl, x + Cm(0.5), y + Cm(1.8), Cm(6.4), Cm(1.8), a, 14, LACI, satir=0.95)
    yazi(sl, x + Cm(0.5), y + Cm(3.7), Cm(6.4), Cm(1.0), y_, 12, GRI)
    rozet(sl, x + Cm(0.5), y + Cm(5.0), t, r, None, 10)

# =====================================================================================
# 14. BULGU 1: SEKTÖREL HAZIRLIK
# =====================================================================================
sl = slayt(f"Bulgu 1 · Sitelerin yalnızca %{tr(T['pq'])}'i kuantum sonrası hazır", bolum="Ölçülen sonuçlar", notlar=(
    f"{N_SITE} siteden {T['pq_k']}'i, yani yüzde {tr(T['pq'])}'i kuantum sonrası anahtar değişimini destekliyor. "
    f"Yüzde {tr(T['tls12'])}'i hâlâ yalnızca TLS 1.2. Sektörler arasında çok büyük fark var. Çubukta yeşil hazır "
    "olanları, mavi yalnızca klasik TLS 1.3'ü, turuncu ise hâlâ TLS 1.2 kullananları gösteriyor."))
kart(sl, Cm(1.6), Cm(3.8), Cm(20.2), Cm(13.6))
cd = CategoryChartData()
cd.categories = [f"{o['sektor']} ({o['n']})" for o in SEKT]
cd.add_series("Kuantum sonrası hazır", [o["pq"] for o in SEKT])
cd.add_series("Yalnız klasik TLS 1.3", [round(o["tls13"] - o["pq"], 1) for o in SEKT])
cd.add_series("Yalnız TLS 1.2", [o["tls12"] for o in SEKT])
gf = sl.shapes.add_chart(XL_CHART_TYPE.BAR_STACKED_100, Cm(2.0), Cm(4.2), Cm(19.4), Cm(12.9), cd).chart
stil_grafik(gf, 14)
gf.has_legend = True; gf.legend.position = XL_LEGEND_POSITION.BOTTOM; gf.legend.include_in_layout = False
gf.legend.font.size = Pt(12)
pl = gf.plots[0]; pl.gap_width = 45; pl.overlap = 100
for s_, r in zip(pl.series, (YESIL, MAVI, MERCAN)):
    s_.format.fill.solid(); s_.format.fill.fore_color.rgb = r
pl.has_data_labels = True
pl.data_labels.number_format = '0"%";;;'; pl.data_labels.number_format_is_linked = False
pl.data_labels.font.size = Pt(12); pl.data_labels.font.color.rgb = BEYAZ; pl.data_labels.font.bold = True
gf.category_axis.reverse_order = True; gf.category_axis.tick_labels.font.size = Pt(14)
gf.category_axis.format.line.fill.background()
gf.value_axis.visible = False; gf.value_axis.has_major_gridlines = False
buyuk_sayi(sl, Cm(22.4), Cm(3.8), Cm(9.8), f"%{tr(T['pq'])}",
           f"hazır ({T['pq_k']}/{T['n']}) · %95 GA {tr(T['pq_ci'][0])}–{tr(T['pq_ci'][1])}", YESIL, 40)
buyuk_sayi(sl, Cm(22.4), Cm(8.5), Cm(9.8), f"%{tr(T['tls12'])}", "hâlâ yalnız TLS 1.2 → önce sürüm yükseltmesi",
           MERCAN, 40)
en_iyi = max(SEKT, key=lambda o: o["pq"]); en_kotu = min(SEKT, key=lambda o: o["pq"])
buyuk_sayi(sl, Cm(22.4), Cm(13.2), Cm(9.8), f"%{tr(en_iyi['pq'], 0)} vs %{tr(en_kotu['pq'], 0)}",
           f"{en_iyi['sektor']} vs {en_kotu['sektor']}", AMBER, 32)

# =====================================================================================
# 15. BULGU 2: CDN
# =====================================================================================
sl = slayt("Bulgu 2 · Belirleyici sektör değil, altyapı (CDN)", bolum="Ölçülen sonuçlar", notlar=(
    f"En önemli bulgu bu. CDN arkasındaki {cdn_n} sitenin {cdn_k}'i hazır; kendi sunucusunu işleten {oz_n} siteden "
    f"sadece {oz_k}'si hazır. Sonra şunu sordum: banka olmak mı önemli, altyapı mı? CDN kullanımını sabit tutup "
    "sektör etiketlerini 20 bin kez karıştırdım; sektör farkı kayboldu. Yani geçiş kurumların kararıyla değil, "
    "altyapı sağlayıcıları sayesinde ilerliyor."))
for i, (pay, payda, et, r, z) in enumerate(((cdn_k, cdn_n, "CDN arkasındaki siteler", YESIL, YESIL_A),
                                            (oz_k, oz_n, "Kendi sunucusunu işletenler", MERCAN, MERCAN_A))):
    x = Cm(1.6 + i * 8.0)
    kart(sl, x, Cm(3.8), Cm(7.5), Cm(8.6), z, None)
    yazi(sl, x + Cm(0.6), Cm(4.3), Cm(6.6), Cm(0.8), et.upper(), 11, r, True)
    yazi(sl, x + Cm(0.6), Cm(5.2), Cm(6.6), Cm(2.6), f"%{tr(100 * pay / payda)}", 50, r, True)
    yazi(sl, x + Cm(0.6), Cm(7.9), Cm(6.6), Cm(0.9), f"{pay} / {payda} site hazır", 15, LACI)
    # oran çubuğu
    sekil(sl, MSO_SHAPE.ROUNDED_RECTANGLE, x + Cm(0.6), Cm(9.6), Cm(6.3), Cm(0.55), BEYAZ, None, yuvarlak=0.5)
    sekil(sl, MSO_SHAPE.ROUNDED_RECTANGLE, x + Cm(0.6), Cm(9.6), max(Cm(0.3), int(Cm(6.3) * pay / payda)),
          Cm(0.55), r, None, yuvarlak=0.5)
    yazi(sl, x + Cm(0.6), Cm(10.5), Cm(6.6), Cm(1.6),
         f"%95 GA: {tr(R['cdn_fisher']['cdn_ci' if i == 0 else 'kendi_ci'][0])}–"
         f"{tr(R['cdn_fisher']['cdn_ci' if i == 0 else 'kendi_ci'][1])}", 12, GRI)
kart(sl, Cm(1.6), Cm(13.0), Cm(15.5), Cm(4.4), LACI, None)
yazi(sl, Cm(2.2), Cm(13.3), Cm(14.5), Cm(0.8), "İSTATİSTİKSEL SINAMA", 11, NANE, True)
yazi(sl, Cm(2.2), Cm(14.1), Cm(14.5), Cm(3.2), [
    "CDN vs kendi sunucu: Fisher **p < 10⁻²⁵**",
    f"Katmansız sektör etkisi: χ² = {tr(R['sektor_kikare_katmansiz']['chi2'], 1)}, p < 10⁻¹⁰",
    f"CDN'e göre katmanlı: **p = {tr(R['sektor_permutasyon_cdn_katmanli']['p'], 2)}** → fark kaybolur"], 14, BEYAZ,
     aralik=3)
# katmanlı tablo
ks, kc = R["katman_kendi_sunucu"], R["katman_cdn"]
kart(sl, Cm(17.7), Cm(3.8), Cm(14.5), Cm(13.6))
yazi(sl, Cm(18.3), Cm(4.2), Cm(13.5), Cm(0.8), "CDN KULLANIMINA GÖRE KATMANLANMIŞ HAZIRLIK", 11, GRI, True)
for j, k in enumerate(("Sektör", "Kendi sunucusu", "CDN")):
    yazi(sl, [Cm(18.3), Cm(24.0), Cm(28.6)][j], Cm(5.2), Cm(5), Cm(0.8), k, 13, GRI, True)
sektor_adlari = list(ks.keys())
rh = min(Cm(1.25), int(Cm(10.2) / max(1, len(sektor_adlari) + 1)))
for i, s_ in enumerate(sektor_adlari + ["Toplam"]):
    y = Cm(6.1) + rh * i
    son = s_ == "Toplam"
    if son:
        sekil(sl, MSO_SHAPE.ROUNDED_RECTANGLE, Cm(18.0), y, Cm(13.9), rh, YESIL_A, None, yuvarlak=0.3)
    else:
        sekil(sl, MSO_SHAPE.RECTANGLE, Cm(18.3), y, Cm(13.3), Cm(0.02), CIZGI)
    a_ = f"{oz_k}/{oz_n}" if son else ks[s_]
    b_ = f"{cdn_k}/{cdn_n}" if son else (kc.get(s_, "–") if kc.get(s_) != "0/0" else "–")
    for j, v in enumerate((s_, a_, b_)):
        yazi(sl, [Cm(18.3), Cm(24.0), Cm(28.6)][j], y, Cm(5.5), rh, v, 14, YESIL if son else LACI, son,
             dikey=MSO_ANCHOR.MIDDLE)

# =====================================================================================
# 16. BULGU 3: AĞ MALİYETİ
# =====================================================================================
sl = slayt("Bulgu 3 · Ağ maliyeti: küçük ama yapısal", bolum="Ölçülen sonuçlar", notlar=(
    "Hibrit el sıkışmada istemci 1184, sunucu 1088 bayt fazla gönderiyor. Bu, ML-KEM'in sabit boyutlu anahtar ve "
    "şifre metninden geliyor; ServerHello tüm hazır sitelerde tam 1210 bayt. Tarayıcı benzeri ClientHello ölçülen "
    "sitelerin tamamında iki segment. Wireshark'ta aynı siteye klasik ClientHello 369 baytlık, hibrit 1591 baytlık "
    "çerçeve. 1514'ü aşmasının nedeni TSO: paket, ağ kartı bölmeden önce yakalanıyor. Kayıpsız ağda süre farkı "
    "ölçülemeyecek kadar küçük."))
kart(sl, Cm(1.6), Cm(3.8), Cm(19.0), Cm(13.6))
cd = CategoryChartData()
cd.categories = ["ClientHello", "ServerHello"]
cd.add_series("Klasik (X25519)", [AG["ch_klasik"], AG["sh_klasik"]])
cd.add_series("Hibrit (X25519MLKEM768)", [AG["ch_hibrit"], AG["sh_hibrit"]])
gf = sl.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Cm(2.0), Cm(4.2), Cm(18.2), Cm(12.9), cd).chart
stil_grafik(gf, 14)
gf.has_legend = True; gf.legend.position = XL_LEGEND_POSITION.TOP; gf.legend.include_in_layout = False
gf.legend.font.size = Pt(13)
pl = gf.plots[0]; pl.gap_width = 70; pl.overlap = -10
for s_, r in zip(pl.series, (MAVI, YESIL)):
    s_.format.fill.solid(); s_.format.fill.fore_color.rgb = r
pl.has_data_labels = True; pl.data_labels.number_format = '0" B"'; pl.data_labels.number_format_is_linked = False
pl.data_labels.font.size = Pt(15); pl.data_labels.font.bold = True; pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
gf.value_axis.visible = False; gf.value_axis.has_major_gridlines = False; gf.value_axis.maximum_scale = 1650
gf.category_axis.tick_labels.font.size = Pt(15)
buyuk_sayi(sl, Cm(21.2), Cm(3.8), Cm(11.0), f"+{int(ek_bayt)} B", "her el sıkışmada · 2 MB'lık sayfanın ≈ %0,11'i",
           YESIL, 36, h=Cm(3.9))
kart(sl, Cm(21.2), Cm(8.2), Cm(11.0), Cm(5.0))
yazi(sl, Cm(21.8), Cm(8.5), Cm(10), Cm(0.8), "WIRESHARK DOĞRULAMASI", 11, GRI, True)
for i, (a, k, h_) in enumerate((("ClientHello çerçevesi", "369 B", "1591 B"), ("ServerHello kaydı", "122 B", "1210 B"))):
    y = Cm(9.5 + i * 1.6)
    yazi(sl, Cm(21.8), y, Cm(5), Cm(1.2), a, 13, LACI, dikey=MSO_ANCHOR.MIDDLE)
    yazi(sl, Cm(26.8), y, Cm(2.3), Cm(1.2), k, 15, MAVI, True, PP_ALIGN.RIGHT, MSO_ANCHOR.MIDDLE)
    yazi(sl, Cm(29.1), y, Cm(2.8), Cm(1.2), h_, 15, YESIL, True, PP_ALIGN.RIGHT, MSO_ANCHOR.MIDDLE)
yazi(sl, Cm(21.8), Cm(12.4), Cm(10.4), Cm(0.8), "1591 B > 1514 B: TSO öncesi yakalama", 11, GRI)
buyuk_sayi(sl, Cm(21.2), Cm(13.6), Cm(11.0), f"{tr(AG['sure_farki_medyan_tur2'], 1)} ms",
           f"kayıpsız ağda ölçülen süre farkı (Wilcoxon p = {tr(AG['sure_wilcoxon_p'], 2)})", GRI, 30, h=Cm(3.8))

# =====================================================================================
# 17. BULGU 4: SİMÜLASYON
# =====================================================================================
sl = slayt("Bulgu 4 · Kayıplı kanalda ikinci segmentin bedeli", bolum="Simülasyon sonuçları", notlar=(
    "Gerçek internette paket kaybını kontrol edemediğim için ölçtüğüm paket boyutlarıyla bir Monte Carlo "
    "simülasyonu yaptım; bu bir ölçüm değil. Varsayımlar: bağımsız segment kaybı, RTO = RTT + 200 ms, SYN için 1 "
    "saniye. Analitik formül 1 eksi (1 eksi p) üzeri n, simülasyonla örtüşüyor. Yüzde 10 kayıpta ortalama süre yaklaşık "
    "yüzde 7 artıyor. Önemli nokta: tarayıcı, sunucu desteklemese de iki payı gönderiyor; hazır olmayan sunucuların "
    "kullanıcıları bu maliyeti korumasız ödüyor."))
rozet(sl, Cm(24.6), Cm(1.75), "SİMÜLASYON · ÖLÇÜM DEĞİL", MERCAN, None, 11, Cm(7.6))
kart(sl, Cm(1.6), Cm(3.8), Cm(19.0), Cm(13.6))
kay = [0.0, 0.005, 0.01, 0.02, 0.05, 0.10]
cd = CategoryChartData()
cd.categories = [f"%{tr(100 * k, 1 if k < 0.01 else 0)}" for k in kay]
cd.add_series("Klasik (1 segment)", [SIM[("Klasik", k)]["ortalama_ms"] for k in kay])
cd.add_series("Hibrit tarayıcı (2 segment)", [SIM[("Hibrit (tarayıcı)", k)]["ortalama_ms"] for k in kay])
gf = sl.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Cm(2.0), Cm(4.2), Cm(18.2), Cm(12.9), cd).chart
stil_grafik(gf, 13)
gf.has_legend = True; gf.legend.position = XL_LEGEND_POSITION.TOP; gf.legend.include_in_layout = False
gf.legend.font.size = Pt(13)
for s_, r in zip(gf.plots[0].series, (MAVI, YESIL)):
    s_.format.line.color.rgb = r; s_.format.line.width = Pt(3.25); s_.smooth = False
    s_.marker.size = 8; s_.marker.format.fill.solid(); s_.marker.format.fill.fore_color.rgb = r
    s_.marker.format.line.color.rgb = BEYAZ
gf.value_axis.has_major_gridlines = True
gf.value_axis.major_gridlines.format.line.color.rgb = CIZGI
gf.value_axis.format.line.fill.background()
gf.value_axis.has_title = True; gf.value_axis.axis_title.text_frame.text = "Ortalama el sıkışma süresi (ms)"
gf.value_axis.axis_title.text_frame.paragraphs[0].runs[0].font.size = Pt(12)
gf.category_axis.has_title = True; gf.category_axis.axis_title.text_frame.text = "Segment kayıp oranı (RTT = 20 ms)"
gf.category_axis.axis_title.text_frame.paragraphs[0].runs[0].font.size = Pt(12)
buyuk_sayi(sl, Cm(21.2), Cm(3.8), Cm(11.0), f"+%{tr(artis10, 1)}", "ortalama süre artışı · %10 kayıpta",
           YESIL, 38, h=Cm(3.9))
buyuk_sayi(sl, Cm(21.2), Cm(8.1), Cm(11.0),
           f"%{tr(100 * k01[0]['gecikme_olasiligi'], 1)} → %{tr(100 * k01[1]['gecikme_olasiligi'], 1)}",
           "yeniden iletim olasılığı · %1 kayıpta (P = 1 − (1 − p)ⁿ, n: 7 → 8)", MAVI, 28, h=Cm(3.9))
kart(sl, Cm(21.2), Cm(12.4), Cm(11.0), Cm(5.0), MERCAN_A, None)
yazi(sl, Cm(21.8), Cm(12.7), Cm(10), Cm(4.5), ["**Kritik nokta**",
                                               "Tarayıcı iki payı sunucu desteklemese de gönderir → hazır olmayan "
                                               "sitelerin kullanıcıları bu bedeli korumasız öder."], 14, MERCAN, aralik=4)

# =====================================================================================
# 18. TUTARLILIK + DÜNYA
# =====================================================================================
sl = slayt("Tutarlılık ve küresel karşılaştırma", bolum="Alternatiflerle karşılaştırma", notlar=(
    "Ölçüm turlarında sitelerin TLS sürümü, PQ desteği, seçilen grup ve sertifika bilgisi birebir aynı çıktı. "
    "Küresel olarak F5 yüzde 54 buluyor; bizdeki oran daha düşük ama örneklemimiz finans ve kamu ağırlıklı. "
    "Dikkat çekici olan yalnız TLS 1.2 oranı: dünya ortalamasının yaklaşık 2,5 katı."))
kart(sl, Cm(1.6), Cm(3.8), Cm(12.4), Cm(13.6))
yazi(sl, Cm(2.2), Cm(4.2), Cm(11.5), Cm(0.8), "ÖLÇÜM TURLARI ARASI TUTARLILIK", 11, GRI, True)
yazi(sl, Cm(2.2), Cm(5.0), Cm(11.5), Cm(2.6), f"{TUT['ayni_site']}/{TUT['toplam']}", 50, YESIL, True)
yazi(sl, Cm(2.2), Cm(7.6), Cm(11.4), Cm(1.6), "sitede TLS sürümü, PQ desteği, grup, HRR ve sertifika birebir aynı", 14,
     GRI)
for i, (a, b) in enumerate(((f"{TUT['ip_degisen']}", "sitenin IP'si değişti (çoğu CDN) → sonuç değişmedi"),
                            (f"r = {tr(TUT['rtt_pearson'], 2)}", "turlar arası RTT korelasyonu"))):
    y = Cm(10.0 + i * 3.4)
    sekil(sl, MSO_SHAPE.RECTANGLE, Cm(2.2), y, Cm(11.2), Cm(0.02), CIZGI)
    yazi(sl, Cm(2.2), y + Cm(0.3), Cm(11.2), Cm(1.4), a, 26, LACI, True)
    yazi(sl, Cm(2.2), y + Cm(1.7), Cm(11.2), Cm(1.4), b, 13, GRI)
kart(sl, Cm(14.6), Cm(3.8), Cm(17.6), Cm(13.6))
yazi(sl, Cm(15.2), Cm(4.2), Cm(16.6), Cm(0.8), "TÜRKİYE (BU PROJE) vs DÜNYA (F5 LABS, 2026)", 11, GRI, True)
cd = CategoryChartData()
cd.categories = ["PQ hazır", "CDN/Cloudflare hariç", "Yalnız TLS 1.2"]
cd.add_series("Türkiye", [T["pq"], round(100 * oz_k / oz_n, 1), T["tls12"]])
cd.add_series("Dünya", [54, 22, 10.5])
gf = sl.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Cm(15.0), Cm(5.0), Cm(16.8), Cm(12.1), cd).chart
stil_grafik(gf, 13)
gf.has_legend = True; gf.legend.position = XL_LEGEND_POSITION.TOP; gf.legend.include_in_layout = False
gf.legend.font.size = Pt(13)
pl = gf.plots[0]; pl.gap_width = 60; pl.overlap = -5
for s_, r in zip(pl.series, (MERCAN, GRI)):
    s_.format.fill.solid(); s_.format.fill.fore_color.rgb = r
pl.has_data_labels = True; pl.data_labels.number_format = '0.0"%"'; pl.data_labels.number_format_is_linked = False
pl.data_labels.font.size = Pt(13); pl.data_labels.font.bold = True; pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
gf.value_axis.visible = False; gf.value_axis.has_major_gridlines = False; gf.value_axis.maximum_scale = 65
gf.category_axis.tick_labels.font.size = Pt(13)

# =====================================================================================
# 19. ÖZGÜN KATKILAR
# =====================================================================================
sl = slayt("Projenin özgün mühendislik katkıları", bolum="Özgün katkılar", notlar=(
    "Dört katkı: Türkiye'ye özgü sektörel ölçüm, hazırlığın belirleyicisinin katmanlı istatistikle gösterilmesi, aynı "
    "veride katmanlar arası ağ maliyeti analizi ve açık araç. Bu çalışmayı bir bildiri olarak göndermeyi planlıyorum."))
kat = (("Türkiye'ye özgü sektörel PQ-TLS ölçümü", f"{len(SEKT)} kritik sektör · {N_LISTE} site · tekrarlı turlar", YESIL),
       ("Belirleyicinin istatistikle ayrıştırılması", "CDN'e göre katmanlı permütasyon: sektör değil altyapı", MAVI),
       ("Katmanlar arası ağ maliyeti", "TLS → TCP segmenti → Ethernet çerçevesi; ölçüm + pcap + simülasyon", AMBER),
       ("Açık ve tekrarlanabilir araç", "Python + OpenSSL + Docker; kurumlar kendi durumunu ölçebilir", MERCAN))
for i, (b, a, r) in enumerate(kat):
    x = Cm(1.6 + (i % 2) * 15.5); y = Cm(3.8 + (i // 2) * 6.9)
    kart(sl, x, y, Cm(15.1), Cm(6.4))
    yazi(sl, x + Cm(0.7), y + Cm(0.5), Cm(3), Cm(2.0), f"0{i + 1}", 40, r, True)
    yazi(sl, x + Cm(0.7), y + Cm(2.6), Cm(13.8), Cm(1.4), b, 19, LACI, True)
    yazi(sl, x + Cm(0.7), y + Cm(4.1), Cm(13.8), Cm(2.0), a, 14, GRI)

# =====================================================================================
# 20. SINIRLILIKLAR / GELECEK
# =====================================================================================
sl = slayt("Sınırlılıklar ve geliştirme önerileri", bolum="Sınırlılıklar", notlar=(
    "Sınırlılıklar: tek ölçüm noktası, yalnız ana sayfa, süre ölçümünde süreç başlatma yükü ve simülasyon "
    "varsayımları. Simülasyonu doğrulamak için Linux'ta netem ile kontrollü bir deney planladım."))
for k, (bas, r, z, maddeler) in enumerate((
        ("Sınırlılıklar", MERCAN, MERCAN_A, ["Tek ölçüm noktası (ev interneti, TR)",
                                             "Yalnız ana sayfa; alt alan adları yok",
                                             "Süre ölçümünde ≈ 1 s süreç yükü",
                                             "Simülasyon: bağımsız kayıp varsayımı",
                                             "CDN–kaynak sunucu bağlantısı görünmez"]),
        ("Planlanan çalışmalar", YESIL, YESIL_A, ["netem deneyi: MTU 1500, 20 ms, %0–10 kayıp",
                                                  "Periyodik ölçümle geçiş hızını izleme",
                                                  "e-Devlet ve internet bankacılığı alt alanları",
                                                  "Farklı ISS'ler ve mobil ağdan ölçüm",
                                                  "SMTP/STARTTLS ve QUIC'e uyarlama"]))):
    x = Cm(1.6 + k * 15.5)
    kart(sl, x, Cm(3.8), Cm(15.1), Cm(13.6))
    sekil(sl, MSO_SHAPE.RECTANGLE, x, Cm(3.8), Cm(15.1), Cm(0.15), r)
    yazi(sl, x + Cm(0.7), Cm(4.3), Cm(14), Cm(1.2), bas, 22, r, True)
    for i, m in enumerate(maddeler):
        y = Cm(6.0 + i * 2.2)
        ikon(sl, x + Cm(0.7), y, Cm(1.1), r, "×" if k == 0 else "→", 13, z)
        yazi(sl, x + Cm(2.2), y - Cm(0.1), Cm(12.4), Cm(1.4), m, 16, LACI, dikey=MSO_ANCHOR.MIDDLE)

# =====================================================================================
# 21. SONUÇ
# =====================================================================================
no[0] += 1
sl = prs.slides.add_slide(prs.slide_layouts[6])
bg = sl.background.fill; bg.solid(); bg.fore_color.rgb = LACI
kafes_deseni(sl, Cm(24.5), Cm(1.0), 9, 17, Cm(1.0), LACI2, Cm(0.16))
yazi(sl, Cm(2.2), Cm(1.6), Cm(20), Cm(0.8), "SONUÇ VE ÖNERİLER", 12, NANE, True)
yazi(sl, Cm(2.2), Cm(2.6), Cm(21.5), Cm(4.2), ["Geçiş başladı, ama **kurumların kararıyla değil,**",
                                               "**altyapı sağlayıcıları (CDN) sayesinde.**"], 28, BEYAZ, aralik=0)
for i, (s_, a) in enumerate(((f"%{tr(T['pq'])}", "siteler hazır"),
                             (f"{B['pq_k']}/{B['n']}" if B else "–", "banka hazır"),
                             (f"+{tr(ek_bayt / 1000)} KB", "el sıkışma başına"))):
    x = Cm(2.2 + i * 7.3)
    yazi(sl, x, Cm(7.0), Cm(7), Cm(1.8), s_, 34, NANE if i != 1 else AMBER, True)
    yazi(sl, x, Cm(8.8), Cm(7), Cm(0.9), a, 14, RGBColor(0xC9, 0xD3, 0xE6))
oner = ("Kendi sunucusu olanlar: önce TLS 1.3, sonra OpenSSL 3.5+ ile X25519MLKEM768",
        "Düzenleyiciler: finans sektörü için geçiş takvimi",
        "CDN kullananlar: CDN–kaynak sunucu bağlantısını da koru",
        "Ağ yöneticileri: parçalı ClientHello'yu işlemeyen cihazları güncelle")
for i, m in enumerate(oner):
    y = Cm(10.6 + i * 1.45)
    ikon(sl, Cm(2.2), y, Cm(0.95), YESIL, str(i + 1), 12)
    yazi(sl, Cm(3.6), y - Cm(0.1), Cm(19.5), Cm(1.2), m, 15, BEYAZ, dikey=MSO_ANCHOR.MIDDLE)
yazi(sl, Cm(2.2), Cm(16.8), Cm(20), Cm(1.2), "Teşekkürler · Sorular?", 22, NANE, True)
sl.notes_slide.notes_text_frame.text = (
    "Özetle: Türkiye'de kuantum sonrası geçiş başladı, ama kurumların kararıyla değil, CDN sağlayıcıları sayesinde. "
    "Kendi sunucusunu işleten bankalar ve kamu kurumları geride. Ağ maliyeti küçük ama yapısal. Dört önerim var. "
    "Teşekkür ederim, sorularınızı alabilirim.")

# =====================================================================================
# 22. KAYNAKÇA
# =====================================================================================
sl = slayt("Kaynakça (seçilmiş)", bolum="Kaynakça",
           notlar="Tam kaynakça raporda APA 7 formatında yer almaktadır.")
kaynak = ["Dubey, V. M., & Varshney, G. (2026). Measurement study of post-quantum readiness of Internet: 2026. arXiv:2606.16473.",
          "F5 Labs. (2026). 2026 state of PQC on the web. F5.",
          "Kwiatkowski, K., Kampanakis, P., Westerbaan, B. E., & Stebila, D. (2026). Post-quantum hybrid ECDHE-MLKEM key "
          "agreement for TLSv1.3 (draft-ietf-tls-ecdhe-mlkem-05). IETF.",
          "Mosca, M. (2018). Cybersecurity in an era with quantum computers: Will we be ready? IEEE Security & Privacy, 16(5), 38–41.",
          "National Institute of Standards and Technology. (2024). Module-lattice-based key-encapsulation mechanism standard (FIPS 203).",
          "Paquin, C., Stebila, D., & Tamvada, G. (2020). Benchmarking post-quantum cryptography in TLS. PQCrypto 2020, LNCS 12100, 72–91.",
          "Paxson, V., Allman, M., Chu, J., & Sargent, M. (2011). Computing TCP's retransmission timer (RFC 6298). IETF.",
          "Rescorla, E. (2018). The Transport Layer Security (TLS) protocol version 1.3 (RFC 8446). IETF.",
          "Shor, P. W. (1997). Polynomial-time algorithms for prime factorization and discrete logarithms on a quantum "
          "computer. SIAM Journal on Computing, 26(5), 1484–1509."]
kart(sl, Cm(1.6), Cm(3.8), Cm(30.6), Cm(13.6))
yazi(sl, Cm(2.3), Cm(4.3), Cm(29.3), Cm(12.8), kaynak, 13, LACI, aralik=7)

prs.core_properties.title = "Kuantum Sonrası TLS Hazırlığı"
prs.core_properties.author = "Rümeysa Betül Özyurt"
prs.save(CIKTI)
print("Kaydedildi:", CIKTI, "| slayt:", no[0])
