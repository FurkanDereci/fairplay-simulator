# ADR-0018 — Import Döngüsünü Kırma: `services` Paket-İmportu → Alt-Modül İmportu

- **Durum:** Kabul edildi
- **Tarih:** 2026-10-12
- **Bağlam:** Kod grafiği (graphify, 2026-10-05) `app/` içinde **5 dosyalık bir döngü** gösterdi:
  `app/__init__ → main → api/__init__ → routes → services → app/__init__`. Döngü çalışma anında
  **hata vermiyor** (Python, kısmen başlatılmış paketi tolere eder) ama `docs/30`'un "app/ ince
  kabuk · tek yönlü bağımlılık" katman iddiasını aşındırıyor. PM raporu (2026-10-07, Ö-5) döngünün
  kırılmasını ve **kırma sırasının** ADR'ye bağlanmasını istedi. 2026-10-12'de döngü
  `graphify extract --code-only` ile birebir yeniden üretildi.

## Kök (ölçüm)

Döngüyü kapatan tek kenar **paket-importudur**: `services.py`'de
`from . import fixtures as fixture_catalog`. graphify, `from . import X` ifadesini *paketin
`__init__`'ine* kenar olarak çözer (`X` alt-modülüne değil). Ölçüm: `app/` ağacında
`from . import <ad>` biçimli geçiş **tek** — bu satır. Kaldırıldığında döngü kapanmaz, çünkü
`app/__init__ → main → api → routes → services` zinciri durur ve geri dönen kenar kalmaz.

## Karar

`services.py`'deki paket-importu **doğrudan alt-modül importuna** çevrildi:

```python
# önce
from . import fixtures as fixture_catalog
# sonra
from .fixtures import Fixture, all_fixtures, closing_odds, kickoff
from .fixtures import get as fixture_get
```

Çağrı yerleri (`fixture_catalog.get(...)` → `fixture_get(...)` vb.) buna göre güncellendi. Böylece
`services`'in gerçek bağımlılığı **`app.fixtures` modülüne** işaret eder (`app.clock`, `app.config`,
`app.errors`, `app.security` gibi diğer alt-modül importlarıyla aynı biçimde); paket `__init__`'ine
kenar kalmaz ve döngü yapısal olarak imkânsızlaşır.

**Kırma sırası:** tek paket-importu olduğu için seçim tekti; önce bu kenar kesildi, çünkü
(i) döngüyü **tek** değişiklikle kapatır ve (ii) **davranışı değiştirmez** — yalnız import biçimi
değişir, çalışma anındaki bağımlılık yönü aynı kalır.

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| `app/__init__`'i tembel yap (`create_app`'i `__getattr__` + `TYPE_CHECKING` ile) | **Ölçüldü, işe yaramadı:** graphify `TYPE_CHECKING`/`__getattr__` gövdesindeki `from .main import` ifadesini de kenar sayıyor → döngü yine sürüyor (denendi, doğrulandı). Ayrıca `create_app`'i zaten herkes `…app.main`'den alıyor; paket ihracı ölü bir kolaylık. |
| `app/__init__`'ten `create_app` ihracını **tamamen sil** | Geriye dönük kolaylığı yok eder (kırıcı); gereksiz. |
| Döngüyü **olduğu gibi bırak** | Çalışıyor ama katman iddiası ile grafik gerçeği ayrışık kalır; yeni geliştirici için yön şaşırtıcı. |
| `deps`/`services`'i paket dışına taşı | Ölçüsüz refaktör; ADR-0007'nin sade repo ilkesiyle uyumsuz. |

## Sonuçlar

- (+) Döngü **yapısal olarak kapandı**: `graphify` modül grafiğinde `app/` içinde döngü **0**
  (2026-10-12 ölçümü; Ö-5 kapanış ölçütü).
- (+) **Davranış değişmedi**: yalnız import biçimi; `app/__init__`'in `create_app` ihracı ve
  tüm çağrı yolları aynı. Kapılar yeşil (**150 test** · `ruff` · `mypy` · `docs-sync`).
- (+) Katman iddiası (`docs/30`) grafikle uyuşuyor: `app/__init__` artık geri işaret almayan bir
  kolaylık yüzeyi.
- (−) `services`'te `get` çakışmasını önlemek için `as fixture_get` takma adı kullanılır; küçük
  isimlendirme maliyeti.
