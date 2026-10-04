# DESIGN.md — FairPlay Simulator arayüz sözleşmesi

Arayüz üretirken kararların **tek kaynağı** burasıdır: bir kural burada yaşar, başka yerde
tekrarlanmaz. Kalite eşikleri (`AGENTS.md` §9) bilinçli olarak burada **yazılmaz** — orada kalır.

Bu dosyanın varlık sebebi: bir ajan yön verilmediğinde eğitim verisinin ortalamasını üretir
(mor gradyan, üç özdeş kart, ortalanmış hero). Ortalamayı **kaydırmanın** yolu, tokenları ve
"ne olmayacak"ları her oturumda okunan bir dosyaya bağlamaktır.

## İlkeler

- **Yoğunluk süsün önünde.** Bu bir finans paneli; vitrin sayfası değil.
- **Görsel dil prototipten gelir.** Arayüz, `istenen prototip` altındaki
  `fairplay_outlier_zanaat_desktop_i_nteraktif_prototip` prototipinin dilini konuşur: Outlier koyu
  tema, 3 kolonlu lab kabuğu (sol menü · kanvas · sağ rail), kart ızgarası, `01 //` modül
  numaralandırması. Görünüm sadıktır; işlev (auth + canlı veri + tüm API akışları) korunur.
- **Durumlar tasarlanır.** Yükleniyor / boş / hata / odak / disabled. Sessiz başarısızlık yasak:
  kullanıcı göremiyorsa o kural yoktur.
- **Anlamsız metrik renk taşımaz.** Örneklem yetersizken risk kutuları nötr kalır (testle bağlı).
- **Ölçüm > izlenim.** Arayüz işi, render edilip bakılmadan bitmez.

## Tokenlar

Renklerin tek kaynağı **`web/assets/app.css` içindeki `:root`**; bileşen stilleri de aynı dosyada
yaşar. Markup'ta prototip dilini taşıyan Tailwind arbitrary-value sınıfları (`bg-[#0b0f17]`)
bulunur; **yeni bir renk gerekiyorsa önce `:root`a token eklenir**, markup'ta hex uydurulmaz.

| Rol | Token | Değer |
| --- | --- | --- |
| Sayfa zemini | `--bg` | `#0b0f17` |
| Çukur alan (giriş, grafik, değerlendirme kutusu) | `--sunken` | `#0a0f16` |
| Panel | `--card` | `#121924` |
| Panel içi kutu | `--card-2` | `#0d141e` |
| Dekoratif ayraç | `--line` | `#1f2b3b` |
| Anlamlı kenarlık | `--line-strong` | `#5b6b84` |
| Metin | `--fg` | `#f8fafc` |
| İkincil metin | `--muted` | `#94a3b8` |
| Eylem / vurgu | `--accent` / `--accent-hover` | `#00d2b4` / `#00b89e` |
| Eylem yüzeyi üstündeki metin | `--on-accent` | `#06151a` (koyu — teal üstünde beyaz **okunmaz**) |
| İnce vurgu | `--accent-soft` | `rgba(0, 210, 180, .16)` |
| Kâr / uyarı / zarar | `--good` / `--warn` / `--bad` | `#34d399` / `#f59e0b` / `#f87171` |
| Kısıt bildirimi kutusu | `--warn-bg` / `--warn-line` | `#1b1915` / `#7a5a19` |
| Hata bildirimi | `--banner-bg` / `--banner-border` / `--banner-fg` | `#2a1417` / `#7f1d1d` / `#fecaca` |
| Yazı tipi — metin | `--font-sans` | `Plus Jakarta Sans`, sistem yığınına düşer |
| Yazı tipi — sayı | `--font-mono` | `JetBrains Mono`, sistem yığınına düşer |
| Yarıçap | `--radius` / `--radius-sm` | `16px` / `10px` |
| Boşluk | `--gap` | `16px` |
| Süre | `--dur` | `200ms` |
| Grafik serileri | `--series-nav` / `--series-random` / `--series-favorite` / `--series-home` | `#00d2b4` / `#f59e0b` / `#3b82f6` / `#94a3b8` |

- **Aralık ritmi:** 4'ün katları (4 / 8 / 10 / 12 / 14 / 16 / 20). Ritim dışı boşluk yazılmaz.
- **Tipografi:** iki rol, iki yığın. **Metin** `--font-sans`; **sayı** `--font-mono` +
  `tabular-nums` — sayısal alan hizalanır, satır satır taranır. Yazı tipleri **yerel** `@font-face`
  ile gelir (`assets/fonts.css` + `assets/fonts/*.woff2`); çalışma anında ağdan font **çekilmez**,
  dosya yoksa sistem yığınına düşer.

## Görsel dil revizyonu (2026-10-04, re-skin)

Arayüz, `fairplay_outlier_zanaat_desktop_i_nteraktif_prototip` prototipine göre yeniden kaplandı.
Sadakat öncelikli olduğu için eski sözleşmenin bazı maddeleri **bilinçli olarak gevşetildi**:

- **Aksan artık prototipin teali `#00d2b4`.** Eskiden desatüre `#2fb3a4` idi; neon kaygısı prototip
  sadakati lehine bırakıldı. `--on-accent` yine **koyu** (`#06151a`): teal dolgu üstünde beyaz
  metin okunmaz (ölçüldü, `app.css` başındaki token notları).
- **Yüzeyler prototip paletinden:** `--card #121924`, `--card-2 #0d141e`, çukur `#0a0f16`.
- **Gradyan / cam / glow artık serbest.** Prototipin dili bunları taşır: üst bar `backdrop-blur`,
  giriş paneli ve sol menü gradyanı, `pulse-glow`, enerji çubuğu glow'u. Bu bir kusur değil,
  bilinçli port kararıdır.
- **Bileşen sınıfları:** `.outlier-card`, `.pill-badge` (is-accent/is-good/is-warn/is-info),
  `.module-head/.module-no/.module-title`, `.energy`, `.side`, `.rail`, `.lab-canvas`.
- **Stil sahipliği:** JS'in `className`'ini yazdığı her öğe (`.energy`, `#energy-display`,
  durum sınıfları) `app.css`'te **sınıf/id** seçicisiyle stillenir — Tailwind Play preflight'ı
  element seçicilerini ezebileceği için bu kural bağlayıcıdır.

## Renk kullanım kuralları

- **Anlamsız metrik renk taşımaz.** `risk.reliability.sharpe_reliable` false iken risk kutuları
  (Sharpe/Sortino/MDD/Beta/Alpha/RAS) **nötr** gösterilir: sayı kalır, kırmızı/yeşil susar. Çünkü
  renk bir **yorum**dur ve `t < 2` iken yorum yasaktır (`docs/20` §2.8, alan 3). Bu kural testle
  kapıya bağlıdır (`tests/ui/test_ui_flow.py`).
- Sıfır değeri nötrdür — yeşil gösterilmez.
- Yeşil/kırmızı **dekor değildir**: yalnız işaretli kâr/zarar ve kupon durumu.
- Grafik serileri anlam taşımadığı için ayrımı **çizgi deseni** de taşır (renk körü ayrımı);
  portföy çizgisi en üstte ve daha kalın çizilir.

## Ne olmayacak (nevers)

- Emoji'yi yapısal simge olarak kullanmak (açılır ok CSS üçgeniyle çizilir; ikonlar Lucide SVG).
- Landing-page klişeleri: ortalanmış hero, tek "Get Started" butonu, "trusted by" logoları.
- Ölçüsüz süs: amaçsız gradyan, ekranı dolduran glow. Gradyan/cam yasak değil ama **prototipin
  taşıdığı yerde** kullanılır; yeni dekor icat edilmez.

## Bileşen kuralları

- `.market` 7 kolonlu ızgaradır (`--market-cols`); **dar kapsayıcıda (≤780px) 2 kolona** düşer
  (container query). Metin kolonu `minmax(0, 1fr)`, `.market-meta` **sarar** — kırpmaz.
  **Ölçüm (2026-10-03):** bu satır 7 kolonda ancak ≈1400px üstünde tek satıra sığar. Bant eskiden
  kusurluydu (sabit kolon komşuya taşıyor, "Bahis" düğmesi örtülüyordu) — bkz. `tests/ui`
  `elementFromPoint` kapısı.
- `details.match > summary` **sarabilir** (`flex-wrap`) — dar ekranda başlık + meta + düğme taşmasın.
- `.market` satırının alanları `.market-head` ipucuyla **adlandırılır** ("p %", "tutar" tek başına
  okunmuyordu). İpucu **ızgara değildir, hizalanmaz**; ≤780px'de gizlenir, erişilebilir ad
  kontrollerin `aria-label`'ında kalır.
- Kullanıcıya görünen metinde **ham enum yaşamaz** (`HOME`, `BTTS_YES`, `OVER_UNDER_2.5`):
  `MARKET_LABELS`/`SELECTION_LABELS` çevirir, API'ye giden `value` ham enum kalır. Kupon durumu
  (`WON`/`LOST`/`BEKLİYOR`) testlerle sabitlendiği için ekranda kod olarak kalır — anlamı `title`'da.
- Süre ve ölçek **okunur birime** çevrilir: `168 saat` yerine `7 gün (168 saat)` (`fmtHours`).
- `.table-wrap` yatay kaydırılır; `contain: inline-size` tablonun sayfayı genişletmesini önler.
- `.tile` ızgarası masaüstünde 3, **≤520px'de 2 kolon**; hero metrik yazısı ≤520px'de 22px.
  `#fund-tiles` 2 kolondur (yerleşim kapısı 375px'de tam 2 kolon ister).
- **Modül başlığı numaralıdır:** `01 // SERMAYE VE FON` — numara `--font-mono` + `--accent`,
  başlık metni `--font-sans`. Sıra, panelin okunma sırasını söyler.
- Kutucuk değerleri **mono**; değer **sarmaz** dışarı doğru kırpılmaz (kırpılan sayı "ölçüm"
  değildir) — gerekiyorsa birden çok satıra iner.
- **Çip iki işi yapar:** (a) lejant toggle — gizli seri `aria-pressed="false"` **ve** üstü çizili
  + `--muted` (yalnız renk solluk ile anlatılmaz); (b) zaman aralığı — tek seçim, basılı çip
  `--accent` dolgusudur.
- **Uyarı kutusu** (`--warn-bg` / `--warn-line`) bir *kısıt bildirimidir*, süs değil: başlık +
  gövde ve **tek** simge (emoji yasak). "Örneklem yetersiz" metni kısaltılmaz, birebir kalır.
- `[hidden] { display: none !important }` şart: `display` kuralı olan her element `hidden`
  özniteliğini ezer. Kural **`index.html` içinde satır içi** durur (testler sunucu gövdesinde arar).
- Enerji kapısının **tek sahibi** `releaseButton`'dır; istek bitince butonu körlemesine açma.

## Erişilebilirlik

`AGENTS.md` §9'da tanımlıdır (kontrast, klavye, odak, durum, hareket, etiket). Burada tekrarlanmaz.

## Doğrulama — "arayüz işi görmeden bitmez"

Kod yazan ajan, işinin ekranda nasıl durduğunu kendi metninden çıkaramaz. Render edip bakmak zorunludur:
375 / 900 / **1200** / 1440 genişliklerinde **yatay taşma yok** (`body.scrollWidth == innerWidth`),
**kırpılan metin yok** (`scrollWidth > clientWidth` taraması), **örtüşme yok** (etkileşimli öğenin
merkezinde `elementFromPoint` **kendisini** döndürmeli), **konsol hatası yok**.

```bash
.venv/bin/python -m pytest tests/ui -q   # akış (gerçek tarayıcı) + yerleşim regresyonu
```

`tests/ui/test_layout_overflow.py` bu ölçümleri **kapıya** çevirir: dört genişlikte taşma,
kırpılma **ve örtüşme** varsa kırmızıya düşer. 2026-09-30'da taşma düzeltmesi geri alınarak testin
**önce kırmızı** olduğu kanıtlandı; 2026-10-03'te örtüşme ölçümü eklendi.

## Tasarım değişikliği süreci

Köklü (görsel-dil seviyesi) bir değişiklik **tartışmaya açılır**, "uygundur" çıkınca ADR-0016'ya göre
entegre edilir. Çerçeve:

- **İki katman:** (i) işlevsel sözleşme + (ii) tasarımdan bağımsız invariantlar (kontrast,
  taşma/kırpılma/örtüşme, "renk tek başına anlam taşımaz", sayı biçimi, klavye, `[hidden]`) →
  **makineyle kaplanır**. (iii) bir tasarımın özgülleri (hex nerede, hangi font, gradyan var mı) →
  **prose**; köklü değişiklikte **silinecek test yoktur**, burası güncellenir.
- **Proposal** (problem · hedef · değişenler · risk altındaki invariantlar · güncellenecek
  dokümanlar) `docs/60-decisions/`'a ADR olarak yazılır; onay ölçütü 4 genişlikte ekran görüntüsü +
  invariant suite yeşil + kontrast kontrolüdür. Entegrasyon **atomiktir** (kod + `DESIGN.md` +
  `docs/80` tek değişiklikte).

## Token kapsamı

Bütün **renkler** `web/assets/app.css` `:root`ta yaşar — **tek kaynak**. `index.html`'deki
`tailwind.config` renkleri `var(--…)` ile buraya referans verir; **markup ham hex yazmaz**
(Tailwind'in nötr paleti `slate`/`emerald` vb. yalnız chrome içindir; anlam taşıyan renkler
`brand`/`good`/`warn`/`bad` token'larından gelir). Grafik serileri ve eksen renkleri HTML'de değil,
`token()` yardımcısıyla CSS değişkeninden okunur — tema/kontrast değişikliği tek satırda kalır.
