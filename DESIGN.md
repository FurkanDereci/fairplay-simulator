# DESIGN.md — FairPlay Simulator arayüz sözleşmesi

Arayüz üretirken kararların **tek kaynağı** burasıdır: bir kural burada yaşar, başka yerde
tekrarlanmaz. Kalite eşikleri (`AGENTS.md` §9) bilinçli olarak burada **yazılmaz** — orada kalır.

Bu dosyanın varlık sebebi: bir ajan yön verilmediğinde eğitim verisinin ortalamasını üretir
(mor gradyan, üç özdeş kart, ortalanmış hero). Ortalamayı **kaydırmanın** yolu, tokenları ve
"ne olmayacak"ları her oturumda okunan bir dosyaya bağlamaktır.

## İlkeler

- **Yoğunluk süsün önünde.** Bu bir finans paneli; vitrin sayfası değil.
- **Renk anlam taşır.** Yeşil/kırmızı **yalnız** kâr/zarar ve durum içindir; eylem rengi ayrıdır (mavi).
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
| Eylem | `--accent` / `--accent-hover` | `#2563eb` / `#1d4ed8` |
| Odak halkası | `--accent-soft` | `#3b82f6` |
| Kâr / uyarı / zarar | `--good` / `--warn` / `--bad` | `#22c55e` / `#f59e0b` / `#ef4444` |
| Yarıçap | `--radius` | `10px` (kutu), `8px` (kontrol), `999px` (pill) |
| Boşluk | `--gap` | `12px` |
| Süre | `--dur` | `180ms` |

- **Aralık ritmi:** 4'ün katları (4 / 8 / 10 / 12 / 14 / 16 / 20). Ritim dışı boşluk yazılmaz.
- **Tipografi:** tek aile — `system-ui` yığını (ağdan font çekilmez). `tabular-nums` zorunlu.
- **Ölçek:** 10,5 / 11,5 / 12 / 13 / 14 (gövde) / 16 (oran) / 26 (hero metrik). Dışına çıkılmaz.

## Renk kullanım kuralları

- Yeşil/kırmızı **dekor değildir**: yalnız işaretli kâr/zarar ve kupon durumu.
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
- `.table-wrap` yatay kaydırılır; `contain: inline-size` tablonun **sayfayı genişletmesini** önler.
- `.tile` ızgarası masaüstünde 3, **≤520px'de 2 kolon**; hero metrik yazısı ≤520px'de 22px.
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
