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
| 1 | **Doğrulama mimarisi** | Golden (spec örnekleri) + property (değişmezler) + **davranış** (gerçek tarayıcı) testleri; kapsam yüzdesi de test sayısı da **çıta değil**; kritik karşılaştırma/sabitler **adlandırılmış sınır testleriyle** kilitli | `pytest` · `tests/ui` · `tests/test_boundaries.py` · `docs/50-test-strategy.md` §9 tablosu (docs-sync doğrular) · ADR-0010 | ✅ |
| 2 | **Domen değişmezleri, tek otorite** | Event-sourced defter **tek gerçek kaynak**; NAV/TWR yalnız `core/`'da hesaplanır | `I1`–`I4` property testleri · `tests/test_docs_sync.py` | ✅ |
| 3 | **Ölçümün tanımı** | Her metriğin formülü + işlenmiş örneği + **"ne zaman anlamsız"** kuralı: `t = SR·√T`, `t < 2` ise "örneklem yetersiz"; `ProfitFactor` kayıp yokken **tanımsız** | `[G-3]`–`[G-7]`, `[G-14]` golden · `tests/api` anlamlılık testi · arayüz notu | ✅ |

## B — Görünürlük alanları

| # | Alan | Karar | Kapı | Durum |
| --- | --- | --- | --- | --- |
| 4 | **Güven sınırı ve yetki** | Durumun ve paranın otoritesi **sunucuda**; istemci sonuç bildirmez; sır için güvensiz varsayılan yok | `test_client_cannot_declare_a_result` · 401/403 testleri · `test_validation_error_is_readable…` | ✅ |
| 5 | **Veri dayanıklılığı** | Yedek **online backup API**'siyle alınır; `journal_mode=WAL` + `synchronous=NORMAL` + `foreign_keys=ON` **yazılı karar** (ADR-0008); kurtarma **tatbikatla** kanıtlanır | `tests/repo` geri yükleme tatbikatı · pragma + FK testleri | ✅ |
| 6 | **Gözlemlenebilirlik ve replay** | Defter biçimi **sürümlenir**; bilinmeyen sürüm **açık hata** (sessiz okuma yok); snapshot tetikleyicisi **sayısal ve ölçülmüş** (> 100.000 olay / > 250 ms) | `tests/data` donmuş defter fixture'ı · `tests/repo` sürüm testleri · `/healthz` · ADR-0009 | ✅ |
| 7 | **Arayüz kalitesi ve durumlar** | **"Arayüz işi görmeden bitmez"**; sessiz başarısızlık yasak; renk/boşluk token'dan (`app.css :root`); tasarıma özgü olgular **prose**, invariantlar **kapılı** | `tests/ui` (akış + taşma/kırpılma/örtüşme) · `DESIGN.md` · ADR-0016 | ✅ |

## C — Fark yaratan alanlar

| # | Alan | Karar | Kapı | Durum |
| --- | --- | --- | --- | --- |
| 8 | **Süreç kapıları, ADR, bağımsız inceleme** | Her mimari karar ADR; "bitti" tanımı testlerle; **yazar kendi işini onaylamaz** (farklı model, salt-okur inceleme) | `docs/60-decisions/` · docs-sync · bağımsız inceleme turu | ✅ |
| 9 | **Kullanıcı, değişim, ürün değeri** | Ürün **eğitir**: kararı kullanıcı verir (`p`), tavsiye/tahmin yok. "Öğretir" iddiası **iki katmana** ayrıldı — davranış ölçümü (kapı var) ve öğrenme (🅿️ insan çalışması, protokol yazılı) | `docs/90-urun-degeri.md` · `GET /api/learning-report` · `[G-16]` golden · `tests/api` örneklem testi | ✅ / 🅿️ |
| 10 | **Mimari sınırlar, geçiş tetikleyicileri** | Tek süreç + SQLite; hedef mimari (PG/Timescale/Redis) **sayısal tetikleyiciye** bağlı | `docs/30-architecture.md` CURRENT/TARGET | ✅ (tetikleyiciler elle; test edilebilir hale getirilebilir) |
| 11 | **Domain paketi (projeye özel matematik)** | Vig arındırma **çarpımsal** (bilinçli sınır: favori–longshot yanlılığı modellenmiyor); R_ruin formülü (§3.4) ve yarım-Kelly; bozuk oran **sınırda reddedilir** | `[G-8]`–`[G-13]`, `[G-17]`–`[G-19]` golden · `tests/test_boundaries.py` | ✅ |

---

## Boşluklar

**Kapısız alan kalmadı** (2026-09-30). Tek açık kalem bilinçli ertelendi:

- 🅿️ **Alan 9'un ikinci katmanı** — "bu sayıları gören kullanıcı daha iyi karar verir" iddiası.
  Otomatik kapısı olamaz (insan çalışması); protokol `docs/90-urun-degeri.md` §4'te ön-kayıtlı,
  **koşulmadı**.

> **Kapananlar (2026-09-30):** Alan 5 (veri dayanıklılığı) — ADR-0008 + geri yükleme tatbikatı;
> bu arada FK zorlamasının hiç açık olmadığı (yazılı ama yürürlükte olmayan kısıtlar) ortaya çıktı
> ve kapatıldı. Alan 3 (metrik anlamlılığı) — `t = SR·√T` kapısı, `[G-14]`, `ProfitFactor`
> tanımsızlığı ve arayüz notu. Alan 6 (olay şeması evrimi) — ADR-0009: sürüm damgası, bilinmeyen
> sürümde açık hata, donmuş `ledger_v1.json` fixture'ı, ölçülmüş snapshot tetikleyicisi.
> Alan 1 (doğrulama mimarisi) — ADR-0010: sınır tablosu (`docs/50-test-strategy.md` §9) +
> `tests/test_boundaries.py`; denetim enerji tavanı kuralını buldu ve `[G-15]` olarak yazıldı.
> Alan 9 (ürün değeri) — `docs/90-urun-degeri.md`: ölçülebilir katman `GET /api/learning-report`
> + `[G-16]`; ölçülemeyen katman protokole bağlandı.

## İlgili belgeler

- `docs/50-test-strategy.md` — risk → test matrisi ve devralınan 4 doğrulama paketi (§8).
- `docs/70-parite-ve-devralma.md` — gereksinim paritesi; R1–R6 kapandı, R7 bilinçli kapsam-dışı.
- `docs/90-urun-degeri.md` — "öğrettiği" nasıl ölçülür: davranış ölçütleri + eşikler (alan 9).
- `docs/30-architecture.md` — CURRENT/TARGET ve geçiş tetikleyicileri (alan 10).
- `DESIGN.md` — arayüz sözleşmesi: tokenlar, "ne olmayacak"lar, doğrulama tanımı (alan 7).
- `AGENTS.md` §9 — arayüz kalite eşiği (alan 7'nin kabul ölçütü).
