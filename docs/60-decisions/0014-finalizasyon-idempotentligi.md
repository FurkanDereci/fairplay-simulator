# ADR-0014 — Finalizasyon İdempotentliği (Bir Maç Bir Kez Üretilir)

- **Durum:** Kabul edildi
- **Tarih:** 2026-10-03
- **Bağlam:** Orijinalin `03_verification...md` Suite 4'ü *"Processing a match finalization event
  multiple times MUST result in exactly 1 payout transaction"* diyor. Çekirdekte bu testliydi
  (`I3`, `AlreadySettled`), ama **uç düzeyinde** eksikti (`docs/70` §7.2, R6). Ölçülen somut kusur:
  `save_match` `INSERT OR IGNORE` kullandığı için ikinci `simulate` çağrısı kaydı değiştirmiyor,
  ama **yanıt yeni bir simülasyonun skorunu** döndürüyordu — yani depo ile yanıt çelişiyordu
  (ödeme idempotentti, ama sonuç tutarsızdı).

## Karar

1. Bir maç **ilk çağrıda** üretilir ve kaydedilir (`seed` istekten gelir).
2. Maç kaydı **zaten varsa** sonuç, kayıtlı `seed` ile **yeniden üretilir** (tohumlu motor
   deterministik → aynı skor **ve** aynı olaylar). Yani sonraki çağrılar kayıtlı sonucu döndürür.
3. Ödeme zaten idempotentti (`open_wagers` kapısı): kupon yalnız bir kez sonuçlandırılır. Karar
   bunu **yanıt tutarlılığıyla** birleştirir.

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| Her çağrıda yeniden simüle etmek (mevcut) | Aynı maç için farklı skorlar döner; "ikinci finalizasyon farklı sonuç" = Suite 4'ün ihlali sayılır |
| İkinci çağrıyı `409` ile reddetmek | Maç zaten oynanmışsa arayüz sonucu tekrar gösteremezdi; gereksiz kırıcı davranış |
| Olayları DB'de saklamak | Şemaya yeni kolon; seed + tohumlu motor zaten aynı sonucu **yeniden üretiyor**, depolamaya gerek yok |
| Seed'i yok sayıp kaydı döndürmek (olaylar olmadan) | `events` üretilemezdi; arayüz arena'sı boşalırdı |

## Sonuçlar

- (+) Suite 4 uç düzeyinde kapandı: `test_repeated_simulation_returns_the_same_score_and_pays_once`.
- (+) Depo ile yanıt her zaman aynı hikâyeyi anlatır.
- (−) **Bilinçli davranış değişikliği:** aynı maç için `simulate` ikinci kez farklı `seed` ile
  çağrılsa bile sonuç **değişmez**. Yeniden simülasyon isteyen bir istemci bunu bilemez; bu yüzden
  parite belgesinin "bilinçli farklar" bölümünde (`docs/70` §3) not edilir.
