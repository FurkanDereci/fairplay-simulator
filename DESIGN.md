# DESIGN.md — FairPlay Simulator arayüz sözleşmesi

Arayüz üretirken kararların **tek kaynağı** burasıdır: bir kural burada yaşar, başka yerde
tekrarlanmaz. Kalite eşikleri (`AGENTS.md` §9) bilinçli olarak burada **yazılmaz** — orada kalır.

Bu dosyanın varlık sebebi: bir ajan yön verilmediğinde eğitim verisinin ortalamasını üretir
(mor gradyan, üç özdeş kart, ortalanmış hero). Ortalamayı **kaydırmanın** yolu, tokenları ve
"ne olmayacak"ları her oturumda okunan bir dosyaya bağlamaktır.

## İlkeler

- **Yoğunluk süsün önünde.** Bu bir finans paneli; vitrin sayfası değil.
- **Renk anlam taşır.** Yeşil/kırmızı **yalnız** kâr/zarar ve durum içindir; eylem rengi ayrıdır
  (desatüre teal).
- **Durumlar tasarlanır.** Yükleniyor / boş / hata / odak / disabled. Sessiz başarısızlık yasak:
  kullanıcı göremiyorsa o kural yoktur.
- **Tek vurgu.** Bir ekranda bir şey öne çıkar; gerisi nötr ve sessiz kalır.
- **Ölçüm > izlenim.** Arayüz işi, render edilip bakılmadan bitmez.

## Tokenlar (dondurulmuş)

`index.html` içindeki `:root`. Bileşenlerde **ham hex yazılmaz**; ihtiyaç duyulan token yoksa
**dur ve sor, uydurma**.

| Rol | Token | Değer |
| --- | --- | --- |
| Sayfa zemini | `--bg` | `#020617` |
| Çukur alan (giriş, grafik, değerlendirme kutusu) | `--sunken` | `#060a16` |
| Panel | `--card` | `#10162b` |
| Panel başlığı / kutu | `--card-2` | `#161d36` |
| Ayraç | `--line` | `#2b3550` |
| Kenarlık | `--line-strong` | `#46527a` |
| Metin | `--fg` | `#f8fafc` |
| İkincil metin | `--muted` | `#94a3b8` |
| Eylem | `--accent` / `--accent-hover` | `#2fb3a4` / `#27998d` (desatüre teal) |
| Eylem yüzeyi üstündeki metin | `--on-accent` | `#06151a` (koyu — teal üstünde beyaz **okunmaz**) |
| Odak halkası / ince vurgu | `--accent-soft` | `#5cc9bb` |
| Kâr / uyarı / zarar | `--good` / `--warn` / `--bad` | `#22c55e` / `#f59e0b` / `#ef4444` |
| Kısıt bildirimi kutusu | `--warn-bg` / `--warn-line` | `#1b1915` / `#9a6a19` |
| Yazı tipi — metin | `--font-sans` | `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` |
| Yazı tipi — sayı | `--font-mono` | `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace` |
| Yarıçap | `--radius` | `10px` (kutu), `8px` (kontrol), `999px` (pill) |
| Boşluk | `--gap` | `12px` |
| Süre | `--dur` | `180ms` |

- **Aralık ritmi:** 4'ün katları (4 / 8 / 10 / 12 / 14 / 16 / 20). Ritim dışı boşluk yazılmaz.
- **Tipografi:** iki rol, iki yığın. **Metin** `--font-sans` (ağdan font **çekilmez**); **sayı**
  `--font-mono` ve `tabular-nums` — sayısal alan hizalansın, satır satır taranabilsin. Mono
  yığın da sistemdir (`ui-monospace` → SFMono / Menlo / Consolas); CDN ya da gömülü font yok.
- **Ölçek:** 10,5 / 11,5 / 12 / 13 / 14 (gövde) / 16 (oran) / 26 (hero metrik). Dışına çıkılmaz.

## Token revizyonu (2026-10-04)

Neden: panel **iki farklı mavi** taşıyordu — eylem mavisi (`#2563eb`) ile odak/ayraç mavisi
(`#3b82f6`) ekranda kâr yeşiliyle yan yana geldiğinde "durum" gibi okunuyor, "tıkla" demiyordu.
Aksan prototipin (FairPlay LAB) diline çekildi: **desatüre teal** — eylem rengi artık mavi değil;
ton olarak kâr yeşiline **komşu**, ama işi sayı renklendirmek değil **kontrol yüzeyi olmak**.
Aynı revizyonda sayısal metin **mono**ya alındı: bu ekranda sayılar *içerik*, metin *kabuk*;
ayrım artık iki rolle taşınıyor.

- **Aksan:** `#2563eb` → `#2fb3a4` (H 173°, S %58, L %44). Prototipin teali `#00d2b4` (S %100)
  doğrudan alınmadı: doygunluk %58'e indirildi — neon parlaklık `nevers` listesindedir ve tam
  doygun teal, kâr yeşilinin yanında **bağırır**. Ton korunur, enerji düşürülür.
- **`--on-accent` beyazdan KOYUYA döndü** (`#ffffff` → `#06151a`). Ölçüldü: `#f8fafc` teal
  üstünde **2,48:1** (eşik 4,5:1) — teal dolgu üstünde beyaz metin okunmaz. Koyu metin 7,17:1.
  Odak halkası (`--accent-soft` `#5cc9bb`) zemine göre 10,1:1, kart üstünde 9,0:1.
- **Teal ↔ kâr yeşili ayrımı:** ölçüldü (Viénot 1999 benzetimi) — deuteranopide iki renk
  yakınsıyor (teal `#786ea9`, yeşil `#817588`). Ayrımı bu yüzden **biçim** taşır ve kural
  bağlayıcıdır: **teal asla bir sayıyı renklendirmez** (yalnız düğme/çip/numara gibi **kontrol
  yüzeylerini** doldurur), **yeşil/kırmızı asla yüzey doldurmaz** (yalnız işaretli sayı ve durum
  metnini renklendirir). Renk körü kullanıcı için ayrım renkte değil bu iki rolde durur.
- **Sayı mono:** `.num`, kutucuk değerleri ve nav/çip içindeki ölçüm metinleri `--font-mono`;
  etiketler ve gövde metni `--font-sans`ta kalır (etiket metindir, sayı değil).
- **Kısıt bildirimi (amber kutu):** "örneklem yetersiz" artık **eksik değil, görünür** bir
  yüzeydir (prototipteki `METODOLOJİK KISIT BİLDİRİMİ`). Metin `--muted` amber zeminde 6,9:1,
  başlık `--warn` 8,2:1, çerçeve 3,7:1 — üçü de eşiği geçer.

## Renk kullanım kuralları

- Yeşil/kırmızı **dekor değildir**: yalnız işaretli kâr/zarar ve kupon durumu.
- **Kontrol yüzeyi ile durum rengi karışmaz:** teal yalnız **yüzeydir** (düğme dolgusu, basılı
  çip, bölüm numarası); yeşil/kırmızı yalnız **metin/sayı** rengidir. Bir sayı teal olmaz, bir
  düğme yeşil olmaz — ayrımı renk köründe de ayakta tutan kural budur (bkz. "Token revizyonu").
- Sıfır değeri nötrdür — yeşil gösterilmez.
- **Anlamsız metrik renk taşımaz.** `risk.reliability.sharpe_reliable` false iken risk kutuları
  (Sharpe/Sortino/MDD/Beta/Alpha/RAS) **nötr** gösterilir: sayı kalır, kırmızı/yeşil susar. Çünkü
  renk bir **yorum**dur ve `t < 2` iken yorum yasaktır (`docs/20` §2.8, alan 3). Ölçüldü
  (2026-10-03, kullanıcı ekran görüntüsü): etiket "yorumlanmamalı" derken MDD ve Alpha kırmızı
  kalıyordu — renk "ölçüm" izlenimi veriyordu.
- Grafik serileri anlam taşımadığı için **nötr palet + çizgi deseni** kullanır (renk körü ayrımı).
  Portföy çizgisi en üstte ve daha kalın çizilir (üst üste binmede görünür kalsın).

## Ne olmayacak (nevers)

- Mor/indigo gradyan, cam efekt (glassmorphism), neon glow.
- Yuvarlak köşe + 0,1 opaklıkta yumuşak gölgeyle "kart" yığmak.
- Emoji'yi yapısal simge olarak kullanmak (katlanır ok CSS üçgeniyle çizilir).
- Ekrana özel gömülü hex; token dışı değer.
- Landing-page klişeleri: ortalanmış hero, tek "Get Started" butonu, "trusted by" logoları.

## Bileşen kuralları

- `.market` 7 kolonlu ızgaradır; **≤860px'de 2 kolona** düşer. Giriş genişlikleri sabittir (60 / 78px).
  Metin kolonu `minmax(0, 1fr)`, `.market-meta` **sarar** (`overflow-wrap: break-word`) — kırpmaz.
  **Ölçüm (2026-10-03):** bu satır 7 kolonda ancak ≈1400px üstünde tek satıra sığar; 1181–1400
  bandında meta 2–4 satıra çıkar. Bu bant **eskiden kusurluydu** (sabit 140px kolon komşu kolona
  taşıyor, "Bahis" düğmesi örtülüyor, `scrollWidth` bunu göstermiyordu) — bkz. `tests/ui`
  `elementFromPoint` kapısı.
- `details.match > summary` **sarabilir** (`flex-wrap`) — dar ekranda başlık + meta + düğme taşmasın.
- `.market` satırının alanları `.market-head` ipucuyla **adlandırılır**: "çıplak 100" ve "p %"
  tek başına okunmuyordu. İpucu **tek satırdır, ızgaraya hizalanmaz**: 1181–1400 bandında `1fr`
  kolonu ~2px'e indiği için hizalı bir başlık o kolonda **harf harf** dizilirdi (ölçüldü
  2026-10-03). ≤860px'de ipucu gizlenir; erişilebilir ad kontrollerin `aria-label`'ında kalır.
- Kullanıcıya görünen metinde **ham enum yaşamaz** (`HOME`, `BTTS_YES`, `OVER_UNDER_2.5`):
  `MARKET_LABELS`/`SELECTION_LABELS` çevirir, API'ye giden `value` ham enum kalır. Kupon durumu
  (`WON`/`LOST`/`BEKLİYOR`) testlerle sabitlendiği için ekranda kod olarak kalır — anlamı `title`'da
  yazılır (aynı kural: kısaltma sabit, açıklama erişilebilir).
- Süre ve ölçek **okunur birime** çevrilir: `168 saat` yerine `7 gün (168 saat)` (`fmtHours`) —
  sayı kaybolmaz, ölçek eklenir. Kademe/tier farkı `title` ile açıklanır, sunucu sayısı uydurulmaz.
- `.table-wrap` yatay kaydırılır; `contain: inline-size` tablonun **sayfayı genişletmesini** önler.
- `.tile` ızgarası masaüstünde 3, **≤520px'de 2 kolon**; hero metrik yazısı ≤520px'de 22px.
- **Modül başlığı numaralıdır:** `01 // SERMAYE VE FON` — numara `--font-mono` + `--accent`,
  başlık metni `--font-sans`. Numarasız bir modül başlığı *çıplaktır*; sıra, panelin okunma
  sırasını söyler (portföy paneli 01–04, grafik 05).
- Kutucuk değerleri **mono** (`--font-mono`); değer **sarmaz** (kolonu taşırmaz), satır içinde
  birden çok satıra çıkabilir — `white-space: nowrap` yazılmaz, kırpılan sayı "ölçüm" değildir.
- **Çip iki işi yapar:** (a) lejant toggle — gizli seri `aria-pressed="false"` **ve** üstü çizili
  + `--muted` (yalnız renk solluk ile anlatılmaz); (b) zaman aralığı — tek seçim, basılı çip
  `--accent` dolgusudur. Lejant çipi **tek `<span>`**tir: sayı/etiket aynı düğümde kalır, toggle
  DOM'u yeniden kurmaz (odak kaybolmaz).
- **Uyarı kutusu** (`--warn-bg` / `--warn-line`) bir *kısıt bildirimidir*, süs değil: başlık +
  gövde ve **tek** simge (CSS ile çizilen `!` kutusu; emoji yasak). Ölçüm notu bu kutuda
  yaşayabilir ama metni kısaltılmaz — "Örneklem yetersiz" birebir kalır.
- `[hidden] { display: none !important }` şart: `display` kuralı olan her element `hidden` özniteliğini ezer.
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
**önce kırmızı** olduğu kanıtlandı; 2026-10-03'te örtüşme ölçümü eklendi (o gün 1200px'de Bahis
düğmesi portföy kutularının altında kalıyordu ve taşma ölçümü bunu **göremiyordu**).

## Token kapsamı

Bütün **renkler** `:root`'ta yaşar; `:root` dışında ham hex **yok** (denetlendi). Grafik serileri ve
eksen renkleri de HTML'de değil, `token()` yardımcısıyla CSS değişkeninden okunur — böylece renk tek
yerde durur ve tema/kontrast değişikliği tek satırda yapılır.

`token()` dışında kalan literal değerler yalnız **ölçüdür** (odak halkası `2px`, yarıçap 8/10/999px) —
renk değil. Disabled opaklığı da token'a bağlıdır (`--opacity-disabled`).

Yazı tipi de aynı kapsamdadır: iki yığın (`--font-sans`, `--font-mono`) yalnız `:root`'ta yazılır;
bileşende `font-family` literali görünmez. Ağdan font **çekilmez** — `--font-mono` bir **sistem**
yığınıdır, gömülü ya da indirilen dosya değil (denetlendi: `<link>`/`@import`/`@font-face` yok).
