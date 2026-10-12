# ADR-0021 — İstek Telemetrisi: Rate Limiting Ertelemesinin Gözlenebilir Koşulu

- **Durum:** Kabul edildi
- **Tarih:** 2026-10-12
- **Bağlam:** `docs/30` rate limiting'i **"gerçek kötüye kullanım gözlemlendiğinde"** diye erteiyor;
  `docs/ROADMAP` ve `docs/00` aynı koşulu tekrarlıyor. Ama **kötüye kullanımı gözleyecek araç
  tanımlı değildi**: `/healthz` var, istek/429 telemetrisi yok. PM raporu (R-4, Ö-11) bunu işaret
  etti — erteleme koşulu görünmez olduğu için **hiç tetiklenmeyebilir**.

## Karar

1. **Süreç-içi sayaçlar:** `/api/` istekleri, kimlik (**istemci host'u**) başına sayılır; ayrıca
   **429** (enerji/hız sınırı) sayısı ve **tekil kimlik** sayısı tutulur.
2. **`GET /api/telemetry`** anlık görüntüyü döner: `uptime_seconds`, `requests_total`,
   `rate_limited_total`, `distinct_identities`, `by_identity` (istek + dakikalık hız). Uç
   **yetki ister** (istismar telemetrisi herkese açık olmamalı).
3. **Kalıcılık yok.** Sayaçlar yeniden başlatmada sıfırlanır — amaç **anlık davranış**, tarih değil.
4. **Yalnız `/api/` sayılır.** Sağlık kontrolü, kök ve varlık istekleri telemetriyi gürültüyle
   bozmasın.

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| Kalıcı telemetri (DB/log) | Tek süreçli MVP'de ölçüsüz; amaç anlık sinyal — geçmiş gerekmez |
| Prometheus / OpenTelemetry | Ölçülü bir tetikleyici yok; rate limiting zaten ertelenmiş, ağır araçlandırma ölçüsüz |
| Sayaçları `/healthz`'e gömmek | Liveness ile savunma-telemetrisini karıştırır; ayrı uç daha net ve yetkilendirilebilir |
| Rate limiting'i **şimdi** eklemek | Tek kullanıcılı MVP; `AGENTS.md §8` ölçülü tetikleyici ister |
| Hiçbir şey yapmamak | R-4: koşul görünmez kalır ve hiç tetiklenmez |

## Sonuçlar

- (+) Erteleme koşulu **gözlenebilir**: kimlik başına istek hızı ve 429 sinyali artık okunabilir.
- (+) Ölçülü tetikleyici artık **ölçülebilir** — rate limiting dilimi, bu sinyal eşiği aşarsa açılır.
- (−) Yetkili de olsa ek bir uç yüzeyi (`docs/40` + TS tipleri yeniden üretilir; parite belgesi
  güncellenir).
- (−) Sayaçlar **süreç-içidir**: çok süreç/worker'a geçilirse (ADR-0017'nin işaret ettiği an) her
  süreç kendi sayacını tutar → merkezî telemetri ayrı bir ADR gerektirir.
