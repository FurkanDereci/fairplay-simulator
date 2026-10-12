# ADR-0019 — Tipli İstemci: OpenAPI → TypeScript Tipleri (Üretilir, Commit Edilir)

- **Durum:** Kabul edildi
- **Tarih:** 2026-10-12
- **Bağlam:** `docs/ROADMAP.md` S7'nin **tek kalanı** ve PM raporu Ö-9: "istemci OpenAPI'den
  üretilmiyor". Bugün arayüz `web/index.html` içinde vanilla JS ve **elle yazılmış ince** bir
  istemci taşıyor; dış (ve gelecekte TS'e geçebilecek) tüketiciler için **tipli** bir sözleşme
  yok. `docs/40-api.md` zaten OpenAPI'den **üretiliyor** ve `docs-sync` ile doğrulanıyor — aynı
  disiplin tiplere de uygulanabilir ("doküman yalan söylemez").

## Karar

1. **Tipler OpenAPI şemasından üretilir**, elle yazılmaz. Şema **koddan** gelir
   (`python -m fairplay_simulator.cli export-openapi`); yani OpenAPI → tipler zincirinin tek
   kaynağı uygulamadır (SSOT).
2. **Üretici `openapi-typescript`** (devDependency, **pinli** `7.13.0`) ve üretim `npm run
   gen:api-types` (`scripts/gen-api-types.mjs`). Üretilen dosya
   **`src/fairplay_simulator/web/api-types.d.ts`** olarak **commit edilir** (dağıtılan artefakt;
   üretmek Node ister, tüketmek istemez).
3. **CI Python-only kalır; npm eklenmez.** Drift, `tests/test_docs_sync.py`'deki yeni testle
   **kapsam düzeyinde** yakalanır: her OpenAPI **yolu** ve **operationId**'si dosyada bulunmalı.
   Birebir eşitlik (yeniden üretip karşılaştırma) **bilinçli olarak** yapılmaz — o, CI'ya Node
   koymak olurdu.
4. **Kapsam yalnız tiplerdir.** Fetch/istemci sarmalayıcısı **üretilmez**: repo içinde tüketici
   yok (arayüz vanilla JS), ince elle-yazılmış istemci zaten var; tam istemci ölçüsüz yüzey olurdu.

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| Tam istemci (`openapi-fetch` / `openapi-typescript-codegen`) | Repo içinde tüketici yok; ölçüsüz yüzey ve bakım yükü |
| Tipleri commit etmeme (kurulumda üret) | Node'u **zorunlu** kılar; Python-only klon/CI ve hızlı başlangıç bozulur |
| Tipleri elle yazmak | OpenAPI'den sapar — `dokuman-kod-sapmasi` sınıfı hata üretir |
| Python'dan TS üretmek | `openapi-typescript`'i yeniden yazmak; gerekçesiz |
| `openapi.json`'u repoda tutup tipleri ondan üretmek | Şema zaten koddan **canlı** üretilebiliyor; ara dosya yeni bir sapma kaynağı olur |

## Sonuçlar

- (+) API yüzeyi **tipli**: yeni bir uç eklendiğinde `docs-sync` testi (npm'siz) tip dosyasının
  yenilenmesini hatırlatır.
- (+) Üretici **pinli** ve tek komut; artefakt commit'li olduğu için TS istemcisi Node olmadan
  kullanılır.
- (−) Dosya **bayatlayabilir**; birebir eşitlik denetimi CI'da yok (bilinçli sınır — madde 3).
  Kapsam testi yolu/işlemi yakalar ama şema **detayındaki** değişimi (ör. bir alanın tipi)
  yakalamaz; bu durumda dosya `npm run gen:api-types` ile yenilenir.
- (−) Repoda **iki ekosistem** (Python + dev-only Node); `node_modules/` ve `package.json`
  `.gitignore`/ürün ağacı ayrımıyla yönetilir (ürün deposu temiz kalır, `AGENTS.md §8`).
