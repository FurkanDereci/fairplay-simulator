# ADR-0022 — Gerçek Sağlayıcı Verisi: Eşik Ö-1 (M2 Öğrenme Çalışması)

- **Durum:** Kabul edildi
- **Tarih:** 2026-10-12
- **Bağlam:** Ürün **varsayılan olarak mock veriyle** çalışır (`docs/00-vision.md`): mock fikstür
  kataloğu, Poisson maç motoru ve **sentetik** kapanış çizgisi (ADR-0005). Gerçek sağlayıcı
  (The Odds API / API-Football / Football-Data.org) `docs/70`'te **hedef-only** listededir ve
  **hiçbir tetikleyicisi yoktur** — Postgres/Redis/snapshot/rate-limit'in sayısal eşiği varken,
  ürünün **en büyük ekseni** (mock → gerçek) eşiksiz kalmıştı. PM raporu (2026-10-07) bu eksende
  veri olmadığını da yazdı: kullanıcı/rakip/fiyat 0 dosya.

## Karar

Gerçek sağlayıcı verisine geçiş, **Ö-1 (M2 öğrenme çalışması) olumlu sonuçlanmasına** bağlıdır.
Ö-1 protokolü zaten ön-kayıtlıdır (5–8 kişi, 30–40 dk, ≥ +1,5/5 ve ≥ %60 doğru CLV yorumu).

- **Olumluysa:** ürün tezi kanıtlanmıştır → gerçek veri fazı açılır (sağlayıcı seçimi + anahtar +
  ücret kararı ilk iş).
- **Olumsuzsa:** ürün, Ö-1'in kendi yanlışlanma maddesi gereği **yeniden konumlanır** (PM §4);
  gerçek veri yatırımı **yapılmaz**.
- Bu bir **karar eşiğidir, sayısal değildir.** `docs/30` TARGET tablosunda bu satır, "sayısal
  tetikleyici" kuralının **yazılı istisnasıdır**.

**Tetiklenince ne değişir (domino — bu yüzden karar eşiği):**

1. **Kapanış çizgisi** sentetik olmaktan çıkar → ADR-0005 geçersizleşir, yerine gerçek kapanış akışı.
2. **Oran + vig** kaynağı gerçek olur → `core/odds` sözleşmesi gerçek veriyle sınanır.
3. **Settlement** kaynağı değişir: bugün sonuç maç motorundan gelir (`docs/30` CURRENT); gerçek
   sonuç sağlayıcıdan gelir → güven sınırı yeniden tanımlanır.
4. Fikstür kataloğu gerçek maçlara bağlanır; **ağ + anahtar + (çoğu sağlayıcıda) ücret** girer.
5. **Redis / TTL önbelleği** gündeme gelir (`docs/70`).

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| Sağlayıcı/maliyet kararı verilince başla | Ürün tezi kanıtlanmadan veri yatırımı; "ölçmeden büyüme" riski |
| Ölçülen tıkanmaya bağla (CLV gerçek kapanış isteyince) | Tepkisel; eşiği tanımlamak geriye dönük olur ve Ö-1 ile ilişkisi kaybolur |
| **Sayısal** eşik koy (ör. "N maç") | Maç sayısı ürün tezini kanıtlamaz; yanlış eşiği ölçer |
| Hemen gerçek veriye geç | Tez kanıtsızken mimari büyük ölçüde değişir; geri dönüş maliyeti yüksek |
| Eşiksiz bırakmak (bugünkü durum) | "Ne zaman" cevapsız kalır; eksen sahipsiz olur |

## Sonuçlar

- (+) Eksen **sahipli**: gerçek verinin ne zaman geleceği artık yazılı bir karara bağlı.
- (+) Disiplin korunur: kanıt (Ö-1) → yatırım sırası; PM raporunun "en ucuz en değerli adım"ı
  (M2) aynı zamanda gerçek verinin **ön koşulu** olur.
- (−) Ö-1 gecikirse (katılımcı bulunamazsa) gerçek veri de gecikir; bu **bilinçli** bir bağımlılıktır.
- (−) Eşik **sayısal değil**; `docs/30`'un "sayısal tetikleyici" ifadesi bu satır için istisna
  olarak yazılmalı (yoksa belge kendi kuralını çiğner).
