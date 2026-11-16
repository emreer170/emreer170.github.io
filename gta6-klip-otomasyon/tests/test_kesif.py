from klip.kesif import depo
from klip.kesif.calistir import kesif_yap
from klip.kesif.dil import dil_tahmin
from klip.kesif.model import Aday
from klip.kesif.twitch import TwitchKesif
from klip.kesif.youtube import YouTubeKesif
from klip.ornek import ornek_anahtar, ornek_istek

CFG = {
    "oyun": {"twitch_kategori_adlari": ["Grand Theft Auto VI"], "youtube_sorgular": ["GTA 6"]},
    "diller": ["tr", "en"],
    "kesif": {"min_izleyici": 5, "twitch_dil_basina_sayfa": 1},
}


def test_dil_tahmin():
    assert dil_tahmin("GTA 6 CANLI YAYIN - İlk Bakış") == "tr"
    assert dil_tahmin("GTA 6 live", bildirilen="tr") == "tr"
    assert dil_tahmin("GTA 6 live", ulke="TR") == "tr"
    assert dil_tahmin("GTA 6 Day One Walkthrough", bildirilen="en-US") == "en"
    assert dil_tahmin("GTA 6 online heists") == "en"
    assert dil_tahmin("GTA 6 EN DIRECTO", bildirilen="es") == "diger"
    assert dil_tahmin("GTA 6 прямой эфир") == "diger"


def test_twitch_token_bir_kez_alinir_ve_dile_gore_ayrilir():
    cagrilar = []

    def istek(method, url, params=None, headers=None):
        cagrilar.append((method, url, headers))
        return ornek_istek(method, url, params, headers)

    tw = TwitchKesif("id", "gizli", istek=istek)
    oyun_id, _ = tw.oyun_bul(["Grand Theft Auto 6", "Grand Theft Auto VI"])
    tr = tw.yayinlar(oyun_id, "tr")
    en = tw.yayinlar(oyun_id, "en")
    assert [a.kanal_adi for a in tr] == ["OrnekTRYayinci1", "OrnekTRYayinci2", "OrnekTRKucuk"]
    assert all(a.dil == "en" for a in en) and len(en) == 3
    assert tr[0].url == "https://www.twitch.tv/ornek_tr_yayinci1"
    assert sum("oauth2/token" in u for _, u, _ in cagrilar) == 1
    assert cagrilar[-1][2]["Authorization"] == "Bearer ornek-token"


def test_twitch_sayfalama():
    def istek(method, url, params=None, headers=None):
        if "token" in url:
            return {"access_token": "t"}
        after = dict(params).get("after")
        uid = "2" if after else "1"
        return {"data": [{"user_id": uid, "user_login": "u" + uid, "user_name": "U" + uid,
                          "type": "live", "viewer_count": 10, "language": "en", "title": ""}],
                "pagination": {} if after else {"cursor": "c1"}}

    assert [a.kanal_id for a in TwitchKesif("i", "s", istek=istek).yayinlar("g", "en", 5)] == ["1", "2"]


def test_youtube_adaylar_ve_kota():
    yt = YouTubeKesif("anahtar", istek=ornek_istek)
    adaylar = {a.kanal_id: a for a in yt.yayinlar(["GTA 6"], ["tr", "en"])}
    assert "UC_sample_en_3" not in adaylar            # bitmis yayin elenir
    assert adaylar["UC_ornek_tr_1"].dil == "tr"       # basliktan
    assert adaylar["UC_ornek_tr_2"].dil == "tr"       # bildirilen dilden
    assert adaylar["UC_sample_en_1"].dil == "en"
    assert adaylar["UC_sample_es_1"].dil == "diger"
    assert adaylar["UC_ornek_tr_1"].izleyici == 12700
    assert adaylar["UC_ornek_tr_1"].takipci == 845000
    assert adaylar["UC_sample_en_2"].takipci is None  # gizli abone sayisi
    assert yt.kota == 2 * 100 + 1 + 1                 # 2 arama + videos + channels


def test_anahtar_basliga_yazilir_urlye_degil():
    gorulen = []

    def istek(method, url, params=None, headers=None):
        gorulen.append((url, dict(params), headers))
        return {"items": []}

    YouTubeKesif("COK-GIZLI", istek=istek).yayinlar(["GTA 6"], ["tr"])
    url, params, headers = gorulen[0]
    assert "COK-GIZLI" not in url and "COK-GIZLI" not in str(params)
    assert headers["X-Goog-Api-Key"] == "COK-GIZLI"


def test_kesif_min_izleyici_ve_eksik_anahtar():
    mesajlar = []
    hepsi = kesif_yap(CFG, istek=ornek_istek, anahtar=ornek_anahtar, log=mesajlar.append)
    assert "OrnekTRKucuk" not in [a.kanal_adi for a in hepsi]   # 3 izleyici < 5
    assert {a.platform for a in hepsi} == {"twitch", "youtube"}

    yalniz_tw = kesif_yap(CFG, istek=ornek_istek, log=mesajlar.append,
                          anahtar=lambda ad: None if ad == "YOUTUBE_API_KEY" else "x")
    assert {a.platform for a in yalniz_tw} == {"twitch"}
    assert any("YouTube atlandi" in m for m in mesajlar)


def test_depo_birlestirme(tmp_path):
    def aday(izleyici, ad="Kanal"):
        return Aday("twitch", "1", ad, "u", "tr", izleyici, "b")

    veri = depo.birlestir({"adaylar": {}}, [aday(100)], simdi="2026-11-19T10:00:00Z")
    veri = depo.birlestir(veri, [aday(50, "YeniAd"), aday(70, "YeniAd")], simdi="2026-11-19T16:00:00Z")
    k = veri["adaylar"]["twitch:1"]
    assert k["gorulme_sayisi"] == 2 and k["en_yuksek_izleyici"] == 100
    assert k["son_izleyici"] == 70 and k["kanal_adi"] == "YeniAd"
    assert k["ilk_gorulme"] == "2026-11-19T10:00:00Z" and k["son_gorulme"] == "2026-11-19T16:00:00Z"

    yol = tmp_path / "adaylar.json"
    csv_yolu = depo.yaz(yol, veri, izinliler={"twitch:1"})
    assert depo.oku(yol) == veri
    assert "evet" in csv_yolu.read_text(encoding="utf-8-sig")
