# gta6-klip-otomasyon

GTA 6 yayınlarındaki en heyecanlı anları bulup Türkçe altyazılı Shorts / TikTok /
Reels ve derleme videolarına çeviren hat. Yalnızca **izin listesindeki**
yayıncıların içeriği işlenir.

## Durum

| # | Modül | Durum |
|---|-------|-------|
| 1 | Keşif (YouTube + Twitch, TR/EN aday listesi) | ✅ kod + testler hazır; canlı çalıştırma için anahtar gerekli |
| 2 | İzin listesi (allowlist) | ✅ hazır |
| 3 | Hype tespiti | ⏳ |
| 4 | Kurgu (ffmpeg, Whisper, Gemini) | ⏳ |
| 5 | Format (dikey kısa / yatay derleme) | ⏳ |
| 6 | Yayın (YouTube yükleme + insan onayı) | ⏳ |
| 7 | Zamanlama (GitHub Actions) | 🟡 keşif için hazır (`.github/workflows/kesif.yml`) |

## Kurulum (bir kez)

Bilgisayarında [Python 3.10+](https://www.python.org/downloads/) kurulu olmalı.
Proje klasöründe bir terminal aç:

```bash
pip install -e ".[dev]"
pytest -q                 # hepsi "passed" olmalı
klip kesif --ornek        # anahtarsız, uydurma örnek veriyle deneme
```

## Anahtarlar

Anahtarlar koda **yazılmaz**. Bilgisayarında `.env` dosyasında, GitHub'da
*Settings → Secrets and variables → Actions* altında durur.

1. `.env.example` dosyasını `.env` adıyla kopyala.
2. **Twitch** — <https://dev.twitch.tv/console/apps> → *Register Your Application*
   (hesapta iki adımlı doğrulama açık olmalı). OAuth Redirect URL:
   `http://localhost`, Category: *Application Integration*, Client Type:
   *Confidential*. Oluşan **Client ID** ve *New Secret* ile aldığın
   **Client Secret** değerlerini `.env` dosyasına yaz.
3. **YouTube** — <https://console.cloud.google.com> → yeni proje →
   *APIs & Services → Library* → "YouTube Data API v3" → *Enable* →
   *Credentials → Create credentials → API key*. Anahtarı
   `YOUTUBE_API_KEY` olarak yaz. (Anahtarı *API restrictions* altında yalnızca
   YouTube Data API v3 ile sınırla.)
4. Aynı üç değeri GitHub deposuna secret olarak ekle (adlar `.env` ile aynı).

> **Kota uyarısı:** YouTube günde 10.000 birim verir. Bir keşif taraması ~200
> birim, bir video yüklemesi ~1.600 birim harcar. Yükleme için ayrı bir Google
> Cloud projesi açmak, keşfin yükleme kotasını yemesini önler.

## Kullanım

```bash
klip kesif                       # iki platformu tara, data/adaylar.json + .csv güncelle
klip kesif --platform twitch     # yalnızca Twitch
klip adaylar --dil tr            # kayıtlı Türkçe adayları göster

# İzin listesi
klip izin ekle twitch:12345 --tur yazili_onay --kanit "docs/onaylar/ornek.png" --kosul "kanal linki açıklamada"
klip izin ekle youtube:UCxxxx --tur acik_politika --kanit "https://yayinci.com/klip-politikasi"
klip izin liste
klip izin dogrula
```

`data/adaylar.csv` Excel / Google Sheets ile açılabilir. Bir kanal kaç taramada
görüldüğü (`gorulme_sayisi`) ve en yüksek izleyicisiyle birlikte tutulur;
düzenli yayın yapan büyük kanallar üstte çıkar.

### Adaydan izinliye

1. `klip adaylar` ile listeye bak.
2. Yayıncının açık klip politikası var mı kontrol et; yoksa
   [`docs/izin-mesaji.md`](docs/izin-mesaji.md) şablonuyla yaz.
3. Kanıtı sakla, `klip izin ekle` ile listeye al.

Kanıtı olmayan, türü geçersiz ya da `aktif: false` olan kayıt izinli sayılmaz;
sonraki modüller işlemeye başlamadan önce `izinli_mi()` denetimini çağırır.

## Klasörler

```
config/ayarlar.yaml    oyun adı, sorgular, diller, eşikler
config/allowlist.yaml  izin listesi
data/                  aday listesi (keşif çıktısı)
docs/                  izin mesajı şablonları
src/klip/kesif/        Modül 1
src/klip/izin/         Modül 2
src/klip/ornek/        örnek modun uydurma verisi
tests/                 testler
```

## Bilinen sınırlar

- Oyun çıkana kadar Twitch'te kategori bulunmayabilir; kesin kategori adını
  `config/ayarlar.yaml` içine ekle.
- YouTube'da "GTA 6" araması başlığında GTA 6 geçen alakasız yayınları da
  getirir (ör. GTA 5 RP). Aday listesi bu yüzden elle gözden geçirilir.
- YouTube'da dil, yayıncı bildirmediyse başlıktan ve kanal ülkesinden tahmin edilir.
