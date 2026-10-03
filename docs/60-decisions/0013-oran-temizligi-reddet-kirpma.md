# ADR-0013 — Oran Temizliği: Reddet, Kırpma

- **Durum:** Kabul edildi
- **Tarih:** 2026-10-03
- **Bağlam:** Orijinalin `docs/architecture/03_verification...md` Suite 3'ü *"Reject negative vig or
  corrupted odds arrays"* diyor. Ölçüm (`docs/70` §7.2, R5): bu depo bozuk oranı **reddetmiyor**,
  `normalize_market` içindeki `overround = max(0, total − 1)` ile **kırpıyor**. Kırpmak, veriyi
  gizlemek demektir; gizlemek kabul etmekten kötüdür.

## Karar

1. Yeni bir saf denetim fonksiyonu: `core/odds.validate_market_odds(market_type, outcomes)`.
   Üç kuralı ihlal eden dizi `InvalidOdds` yükseltir → HTTP **400**:
   - pazarın zorunlu sonuçları eksiksiz (1X2 için `HOME`/`DRAW`/`AWAY`),
   - her oran `> 1`,
   - `Σ(1/O_i) > 1` (aksi hâlde negatif vig = bahisçi lehine garanti kâr).
2. Denetim **sınırda** çağrılır: kullanıcı oranı kabul eden tek uç olan
   `POST /api/matches/monte_carlo` (hem katalog hem ham `odds_1x2` yolu).
3. **`normalize_market` saf kalır** ve `max(0, …)` davranışı korunur — o fonksiyonun sözleşmesi
   budur ve `docs/50` §9 sınır tablosunda testlidir. Bozuk girdiyi gizlememesi için ondan **önce**
   denetim çalışır; denetim geçerse kırpma hiç devreye girmez.

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| `normalize_market`'ı fırlatıcı yapmak | Saf arındırma fonksiyonunu kullanıcı girdisine bağlar; katalog yükleme yolunu da kırar ve `[G-8]`'in sözleşmesini bozar |
| Kırpmayı kaldırıp negatif overround'u göstermek | "Bozuk ama kabul edilmiş" veri üretir; Suite 3 zaten **reddetmeyi** istiyor |
| Yalnız `O ≤ 0`'ı reddetmek | Negatif vig asıl senaryo; `{3.5, 3.5, 3.5}` geçerli görünür ama garanti kâr dizisidir |
| Her uçta ayrı denetim | SSOT ihlali; denetim `core/`'da tek yerde yaşar |

## Sonuçlar

- (+) Suite 3 kapandı: `[G-19]` golden + `tests/api` uç testi.
- (+) Bozuk besleme artık sessizce "düzeltilmiyor"; görünür bir `400` ve gerekçe döner.
- (−) Katalog oranları sabit ve geçerli olduğundan bu denetim üretim akışında nadiren tetiklenir;
  değeri, **kullanıcı oranı kabul eden** uçtadır.
