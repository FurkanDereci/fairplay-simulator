# ADR-0012 — Disiplin Rozetleri ve Cooldown İndirimi

- **Durum:** Kabul edildi
- **Tarih:** 2026-10-03
- **Bağlam:** Orijinalin `docs/architecture/01_gamification_...md` §3 belgesi *"Earning 3+ Discipline
  Badges reduces max T(n) cap from 168 hours to 72 hours"* diyor. Ölçüm (`docs/70` §7.2, R2):
  **rozet kavramı iki projede de yok** — yani kural yazılı ama rozetler tanımsız. `Badge` varlığı
  `docs/10` §1'de zaten listeliydi ("oyunlaştırma katmanı, politika").

## Karar

1. **Rozetler yeni veri gerektirmez; var olan ölçütlerden türetilir.** `learning-report` (§6) zaten
   bahis disiplinini, CLV başarısını ve pazar çeşitliliğini ölçüyor. Üç rozet tanımlanır:
   - `ölçülü-bahis` — ortalama bahis/kasa ≤ %15 (`stake_verdict == "ölçülü"`),
   - `clv-ustası` — ortalama CLV > 0,
   - `pazar-gezgini` — pazar çeşitliliği ≥ 3.
2. **Her rozet `N ≥ MIN_SAMPLE` (6) ister.** Az örneklemden "disiplinli" hükmü çıkarmak `[G-14]`'ün
   yasakladığı sınıftır; `reliable` değilse **hiç rozet verilmez**.
3. **Üçünün tamamı → tavan 72.** Kısmi rozet indirim getirmez (eşik = 3 = rozet sayısı). Tavan
   `min(tavan, 4^(n−1))` ile uygulanır; yani tier 4'te (64 saat) indirim görünmez, tier 5'te görünür.
4. **Rozet bir "favori yanlılığı yok" rozeti içermez:** o ölçüt neredeyse herkeste doğru çıkar ve
   eşiği anlamsız kılar (bilgi taşımayan metrik yasağı, ADR-0005/0006 sınıfı).
5. Rozetler **sunucuda** hesaplanır ve `GET /api/portfolio` / `GET /api/learning-report` cevabında
   görünür; arayüz yalnız gösterir.

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| Yeni bir "rozet" veri tablosu / olay akışı kurmak | Aynı bilgi zaten defterden türetiliyor; ikinci bir kaynak SSOT'u bozar ve uydurma veri üretir |
| Rozetsiz, doğrudan bir "disiplin sayacı" | Dökümanın dili "rozet"; ölçüt adlarının kullanıcıya görünmesi eğitici değeri taşır |
| "Favorisiz" rozeti eklemek | Neredeyse her zaman doğru → eşik işlevsiz |
| R2'yi kapsam-dışı bırakmak | Orijinalde de rozet yoktu ama kural **yazılı**; kapatmak için gerekçe gerekirdi — ölçütler elimizde olduğu için kapatmak yerine karşılamak seçildi |

## Sonuçlar

- (+) Kural artık ölçülebilir: `[G-18]` (indirim) + `tests/api` (rozet türetimi) + `I6` property.
- (+) Yeni veri yok; rozetler defterin projeksiyonundan çıkar.
- (+) Kullanıcı üç rozeti görünce neyi iyi yaptığını **kendi sayılarından** okur (eğitici).
- (−) Rozetler yalnız `N ≥ 6` sonrası görünür; yeni kullanıcıda boş kalır. Bilinçli: erken rozet
  "iyi oynuyorsun" yanılsaması yaratırdı.
