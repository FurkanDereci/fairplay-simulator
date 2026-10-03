# Mimari — Mevcut ve Hedef

> Bu belge **iki bölümlüdür ve karıştırılmaz.** **CURRENT** = gerçekten var olan.
> **TARGET** = hedef + ona geçiş için **sayısal tetikleyici**. Hedefi "varmış" gibi yazmak yasaktır.

---

## CURRENT (bugün gerçek olan)

**S1–S7 tamam** (S8 hariç). Çalışan sistem: `core/` saf çekirdek · `repo/` SQLite · `engines/` maç
motoru + benchmark botları · `app/` FastAPI kabuğu (servis + router) · `web/` tek sayfa arayüz.
Sunucu: `python -m fairplay_simulator.cli serve`; şema/doküman: `export-openapi` · `render-api-docs`.
Testler: golden · property · repo · engines · api · **ui (gerçek tarayıcı)** · docs-sync — kapılar yeşil.
Kapılar: `ruff check .` · `mypy --strict` · `pytest -q`. Ölçülen ortam: Python 3.10.12.

**CURRENT'da olmayan (TARGET'ta duran) şeyler:**
- Arayüz istemcisi OpenAPI'den **üretilmiyor**; elle yazılmış ince bir `fetch` istemcisi var
  (mock state yok).
- Rozetler ve solvent-gün tier indirimi duvar saatiyle işlenmiyor (çekirdek fonksiyon testli).
- Rate limiting, PostgreSQL, Redis, mikroservis — tetikleyici bekliyor (aşağıda).

## TARGET (hedef mimari)

Tek süreç · tek depo · SQLite · arayüz tek sayfa. Katmanlar:

```
core/                      SAF ALAN — framework/DB/saat/RNG import ETMEZ
  errors.py                alan hataları (istisna hiyerarşisi)
  money.py                 Decimal + tek yuvarlama politikası
  ledger.py                olay tipleri + append-only kayıt (durum tutmaz)
  nav.py                   birimleştirme projeksiyonu (Fund) + twr
  metrics.py               TWR · MDD · Sharpe · Sortino · Beta/Alpha · RAS · işlem istatistikleri
  odds.py                  vig/overround · fair odds · Kelly · EV · CLV
  settlement.py            ödeme kuralları + kupon sonuçlandırma
  energy.py                enerji (politika katmanı)
  cooldown.py              kademeli kilit (politika katmanı)
  learning.py              öğrenme ölçütleri (defterden türeyen davranış metrikleri)
app/                       İNCE API KABUĞU — parse → authz → servis → kalıcılık → serialize
  api/ · services/ · repo/ · auth · deps (Clock, Config, Session)      [S4]
engines/                   match (tohumlu Poisson/MC) · bots (tohumlu) [S5–S6]
cli.py                     replay · simulate · export-ledger           [S3]
web/                       OpenAPI'den üretilen tipli istemci — mock state YOK [S7]
tests/                     golden · property · docs-sync
```

### Katman sözleşmeleri
- **core → hiçbir şey.** Saf fonksiyonlar + veri sınıfları. Zaman ve rastgelelik enjekte edilir.
- **app → core.** `app/` iş kuralı taşımaz; yalnız orkestre eder. Bir endpoint'te `NAV`, `TWR`,
  iflas, enerji veya cooldown **hesabı** görürsen, tasarım bozulmuştur.
- **engines → core.** Motorlar sonucu core'un anlayacağı bir olguya çevirir; para matematiğine dokunmaz.
- **web → app (OpenAPI).** Şema kaynaktır; şema değişince contract testi kırılır.

### Depolama
- **Ledger merkezli:** `ledger_entries` append-only tablo; `balances`/`nav_history` **projeksiyon**dur
  (gerekirse yeniden üretilebilir). Para kolonları `Numeric`/string (Decimal), `Float` değil.

### Zaman / rastgelelik
- `Clock` arayüzü enjekte edilir; `datetime.now()` core'da geçmez.
- Simülasyon tohumlu `random.Random(seed)` kullanır: aynı seed → aynı sonuç.

### Idempotency
- Para hareket ettiren uçlar (`wager`, `settle`, `refill`) bir idempotency anahtarı alır; tekrar
  gönderim yeni kayıt üretmez, ilk sonucu döner (`409` veya ilk yanıt).

---

## TARGET'e geçiş tetikleyicileri

Aşağıdakilerden **biri ölçülüp gerçekleşene kadar** ilgili teknoloji eklenmez:

| Teknoloji | Tetikleyici |
| --- | --- |
| PostgreSQL | Eşzamanlı yazıcı > 1 süreç, ya da tek DB dosyası kilitlenmeye başladığında |
| TimescaleDB | `ledger_entries` > ~50M satır veya zaman-serisi sorguları SLA'yı bozduğunda |
| Redis / önbellek | Portföy ucu p95 > 200 ms ve DB profili önbelleği işaret ettiğinde |
| Mikroservis ayrımı | Tek süreç derleme+test süresi > 10 dk, ya da bağımsız ölçekleme gerekene kadar |
| Rate limiting | Gerçek kötüye kullanım gözlemlendiğinde |
| Defter snapshot'ı | Kullanıcı başına **> 100.000 olay** veya `cli replay` **> 250 ms** (ölçüm 2026-09-30: 5.001 olay → 7,1 ms; ADR-0009) |

## Kayıt

Her mimari karar `docs/60-decisions/` altında tarihli bir ADR'dir. Bir TARGET iddiası ancak bir ADR'ye
dayanıyorsa geçerlidir.
