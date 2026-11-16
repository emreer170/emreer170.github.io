"""YouTube Data API v3 ile canli oyun yayinlarini bulur.

Kota maliyeti: search.list = 100 birim, videos.list = 1, channels.list = 1.
Gunluk ucretsiz kota 10.000 birimdir; arama sayisini dusuk tut.
"""
from __future__ import annotations

from klip import http
from klip.kesif.dil import dil_tahmin
from klip.kesif.model import Aday

API = "https://www.googleapis.com/youtube/v3"
OYUN_KATEGORISI = "20"  # YouTube "Gaming" kategorisi


def _parcalar(liste: list[str], boyut: int = 50):
    for i in range(0, len(liste), boyut):
        yield liste[i:i + boyut]


class YouTubeKesif:
    def __init__(self, api_anahtari: str, istek=http.istek):
        # Anahtar URL'ye degil basliga yazilir; hata mesajlarina sizmaz.
        self._basliklar = {"X-Goog-Api-Key": api_anahtari}
        self._istek = istek
        self.kota = 0  # bu calistirmada harcanan tahmini kota

    def _get(self, yol: str, params: dict, maliyet: int) -> dict:
        self.kota += maliyet
        return self._istek("GET", f"{API}/{yol}", params=params, headers=self._basliklar)

    def canli_ara(self, sorgu: str, dil: str, en_fazla: int = 50) -> list[dict]:
        yanit = self._get("search", {
            "part": "snippet", "type": "video", "eventType": "live",
            "q": sorgu, "relevanceLanguage": dil, "order": "viewCount",
            "videoCategoryId": OYUN_KATEGORISI, "maxResults": min(en_fazla, 50),
        }, maliyet=100)
        return yanit.get("items", [])

    def _detay(self, yol: str, part: str, idler: list[str]) -> dict[str, dict]:
        sonuc: dict[str, dict] = {}
        for grup in _parcalar(sorted(set(idler))):
            yanit = self._get(yol, {"part": part, "id": ",".join(grup),
                                    "maxResults": 50}, maliyet=1)
            for oge in yanit.get("items", []):
                sonuc[oge["id"]] = oge
        return sonuc

    def yayinlar(self, sorgular: list[str], diller: list[str], en_fazla: int = 50) -> list[Aday]:
        bulunan: dict[str, dict] = {}  # video_id -> arama sonucu
        for sorgu in sorgular:
            for dil in diller:
                for oge in self.canli_ara(sorgu, dil, en_fazla):
                    vid = (oge.get("id") or {}).get("videoId")
                    if vid:
                        bulunan.setdefault(vid, oge)
        if not bulunan:
            return []

        videolar = self._detay("videos", "snippet,liveStreamingDetails", list(bulunan))
        kanallar = self._detay(
            "channels", "snippet,statistics",
            [o["snippet"]["channelId"] for o in bulunan.values()])

        adaylar: list[Aday] = []
        for vid, oge in bulunan.items():
            video = videolar.get(vid)
            if not video:
                continue
            canli = video.get("liveStreamingDetails") or {}
            if "concurrentViewers" not in canli:
                continue  # yayin bitmis ya da izleyici sayisi gizli
            vs = video.get("snippet", {})
            kanal_id = vs.get("channelId") or oge["snippet"]["channelId"]
            kanal = kanallar.get(kanal_id, {})
            ulke = (kanal.get("snippet") or {}).get("country")
            ist = kanal.get("statistics") or {}
            abone = None if ist.get("hiddenSubscriberCount") else ist.get("subscriberCount")
            baslik = vs.get("title", "")
            adaylar.append(Aday(
                platform="youtube",
                kanal_id=kanal_id,
                kanal_adi=vs.get("channelTitle", ""),
                url=f"https://www.youtube.com/watch?v={vid}",
                dil=dil_tahmin(baslik, vs.get("defaultAudioLanguage") or vs.get("defaultLanguage"), ulke),
                izleyici=int(canli["concurrentViewers"]),
                baslik=baslik,
                takipci=int(abone) if abone is not None else None,
                ulke=ulke,
                etiketler=(vs.get("tags") or [])[:10],
            ))
        return adaylar
