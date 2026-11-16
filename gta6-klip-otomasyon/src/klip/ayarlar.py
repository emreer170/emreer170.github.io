"""Ayar dosyalari, dosya yollari ve gizli anahtarlarin okunmasi."""
from __future__ import annotations

import os
from pathlib import Path

import yaml


def kok() -> Path:
    """Proje kok klasoru: komutun calistirildigi yer (ya da KLIP_KOK)."""
    return Path(os.environ.get("KLIP_KOK") or Path.cwd())


def ayarlar_yolu() -> Path:
    return kok() / "config" / "ayarlar.yaml"


def allowlist_yolu() -> Path:
    return kok() / "config" / "allowlist.yaml"


def adaylar_yolu(ornek: bool = False) -> Path:
    return kok() / "data" / ("ornek_adaylar.json" if ornek else "adaylar.json")


def env_yukle() -> None:
    """.env dosyasindaki ANAHTAR=deger satirlarini ortam degiskenlerine ekler."""
    dosya = kok() / ".env"
    if not dosya.exists():
        return
    for satir in dosya.read_text(encoding="utf-8").splitlines():
        satir = satir.strip()
        if not satir or satir.startswith("#") or "=" not in satir:
            continue
        ad, deger = satir.split("=", 1)
        os.environ.setdefault(ad.strip(), deger.strip().strip("\"'"))


def ayarlari_oku() -> dict:
    with open(ayarlar_yolu(), encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def anahtar(ad: str) -> str | None:
    return os.environ.get(ad) or None
