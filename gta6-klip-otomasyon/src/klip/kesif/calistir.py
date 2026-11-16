"""Kesif modulunun ana akisi."""
from __future__ import annotations

from klip import ayarlar, http
from klip.kesif.model import Aday
from klip.kesif.twitch import TwitchKesif
from klip.kesif.youtube import YouTubeKesif


def kesif_yap(cfg: dict, platform: str = "hepsi", istek=http.istek,
              anahtar=ayarlar.anahtar, log=print) -> list[Aday]:
    """Ayarlara gore platformlari tarar. Anahtari eksik platform atlanir."""
    diller = cfg.get("diller", ["tr", "en"])
    k = cfg.get("kesif", {})
    oyun = cfg.get("oyun", {})
    adaylar: list[Aday] = []
    denenen = 0

    if platform in ("hepsi", "twitch"):
        cid, sec = anahtar("TWITCH_CLIENT_ID"), anahtar("TWITCH_CLIENT_SECRET")
        if not (cid and sec):
            log("! Twitch atlandi: TWITCH_CLIENT_ID / TWITCH_CLIENT_SECRET tanimli degil.")
        else:
            denenen += 1
            tw = TwitchKesif(cid, sec, istek=istek)
            adlar = oyun.get("twitch_kategori_adlari", [])
            bulunan = tw.oyun_bul(adlar)
            if not bulunan:
                log(f"! Twitch'te kategori bulunamadi: {adlar} "
                    "(oyun cikmamis ya da kategori adi farkli olabilir).")
            else:
                oyun_id, ad = bulunan
                for dil in diller:
                    liste = tw.yayinlar(oyun_id, dil, k.get("twitch_dil_basina_sayfa", 1))
                    log(f"  Twitch [{ad}] dil={dil}: {len(liste)} canli yayin")
                    adaylar += liste

    if platform in ("hepsi", "youtube"):
        api = anahtar("YOUTUBE_API_KEY")
        if not api:
            log("! YouTube atlandi: YOUTUBE_API_KEY tanimli degil.")
        else:
            denenen += 1
            yt = YouTubeKesif(api, istek=istek)
            liste = yt.yayinlar(oyun.get("youtube_sorgular", []), diller,
                                k.get("youtube_sorgu_basina_sonuc", 50))
            log(f"  YouTube: {len(liste)} canli yayin (harcanan kota ~{yt.kota} birim)")
            adaylar += liste

    if denenen == 0:
        raise SystemExit("Hic API anahtari bulunamadi. README'deki 'Anahtarlar' "
                         "bolumune bak ya da '--ornek' ile ornek veriyle dene.")
    alt = k.get("min_izleyici", 0)
    return [a for a in adaylar if a.izleyici >= alt]
