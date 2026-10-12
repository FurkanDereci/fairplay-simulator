# API Referansı

> **Bu dosya elle yazılmaz.** OpenAPI şemasından üretilir; şema uygulamadan türetildiği
> için belge ile kod arasında sapma oluşamaz (P11).
>
> Üretim: `python -m fairplay_simulator.cli render-api-docs --output docs/40-api.md`
>
> TypeScript tipleri: `src/fairplay_simulator/web/api-types.d.ts` (OpenAPI'den üretilir, ADR-0019).

Toplam **12 uç**.

| Metot | Yol | Özet |
| --- | --- | --- |
| GET | `/` | Root |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/register` | Register |
| POST | `/api/estimate` | Estimate |
| GET | `/api/fixtures` | Fixtures |
| GET | `/api/learning-report` | Learning Report |
| POST | `/api/matches/monte_carlo` | Monte Carlo |
| POST | `/api/matches/simulate` | Simulate |
| GET | `/api/portfolio` | Portfolio |
| POST | `/api/refill` | Refill |
| POST | `/api/wager` | Place Wager |
| GET | `/healthz` | Healthz |
