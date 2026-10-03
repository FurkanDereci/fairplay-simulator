# ADR-0005 — CLV için Sentetik Kapanış Çizgisi (ADR-0004'ü geçersiz kılar)

- **Durum:** Kabul edildi
- **Tarih:** 2026-09-30
- **Bağlam:** ADR-0004, kapanış oranı vekili olarak vig'siz **fair oranı** seçmişti. Uygulamada
  görüldü ki bu seçim CLV'yi **yapı gereği** hep negatife kilitliyor: fair oran her zaman bookmaker
  oranından uzundur (marj nedeniyle), dolayısıyla `O_konulan / O_fair − 1 < 0`. Arayüzde beş kuponun
  CLV'si de negatif çıktı (−3.94, −5.17, −3.94, −3.37, −4.32). **Bilgi taşımayan bir metrik,
  olmayan metriktir** — bu yüzden ADR-0004 reddedildi.

## Karar

Kapanış oranı, açılış oranının **deterministik piyasa hareketi** olarak modellenir:

```
bp        = sha256("{match_id}:{selection}") ilk 4 bayt mod 1201 − 600     # −600 … +600 baz puan
O_kapanış = yuvarla(O_açılış × (1 + bp/10000), 2)
```

Hareket ±%6 aralığında ve **iki yöne de** açıktır. Aynı (maç, seçim) her zaman aynı hareketi verir
→ determinizm korunur, replay (I2) etkilenmez.

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| Fair oranı vekil tutmak (ADR-0004) | CLV'yi yapı gereği negatife kilitler; bilgi taşımaz — **reddedildi** |
| CLV'yi hiç göstermeme | Sözleşmede (`20-accounting-spec.md` §3.3) var; sütun boş kalırdı |
| Gerçek kapanış akışı (The Odds API) | MVP'de ağ + anahtar yönetimi; ileride aynı alan gerçek değerle dolar |
| Kayıtsız rastgele hareket | Determinizmi bozar, tekrar üretilemez, test edilemez |

## Sonuçlar

- (+) CLV artık işaret değiştirir: "çizgi lehime mi hareket etti?" sorusuna cevap verir.
- (+) Determinizm korunur; `closing_odds` saf, tekrar üretilebilir bir fonksiyondur.
- (+) Sözleşme değişmez: gerçek kapanış akışı gelince aynı alan gerçek değerle doldurulur.
- (−) Model **sentetiktir** ve gerçek piyasa hareketine kalibre değildir (düzgün dağılım varsayar).
  Bu, mock fikstür kataloğu ve Poisson maç motoruyla aynı sınıftadır: sentetik, ama açıkça yazılı.
- **Regresyon koruması:** `tests/api/test_api.py::test_clv_is_not_always_negative`, CLV'nin tek
  işarete kilitlenmesini engeller.

## İlgili not — aynı sınıftan bir uyarı

Kelly ve EV de aynı tuzağa açıktır: `p` olarak **piyasanın fair olasılığı** kullanılırsa `f*`
her zaman 0 çıkar (G-9). Bu yüzden Kelly şu an arayüzde **gösterilmiyor**: anlamlı olması için
kullanıcının kendi olasılık tahminine ihtiyaç var. Bu ayrı bir karar gerektirir (kullanıcı `p`
girişi mi, model `p` üretimi mi).
