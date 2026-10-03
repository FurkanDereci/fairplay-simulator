# ADR-0002 — Event-Sourced Defter (Ledger)

- **Durum:** Kabul edildi
- **Tarih:** 2026-09-29
- **Bağlam:** Devralınan projede aynı para matematiği iki yerde yaşıyordu: bir motor sınıfı ve
  API endpoint'lerinin içi. Endpoint'ler motoru **bypass** ettiği için motordaki bir düzeltme
  (seriler arası bileşik TWR) kullanıcıya hiç ulaşmadı. Bu, "iki uygulama → sessiz sapma" sınıfıdır.

## Karar

Bakiye/NAV **türetilmiş** değerlerdir; **tek gerçek kaynak** append-only bir olay defteridir
(`LedgerEntry`). Bakiye, NAV, TWR, MDD ve işlem istatistikleri bu defterin **saf projeksiyonlarıdır**.

```
LedgerEntry: (seq, ts, tip, payload)
  DEPOSIT | REFILL | WAGER_PLACED | WAGER_SETTLED
        │
        ▼  saf fonksiyon
State { cash, locked, units, series_growth, series_id, wagers... }
```

Seri kapanışı (iflas) ayrı bir olay **değildir**; V=0'a indiği sonuçlanma kaydından **türetilir**.
Böylece "olay var ama türetme farklı" sınıfı hata oluşamaz.

## Gerekçe

- **SSOT:** Bir kural tek yerde. "Aynı matematiği endpoint'te tekrar yazma" yapısal olarak imkânsız —
  endpoint'te hesaplanacak bir mutasyon durumu yok, yalnız entry üretilir.
- **İdempotentlik (I3):** "Bu settlement uygulandı mı?" = "bu entry defterde var mı?". Doğal.
- **Denetlenebilirlik:** `replay(entries)` herhangi bir ana kadarki durumu birebir üretir (I2).
- **Hata ayıklama:** Bir hata raporu = bir entry dizisi; tekrar oynatılır, deterministik yeniden üretilir.
- **Test edilebilirlik:** Çekirdek saf; property testleri için ideal.

## Sonuçlar

- (+) Doküman (`20-accounting-spec.md`) tek bir uygulamaya karşı doğrulanır.
- (+) Restart, projeksiyonun yeniden üretilmesiyle tutarlıdır.
- (−) Okuma yolu için projeksiyon gerekir (istek üzerine hesaplanır veya hızlı tabloya yazılır);
  bu bir önbellektir, **kaynak değildir** — silinebilir ve yeniden üretilebilir.
- (−) Şema, klasik "mutasyonla güncellenen tablo"dan farklıdır; `30-architecture.md`'de belgelenmiştir.
- **Not:** Bu karar tek süreç + SQLite varsayımıyla uyumludur; ölçek gerektiğinde (bkz. tetikleyiciler)
  defter aynı kalır, yalnız depolama değişir.
