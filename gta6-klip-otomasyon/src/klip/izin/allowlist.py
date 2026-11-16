"""Izin listesi (allowlist): yalnizca burada onayli yayincilarin icerigi islenir."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

IZIN_TURLERI = ("acik_politika", "yazili_onay")
PLATFORMLAR = ("youtube", "twitch")

_BASLIK = """\
# IZIN LISTESI (allowlist)
# Sistem YALNIZCA bu listedeki, aktif ve kaniti olan yayincilarin icerigini isler.
# Elle duzenleyebilir ya da "klip izin ekle ..." komutunu kullanabilirsin.
#
# izin_turu:
#   acik_politika -> yayincinin herkese acik klip/yeniden kullanim politikasi var
#   yazili_onay   -> yayinci sana yazili (e-posta/DM) izin verdi
# kanit: politikanin linki ya da onay ekran goruntusunun/e-postanin yeri (ZORUNLU)
"""


class IzinHatasi(ValueError):
    pass


def oku(yol: Path) -> list[dict]:
    if not yol.exists():
        return []
    veri = yaml.safe_load(yol.read_text(encoding="utf-8")) or {}
    return veri.get("yayincilar") or []


def yaz(yol: Path, kayitlar: list[dict]) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    govde = yaml.safe_dump({"yayincilar": kayitlar}, allow_unicode=True, sort_keys=False)
    yol.write_text(_BASLIK + govde, encoding="utf-8")


def anahtar(kayit: dict) -> str:
    return f"{kayit.get('platform')}:{kayit.get('kanal_id')}"


def kayit_hatalari(kayit: dict) -> list[str]:
    hatalar = []
    if kayit.get("platform") not in PLATFORMLAR:
        hatalar.append(f"platform {PLATFORMLAR} icinden olmali")
    if not str(kayit.get("kanal_id") or "").strip():
        hatalar.append("kanal_id bos")
    if kayit.get("izin_turu") not in IZIN_TURLERI:
        hatalar.append(f"izin_turu {IZIN_TURLERI} icinden olmali")
    if not str(kayit.get("kanit") or "").strip():
        hatalar.append("kanit bos (politika linki ya da onay belgesi sart)")
    return hatalar


def dogrula(kayitlar: list[dict]) -> list[str]:
    """Tum listeyi denetler; sorunlari okunabilir satirlar olarak dondurur."""
    sorunlar, gorulen = [], set()
    for i, k in enumerate(kayitlar, 1):
        ad = k.get("kanal_adi") or anahtar(k)
        for h in kayit_hatalari(k):
            sorunlar.append(f"{i}. kayit ({ad}): {h}")
        if anahtar(k) in gorulen:
            sorunlar.append(f"{i}. kayit ({ad}): ayni kanal iki kez yazilmis")
        gorulen.add(anahtar(k))
    return sorunlar


def izinliler(kayitlar: list[dict]) -> set[str]:
    """Aktif VE gecerli kayitlarin 'platform:kanal_id' kumesi."""
    return {anahtar(k) for k in kayitlar
            if k.get("aktif", True) and not kayit_hatalari(k)}


def izinli_mi(kayitlar: list[dict], platform: str, kanal_id: str) -> bool:
    """Sonraki moduller (hype, kurgu, yayin) islemeden once bunu cagirir."""
    return f"{platform}:{kanal_id}" in izinliler(kayitlar)


def ekle(kayitlar: list[dict], platform: str, kanal_id: str, kanal_adi: str,
         izin_turu: str, kanit: str, kosullar: str = "", url: str = "") -> dict:
    yeni = {
        "platform": platform, "kanal_id": str(kanal_id), "kanal_adi": kanal_adi,
        "url": url, "izin_turu": izin_turu, "kanit": kanit,
        "izin_tarihi": date.today().isoformat(), "kosullar": kosullar, "aktif": True,
    }
    hatalar = kayit_hatalari(yeni)
    if hatalar:
        raise IzinHatasi("; ".join(hatalar))
    if any(anahtar(k) == anahtar(yeni) for k in kayitlar):
        raise IzinHatasi(f"{anahtar(yeni)} zaten listede")
    kayitlar.append(yeni)
    return yeni
