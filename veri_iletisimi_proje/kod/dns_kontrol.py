#!/usr/bin/env python3
"""Ölçümden ÖNCE site listesindeki alan adlarının çözülüp çözülmediğini kontrol eder.
Çözülmeyenler için 'www.' olmadan dener ve öneri verir. Hiçbir siteye bağlanmaz.

Kullanım:  python3 dns_kontrol.py --girdi ../veri/siteler_500.csv
Çıktı:     dns_sorunlu.csv  (düzeltilmesi gereken satırlar)"""
import argparse
import csv
import socket
from concurrent.futures import ThreadPoolExecutor


def coz(alan):
    try:
        return socket.getaddrinfo(alan, 443, type=socket.SOCK_STREAM)[0][4][0]
    except OSError:
        return None


def kontrol(satir):
    sektor, alan = satir
    ip = coz(alan)
    if ip:
        return sektor, alan, ip, ""
    yalin = alan[4:] if alan.startswith("www.") else "www." + alan
    return sektor, alan, None, (yalin if coz(yalin) else "BULUNAMADI")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--girdi", default="../veri/siteler_500.csv")
    ap.add_argument("--cikti", default="dns_sorunlu.csv")
    a = ap.parse_args()
    with open(a.girdi, encoding="utf-8-sig") as f:
        satirlar = [(r["sektor"], r["alan_adi"].strip()) for r in csv.DictReader(f)]
    with ThreadPoolExecutor(16) as ex:
        sonuc = list(ex.map(kontrol, satirlar))
    sorunlu = [r for r in sonuc if r[2] is None]
    print(f"{len(satirlar)} alan adı, {len(satirlar) - len(sorunlu)} çözüldü, {len(sorunlu)} sorunlu")
    for s, alan, _, oneri in sorunlu:
        print(f"  {s:<14} {alan:<36} öneri: {oneri}")
    with open(a.cikti, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["sektor", "alan_adi", "oneri"])
        w.writerows((s, alan, o) for s, alan, _, o in sorunlu)
    print(f"Sorunlu liste: {a.cikti}  (öneri 'www.'siz sürümse siteler_500.csv'de düzeltin; "
          f"BULUNAMADI ise satırı silin veya doğru alan adını yazın)")


if __name__ == "__main__":
    main()
