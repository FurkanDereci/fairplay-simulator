# ADR-0006 — Kelly/EV için Kullanıcı Olasılığı

- **Durum:** Kabul edildi
- **Tarih:** 2026-09-30
- **Bağlam:** Kelly kriteri ve EV, ürünün vitrin özellikleri arasında (`00-vision.md`). Ama `p` olarak
  **piyasanın fair olasılığı** kullanılırsa `f* = (p·o − 1)/(o − 1)` **her zaman 0** çıkar (bkz.
  `[G-9]`): bookmaker oranı her zaman fair orandan kısadır. Yani Kelly, CLV'nin düştüğü tuzağın
  aynısına düşer — sabit ve bilgi taşımayan bir metrik olur. Bu uyarı ADR-0005'in sonunda not edilmişti.

## Karar

`p` **kullanıcıdan** gelir. Kullanıcı kendi olasılık tahminini yazar (%); sunucu EV, Kelly oranını ve
**önerilen stake**'i hesaplar.

- `POST /api/wager` opsiyonel `probability` alanı taşır; verilirse cevap `assessment` içerir.
- `POST /api/estimate` bahis **oynamadan** danışma sağlar (aynı matematik, yan etkisiz).
- Arayüz tahmini yüzde olarak alır, sunucuya 0–1 aralığında gönderir; sonuç satır altında
  "EV … · Kelly %… · önerilen stake … TL" olarak görünür.

## Neden sahte bir "model olasılığı" üretmiyoruz

Fikstürler mock ve elimizde kalibre bir tahmin modeli yok. Uydurulmuş bir `p` üretmek, ADR-0004'ün
(CLV hep negatif) yaptığı hatanın aynısı olurdu: **anlamlı görünen ama hiçbir şey söylemeyen sayı.**
Kullanıcı olasılığı ise ürünün eğitici teziyle uyumlu — "kararı sen veriyorsun, disiplin aracı bizden".

## Sonuçlar

- (+) Kelly/EV artık gerçekten bilgi taşır: `p` fair'den büyükse pozitif EV ve pozitif stake önerisi.
- (+) Matematik sunucuda kalır (SSOT); arayüz hesap yapmaz.
- (+) Kullanıcı "tahminim yanlışsa ne olur"u bahis oynamadan görebilir (eğitici değer).
- (−) Ek bir alan ister; opsiyonel olduğu için akışı tıkamaz.
- (−) Kullanıcı `p` girmezse Kelly gösterilmez. Bu bilinçli: **boş bırakmak, yanlış sayı göstermekten iyidir**.
