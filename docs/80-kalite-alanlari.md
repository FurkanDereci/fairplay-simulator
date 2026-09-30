# Kalite Alanları — Karar ve Kapı İndeksi

Bu dosya, vault'taki `kalite-alanlari-haritasi` iskeletinin (11 alan, A/B/C blokları) **bu
projedeki karşılığıdır**: her alan için **bir karar** ve **bir kapı**. Alanların gerekçesi burada
tekrar anlatılmaz — her karar **yaşadığı dosyaya** işaret eder (depo kuralı: bir kuralı iki kez
yazmak yasak).

- **Karar**: bu alanda bizim seçimimiz ne (yapılacak/yapılmayacak).
- **Kapı**: kararın **olmadan geçilemediği** kontrol — komut ya da test.
- **Durum**: ✅ kapı var ve yeşil · ⏳ kapı yok ya da eksik · 🅿️ bilinçli ertelendi.

---

## A — Kapı alanları (atlarsan gerisi doğrulanamaz)

| # | Alan | Karar | Kapı | Durum |
| --- | --- | --- | --- | --- |
| 1 | **Doğrulama mimarisi** | Golden (spec örnekleri) + property (değişmezler) + **davranış** (gerçek tarayıcı) testleri; coverage yüzdesi hedef değil, **test sayısı çıta değil** | `pytest` · `tests/ui` · `tests/golden` · `tests/property` | ✅ (mutation testing ⏳) |
| 2 | **Domen değişmezleri, tek otorite** | Event-sourced defter **tek gerçek kaynak**; NAV/TWR yalnız `core/`'da hesaplanır | `I1`–`I4` property testleri · `tests/test_docs_sync.py` | ✅ |
| 3 | **Ölçümün tanımı** | Her metriğin formülü + işlenmiş örneği + **"ne zaman anlamsız"** kuralı: `t = SR·√T`, `t < 2` ise "örneklem yetersiz"; `ProfitFactor` kayıp yokken **tanımsız** | `[G-3]`–`[G-7]`, `[G-14]` golden · `tests/api` anlamlılık testi · arayüz notu | ✅ |

## B — Görünürlük alanları

| # | Alan | Karar | Kapı | Durum |
| --- | --- | --- | --- | --- |
| 4 | **Güven sınırı ve yetki** | Durumun ve paranın otoritesi **sunucuda**; istemci sonuç bildirmez; sır için güvensiz varsayılan yok | `test_client_cannot_declare_a_result` · 401/403 testleri · `test_validation_error_is_readable…` | ✅ |
| 5 | **Veri dayanıklılığı** | Yedek **online backup API**'siyle alınır; `journal_mode=WAL` + `synchronous=NORMAL` + `foreign_keys=ON` **yazılı karar** (ADR-0008); kurtarma **tatbikatla** kanıtlanır | `tests/repo` geri yükleme tatbikatı · pragma + FK testleri | ✅ |
| 6 | **Gözlemlenebilirlik ve replay** | Defter şeması **sürümlü**; değişiklik **upcaster** gerektirir; snapshot tetikleyicisi **sayısal** yazılır | donmuş defter fixture'ıyla replay testi · `/healthz` | ⏳ (replay var, şema evrim kuralı yok) |
| 7 | **Arayüz kalitesi ve durumlar** | **"Arayüz işi görmeden bitmez"**; sessiz başarısızlık yasak; renk/boşluk token'dan | `tests/ui` (akış + taşma/kırpılma) · `DESIGN.md` token testi | ✅ |

## C — Fark yaratan alanlar

| # | Alan | Karar | Kapı | Durum |
| --- | --- | --- | --- | --- |
| 8 | **Süreç kapıları, ADR, bağımsız inceleme** | Her mimari karar ADR; "bitti" tanımı testlerle; **yazar kendi işini onaylamaz** (farklı model, salt-okur inceleme) | `docs/60-decisions/` · docs-sync · bağımsız inceleme turu | ✅ |
| 9 | **Kullanıcı, değişim, ürün değeri** | Ürün **eğitir**: kararı kullanıcı verir (`p`), ürün disiplin aracıdır; tavsiye/tahmin yok | — | ⏳ **kapı yok** (bilinçli boşluk; "öğrettiği gösterilebilir" nasıl ölçülür karar bekler) |
| 10 | **Mimari sınırlar, geçiş tetikleyicileri** | Tek süreç + SQLite; hedef mimari (PG/Timescale/Redis) **sayısal tetikleyiciye** bağlı | `docs/30-architecture.md` CURRENT/TARGET | ✅ (tetikleyiciler elle; test edilebilir hale getirilebilir) |
| 11 | **Domain paketi (projeye özel matematik)** | Vig arındırma **çarpımsal** (bilinçli sınır: favori–longshot yanlılığı modellenmiyor); R_ruin formülü ve yarım-Kelly | `[G-8]`–`[G-13]` golden · planlanan ruin tablosu testi | ✅ / ⏳ (R1 açık) |

---

## Boşluklar (öncelik sırasıyla)

1. **Alan 6 — olay şeması evrim kuralı yok.** Defter sürümlenmiyor; ilk şema değişikliğinde
   sessiz bozulma riski (upcaster + donmuş fixture yok).
2. **Alan 1 — mutation testing yok.** Davranış testleri güçlü ama "test ölü kodu mu görüyor"
   sorusunun kapısı yok.
3. **Alan 9 — ürün değeri ölçüsüz.** "Öğretiyor mu" iddiasının kapısı tanımlı değil.

> **Kapananlar (2026-09-30):** Alan 5 (veri dayanıklılığı) — ADR-0008 + geri yükleme tatbikatı;
> bu arada FK zorlamasının hiç açık olmadığı (yazılı ama yürürlükte olmayan kısıtlar) ortaya çıktı
> ve kapatıldı. Alan 3 (metrik anlamlılığı) — `t = SR·√T` kapısı, `[G-14]`, `ProfitFactor`
> tanımsızlığı ve arayüz notu; tek işlemli portföyde çıplak `99` gösterilmiyor.

## İlgili belgeler

- `docs/50-test-strategy.md` — risk → test matrisi ve devralınan 4 doğrulama paketi (§8).
- `docs/70-parite-ve-devralma.md` — gereksinim paritesi; R1–R7 (alan 3 ve 11'in açık maddeleri).
- `docs/30-architecture.md` — CURRENT/TARGET ve geçiş tetikleyicileri (alan 10).
- `DESIGN.md` — arayüz sözleşmesi: tokenlar, "ne olmayacak"lar, doğrulama tanımı (alan 7).
- `AGENTS.md` §9 — arayüz kalite eşiği (alan 7'nin kabul ölçütü).
