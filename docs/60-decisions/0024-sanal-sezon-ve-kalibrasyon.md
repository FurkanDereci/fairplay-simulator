# ADR-0024 — Sanal Sezon + Kalibrasyon: Döngünün Üç Yapı Taşı

- **Durum:** Kabul edildi
- **Tarih:** 2026-10-12
- **Bağlam:** Ürünün **döngüsü yok**: kullanıcı 5 statik fikstürü oynar, biter. PM bulgusu (R-1) ve
  M2 sahası bunu doğruladı ("kimse 7 gün kullanmaz"). Günlük döngü **taze veri** ister; taze veri
  (ADR-0022) Ö-1 kanıtına bağlı; Ö-1 ise 7 gün kullanım ister → **kısır döngü**. Karar bir **konsey
  turu** ile alındı (3 üye farklı aile + başkan; kayıt `model-karar-gunlugu.md` 2026-10-12).
- **Doğrulanan gerçekler (kod):** `derive_lambdas` sonucu **oranların fair olasılığından** üretir
  (`engines/match.py:111-123`) → her bahsin EV'si yapı gereği ≈ −marj. `Fund.series_id` **iflasta
  değil, iflas sonrası ilk refill'de** artar (`core/nav.py:77-79`). `WagerRecord`'ta `probability`
  **yok**; `brier`/kalibrasyon kodu **yok**.

## Karar

1. **Birincil skor = kalibrasyon karnesi** (yazdığın yüzdeler gerçekleşiyor mu; Brier/log-loss +
   eğri). Kasa ve bot NAV'ı **yan bilgidir**; **vitrinde kasa sıralaması gösterilmez** (varyansı
   ödüllendirmemek için).
2. **Oran ile sonuç ayrılır:** sonuç, oranlardan **bağımsız** bir **latent takım gücü** modelinden
   üretilir; oranlara **bilinçli verimsizlik** gömülür (sabit marj + **favori–longshot yanlılığı**).
   Böylece "değer bulma / vig arındırma / stake disiplini" **gerçek sonuç** doğurur; oyun şans
   ölçmez.
3. **Sezon ayrı bir kimliktir** (`season_id` + `season_opened/closed` olayları, sabit başlangıç
   kasası). İflas serisi (`series_id`) **dokunulmaz**; metrikler **sezon penceresine** kesilir.
4. **Olasılık girişi kalibrasyon modunda şarttır**, sezon bahsinde **gönüllüdür**. Zorunlu kılmak,
   yazılan yüzdeyi inançtan **kuponun gerekçesine** çevirir (konsey itirazı).

## Yapı taşları — bunlar bitmeden sezon bağlanmaz

| # | Taş | İçerik | Kapı |
| --- | --- | --- | --- |
| S1 | Oran–sonuç ayrımı | latent güç modeli + marj/favori–longshot yanlılığı | **"İyi strateji 100+ maçta +EV"** testi |
| S2 | Kalibrasyon zemini | `probability` kaydı + idempotent şema göçü + Brier/eğri | Karnesiz sezon başlamaz (test) |
| S3 | Sezon kimliği + üreteç | `season_id` olayları, 6–10 takım tek devre tohumlu takvim, gürültülü form | determinizm · sızıntı · docs-sync |

Yüzey işleri taşlardan **sonra**: S4 sezon yüzeyi (maç günü akışı, özet ekranı, günlük bahis
limiti), S5 bankrollsuz kalibrasyon modu.

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| Skor = kasa | Varyansı ödüllendirir; geride kalan için all-in rasyonel hale gelir (kumar teşviki) |
| Orana dokunma, sonuca sadece gürültü ekle | Ayrım olur ama verimsizlik zayıf/tesadüfi; öğretilen beceri zayıf |
| Sezon = `series_id` | Sezon sınırını **iflasa** kilitler; iki reset tek kimlikte ayırt edilemez (kod) |
| Olasılığı her bahiste zorunlu kılmak | Ölçüm güçlenir ama yazılan yüzde inanç olmaktan çıkar |
| Döngüyü gerçek veriye bağlamak | ADR-0022 kapısı kapalı; Ö-1 kanıtı yokken veri yatırımı yapılmaz |
| Döngüyü kurmamak | Ürün kullanılmaz; öğreti hiç ulaşmaz |

## Sonuçlar

- (+) **Döngü sağlayıcısız kurulur**: sezon tohumlu bir **mock dünya**; ADR-0022 kapısı kapalı kalır.
- (+) Sezon, **Ö-1 için zemin** olur (katılım + ölçüm), kısır döngü çözülür.
- (+) "İyi fiyat ≠ kârlı" öğretisi **sonuç doğuran** bir oyunda tekrar edilir.
- (−) `derive_lambdas` değişir → mevcut fikstür/skor testleri **gözden geçirilir** (bilinçli kırılma).
- (−) Şema göçü gerekir (idempotent; ADR-0015 deseni) ve kalibrasyon metriği sıfırdan yazılır.
- (−) **Kumar kancası riski:** yasak mekanikler yazılı — giriş serisi yok, "son maç günü" dürtüsü yok,
  kasa liderliği yok, iflas dramatize edilmez.
