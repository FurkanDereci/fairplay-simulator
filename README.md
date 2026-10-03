# FairPlay Echo

Sıfırdan çizilmiş FairPlay: gerçek para içermeyen, eğitici futbol tahmin/**portföy** simülatörü.
Kupon bir fon pozisyonu gibi ele alınır — birim NAV, vig arındırma, Kelly, Sharpe/Sortino/MDD,
CLV ve iflasta kademeli bekleme kilidi.

**İlkeler:** sözleşme-önce · tek uygulama (SSOT) · saf çekirdek · event-sourced defter ·
para `Decimal` / istatistik `float` · **sunucu-otoriteli settlement** · determinizm ·
doküman yalan söylemez.

## Kurulum

```bash
python3 -m venv .venv          # veya: python3 -m virtualenv .venv
.venv/bin/pip install -e ".[dev]"
```

## Çalıştırma

```bash
.venv/bin/fairplay-echo serve --db fairplay.db --port 8000
# arayüz: http://127.0.0.1:8000  (kayıt ol → 1.000 TL sanal bakiye)
```

Aynı ikili `replay`, `export-openapi`, `render-api-docs` ve `version` alt komutlarını da taşır.

## Nasıl test edilir

**1. Otomatik testler** — golden · property · repo · engines · api · ui · docs-sync:

```bash
.venv/bin/pytest                # tümü geçmeli
```

**2. Kalite kapıları:**

```bash
.venv/bin/ruff check .          # lint
.venv/bin/mypy                  # tip (strict)
```

**3. Elle, tarayıcıdan** — `fairplay-echo serve` ile aç; kayıt ol, bahis yap (enerji başlıkta
görünür), "Simüle" ile maçı sonuçlandır, NAV ve benchmark eğrilerini izle. Kasanın %15'ini aşan bir
stake girersen **onay modalı** çıkar (risk kapısı); 6+ bahis sonrası `learning-report` ölçütlerinden
**disiplin rozetleri** görünür.

> `pip install -e ".[dev]"` yapılmadıysa komut yerine
> `PYTHONPATH=src .venv/bin/python -m fairplay_echo.cli <komut>` kullan.

### Arayüz açılmıyorsa

Sayfayı **sunucudan** aç: `http://127.0.0.1:8000`. HTML dosyasını çift tıklayıp açarsan adres
`file://` olur ve istekler `file:///api/...` biçiminde çözülemez. Yine de dosyadan açmak istersen:
sayfa API'ye `http://127.0.0.1:8000` üzerinden bağlanır (CORS'ta `null` kökeni izinlidir) — yani
sunucu 8000 portunda çalışıyorsa dosyadan açmak da çalışır. Ulaşamazsa sayfa üstünde kırmızı bir
uyarı bandı çıkar.

## Faydalı komutlar

```bash
# Bir kullanıcının defterini oynat ve durumu bas (I2: replay durumu birebir üretir)
.venv/bin/fairplay-echo replay aytek --db fairplay.db

# API dokümanını OpenAPI'den yeniden üret (elle yazılmaz)
.venv/bin/fairplay-echo render-api-docs --output docs/40-api.md

# OpenAPI şeması
.venv/bin/fairplay-echo export-openapi | head -40
```

## Nereden bakılır

| Ne | Dosya |
| --- | --- |
| Neden var, ne değil | `docs/00-vision.md` |
| Varlıklar, durum makineleri, değişmezler (I1–I6) | `docs/10-domain-model.md` |
| **Sözleşme** — formüller + işlenmiş örnekler (`[G-x]`) | `docs/20-accounting-spec.md` |
| **Arayüz sözleşmesi** (tokenlar, nevers, bileşen kuralları) | `DESIGN.md` |
| Mevcut vs hedef mimari + geçiş tetikleyicileri | `docs/30-architecture.md` |
| API (OpenAPI'den üretilir) | `docs/40-api.md` |
| Risk → test matrisi | `docs/50-test-strategy.md` |
| İnşa sırası ve durum | `docs/ROADMAP.md` |
| **Kalite alanları — karar ve kapı indeksi** | `docs/80-kalite-alanlari.md` |
| Ürün değeri: "öğrettiği" nasıl ölçülür | `docs/90-urun-degeri.md` |
| Orijinal repo ile parite + devralma planı | `docs/70-parite-ve-devralma.md` |
| Mimari kararlar (ADR) | `docs/60-decisions/` |

## Bu deponun tek kuralı

**Hiçbir döküman yalan söylemez.** Her olgusal iddia ya üretilir (`40-api.md` ← OpenAPI) ya da bir
testle bağlanır (`tests/test_docs_sync.py`: spec örnekleri ↔ golden testler, belgedeki uç listesi ↔
OpenAPI şeması, belgedeki test yolları ↔ gerçek dosyalar).
