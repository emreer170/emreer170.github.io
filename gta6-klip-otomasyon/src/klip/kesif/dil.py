"""Baslik/ulke bilgisinden yayin dili tahmini (YouTube icin)."""
from __future__ import annotations

import re

_TR_HARF = set("ğĞşŞıİ")
_TR_KELIME = re.compile(
    r"\b(canl[ıi]|yay[ıi]n|t[üu]rk[çc]e|b[öo]l[üu]m|oynuyoruz|ilk bak[ıi]ş|"
    r"hikaye|ve|bir|ile|için|çok|yeni|geldi|başl[ıa]|izle)\b",
    re.IGNORECASE,
)


def dil_tahmin(baslik: str, bildirilen: str | None = None, ulke: str | None = None) -> str:
    """'tr', 'en' ya da 'diger' dondurur.

    Oncelik: yayincinin bildirdigi dil > basliktaki Turkce ipuclari >
    kanal ulkesi > Latin harfli baslik (en varsayilir).
    """
    if bildirilen:
        kod = bildirilen.lower().split("-")[0]
        return kod if kod in ("tr", "en") else "diger"
    if any(h in _TR_HARF for h in baslik) or len(_TR_KELIME.findall(baslik)) >= 2:
        return "tr"
    if (ulke or "").upper() == "TR":
        return "tr"
    harfler = [c for c in baslik if c.isalpha()]
    if harfler and sum(c.isascii() for c in harfler) / len(harfler) > 0.9:
        return "en"
    return "diger"
