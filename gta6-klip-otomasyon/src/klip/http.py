"""Kucuk HTTP yardimcisi (ek kutuphane gerektirmez)."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request


class ApiHatasi(RuntimeError):
    pass


def istek(method: str, url: str, params=None, headers=None) -> dict:
    """JSON donduren bir HTTP istegi yapar.

    params: dict ya da (ad, deger) listesi. Hata mesajlarina sorgu
    parametreleri yazilmaz; boylece anahtarlar loglara sizmaz.
    """
    sorgu = urllib.parse.urlencode(params or [], doseq=True)
    if method == "POST":
        req = urllib.request.Request(url, data=sorgu.encode(), method="POST")
    else:
        req = urllib.request.Request(f"{url}?{sorgu}" if sorgu else url)
    for ad, deger in (headers or {}).items():
        req.add_header(ad, deger)
    try:
        with urllib.request.urlopen(req, timeout=30) as yanit:
            return json.loads(yanit.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        govde = e.read().decode("utf-8", "replace")[:500]
        raise ApiHatasi(f"{url} -> HTTP {e.code}: {govde}") from None
    except urllib.error.URLError as e:
        raise ApiHatasi(f"{url} -> baglanti hatasi: {e.reason}") from None
