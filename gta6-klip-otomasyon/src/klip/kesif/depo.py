"""Aday listesinin dosyada saklanmasi (JSON + okunabilir CSV)."""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from klip.kesif.model import Aday

CSV_SUTUNLAR = ["platform", "kanal_adi", "dil", "en_yuksek_izleyici", "takipci",
                "gorulme_sayisi", "izinli", "url", "son_baslik", "kanal_id",
                "ilk_gorulme", "son_gorulme"]


def oku(yol: Path) -> dict:
    if not yol.exists():
        return {"guncellendi": None, "adaylar": {}}
    return json.loads(yol.read_text(encoding="utf-8"))


def birlestir(mevcut: dict, yeni: list[Aday], simdi: str | None = None) -> dict:
    """Yeni gorulen yayinlari mevcut listeye isler; kanal basina tek kayit tutar."""
    simdi = simdi or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    adaylar = mevcut.setdefault("adaylar", {})
    # Ayni kanal bir taramada iki kez gelirse en yuksek izleyicili olan kalir.
    tekil: dict[str, Aday] = {}
    for a in yeni:
        if a.anahtar not in tekil or a.izleyici > tekil[a.anahtar].izleyici:
            tekil[a.anahtar] = a
    for anahtar, a in tekil.items():
        k = adaylar.get(anahtar)
        if k is None:
            k = adaylar[anahtar] = {
                "platform": a.platform, "kanal_id": a.kanal_id,
                "ilk_gorulme": simdi, "gorulme_sayisi": 0, "en_yuksek_izleyici": 0,
            }
        k.update({
            "kanal_adi": a.kanal_adi, "url": a.url, "dil": a.dil,
            "son_izleyici": a.izleyici, "son_baslik": a.baslik,
            "ulke": a.ulke or k.get("ulke"),
            "takipci": a.takipci if a.takipci is not None else k.get("takipci"),
            "son_gorulme": simdi,
        })
        k["gorulme_sayisi"] += 1
        k["en_yuksek_izleyici"] = max(k["en_yuksek_izleyici"], a.izleyici)
    mevcut["guncellendi"] = simdi
    return mevcut


def sirali(veri: dict, dil: str | None = None) -> list[dict]:
    kayitlar = [k for k in veri.get("adaylar", {}).values() if not dil or k["dil"] == dil]
    return sorted(kayitlar, key=lambda k: -k["en_yuksek_izleyici"])


def yaz(yol: Path, veri: dict, izinliler: set[str] = frozenset()) -> Path:
    """JSON'u ve yanina ayni adla CSV'yi yazar. CSV yolunu dondurur."""
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    csv_yolu = yol.with_suffix(".csv")
    with open(csv_yolu, "w", newline="", encoding="utf-8-sig") as f:  # Excel icin BOM
        w = csv.DictWriter(f, fieldnames=CSV_SUTUNLAR, extrasaction="ignore")
        w.writeheader()
        for k in sirali(veri):
            izinli = "evet" if f"{k['platform']}:{k['kanal_id']}" in izinliler else ""
            w.writerow({**k, "izinli": izinli})
    return csv_yolu
