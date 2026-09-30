# Parite ve Devralma

Bu depo, mevcut **`github.com/FurkanDereci/fairplay-simulator`** reposunun **yerine geçme
adayıdır**; ayrı bir repo değildir. Bu dosyanın amacı o kararı kanaate bırakmamak: iddiaları
ölçülebilir hâle getirmek.

> **Provenans (önemli).** Orijinal repo hakkındaki satırlar **2026-09-30**'da
> `~/dev/fairplay_simulator_src` (`4c34c53`, `origin/main` ile senkron) üzerinde **ölçülerek**
> alındı; bu deponun test koşusunun parçası olmadıkları için `docs-sync` onları doğrulayamaz —
> bu yüzden her satırın yanında ölçüm kaynağı yazılıdır. **echo tarafı** iddiaları ise
> `tests/test_docs_sync.py` ile bağlıdır.

---

## 1. API paritesi

| Uç | Orijinal | echo | Not |
| --- | --- | --- | --- |
| `GET /` | var | var | |
| `GET /api/fixtures` | var | var | |
| `GET /api/portfolio` | var | var | |
| `POST /api/auth/register` | var | var | |
| `POST /api/auth/login` | var | var | |
| `POST /api/wager` | var | var | echo'da idempotency anahtarı + enerji kapısı |
| `POST /api/refill` | var | var | |
| `POST /api/matches/simulate` | var | var | echo'da **tohumlu** (aynı seed → aynı skor) |
| `POST /api/matches/monte_carlo` | var | var | echo'da `match_id` **veya** ham oran + `seed` |
| `POST /api/wager/settle` | var | **yok** | bilinçli kaldırıldı — bkz. §3 |
| `GET /healthz` | yok | var | |
| `POST /api/estimate` | yok | var | kullanıcı olasılığından EV/Kelly (ADR-0006) |

**Ölçüm:** orijinalin uçları `src/backend/app.py` içindeki `@app.*` dekoratörlerinden, echo'nunki
`docs/40-api.md`'den (OpenAPI'den üretilir) okundu.

**Arayüz kullanımı:** orijinalin SPA'sı (`src/frontend/index.html`) yalnız şu uçları çağırıyor:
`register · fixtures · simulate · portfolio · refill · wager`. Yani `monte_carlo` ve `wager/settle`
farkları **arayüz akışını etkilemez**, yalnız API yüzeyini etkiler.

## 2. Risk paritesi

Orijinalin 2026-09-10 incelemesinde çıkan ve belgelenen kod riskleri:

| Orijinalin riski | echo'daki durum | Kanıt |
| --- | --- | --- |
| `auth.py`: `JWT_SECRET_KEY` yoksa **bilinen sabit** varsayılana düşüyor | env yoksa rastgele anahtar + `RuntimeWarning` | `app/config.py` · `tests/api` (token akışı) |
| `calculate_twr` seriler arası bileşik değil | `Fund.twr` seriler arası **bileşik** | `core/nav.py` · `[G-2]` · `I4` |
| `simulation_energy` hiç yenilenmiyor | saatte 10 yenilenir, <10'da bahis reddi (429) | `core/energy.py` · `[G-12]` · `I5` |
| `benchmark_engine`: `except Exception: pass` + botlar bellekte, restart'ta sıfırlanıyor | botlar **durum tutmaz**; eğriler maç kayıtlarından türetilir | `engines/bots.py` · `tests/engines/test_bots.py` |
| CORS `*` | `CORS_ORIGINS` ile yapılandırılabilir; varsayılan localhost + `null` | `app/config.py` · `app/main.py` |
| `WagerModel.created_at` yok → bekleyen kuponu olan kullanıcıda `/api/portfolio` çöküyordu | böyle bir model yok; kupon durumu defterden türer | `core/nav.py` · `tests/api` |

**Kapılar:** orijinal 40 test (`unittest`) · echo **86 test** (`pytest` + Hypothesis + gerçek
tarayıcı). Test sayısı tek başına üstünlük değildir; asıl fark **neyin** test edildiğidir (§4).

## 3. Bilinçli farklar (eksik değil)

- **`POST /api/wager/settle` kaldırıldı.** Orijinalde istemci "bu kupon kazandı" diyebiliyordu;
bu bir **güven sınırı ihlali** (bedava kupon). echo'da sonuç yalnız maç simülasyonundan gelir.
Ölçüm: orijinalin arayüzü de bu ucu kullanmıyordu, yani kaldırmak mevcut akışı bozmuyor — ama
**dış istemciler için kırıcı bir değişikliktir** ve devralmada not edilmelidir.
- **`monte_carlo` ucu kimlik doğrulaması ister.** Orijinalde anonimdi; echo'da `/api/matches/*`
tutarlılığı için token gerekir.
- **Oranlar katalogdan gelir.** Orijinal `simulate` ucu da katalogdan okuyordu; echo'da
`monte_carlo` hem katalog hem **varsayımsal oran** kabul eder (parite korunur).

## 4. echo'nun ekledikleri

- **Ölçülebilir doküman dürüstlüğü:** `docs-sync` testi; spec örnekleri (`[G-x]`) ↔ golden testler,
  belgedeki uç listesi ↔ OpenAPI şeması, belgedeki test yolları ↔ gerçek dosyalar.
  Orijinalde doküman-kod sapması **oluştu** ve sonradan etiketlenerek yamandı.
- **Gerçek tarayıcı testleri** (`tests/ui`): akış + yerleşim taşması kapısı. Orijinalde yoktu;
  orijinalde enerji göstergesi kusuru bu yüzden ancak elle yakalandı.
- **Determinizm:** enjekte `Clock`, tohumlu `Random` (maç motoru, botlar, Monte Carlo, kapanış çizgisi).
- **Event-sourced defter:** bakiye/NAV türetilir; `cli replay` bir durumu yeniden üretir.
- **Kurulabilirlik:** `pyproject.toml` + temiz ortamda doğrulanmış kurulum (orijinal
  `requirements.txt`'i sonradan kazandı).

## 5. Devralma planı (henüz **uygulanmadı**)

Karar: bu depo daha iyi bulunursa içerik doğrudan `fairplay-simulator` reposuna gider.

Önerilen yol **(dal + PR)**, force-push **değil**:

1. `fairplay_echo` uzak olarak `git@github.com:FurkanDereci/fairplay-simulator.git` eklenir.
2. İçerik **ayrı bir dalda** yayınlanır (ör. `v2`), `main`'e doğrudan yazılmaz.
3. PR ile **diff olarak** incelenir: parite kaybı var mı, kırıcı değişiklik ne, testler ne diyor.
4. Kabul edilirse `main`'e merge edilir; edilmezse dal silinir.

Gerekçe: orijinalin commit geçmişi korunur, karar **incelenebilir bir diff** olur (kanaat değil) ve
geri dönüşü vardır. Force-push, public repoda geçmişi geri dönüşsüz siler.

**Devralma anında çözülecek iki şey:**

- **İki yerel klon:** `~/dev/fairplay_simulator_src` ve `~/dev/fairplay_echo`. Hangisi çalışma klonu
  olacak, diğeri ne olacak? (Vault'taki `fairplay-simulator` notu şu an ilkini işaret ediyor.)
- **`wager/settle` kırıcı değişikliği** PR açıklamasında açıkça yazılmalı.

## 6. Açık sorular

- Karşılaştırmanın **karar anı** kimin: hangi ölçüt "daha iyi" sayılacak? (Bu dosya ölçütü
  tablolaştırır; eşiği kullanıcı koyar.)
- Orijinal repodaki `docs/agents/*` rol promptları ve `tooling/agent_workflow/` devralmada
  **taşınmayacak** (ADR-0007: geliştirme aracı ürün repo'sunda durmaz).
- `brand` kararı (logo/ görsel kimlik): aynada kaynak adıyla yazılı olmadığı için kurulmadı;
  devralmada gerekiyorsa ayrı iş.
