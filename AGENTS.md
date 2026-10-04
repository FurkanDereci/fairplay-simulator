# Bu Depoda Ajan Kuralları

Bu depo, "sözleşme-önce" yöntemiyle inşa edilir. Aşağıdaki kurallar bağlayıcıdır.

## 1. Sözleşme-önce
- Bir davranış kodlanmadan önce **`docs/20-accounting-spec.md`**'te tarif edilmiş olmalı.
- Spec'teki işlenmiş örnekler (`[G-x]`) koda geçtiğinde **golden test** olur; sayı birebir tutmalıdır.

## 2. Tek uygulama (SSOT)
- Para/politika matematiği **yalnız `core/` içinde** yaşar. API katmanı (`app/`) hesap yapmaz;
  parse → yetki → servis → kalıcılık → serileştirme yapar.
- Bir kuralı ikinci kez yazmak yasaktır. Aynı sonucu iki yerde gördüysen, biri silinir.

## 3. Saf çekirdek
- `core/` hiçbir framework, DB, saat veya RNG **import etmez**. Zaman ve rastgelelik **enjekte edilir**
  (`Clock`, tohumlu `random.Random`). Çekirdek saf fonksiyonlar ve veri sınıflarından oluşur.

## 4. Doküman yalan söylemez
- `40-api.md` elle yazılmaz; OpenAPI'den üretilir.
- `30-architecture.md` iki bölümlüdür: **CURRENT** (var olan) ve **TARGET** (hedef + geçiş tetikleyicisi).
  Bir şeyi hedef diye yazıp var gibi göstermek yasaktır.
- `tests/test_docs_sync.py` yeşil değilse iş bitmemiştir.

## 5. Doğrulama standardı (her değişiklikte)
1. `pytest -q` — tümü geçer.
2. `mypy` — tip hatası yok. (Ayarlar `pyproject.toml`'da: `strict = true`,
   `files = ["src/fairplay_simulator"]`, `mypy_path = "src"`. Yol vermek gerekmez; `core app` kökte yok.)
3. `ruff check .` — lint temiz.
4. `docs-sync` geçer (iddialar gerçekle uyuşur).

## 6. Para ve zaman disiplini
- Para: `Decimal`. İstatistik: `float`. Yuvarlama yalnız sınırlarda ve tek bir politikayla
  (`core/money.py`).
- Zaman: `datetime.now()` doğrudan çağrılmaz; enjekte edilen saat kullanılır.

## 7. Güven sınırı
- **Sunucu otoritedir.** İstemci bir maç sonucunu veya settlement'ı bildirmez; sonuç maç
  motorundan/ingest kaydından gelir.
- Para hareket ettiren uçlar **idempotent** olmalıdır.

## 8. Sade tut
- Gereksiz mühendislikten kaçın: rate limiting, mikroservis, önbellek katmanı vb. ölçülü bir
  tetikleyici olmadan eklenmez.
- Ürün depoları temiz kalır: ajan araçları, üretilmiş raporlar, editör/OS artıkları commit edilmez
  (gerekçe: ADR-0007).

## 9. Arayüz kalite eşiği (UI/UX)

Arayüz değişiklikleri şu eşikleri geçmeden "bitti" sayılmaz:

- **Kontrast:** gövde metni ≥ 4,5:1; ikincil metin de ≥ 4,5:1; anlam taşıyan kenarlık/ikon ≥ 3:1.
  Koyu tema için ayrı ölçülür (aydınlık tema değerlerinin çalıştığı varsayılmaz).
- **Renk tek başına anlam taşımaz.** Kâr/zarar renkleri (yeşil/kırmızı) yalnız bu anlamda kullanılır;
  eylem rengi ayrıdır — yoksa "yeşil buton" ile "kâr" karışır.
- **Durumlar tasarlanır:** yükleniyor / boş / hata. Sessiz başarısızlık yasak: kullanıcı göremiyorsa o
  kural yoktur (bkz. `enerji-mekanigi-ve-gorunurluk` dersi).
- **Klavye:** her etkileşim klavyeyle erişilebilir; `:focus-visible` görünür; form alanlarının
  `label`/`for` eşleşmesi veya `aria-label`ı vardır; aç/kapa düğmeleri `aria-pressed` bildirir.
- **Hareket:** `prefers-reduced-motion` saygı görür; geçişler 150–300 ms.
- **Simge:** yapısal simge olarak emoji kullanılmaz; arka plan görseli yerine vektör tercih edilir.
- **Belirteç:** görsel dil tek kaynaktan yönetilir (`DESIGN.md` → Tailwind `theme` + `app.css`); ayrıntı ve istisnalar `DESIGN.md`'dedir.
- **Sayı biçimi:** para `tr-TR` (virgül ondalık); **oranlar bahisçi konvansiyonu olarak nokta kalır**
  (bilinçli istisna).
- **İnceleme:** arayüz işi, yazarın kendi onayıyla kapanmaz; bağımsız bir alt ajana inceletilir (ADR-0007).

## 10. Commit kimliği
- Commit mesajlarına **araç/otomatik ortak yazar eklenmez.** `Co-authored-by:` trailer'ı (özellikle
  `CommandCodeBot`) yazılmaz: GitHub bu satırı commit'e **ortak yazar** olarak işler ve katkı
  listesinde araç görünür. Katkı listesinde yalnız **gerçek insan yazarlar** bulunur.
- Gerekçe: bu depo herkese açık yayınlanır; katkı grafiği kimin işi olduğunu göstermelidir.
- **Kapı:** `.pre-commit-config.yaml` → `no-bot-coauthor` (`commit-msg` aşaması). Kural yazılı
  kalmaz, ölçülür; `pre-commit install` ile yerel kancaya bağlanır.

## 11. Dil: README ve commit'ler İngilizce
- **`README.md` ve commit mesajları İngilizce** yazılır. Depo public; GitHub'da ilk okunan iki
  yüzey bunlar (commit listesi + README).
- **Geri kalan her şey Türkçe kalır:** `docs/`, `DESIGN.md`, `AGENTS.md`, kod yorumları, arayüz
  metinleri, test adları ve docstring'ler. Bu **bilinçli bir ayrımdır**, tutarsızlık değil;
  gerekçe §11'in ilk maddesinde.
- Commit başlığı emir kipi ve kısa; gövde "ne değişti + niye" der (mevcut alışkanlık korunur).

## 12. Tasarım değişikliği süreci

- **Tasarıma özgü olgular makineyle kaplanmaz; invariantlar kaplanır.** Kontrast, taşma/kırpılma/
  örtüşme, "renk tek başına anlam taşımaz", sayı biçimi, klavye ve `[hidden]` **kapılıdır**;
  hex'in nerede yaşadığı, fontun kaynağı, gradyan/cam/glow gibi görsel-dil tercihleri `DESIGN.md`'de
  **prose**dur — test olmaz, köklü değişiklikte silinecek kapı yoktur.
- **Köklü görsel değişiklik proposal ister** (ADR-0016): problem · hedef görünüm · değişenler ·
  risk altındaki invariantlar · güncellenecek dokümanlar. Onay ölçütü: 4 genişlikte
  (375/900/1200/1440) ekran görüntüsü + invariant suite yeşil + kontrast kontrolü. Kayıt
  `docs/60-decisions/`.
- **Renk tek kaynak:** `web/assets/app.css` `:root`; Tailwind `theme` ona `var()` ile referans
  verir; markup ham hex yazmaz.
