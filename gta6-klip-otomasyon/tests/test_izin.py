import pytest

from klip import cli
from klip.izin import allowlist as al


def test_ekle_dogrula_izinli_mi(tmp_path):
    kayitlar = []
    al.ekle(kayitlar, "twitch", "1001", "OrnekTR", "yazili_onay", "docs/onaylar/ornek.png")
    assert al.izinli_mi(kayitlar, "twitch", "1001")
    assert not al.izinli_mi(kayitlar, "twitch", "9999")
    assert not al.izinli_mi(kayitlar, "youtube", "1001")
    assert al.dogrula(kayitlar) == []

    yol = tmp_path / "allowlist.yaml"
    al.yaz(yol, kayitlar)
    assert al.oku(yol) == kayitlar
    assert yol.read_text(encoding="utf-8").startswith("# IZIN LISTESI")


def test_kanitsiz_ya_da_pasif_kayit_izinli_sayilmaz():
    kayitlar = [
        {"platform": "twitch", "kanal_id": "1", "izin_turu": "yazili_onay", "kanit": ""},
        {"platform": "twitch", "kanal_id": "2", "izin_turu": "sozlu", "kanit": "x"},
        {"platform": "twitch", "kanal_id": "3", "izin_turu": "acik_politika", "kanit": "https://x", "aktif": False},
        {"platform": "twitch", "kanal_id": "4", "izin_turu": "acik_politika", "kanit": "https://x"},
        {"platform": "twitch", "kanal_id": "4", "izin_turu": "acik_politika", "kanit": "https://x"},
    ]
    assert al.izinliler(kayitlar) == {"twitch:4"}
    sorunlar = al.dogrula(kayitlar)
    assert len(sorunlar) == 3 and "iki kez" in sorunlar[-1]


def test_ekle_reddeder():
    kayitlar = []
    with pytest.raises(al.IzinHatasi):
        al.ekle(kayitlar, "twitch", "1", "A", "yazili_onay", kanit="")
    al.ekle(kayitlar, "twitch", "1", "A", "yazili_onay", "k")
    with pytest.raises(al.IzinHatasi):
        al.ekle(kayitlar, "twitch", "1", "A", "yazili_onay", "k")


def test_cli_uctan_uca(tmp_path, monkeypatch, capsys):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "ayarlar.yaml").write_text(
        "oyun:\n  twitch_kategori_adlari: ['Grand Theft Auto VI']\n  youtube_sorgular: ['GTA 6']\n"
        "diller: [tr, en]\nkesif: {min_izleyici: 5}\n", encoding="utf-8")
    monkeypatch.setenv("KLIP_KOK", str(tmp_path))

    assert cli.main(["kesif", "--ornek"]) == 0
    assert (tmp_path / "data" / "ornek_adaylar.csv").exists()
    # gercek aday listesi bos -> ad verilmeden eklenemez, kanit zorunlu
    assert cli.main(["izin", "ekle", "twitch:1001", "--tur", "yazili_onay", "--kanit", "k"]) == 1
    assert cli.main(["izin", "ekle", "twitch:1001", "--tur", "yazili_onay", "--kanit", "k",
                     "--ad", "OrnekTRYayinci1"]) == 0
    assert cli.main(["izin", "dogrula"]) == 0
    capsys.readouterr()
    cli.main(["adaylar", "--ornek", "--dil", "tr"])
    cikti = capsys.readouterr().out
    satir = next(s for s in cikti.splitlines() if "twitch:1001" in s)
    assert "EVET" in satir
