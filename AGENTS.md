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
   `files = ["src/fairplay_echo"]`, `mypy_path = "src"`. Yol vermek gerekmez; `core app` kökte yok.)
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
- **Belirteç:** renkler/boşluklar CSS değişkeniyle yönetilir; ekrana özel gömülü hex yazılmaz.
- **Sayı biçimi:** para `tr-TR` (virgül ondalık); **oranlar bahisçi konvansiyonu olarak nokta kalır**
  (bilinçli istisna).
- **İnceleme:** arayüz işi, yazarın kendi onayıyla kapanmaz; bağımsız bir alt ajana inceletilir (ADR-0007).
