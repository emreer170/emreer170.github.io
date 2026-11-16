"""Komut satiri: klip kesif | adaylar | izin ..."""
from __future__ import annotations

import argparse

from klip import ayarlar
from klip.izin import allowlist
from klip.kesif import depo
from klip.kesif.calistir import kesif_yap


def _tablo(kayitlar: list[dict], izinli: set[str], limit: int) -> None:
    print(f"{'#':>3} {'platform':8} {'dil':5} {'izleyici':>8} {'gorulme':>7} {'izin':4}  kanal  (kimlik)")
    for i, k in enumerate(kayitlar[:limit], 1):
        kimlik = f"{k['platform']}:{k['kanal_id']}"
        print(f"{i:>3} {k['platform']:8} {k['dil']:5} {k['en_yuksek_izleyici']:>8} "
              f"{k['gorulme_sayisi']:>7} {'EVET' if kimlik in izinli else '-':4}  "
              f"{k['kanal_adi']}  ({kimlik})")
    if len(kayitlar) > limit:
        print(f"... ve {len(kayitlar) - limit} kanal daha (tam liste CSV dosyasinda)")


def cmd_kesif(a) -> int:
    cfg = ayarlar.ayarlari_oku()
    if a.ornek:
        from klip.ornek import ornek_anahtar, ornek_istek
        print("ORNEK MOD: gercek API cagrilmiyor, uydurma ornek veri kullaniliyor.")
        yeni = kesif_yap(cfg, a.platform, istek=ornek_istek, anahtar=ornek_anahtar)
    else:
        yeni = kesif_yap(cfg, a.platform)
    yol = ayarlar.adaylar_yolu(a.ornek)
    onceki = depo.oku(yol)
    onceki_sayi = len(onceki["adaylar"])
    veri = depo.birlestir(onceki, yeni)
    izinli = allowlist.izinliler(allowlist.oku(ayarlar.allowlist_yolu()))
    csv_yolu = depo.yaz(yol, veri, izinli)
    print(f"\nBu taramada {len(yeni)} yayin; listede toplam {len(veri['adaylar'])} kanal "
          f"({len(veri['adaylar']) - onceki_sayi} yeni).")
    for dil in cfg.get("diller", []):
        print(f"\n--- {dil.upper()} adaylari ---")
        _tablo(depo.sirali(veri, dil), izinli, a.limit)
    print(f"\nKaydedildi: {yol}  ve  {csv_yolu}")
    return 0


def cmd_adaylar(a) -> int:
    veri = depo.oku(ayarlar.adaylar_yolu(a.ornek))
    izinli = allowlist.izinliler(allowlist.oku(ayarlar.allowlist_yolu()))
    _tablo(depo.sirali(veri, a.dil), izinli, a.limit)
    return 0


def cmd_izin_liste(a) -> int:
    kayitlar = allowlist.oku(ayarlar.allowlist_yolu())
    if not kayitlar:
        print("Izin listesi bos. 'klip izin ekle ...' ile ekleyebilirsin.")
    gecerli = allowlist.izinliler(kayitlar)
    for k in kayitlar:
        durum = "AKTIF" if allowlist.anahtar(k) in gecerli else "GECERSIZ/PASIF"
        print(f"[{durum}] {k.get('kanal_adi')} ({allowlist.anahtar(k)}) "
              f"- {k.get('izin_turu')} - kanit: {k.get('kanit')}")
    return 0


def cmd_izin_dogrula(a) -> int:
    kayitlar = allowlist.oku(ayarlar.allowlist_yolu())
    sorunlar = allowlist.dogrula(kayitlar)
    for s in sorunlar:
        print("HATA:", s)
    if sorunlar:
        return 1
    print(f"Izin listesi gecerli: {len(allowlist.izinliler(kayitlar))} aktif yayinci.")
    return 0


def cmd_izin_ekle(a) -> int:
    if ":" not in a.kimlik:
        print("Kimlik 'platform:kanal_id' biciminde olmali (ornek: twitch:12345).")
        return 1
    platform, kanal_id = a.kimlik.split(":", 1)
    aday = depo.oku(ayarlar.adaylar_yolu())["adaylar"].get(a.kimlik, {})
    ad = a.ad or aday.get("kanal_adi")
    if not ad:
        print("Bu kanal aday listesinde yok; --ad ile kanal adini ver.")
        return 1
    url = aday.get("url", "")
    if platform == "youtube":
        url = f"https://www.youtube.com/channel/{kanal_id}"
    yol = ayarlar.allowlist_yolu()
    kayitlar = allowlist.oku(yol)
    try:
        allowlist.ekle(kayitlar, platform, kanal_id, ad, a.tur, a.kanit, a.kosul, url)
    except allowlist.IzinHatasi as e:
        print("Eklenemedi:", e)
        return 1
    allowlist.yaz(yol, kayitlar)
    print(f"Eklendi: {ad} ({a.kimlik}) -> {yol}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="klip", description="GTA 6 klip otomasyonu")
    alt = p.add_subparsers(dest="komut", required=True)

    k = alt.add_parser("kesif", help="Canli yayinlari tara, aday listesini guncelle")
    k.add_argument("--platform", choices=["hepsi", "youtube", "twitch"], default="hepsi")
    k.add_argument("--ornek", action="store_true", help="API yerine ornek veriyle calis")
    k.add_argument("--limit", type=int, default=15)
    k.set_defaults(f=cmd_kesif)

    ad = alt.add_parser("adaylar", help="Kayitli aday listesini goster")
    ad.add_argument("--dil", choices=["tr", "en", "diger"])
    ad.add_argument("--ornek", action="store_true")
    ad.add_argument("--limit", type=int, default=30)
    ad.set_defaults(f=cmd_adaylar)

    iz = alt.add_parser("izin", help="Izin listesi (allowlist) islemleri")
    izalt = iz.add_subparsers(dest="alt", required=True)
    izalt.add_parser("liste", help="Listeyi goster").set_defaults(f=cmd_izin_liste)
    izalt.add_parser("dogrula", help="Listeyi denetle").set_defaults(f=cmd_izin_dogrula)
    e = izalt.add_parser("ekle", help="Yayinci ekle")
    e.add_argument("kimlik", help="platform:kanal_id (aday tablosundaki kimlik)")
    e.add_argument("--tur", required=True, choices=allowlist.IZIN_TURLERI)
    e.add_argument("--kanit", required=True, help="Politika linki ya da onay belgesinin yeri")
    e.add_argument("--kosul", default="", help="Yayincinin koydugu sartlar")
    e.add_argument("--ad", help="Kanal adi (aday listesinde yoksa)")
    e.set_defaults(f=cmd_izin_ekle)

    a = p.parse_args(argv)
    ayarlar.env_yukle()
    return a.f(a)
