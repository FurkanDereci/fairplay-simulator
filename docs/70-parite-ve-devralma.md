# Parite ve Devralma

Bu depo, mevcut **`github.com/FurkanDereci/fairplay-simulator`** reposunun **yerine geçme
adayıdır**; ayrı bir repo değildir. Bu dosyanın amacı o kararı kanaate bırakmamak: iddiaları
ölçülebilir hâle getirmek.

> **Ad notu (2026-10-03).** Bu depo geliştirme boyunca **"FairPlay Echo"** çalışma adını taşıyordu;
> devralma kararı netleşince ad **`fairplay-simulator`** oldu (upstream ile aynı). Belgede
> **"orijinal"** = bugünkü upstream (`main`), **"bu depo"** = yerine geçme adayı olan bu çalışma.

> **Provenans (önemli).** Orijinal repo hakkındaki satırlar **2026-09-30**'da
> `~/dev/fairplay_simulator_src` (`4c34c53`, `origin/main` ile senkron) üzerinde **ölçülerek**
> alındı; bu deponun test koşusunun parçası olmadıkları için `docs-sync` onları doğrulayamaz —
> bu yüzden her satırın yanında ölçüm kaynağı yazılıdır. **Bu depo tarafı** iddiaları ise
> `tests/test_docs_sync.py` ile bağlıdır.

---

## 1. API paritesi

| Uç | Orijinal | bu depo | Not |
| --- | --- | --- | --- |
| `GET /` | var | var | |
| `GET /api/fixtures` | var | var | |
| `GET /api/portfolio` | var | var | |
| `POST /api/auth/register` | var | var | |
| `POST /api/auth/login` | var | var | |
| `POST /api/wager` | var | var | bu depoda idempotency anahtarı + enerji kapısı |
| `POST /api/refill` | var | var | |
| `POST /api/matches/simulate` | var | var | bu depoda **tohumlu** (aynı seed → aynı skor) |
| `POST /api/matches/monte_carlo` | var | var | bu depoda `match_id` **veya** ham oran + `seed` |
| `POST /api/wager/settle` | var | **yok** | bilinçli kaldırıldı — bkz. §3 |
| `GET /healthz` | yok | var | |
| `POST /api/estimate` | yok | var | kullanıcı olasılığından EV/Kelly (ADR-0006) |
| `GET /api/learning-report` | yok | var | öğrenme ölçütleri: davranış metrikleri, tavsiye değil (`docs/90`) |

**Ölçüm:** orijinalin uçları `src/backend/app.py` içindeki `@app.*` dekoratörlerinden, bu deponunki
`docs/40-api.md`'den (OpenAPI'den üretilir) okundu.

**Arayüz kullanımı:** orijinalin SPA'sı (`src/frontend/index.html`) yalnız şu uçları çağırıyor:
`register · fixtures · simulate · portfolio · refill · wager`. Yani `monte_carlo` ve `wager/settle`
farkları **arayüz akışını etkilemez**, yalnız API yüzeyini etkiler.

## 2. Risk paritesi

Orijinalin 2026-09-10 incelemesinde çıkan ve belgelenen kod riskleri:

| Orijinalin riski | bu depodaki durum | Kanıt |
| --- | --- | --- |
| `auth.py`: `JWT_SECRET_KEY` yoksa **bilinen sabit** varsayılana düşüyor | env yoksa rastgele anahtar + `RuntimeWarning` | `app/config.py` · `tests/api` (token akışı) |
| `calculate_twr` seriler arası bileşik değil | `Fund.twr` seriler arası **bileşik** | `core/nav.py` · `[G-2]` · `I4` |
| `simulation_energy` hiç yenilenmiyor | saatte 10 yenilenir, <10'da bahis reddi (429) | `core/energy.py` · `[G-12]` · `I5` |
| `benchmark_engine`: `except Exception: pass` + botlar bellekte, restart'ta sıfırlanıyor | botlar **durum tutmaz**; eğriler maç kayıtlarından türetilir | `engines/bots.py` · `tests/engines/test_bots.py` |
| CORS `*` | `CORS_ORIGINS` ile yapılandırılabilir; varsayılan localhost + `null` | `app/config.py` · `app/main.py` |
| `WagerModel.created_at` yok → bekleyen kuponu olan kullanıcıda `/api/portfolio` çöküyordu | böyle bir model yok; kupon durumu defterden türer | `core/nav.py` · `tests/api` |

**Kapılar:** orijinal 40 test (`unittest`; 2026-09-30 ölçümü) · bu deponun paketi `pytest` + Hypothesis +
gerçek tarayıcı (güncel sayı bilinçli olarak yazılmaz — sayı kayar, kapı kalır; bkz. `docs/80`). Asıl fark
**neyin** test edildiğidir (§4).

## 3. Bilinçli farklar (eksik değil)

- **`POST /api/wager/settle` kaldırıldı.** Orijinalde istemci "bu kupon kazandı" diyebiliyordu;
bu bir **güven sınırı ihlali** (bedava kupon). bu depoda sonuç yalnız maç simülasyonundan gelir.
Ölçüm: orijinalin arayüzü de bu ucu kullanmıyordu, yani kaldırmak mevcut akışı bozmuyor — ama
**dış istemciler için kırıcı bir değişikliktir** ve devralmada not edilmelidir.
- **`monte_carlo` ucu kimlik doğrulaması ister.** Orijinalde anonimdi; bu depoda `/api/matches/*`
tutarlılığı için token gerekir.
- **Oranlar katalogdan gelir.** Orijinal `simulate` ucu da katalogdan okuyordu; bu depoda
  `monte_carlo` hem katalog hem **varsayımsal oran** kabul eder (parite korunur).
- **Kasa eşiğini aşan bahis onay ister.** Tek kupon kasanın %15'ini aşarsa bu depo isteği `409` +
  `ruin` gövdesiyle reddeder; istemci onaylarsa (`confirm_ruin`) işlenir. Orijinalde yalnız
  istemci tarafında bir uyarı vardı ve eşik/formül sunucuda değildi (ADR-0011) — dış istemciler
  için davranış farkı.
- **`simulate` bir maçı bir kez üretir.** İkinci çağrı (farklı `seed` ile bile) kayıtlı sonucu
  döndürür; Suite 4 idempotentliği (ADR-0014). Yeniden simülasyon bekleyen istemci için fark.

## 4. bu deponun ekledikleri

- **Ölçülebilir doküman dürüstlüğü:** `docs-sync` testi; spec örnekleri (`[G-x]`) ↔ golden testler,
  belgedeki uç listesi ↔ OpenAPI şeması, belgedeki test yolları ↔ gerçek dosyalar.
  Orijinalde doküman-kod sapması **oluştu** ve sonradan etiketlenerek yamandı.
- **Gerçek tarayıcı testleri** (`tests/ui`): akış + yerleşim taşması kapısı. Orijinalde yoktu;
  orijinalde enerji göstergesi kusuru bu yüzden ancak elle yakalandı.
- **Determinizm:** enjekte `Clock`, tohumlu `Random` (maç motoru, botlar, Monte Carlo, kapanış çizgisi).
- **Event-sourced defter:** bakiye/NAV türetilir; `cli replay` bir durumu yeniden üretir.
- **Kurulabilirlik:** `pyproject.toml` + temiz ortamda doğrulanmış kurulum (orijinal
  `requirements.txt`'i sonradan kazandı).

## 5. Devralma planı

> **Durum (2026-10-03, kapandı):** parite ön koşulu kapandı — R1–R6 karşılandı (§7.2), dört kapı yeşil.
> İki geçmiş **ilgisiz** olduğu için GitHub `v2`den PR açmadı; içerik **`v2-merge`** dalında `main`
> geçmişinin **üstüne** konuldu ve **PR #1** açıldı. Karar verildi ve PR **merge edildi**:
> **`e3ee368`** (merge commit) — `main` artık bu koddur, orijinalin commit geçmişi **ata olarak
> korunur**. `main`'e doğrudan yazılmadı, force-push yapılmadı.

Karar verildi: bu depo daha iyi bulundu ve **upstream'in yerine geçti**. (Bu depo artık aynı adı
taşıyor: `fairplay-simulator`; "echo" çalışma adı bırakıldı.)

Uygulanan yol **(dal + PR)**, force-push **değil**:

1. Bu depo, `origin` olarak `git@github.com:FurkanDereci/fairplay-simulator.git`'e bağlandı.
2. İçerik **ayrı bir dalda** yayınlandı (`v2`; PR için `v2-merge`), `main`'e doğrudan yazılmadı.
3. PR ile **diff olarak** incelendi: parite kaybı var mı, kırıcı değişiklik ne, testler ne diyor
   → **PR #1**: https://github.com/FurkanDereci/fairplay-simulator/pull/1
4. ✅ `main`'e **merge edildi** (`e3ee368`); PR kapanışta `v2`/`v2-merge` dalları silinebilir.

Gerekçe: orijinalin commit geçmişi korunur, karar **incelenebilir bir diff** olur (kanaat değil) ve
geri dönüşü vardır (merge geri alınabilir). Force-push, public repoda geçmişi geri dönüşsüz siler.

**Devralmada uygulananlar ve kalanlar:**

- `LICENSE` upstream'den **birebir geri konuldu** (yeni ağaçta yoktu; public repo lisanssız kalmasın).
- **Devralınan belgeler ağaçta yok, geçmişte durur:** upstream'in `docs/architecture/00–03`,
  `docs/research/01–02`, `docs/agents/*` ve eski kod (`src/backend`, `src/frontend`,
  `src/data_ingestion`, `tooling/`) yeni ağaçta yer almaz; hepsi **`4c34c53` ata commit'inde**
  erişilebilir (bu belgenin §6–§7 atıfları zaten o commit'e bağlı).
- **Kalan (2026-10-03):** iki yerel klon kararı — `~/dev/fairplay_simulator_src` (eski upstream klonu,
  artık gereksiz) ve `~/dev/fairplay-simulator` (çalışma klonu). İkincisi esas alınır; ilki emekliye
  ayrılır.

## 6. Özellik paritesi (ölçülmüş, 2026-09-30)

Uç paritesi (§1) **yüzeyi** ölçer; bu bölüm **ürün davranışını** ölçer. Ölçüm: orijinalin
`src/frontend/index.html` kimlikleri (58) ↔ bu deponunki (42), `src/` içindeki terim taraması ve
GDD'nin vaatleri.

### 6.1 bu depoda olmayan, orijinalde olan

| # | Özellik | Orijinalde kanıt | bu depodaki durum | Durum |
| --- | --- | --- | --- | --- |
| F1 | **Maç olayları (gol/dakika zaman çizelgesi)** | `match_engine.py` `MatchEvent` + `events.sort(...)`, `app.py` cevabında `"events"` | `MatchEvent` + `_build_events`; cevapta `events` (dakika, takım, tür, **anlık skor**) | ✅ |
| F2 | **Simülasyon arenası** (skor + pazar bazında sonuçlar paneli) | `simulation-arena`, `sim-score-display`, `sim-outcome-1x2/ou/btts` | `#sim-panel`: skor, 3 pazar sonucu, olay listesi | ✅ |
| F3 | **Kupon fişi (slip)** — odaklı onay yüzeyi | `slip-*` (14 kimlik): maç, market, seçim, oran, fair, vig, Kelly, stake, tavan kasa, ödeme, enerji maliyeti | Satır içi form; fair/vig satırda var, "fiş" yok | ⏳ |
| F4 | **Factsheet kartı** (paylaşılabilir fon özeti) | `factsheet-*` (9 kimlik): NAV/TWR/Sharpe/Sortino/MDD/PF/winrate/alpha-beta | Metrik kutuları var; ayrı bir özet kartı yok | ⏳ |
| F5 | **Solvent gün serisi göstergesi** | `streak-display`, `streak-bar`, `cd-tier-display` | `t-solvent` + `.streak-bar`; **sayaç gerçekten işliyor** (duvar saati, `portfolio`/`wager` tick'i) | ✅ |
| F6 | **Kalıcı "ruin" uyarı kutusu** | `ruin-warning-box` | `#ruin-box`: onaylanan yüksek riskli bahis **kapatılana dek** görünür (toast'a ek, kalıcı yüzey) | ✅ |

> **F1/F2 kapatıldı (2026-09-30):** motor artık gol olaylarını üretiyor (gol sayısı çekildikten
> **sonra**, böylece eski tohumların skorları değişmedi) ve cevap `events` döndürüyor; arayüzde
> sağ kolonun tepesinde simülasyon arenası var. Doğrulama: motor testleri + gerçek tarayıcıda
> sürülüp ekran görüntüsü alındı; arena açıkken 375/900/1440'ta taşma/kırpılma kapısı eklendi.

> **F5/F6 kapatıldı (2026-10-03).** **F5** yalnız gösterge değildi: `register_solvent_day` çekirdekte
> tanımlı ve `I6` ile testliydi ama **hiçbir yerden çağrılmıyordu** — yani uygulamada tier **hiç
> düşmüyordu**. Gün sınırı artık işleniyor (`portfolio`/`wager` tick'i, `last_solvent_day` imleci,
> iflasta geçen günler yanar) ve arayüzde `t-solvent` + `.streak-bar` gösteriliyor (`[G-20]`,
> ADR-0015). İlk şema göçü de bu turda geldi (idempotent `ALTER TABLE`). **F6** kalıcı `#ruin-box`
> ile karşılandı. Doğrulama: `tests/ui` (gösterge + kalıcı kutu, gerçek tarayıcı) + API testleri +
> yeni golden; dört kapı yeşil.

### 6.2 İkisinde de olmayan (GDD vaadi, kodda yok — parite eksiği **değil**)

- **Historical Sandbox / Time Machine** (geçmiş sezon backtest): orijinal `src/` içinde
  `sandbox|historical|time_machine|backtest` = **0**.
- **Disiplin rozetleri** (Positive EV Hunter, Bankroll Guardian, CLV Master): orijinaldeki 5
  `badge` referansı **kupon fişi ve bekleyen-sayısı etiketleri**; disiplin rozeti yok.
- **Virtual Copy Fund / sosyal lig**: GDD'de açıkça Faz 2'ye ertelenmiş.

### 6.3 bu deponun önde olduğu yerler (ölçülmüş)

- **Kelly — orijinaldeki uygulama güvenilmez:** `slip-kelly-val` **istemci tarafında** hesaplanıyor
  ve kenar yokken **varsayılan %5 öneriyor** (`kellyFraction = edge > 0 ? ... : 0.05`) — yani
  pozitif kenar olmadığında da "Kelly %5.0 (50 TL)" yazıyor. bu depoda hesap **sunucuda**, `p`
  kullanıcıdan gelir ve kenar yoksa açıkça "pozitif EV yok (Kelly %0)" der (ADR-0006).
- **CLV — orijinalde hiç yok:** `clv|closing` = **0**. bu depoda var (ADR-0005) ve ~10 referans.
- **Gerçek tarayıcı testleri + yerleşim taşma kapısı:** orijinalde yok.
- **Lig filtresi**, `/api/estimate`, `/healthz`.
- **Tasarım token'ları + `DESIGN.md`**: renk tek yerde, ham hex yok (testle bağlı).

### 6.4 Eşitleme sırası

Değer/emek sırasına göre: ~~**F1 + F2** (motor olayları + arena)~~ **✅** →
~~**F5** (küçük, oyunlaştırma hikâyesini tamamlar)~~ **✅** → ~~**F6** (küçük)~~ **✅** →
**F3** (fiş; bu depoda işlev zaten satır içinde) → **F4** (factsheet; kozmetik, metrikler var).

## 7. Gereksinim paritesi — orijinalin **dökümanlarından** (2026-09-30)

> Özellik paritesi (§6) **ne yapıldığını**, bu bölüm **neyin istendiğini** ölçer. Kaynak: orijinalin
> `docs/architecture/00–03`, `docs/research/01–02`, `docs/ROADMAP.md`, `docs/agents/*` (`4c34c53`).
> Bunlar gerçek gereksinim belgeleri; **kabul ölçütü olarak** okunmalı.
>
> **Neden bu bölüm sonradan eklendi:** ilk turlarda yalnız GDD + ROADMAP okunmuştu; `01_gamification`
> ve `03_verification` okunmadan geliştirme yapıldı. Eksik okumanın bedeli bu bölümün bulgularıdır.

### 7.1 bu deponun karşıladığı gereksinimler

| Gereksinim | Kaynak | bu depodaki kanıt |
| --- | --- | --- |
| **Kelly'de `p` kullanıcıdan gelir** — doc: *"Given **user-estimated** or benchmark true probability p ∈ (0,1)"* | `01` §1.1 | `POST /api/estimate` + bahiste `probability`; ADR-0006. **Orijinalin kodu kendi dökümanından sapıyor** (§7.4) |
| Risk-of-Ruin **eşiği**: tek kupon > %15 kasa → uyarı | `01` §1.2 | `risk_of_ruin_threshold = 0.15` · `ruin_risk_warning` |
| **CLV formülü** | `01` §2 | `core/odds.clv_pct` · ADR-0005 · `[G-11]` |
| **Cooldown** `T(n)=min(168,4^(n−1))` + **tier decay** (3 solvent gün) | `01` §3 | `core/cooldown.py` · `[G-13]` · `I6` |
| **Unit NAV**, refill invariance, seriler arası bileşik TWR | `research/02` | `core/nav.py` · `I1` · `I4` · `[G-1/2]` |
| **Vig/overround** arındırma, fair odds | `research/02` | `core/odds.normalize_market` · `[G-8]` |
| **3 benchmark indeksi** (Random Walk, Favorite Heavy, Home-Advantage) | `00` Rule 3 | `engines/bots.py` (3 strateji) |
| Poisson + Monte Carlo, çoklu pazar (1X2 / O-U / BTTS) | `00`, `research/01` | `engines/match.py` · `/api/matches/monte_carlo` |
| **Settlement idempotentliği** (Suite 4) | `03` Suite 4 | `I3` + `AlreadySettled`; orijinalde **0** test |

### 7.2 Gereksinim paritesi — R1–R7 sonucu (2026-10-03)

| # | Gereksinim | Kaynak | Durum (2026-10-03) |
| --- | --- | --- | --- |
| R1 | **Risk of Ruin formülü** `R_ruin = ((1−Edge)/(1+Edge))^Units` **ve** onay isteyen uyarı **modalı** | `01` §1.2 | ✅ spec §3.4 · `[G-17]` · `core/odds.risk_of_ruin` · sunucu-zorlamalı kapı (`confirm_ruin`, 409) · modal + ADR-0011 |
| R2 | **Disiplin indirimi**: 3+ rozet → cooldown tavanı 168 → **72** | `01` §3 | ✅ spec §4.2 · `[G-18]` · üç rozet ölçütlerden türetilir · ADR-0012 |
| R3 | **Suite 1**: kilit süresi **geçtikten sonra** bahis yeniden serbest | `03` Suite 1 | ✅ `test_cooldown_unlocks_after_expiry` (enjekte saat) |
| R4 | **Suite 2**: `NAV_t × U_t = Cash_t + Exposure_t` | `03` Suite 2 | ✅ `test_i2_nav_times_units_equals_value` + `test_nav_identity_holds_at_the_endpoint` |
| R5 | **Suite 3**: `Σ(1/o_i) > 1`; negatif vig / bozuk oran **reddedilmeli** | `03` Suite 3 | ✅ `[G-19]` · `core/odds.validate_market_odds` · sınırda `400` (kırpma yok) · ADR-0013 |
| R6 | **Suite 4 (uç düzeyi)**: aynı finalizasyon tekrar işlenirse **tek ödeme** | `03` Suite 4 | ✅ `test_repeated_simulation_returns_the_same_score_and_pays_once` · bir maç bir kez üretilir · ADR-0014 |
| R7 | **Asian Handicap / double-chance** pazarları | `research/01` §2.1 | ⚪ **bilinçli kapsam-dışı** — MVP 1X2 / O-U / BTTS. Yarım kazanç/kayıp altyapısı (`HALF_WON/HALF_LOST`) hazır ama kullanılmıyor |

### 7.3 İkisinde de olmayan, **hedef** olduğu açıkça yazılı olanlar

Bunlar "eksik" değil, planlı hedef: PostgreSQL 16 + TimescaleDB + Redis + pub/sub broadcaster ve DDL
şeması (`02`, belgenin başında HEDEF olarak etiketli) · gerçek sağlayıcı entegrasyonu (The Odds API /
API-Football / Football-Data.org) + Redis TTL önbelleği (`research/01`) · `bet_legs` (çok bacaklı
kupon) · dokümanın hedef DDL'inde `odds_snapshots` geçmişi · OpenTelemetry + Docker limitleri
(`agents/devops`) · Time Machine, kopya fon (Faz 2).

### 7.4 Orijinalin **kendi dökümanından saptığı** yer (ölçülmüş)

- `01` §1.1 Kelly'de `p`'nin **kullanıcı tahmini** olmasını istiyor; orijinalin kodu ise istemci
  tarafında hesaplayıp **kenar yokken varsayılan %5** öneriyor (`edge > 0 ? … : 0.05`) — yani
  dökümanın istediği "kullanıcı tahmini" akışı **uygulanmamış**, yerine sabit bir öneri konmuş.
- `03` Suite 4 orijinalde **0 test**; Suite 1/2 de yarım (ölçüm: yukarıdaki grep).

**Sonuç (2026-10-03).** Kapanış turunda **R1–R6 karşılandı**, **R7 bilinçli kapsam-dışı** bırakıldı.
Özetle bu depo: bozuk oranı artık **reddediyor** (Suite 3), kilit **açılmasını** test ediyor (Suite 1),
`NAV × U = V` kimliğini hem property hem uç düzeyinde doğruluyor (Suite 2) ve tekrarlanan
finalizasyonu **tek ödemeye** indiriyor (Suite 4). Kelly'de ve Suite 4'te orijinalin **önünde**ydi;
şimdi Suite 3 ve R1/R2 açıkları da kapandı. Devralma kararının **kabul ölçütü** bu tablo olmalı:
R1–R6 kapandı, "daha iyi mi" eşiğini **kullanıcı** koyar.

## 8. Açık sorular

- Karşılaştırmanın **karar anı** kimin: hangi ölçüt "daha iyi" sayılacak? (Bu dosya ölçütü
  tablolaştırır; eşiği kullanıcı koyar.)
- Orijinal repodaki `docs/agents/*` rol promptları ve `tooling/agent_workflow/` devralmada
  **taşınmayacak** (ADR-0007: geliştirme aracı ürün repo'sunda durmaz).
- `brand` kararı (logo/ görsel kimlik): aynada kaynak adıyla yazılı olmadığı için kurulmadı;
  devralmada gerekiyorsa ayrı iş.
