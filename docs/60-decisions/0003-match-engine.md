# ADR-0003 — Maç Motoru ve Lambda Türetme

- **Durum:** Kabul edildi
- **Tarih:** 2026-09-29
- **Bağlam:** Simülasyon bir kazanan üretmeli, ama bu kazanan **sunucu tarafında** doğmalı
  (istemci sonuç bildirmemeli). Ayrıca aynı girdi her zaman aynı sonucu vermeli ki test edilebilsin.

## Karar

- Sonuç **Poisson** ile üretilir: `home ~ Poisson(λ_home)`, `away ~ Poisson(λ_away)`.
- Örnekleme **Knuth** yöntemiyle, enjekte edilen `random.Random(seed)` üzerinden yapılır.
  Rastgelelik çağrı sırası sabittir → **aynı seed aynı skoru verir**.
- λ'lar **piyasadan** türetilir: fair olasılıklardan `home_share = p_home/(p_home+p_away)`,
  `λ_home = T·home_share`, `λ_away = T·(1−home_share)`, `T = 2.6` (lig ortalaması).

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| İstemcinin sonucu bildirmesi | Güven sınırı ihlali: bedava bahis üretir (devralınan projedeki `won: bool` kusuru) |
| Gerçek API sonucu (football-data.org) | MVP'de ağ bağımlılığı ve anahtar yönetimi; ileride aynı arayüzün arkasına konur |
| Rastgele skor (Poisson'suz) | Piyasa oranlarıyla ilişkisiz; vig/Kelly/CLV matematiği anlamsızlaşır |
| Kalibrasyonlu Dixon-Coles modeli | MVP için gereğinden ağır; λ türetme ayrı bir ADR ile değiştirilebilir |

## Sonuçlar

- (+) Determinizm: `simulate_match(..., seed=42)` tekrarlanabilir → test edilebilir.
- (+) Sonuç piyasayla tutarlı: favori daha çok gol bekliyor.
- (+) Settlement sunucu-otoriteli olur; istemci yalnız "bu maçı simüle et" der.
- (−) `T = 2.6` kaba bir varsayım; gerçek kalibrasyon (lig bazlı λ) ileride ayrı ADR gerektirir.
- (−) Poisson bağımsızlık varsayar (Dixon-Coles'ta düzeltilen düşük skor sapması burada yok).
