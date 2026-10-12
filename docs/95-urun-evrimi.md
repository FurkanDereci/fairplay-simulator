# Ürün Evrimi — Nerede, Neye Doğru, Ne Zaman

> **Bu sayfa bir özettir, sözleşme değil.** Amacı tek bakışta yön vermek; her satır kendi
> **tek doğruluk kaynağına** bağlanır ve bir kural burada **tekrar yazılmaz** (`AGENTS.md` §2).
> Mimari sözleşme `docs/30-architecture.md`, kapsam `docs/00-vision.md`, dilimler `docs/ROADMAP.md`.

## 1. Nerede duruyoruz

- **Vizyon / non-goal:** `docs/00-vision.md` (VISION etiketli — vaat ≠ mevcut durum).
- **Dilimler:** `docs/ROADMAP.md` — S0–S8 (durum kolonu güncel tutulur).
- **Mimari (CURRENT vs TARGET):** `docs/30-architecture.md`.
- **Kalite indeksi:** `docs/80-kalite-alanlari.md` (11 alanın karar + kapı karşılığı).
- **Kod haritası (devir için):** `docs/85-kod-haritasi.md`.
- **Kapılar:** `ruff` · `mypy` · `pytest` · `docs-sync` (kurulum: `README.md`).

## 2. Neye doğru (eksen)

- Ürün **eğiticidir**: bir kupon fon **pozisyonu** gibi modellenir; amaç disiplin/ölçüm, tavsiye
  değil → `docs/00-vision.md`, `docs/90-urun-degeri.md`.
- **Bilinçli kapsam-dışı** (değişmedi): gerçek para, tavsiye, sosyal/kopya fon (Faz 2) ve R7
  (asya handikapı) → `docs/00-vision.md`, `docs/70-parite-ve-devralma.md`.
- **Ticari/pazar ekseni bu sayfada iddia edilmez:** bu repoda kullanıcı/rakip/fiyat verisi yok
  (PM raporu 2026-10-07 §9). Bugün konumlandırma bir **iddia** değil, boş bir eksendir.

## 3. Sırada ne (açık işler)

| İş | Neden | Kaynak |
| --- | --- | --- |
| **Sanal sezon + kalibrasyon (S9)** | Ürünün **döngüsü yok**; bu, döngüyü **sağlayıcısız** (mock dünya) kurar ve Ö-1'e zemin olur. Üç yapı taşı bitmeden başlamaz: oran–sonuç ayrımı · olasılık kaydı+Brier · sezon kimliği | `docs/60-decisions/0024-sanal-sezon-ve-kalibrasyon.md` · `docs/ROADMAP.md` |
| **Ö-1 — M2 öğrenme çalışması** | Ürün tezinin ("öğretir") **tek açık kanıtı**; insan katılımcı gerektirir, kod işi değil — katılımcı yoksa **n=1 pilot** varyantı: `docs/90-urun-degeri.md` §4.1 | PM raporu §5 (Ö-1) |
| **Parite: F3 kupon fişi → F4 factsheet** | Arayüz paritesi; **kabul ölçütü değil**, iyileştirme | `docs/70-parite-ve-devralma.md` |
| **Parola sıfırlama / hesap kurtarma** | Bugün akış yok; parola unutulursa hesap arayüzden erişilemez | Vault `Backlog` (FairPlay / parola sıfırlama) |

## 4. Koşullu tetikleyiciler — "ne zaman ne olur"

Eşiklerin **yazılı olduğu yer `docs/30-architecture.md` §"TARGET'e geçiş tetikleyicileri"**dir;
burada yalnız **nasıl ölçüleceği** ve neyin ateşleneceği özetlenir (sayı tekrarı yok).

| Konu | Bugünkü durum | Ölçüm yolu | Ne ateşlenir |
| --- | --- | --- | --- |
| **Gerçek maç verisi (mock → sağlayıcı)** | yok (mock fikstür + sentetik kapanış) | — (sayısal değil) | **Ö-1 (M2) olumlu** → sağlayıcı fazı (ADR-0022; `docs/30-architecture.md`) |
| Ölçek göçü (PostgreSQL / TimescaleDB / Redis) | yok (tek süreç + SQLite) | `fairplay-simulator scale-report` | `docs/30-architecture.md` TARGET geçişi |
| Defter snapshot'ı | yok (her okuma baştan replay) | `fairplay-simulator scale-report` | snapshot katmanı (ADR-0009) |
| Rate limiting | yok | `GET /api/telemetry` (yetkili) | hız sınırı dilimi (ADR-0021) |
| Mikroservis ayrımı | yok (tek süreç) | derleme + test süresi | `docs/30-architecture.md` TARGET |

## 5. Karar noktaları (kapı değil, insan kararı)

- **Ö-1 sonucu ürün tanımını belirler:** olumluysa gerçek sağlayıcı verisi fazı açılır (ADR-0022) ve
  öğretici yüzey öne çıkar; olumsuzsa ürün dürüstçe yeniden konumlanır ve gerçek veri yatırımı
  yapılmaz (PM raporu §4).
- **Parola sıfırlama biçimi:** e-posta token'ı mı, "tek kullanıcılı MVP → kabul" mi, `cli
  reset-password` mı → **ADR** bekler.
- **Köklü görsel değişiklikler**: proposal + ADR süreci → `docs/60-decisions/0016-*`, `DESIGN.md`.

## Kaynaklar

- `docs/00-vision.md` · `docs/30-architecture.md` · `docs/50-test-strategy.md` ·
  `docs/70-parite-ve-devralma.md` · `docs/80-kalite-alanlari.md` · `docs/85-kod-haritasi.md` ·
  `docs/90-urun-degeri.md` · `docs/ROADMAP.md` · `docs/60-decisions/`
