# ADR-0011 — Risk of Ruin: Onay Kapısı (Sunucu Zorlar)

- **Durum:** Kabul edildi
- **Tarih:** 2026-10-03
- **Bağlam:** Orijinalin `docs/architecture/01_gamification_...md` §1.2 belgesi, tek kupon kasanın
  %15'ini aşarsa **Risk of Ruin** hesaplanmasını ve *"explicit warning modal requiring user
  confirmation"* gösterilmesini istiyor. Devralınan kodda bu, istemci tarafında hesaplanan bir
  sayı + `won: bool` sınıfı güven açıklarıyla birlikte yaşıyordu. Echo'da ise yalnız
  `ruin_risk_warning: bool` bayrağı ve bir toast vardı: **formül yok, onay kapısı yok**
  (`docs/70` §7.2, R1).

## Karar

1. **Formül** spec §3.4'e yazılır ve `core/odds.py`'de yaşar:
   `R_ruin = ((1 − Edge)/(1 + Edge))^Units`. `Edge` bahis başına beklenen getiridir (`p·o − 1`),
   `Units` kasadaki eşit-bahis sayısıdır (`cash/stake`). Kenar pozitif değilse iflas kaçınılmazdır
   → `100.00`; formül negatif sayı üretmez.
2. **`p` kullanıcıdandır** (ADR-0006 ile aynı çizgi). `p` verilmezse `risk_of_ruin_pct = null`
   döner; **sayı uydurulmaz**, uyarı niteliksel kalır.
3. **Kapı sunucudadır.** `stake > %15 × cash` ve `confirm_ruin` yoksa istek **409** + yapısal
   `ruin` gövdesiyle reddedilir. İstemci uyarıyı gösterir, onay alırsa **aynı isteği**
   `confirm_ruin=true` ile tekrar gönderir. İstemci eşiği ve formülü **hesaplamaz** (SSOT).
4. **Kapı yasaklamaz.** Onaylanan bahis işlenir; amaç kullanıcıyı durdurmak değil, kararı
   bilinçli kılmaktır.
5. **Reddedilen istek yan etki bırakmaz.** `_place_wager` sırası yeniden kuruldu: doğrulama ve
   ruin kapısı **enerji harcamasından ve defter kaydından önce** çalışır (bu arada eski sıranın
   bilinmeyen markette bile enerji harcadığı ölçüldü ve düzeltildi).

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| Kapıyı yalnız istemcide tutmak | Güven sınırı istemcide olur; atlanabilir (devralınan projenin düştüğü sınıf). Eşik ve formül iki yerde yaşardı (SSOT ihlali) |
| Bahsi tamamen yasaklamak (400) | Belge "onay ister" diyor, "yasaklar" demiyor; karar kullanıcıda kalmalı |
| `p` yoksa varsayılan bir kenar uydurmak | ADR-0004/0005'in sınıfı: anlamlı görünen ama bilgi taşımayan sayı |
| Sayıyı yalnız toast'ta göstermek | Toast kalıcı bir karar yüzeyi değil; belge açıkça **modal** istiyor |

## Sonuçlar

- (+) Formül tek yerde; golden `[G-17]` ile kilitli (100 birim @ %1 → %13,53).
- (+) Kapı gerçek: `confirm_ruin` olmadan bahis işlenmez, testli (`tests/api`).
- (+) İstemci hesap yapmaz; modal veriyi sunucudan alır.
- (−) Modal, arayüzün yeni bir durumudur; Playwright turu zorunlu (arayüz işi görmeden bitmez).
- (−) `p` girilmezse `R_ruin` sayısı gösterilmez. Bilinçli: boş bırakmak, yanlış sayı göstermekten iyidir.
