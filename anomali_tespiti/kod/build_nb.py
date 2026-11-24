import json, sys
from pathlib import Path
C = Path(__file__).parent
def md(s): return {"cell_type": "markdown", "metadata": {}, "source": s}
def code(s): return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s}
def wf(name): return code(f"%%writefile /content/code/{name}\n" + (C / name).read_text())
cells = [
 md("# Hafta 9-10: Tüm fan ID'leri, 8 kanal ve makine ID sınıflandırıcısı\n\n"
    "Bu defter Hafta 1-8 defterinin devamıdır. Yenilikler:\n\n"
    "1. **Veri:** fan id_00, 02, 04, 06 × +6 / 0 / −6 dB, **8 kanalın tamamı** (öncekinde yalnızca id_00 ve ilk kanal).\n"
    "2. **8 kanal birleştirme:** `ch1` (ilk kanal), `ort8` (8 kanal dalga ortalaması), `gort8` (8 kanal güç spektrogramı ortalaması).\n"
    "3. **Makine ID sınıflandırıcısı** (proje planındaki, yapılmamış model): yalnızca normal seslerle, sesin hangi fana ait olduğunu öğrenen CNN + SpecAugment. Anomali skoru = −log p(doğru ID).\n"
    "4. **ID-XAI (önerilen, etiketsiz):** XAI öznitelik seçimi arıza etiketi yerine makine kimliği ile yapılır (RF bire karşı diğerleri, yalnız normal kayıt) + kNN, k ∈ {5,10,20,33} topluluğu, 1. kanal + 8 kanal ortalaması öznitelikleri.\n"
    "5. **Füzyon:** ID sınıflandırıcısı ve öznitelik kNN skorlarının sıra ortalaması (etiket kullanmaz).\n"
    "6. 3 tohum, tohum **bölünmeyi de** değiştirir; dengeli protokol + tez protokolü; AUC ve pAUC.\n\n"
    "Tüm ara dosyalar Drive'da `mimii/hafta9` altında tutulur; oturum koparsa hücreleri tekrar çalıştırmak kaldığı yerden devam eder."),
 code("from google.colab import drive\ndrive.mount('/content/drive')\n!pip install -q librosa soundfile scikit-learn\n"
      "import os; os.makedirs('/content/code', exist_ok=True)\n"
      "WORK = '/content/drive/MyDrive/mimii/hafta9'; os.makedirs(WORK, exist_ok=True); os.chdir(WORK); print(os.getcwd())"),
 md("## Kod modülleri\n`hand.py`: Hafta 7'deki 145 öznitelik. `feats.py`: 8 kanallı kayıttan üç modda log-mel ve öznitelik. `prep_colab.py`: zip'i bütün halde indirip açmadan işler. `exp.py`: modeller. `run.py`: deney koşucusu. `analyze.py`: tablolar ve füzyon. `plots.py`: şekiller."),
 wf("hand.py"), wf("feats.py"), wf("prep_colab.py"), wf("exp.py"), wf("run.py"), wf("sel.py"), wf("analyze.py"), wf("final_tables.py"), wf("plots.py"),
 md("## 1. Veri hazırlığı (SNR başına ~10 GB indirme, sonra silinir; Drive'a yalnızca öznitelikler yazılır, SNR başına ~1,3 GB)"),
 code("for snr in ['6', '0', '-6']:\n    !python /content/code/prep_colab.py {snr}\n!ls -la feat"),
 md("## 2. Deneyler\nGPU'da ID sınıflandırıcısı tam genişlikte (w=32, 40 epoch) çalışır. Sonuç satırları `results.csv`, klip skorları `scores/` altına yazılır."),
 code("A = 'id_00,id_02,id_04,id_06'\nfor snr in ['6', '0', '-6']:\n"
      "    !python /content/code/run.py {snr} {A} knn,hand ch1,ort8,gort8 42,43,44\n"
      "    !python /content/code/run.py {snr} {A} idxai ch1,ort8,both 42,43,44\n"
      "    !IDC_W=32 IDC_EP=40 python /content/code/run.py {snr} {A} idc ch1,gort8 42,43,44\n"
      "    !python /content/code/run.py {snr} {A} dense ch1 42"),
 code("# Tez protokolü (normallerin %80'i eğitim; %20 normal + tüm arızalılar test) — tez Tablo 4.6 / 4.16 ile kıyas için\n"
      "for snr in ['6', '0', '-6']:\n"
      "    !PROTO=tez python /content/code/run.py {snr} {A} knn,hand,idxai ch1,ort8,both 42,43,44\n"
      "    !PROTO=tez IDC_W=32 IDC_EP=40 python /content/code/run.py {snr} {A} idc ch1 42,43,44"),
 md("## 3. XAI öznitelik seçimi: arıza etiketli (tez yöntemi) ve etiketsiz ID-XAI, k ve detektör taraması + ablasyonlar"),
 code("!python /content/code/sel.py 6,0,-6 42,43,44 h_ch1\n!DROP_LEVEL=1 PROTOS=F KS=5,10,20 python /content/code/sel.py 6,0,-6 42,43,44 h_ch1\n!PROTOS=F KS=5,10,20 python /content/code/sel.py 6,0,-6 42,43,44 h_ort8"),
 md("## 4. Tablolar, istatistik testleri ve şekiller"),
 code("!python /content/code/analyze.py denge > /dev/null\n!python /content/code/analyze.py tez > /dev/null\n!python /content/code/final_tables.py\n!python /content/code/plots.py\n"
      "from IPython.display import Image, display\ndisplay(Image('sekil8_hafta9.png')); display(Image('sekil9_hafta9.png')); display(Image('sekil10_hafta10.png'))"),
]
nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": []}, "kernelspec": {"display_name": "Python 3", "name": "python3"}}, "nbformat": 4, "nbformat_minor": 0}
Path(sys.argv[1]).write_text(json.dumps(nb, ensure_ascii=False, indent=1))
print("yazıldı", sys.argv[1])
