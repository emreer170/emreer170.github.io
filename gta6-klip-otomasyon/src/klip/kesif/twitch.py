"""Twitch Helix API ile bir oyun kategorisindeki canli yayinlari bulur."""
from __future__ import annotations

from klip import http
from klip.kesif.model import Aday

TOKEN_URL = "https://id.twitch.tv/oauth2/token"
HELIX = "https://api.twitch.tv/helix"


class TwitchKesif:
    def __init__(self, client_id: str, client_secret: str, istek=http.istek):
        self._id = client_id
        self._secret = client_secret
        self._istek = istek
        self._token: str | None = None

    def _basliklar(self) -> dict:
        if self._token is None:
            yanit = self._istek("POST", TOKEN_URL, params={
                "client_id": self._id,
                "client_secret": self._secret,
                "grant_type": "client_credentials",
            })
            self._token = yanit["access_token"]
        return {"Client-Id": self._id, "Authorization": f"Bearer {self._token}"}

    def oyun_bul(self, adlar: list[str]) -> tuple[str, str] | None:
        """Verilen adlardan ilk eslesen kategorinin (id, ad) bilgisini dondurur."""
        yanit = self._istek("GET", f"{HELIX}/games",
                            params=[("name", a) for a in adlar],
                            headers=self._basliklar())
        bulunan = {o["name"]: o["id"] for o in yanit.get("data", [])}
        for ad in adlar:
            if ad in bulunan:
                return bulunan[ad], ad
        return None

    def yayinlar(self, oyun_id: str, dil: str, sayfa_sayisi: int = 1) -> list[Aday]:
        adaylar: list[Aday] = []
        imlec = None
        for _ in range(sayfa_sayisi):
            params = [("game_id", oyun_id), ("language", dil), ("first", "100")]
            if imlec:
                params.append(("after", imlec))
            yanit = self._istek("GET", f"{HELIX}/streams", params=params,
                                headers=self._basliklar())
            for y in yanit.get("data", []):
                if y.get("type") != "live":
                    continue
                d = y.get("language") or dil
                adaylar.append(Aday(
                    platform="twitch",
                    kanal_id=y["user_id"],
                    kanal_adi=y.get("user_name") or y.get("user_login", ""),
                    url=f"https://www.twitch.tv/{y.get('user_login', '')}",
                    dil=d if d in ("tr", "en") else "diger",
                    izleyici=int(y.get("viewer_count", 0)),
                    baslik=y.get("title", ""),
                    etiketler=y.get("tags") or [],
                ))
            imlec = (yanit.get("pagination") or {}).get("cursor")
            if not imlec:
                break
        return adaylar
