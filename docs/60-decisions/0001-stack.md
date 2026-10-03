# ADR-0001 — Teknoloji Seçimi

- **Durum:** Kabul edildi
- **Tarih:** 2026-09-29
- **Bağlam:** Aynı gereksinimlerle sıfırdan bir kurulum; stack serbest bırakıldı.

## Karar

**Python 3.10+ çekirdek · FastAPI (ince kabuk) · SQLite · pytest + Hypothesis · ruff + mypy(strict).**

> Sürüm notu: ilk taslakta 3.11+ yazılmıştı; **ölçülen ortam 3.10.12** olduğu için hedef 3.10'a
> çekildi (docs-sync testi bu iddiayı `pyproject.toml` ile karşılaştırır). 3.11+ gerektiren
> dil özellikleri (ör. `tomllib`, `StrEnum`, `typing.Self`) kullanılmaz.

- Dil olarak Python: projenin özü **sayısal/finansal** (Decimal para, istatistik). Alanın en olgun
  araçları ve mevcut kullanıcı ortamı burada.
- Arayüz: **tek sayfa**, framework'süz, yalnız API'den beslenir (mock state yok).
- Test: `pytest` + `Hypothesis` (değişmezler property ile). `unittest` değil — property testleri
  birinci sınıf ihtiyaç.

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| TypeScript/Node | Para matematiği için `Decimal` ekosistemi ve sayısal test araçları Python kadar hazır değil |
| Go | Hızlı, ama sayısal/prototipleme hızı ve istatistik kütüphaneleri MVP için elverişsiz |
| `unittest` | Property tabanlı testler için sürtünme yüksek |
| Hazır bir "batteries-included" web framework | Core'un saflığını korumak istiyorum; kabuk ince olmalı |

## Sonuçlar

- (+) Alanın en zengin sayısal araç seti; hızlı iterasyon.
- (+) Hypothesis ile değişmezler doğrudan test edilebilir.
- (−) Tip güvenliği için `mypy --strict` disiplini şart (Python'un varsayılanı değil).
- (−) Performans kritik olursa sıcak yol (ör. Monte Carlo) gerekirse ayrı ele alınır (ADR gerekir).
