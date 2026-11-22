#!/usr/bin/env python3
"""130 sitelik ilk listeyi 7 sektör, 500 siteye genişletir (veri/siteler_500.csv).
İlk 130 site aynen korunur (zaman içi karşılaştırma için). Alan adları elle derlenmiştir;
ölçümden önce dns_kontrol.py ile doğrulanmalı, çözülmeyenler düzeltilmelidir."""
import csv
import os

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
eski = list(csv.DictReader(open(os.path.join(KOK, "veri", "siteler.csv"), encoding="utf-8-sig")))

EK = {
    "Banka": """pashabank.com.tr aktifbank.com.tr hayatfinans.com.tr dunyakatilim.com.tr tombank.com.tr
        eximbank.gov.tr iller.gov.tr kalkinma.com.tr tskb.com.tr nurolbank.com.tr bankpozitif.com.tr
        citibank.com.tr misyonbank.com.tr turkishbank.com adabank.com.tr cepteteb.com.tr tbb.org.tr tkbb.org.tr""",
    "SigortaFinans": """anadolusigorta.com.tr allianz.com.tr axasigorta.com.tr aksigorta.com.tr sompo.com.tr
        mapfre.com.tr hdisigorta.com.tr turkiyesigorta.com.tr neovasigorta.com raysigorta.com.tr quicksigorta.com
        unicosigorta.com.tr dogasigorta.com bereketsigorta.com.tr ankarasigorta.com.tr generali.com.tr agesa.com.tr
        anadoluhayat.com.tr metlife.com.tr vakifemeklilik.com.tr bnpparibascardif.com.tr katilimemeklilik.com.tr
        borsaistanbul.com mkk.com.tr takasbank.com.tr isyatirim.com.tr garantibbvayatirim.com.tr
        yapikrediyatirim.com.tr akyatirim.com.tr gedik.com infoyatirim.com getmidas.com vakifyatirim.com.tr
        halkyatirim.com.tr ziraatyatirim.com.tr papara.com iyzico.com param.com.tr paycell.com.tr tosla.com
        ininal.com paytr.com troyodeme.com bkm.com.tr sigortam.net""",
    "Kamu": """diyanet.gov.tr danistay.gov.tr yargitay.gov.tr anayasa.gov.tr sayistay.gov.tr hsk.gov.tr ysk.gov.tr
        bddk.org.tr spk.gov.tr epdk.gov.tr rekabet.gov.tr kvkk.gov.tr tkgm.gov.tr nvi.gov.tr egm.gov.tr
        jandarma.gov.tr afad.gov.tr mgm.gov.tr kgm.gov.tr dsi.gov.tr tse.org.tr tubitak.gov.tr iskur.gov.tr
        turkpatent.gov.tr ptt.gov.tr trt.net.tr aa.com.tr iletisim.gov.tr sbb.gov.tr titck.gov.tr kosgeb.gov.tr
        ssb.gov.tr mta.gov.tr ogm.gov.tr vgm.gov.tr toki.gov.tr uyap.gov.tr mit.gov.tr
        adana.bel.tr aydin.bel.tr balikesir.bel.tr denizli.bel.tr diyarbakir.bel.tr erzurum.bel.tr eskisehir.bel.tr
        gaziantep.bel.tr hatay.bel.tr kayseri.bel.tr mardin.bel.tr manisa.bel.tr kahramanmaras.bel.tr malatya.bel.tr
        mersin.bel.tr mugla.bel.tr ordu.bel.tr sakarya.bel.tr samsun.bel.tr sanliurfa.bel.tr tekirdag.bel.tr
        trabzon.bel.tr van.bel.tr
        istanbul.gov.tr ankara.gov.tr izmir.gov.tr bursa.gov.tr antalya.gov.tr adana.gov.tr konya.gov.tr
        gaziantep.gov.tr kocaeli.gov.tr mersin.gov.tr diyarbakir.gov.tr kayseri.gov.tr samsun.gov.tr trabzon.gov.tr
        erzurum.gov.tr eskisehir.gov.tr""",
    "Universite": """ibu.edu.tr adu.edu.tr agri.edu.tr aku.edu.tr amasya.edu.tr ardahan.edu.tr artvin.edu.tr
        aksaray.edu.tr balikesir.edu.tr bartin.edu.tr batman.edu.tr bayburt.edu.tr bilecik.edu.tr bingol.edu.tr
        beu.edu.tr mehmetakif.edu.tr btu.edu.tr comu.edu.tr karatekin.edu.tr hitit.edu.tr dicle.edu.tr trakya.edu.tr
        ebyu.edu.tr erzurum.edu.tr gantep.edu.tr giresun.edu.tr gumushane.edu.tr hakkari.edu.tr mku.edu.tr
        igdir.edu.tr sdu.edu.tr isparta.edu.tr iuc.edu.tr medeniyet.edu.tr ikc.edu.tr bakircay.edu.tr ksu.edu.tr
        karabuk.edu.tr kmu.edu.tr kafkas.edu.tr kastamonu.edu.tr agu.edu.tr klu.edu.tr kku.edu.tr ahievran.edu.tr
        kilis.edu.tr ktun.edu.tr erbakan.edu.tr dpu.edu.tr ozal.edu.tr cbu.edu.tr artuklu.edu.tr mersin.edu.tr
        mu.edu.tr alparslan.edu.tr nevsehir.edu.tr ohu.edu.tr odu.edu.tr erdogan.edu.tr subu.edu.tr siirt.edu.tr
        sinop.edu.tr cumhuriyet.edu.tr harran.edu.tr sirnak.edu.tr nku.edu.tr gop.edu.tr munzur.edu.tr usak.edu.tr
        yyu.edu.tr yalova.edu.tr bozok.edu.tr beun.edu.tr ahbv.edu.tr aybu.edu.tr asbu.edu.tr sbu.edu.tr iste.edu.tr
        atu.edu.tr msgsu.edu.tr gsu.edu.tr tau.edu.tr
        atilim.edu.tr cankaya.edu.tr etu.edu.tr ufuk.edu.tr thk.edu.tr istinye.edu.tr isikun.edu.tr iku.edu.tr
        okan.edu.tr beykent.edu.tr gelisim.edu.tr arel.edu.tr esenyurt.edu.tr nisantasi.edu.tr uskudar.edu.tr
        fsm.edu.tr izu.edu.tr 29mayis.edu.tr acibadem.edu.tr bezmialem.edu.tr biruni.edu.tr halic.edu.tr
        altinbas.edu.tr maltepe.edu.tr topkapi.edu.tr yeniyuzyil.edu.tr ieu.edu.tr yasar.edu.tr tedu.edu.tr
        hku.edu.tr sanko.edu.tr cag.edu.tr antalya.edu.tr mef.edu.tr khas.edu.tr ostimteknik.edu.tr""",
    "ETicaret": """koctas.com.tr bauhaus.com.tr tekzen.com.tr e-bebek.com toyzzshop.com decathlon.com.tr
        sportive.com.tr network.com.tr vakko.com ipekyol.com.tr colins.com.tr ltbjeans.com kigili.com
        altinyildizclassics.com sarar.com derimod.com.tr hotic.com.tr desa.com.tr penti.com suwen.com.tr
        karaca.com emsan.com.tr bellona.com.tr istikbal.com.tr dogtas.com enzahome.com.tr armut.com biletix.com
        obilet.com enuygun.com jollytur.com etstur.com istegelsin.com sokmarket.com.tr bim.com.tr
        macrocenter.com.tr sephora.com.tr rossmann.com.tr eve.com.tr flormar.com.tr pttavm.com modanisa.com
        dsdamat.com incehesap.com itopya.com arabam.com emlakjet.com hepsiemlak.com cimri.com akakce.com""",
    "Saglik": """acibadem.com.tr memorial.com.tr medicalpark.com.tr livhospital.com florence.com.tr
        amerikanhastanesi.org medipol.com.tr medicana.com.tr dunyagoz.com hisarhospital.com medistate.com.tr
        anadolusaglik.org medline.com.tr bayindirhastanesi.com.tr guven.com.tr batigoz.com yeditepehastaneleri.com
        hospitadent.com enabiz.gov.tr mhrs.gov.tr teb.org.tr ttb.org.tr selcukecza.com.tr abdiibrahim.com.tr
        eczacibasi.com.tr duzen.com.tr""",
    "Altyapi": """turktelekom.com.tr turkcell.com.tr vodafone.com.tr superonline.net turknet.com.tr
        millenicom.com.tr dsmart.com.tr turksat.com.tr nic.tr botas.gov.tr teias.gov.tr euas.gov.tr epias.com.tr
        enerjisa.com.tr igdas.istanbul baskentdogalgaz.com.tr tupras.com.tr opet.com.tr shell.com.tr
        petrolofisi.com.tr bedas.com.tr ayedas.com.tr toroslaredas.com.tr iski.istanbul aski.gov.tr izsu.gov.tr
        turkishairlines.com flypgs.com ajet.com sunexpress.com istairport.com sabihagokcen.aero
        tcddtasimacilik.gov.tr tcdd.gov.tr metro.istanbul iett.istanbul ido.com.tr dhmi.gov.tr udhb.gov.tr
        kiyiemniyeti.gov.tr aselsan.com.tr havelsan.com.tr roketsan.com.tr tusas.com""",
}
# Hedef dağılım (toplam 500); ilk listedeki siteler her zaman korunur.
HEDEF = {"Banka": 45, "SigortaFinans": 45, "Kamu": 110, "Universite": 150, "ETicaret": 80, "Saglik": 26,
         "Altyapi": 44}

satirlar, gorulen = [], set()
for r in eski:
    a = r["alan_adi"].strip().lower()
    satirlar.append((r["sektor"], a)); gorulen.add(a)
for sektor, metin in EK.items():
    mevcut = sum(1 for s, _ in satirlar if s == sektor)
    for d in metin.split():
        a = d if d.startswith("www.") else "www." + d
        if a in gorulen or mevcut >= HEDEF[sektor]:
            continue
        satirlar.append((sektor, a)); gorulen.add(a); mevcut += 1

yol = os.path.join(KOK, "veri", "siteler_500.csv")
with open(yol, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["sektor", "alan_adi"]); w.writerows(satirlar)
from collections import Counter
print(Counter(s for s, _ in satirlar), "toplam", len(satirlar), "->", yol)
