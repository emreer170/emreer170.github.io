"""Ornek mod: gercek API yerine paketle gelen UYDURMA yanitlari dondurur.

Amac, anahtarlar alinmadan once ciktinin neye benzedigini gormek ve testlerde
ayni veriyi kullanmaktir. Kanal adlari ve sayilar gercek degildir.
"""
from __future__ import annotations

import json
from pathlib import Path

_KLASOR = Path(__file__).parent


def _yukle(ad: str) -> dict:
    return json.loads((_KLASOR / ad).read_text(encoding="utf-8"))


def ornek_anahtar(ad: str) -> str:
    return "ornek"


def ornek_istek(method: str, url: str, params=None, headers=None) -> dict:
    p = dict(params or [])
    if "oauth2/token" in url:
        return {"access_token": "ornek-token"}
    if url.endswith("/games"):
        return _yukle("twitch_games.json")
    if url.endswith("/streams"):
        veri = _yukle("twitch_streams.json")
        return {"data": [y for y in veri["data"] if y["language"] == p.get("language")],
                "pagination": {}}
    if url.endswith("/search"):
        return _yukle("youtube_search.json")
    if url.endswith("/videos"):
        return _yukle("youtube_videos.json")
    if url.endswith("/channels"):
        return _yukle("youtube_channels.json")
    raise ValueError(f"Ornek modda bilinmeyen adres: {url}")
