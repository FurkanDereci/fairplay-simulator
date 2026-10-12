# Ürün Değeri — "Öğrettiği" Nasıl Ölçülür

Alan 9'un **kapısı yoktu**, çünkü iddia ölçülemez biçimde yazılmıştı: *"bu simülatör öğretir."*
Yanlışlanamayan cümle kapı alamaz. Bu belge iddiayı ikiye ayırıp ölçülebilir yarısını sayıya bağlar.

## 1. İddia iki katman

| Katman | İfade | Durum |
| --- | --- | --- |
| **Ölçülen** | "Kullanıcı kendi davranışını sayıyla görür: bahis boyutu, favori yanlılığı, CLV eğilimi." | ✅ `GET /api/learning-report` · `[G-16]` · `tests/api` |
| **Ölçülmeyen** | "Bu sayıları gören kullanıcı zamanla daha iyi karar verir." | 🅿️ protokol §4'te (5–8 kişi) ve §4.1'de (n=1 pilot) yazılı, **koşulmadı** |

Birinci katman ölçülebilir çünkü metrikler **defterden** türer ve formülleri
`docs/20-accounting-spec.md` §6'da yazılıdır: aynı defter → aynı sayı (determinizm, I2).
İkinci katman ürün kodunun kanıtlayabileceği bir şey değildir; onu **çalışma** gösterir.

## 2. Ölçütler ve eşiklerin gerekçesi

| Ölçüt | Eşik | Neden bu eşik |
| --- | --- | --- |
| Bahis sayısı (`N`) | `N ≥ 6` | Alan 3'ün `t = SR·√T` kuralının ikizi. Üç bahisten "eğilim" okumak, tek işlemli portföyde `Profit Factor 99` okumakla aynı hatadır |
| Bahis oranı | `> %15` → `aşırı` | Tam Kelly tavanı. Üstü yasak değil, **bildirilir**: ürün kararı kullanıcıya bırakır |
| Favori payı | `> %70` → `favori ağırlıklı` | Oranı `2.00` altı bahisler. Favori–longshot yanlılığı bilinen bir sapmadır; vig arındırmanın çarpımsal kalması da aynı sınırdan gelir (`docs/70` §7.3) |
| Pazar çeşitliliği | — | Bilgi: tek markette kalmak bir *alışkanlıktır*, hata değil |
| CLV eğilimi | fark `≥ +1,00` → `iyileşiyor` | Tek bahsin CLV'i gürültüdür; bant, yanlış "iyileşiyorum" sinyalini engeller |

Eşikler **politika** değerleridir, doğa yasası değil: değiştirilebilir — ama değişirse burada ve
`docs/20` §6'da **aynı anda** yazılır (tek yerden okunur kural).

## 3. Ürünün yapmadıkları (kapının negatif yarısı)

- **Tavsiye yok.** "Şu maça oyna" üretecek uç bulunmaz; `learning-report` yalnız geçmişi sayar.
- **Tahmin yok.** Model olasılığı uydurulmaz: `p` kullanıcıdan gelir (ADR-0006). Orijinalin
  `slip-kelly-val` alanı kenar `≤ 0` iken **0.05'e düşüyordu**, yani kullanıcıya uydurma bir
  bahis oranı gösteriyordu — bu sınıf burada kapatıldı.
- **Beceri iddiası yok.** CLV eğilimi *"kapanış çizgisini daha sık geçiyorsun"* der;
  *"iyi bahisçisin"* demez.

## 4. 🅿️ Ertelenen: kullanıcı çalışması (ön-kayıtlı protokol)

İkinci katmanı ölçmenin tek yolu insanlarla çalışmaktır; **koşulmadı**. Protokol şimdi yazılı ki
sonradan "zaten öğretiyordu" denemesin:

- **Katılımcı:** 5–8 kişi, 30–40 dk, tek oturum.
- **Ön/son ölçüm:** 5 soruluk kavram testi (vig nedir, Kelly neyi çözer, CLV neyi gösterir,
  örneklem neden gerekir, bahis boyutu nasıl seçilir).
- **Başarı ölçütü:** ortalama skor artışı **≥ +1,5/5** *ve* katılımcıların **≥ %60'ı** kendi CLV
  eğilimini doğru yorumlar.
- **Yanlışlanma:** artış yoksa ya da katılımcılar kendi metriklerini yanlış okuyorsa iddia düşer ve
  ürün "sayı gösteren ama öğretmeyen" olarak yeniden tanımlanır.
- **Neden otomatik kapı değil:** insan zamanı gerektirir; koşulmadan yeşil görünen bir kapı,
  kapı olmamasından kötüdür.

### 4.1 n=1 öz-çalışma (sapma; **kanıt değil, pilot**)

§4'ün 5–8 kişilik hâli, katılımcı havuzu yokluğunda koşulamıyor. Yerine **zayıf** ama hemen
başlanabilir bir varyant; sınırları **baştan yazılı** ki sonradan "zaten öğretiyordu" denmesin.

**Tasarım (7 gün).**

1. **T0 — bugün, ürünü kullanmadan önce.** Aşağıdaki 5 soruyu cevapla; her soruya **özgüven**
   (1–5) ve bir cümle gerekçe yaz. Cevapları bu bölümün altına **tarihle** yaz ve commit'le
   (bu, ön-kayıttır — sonradan değiştirilmez).
2. **Ara — 7 gün, günde ~5 dk.** Ürünü normal kullan (Kupon Simülatörü + Genel Bakış +
   `learning-report`). İsteğe bağlı günlük: "bugün hangi sayıyı okudum, ne anladım".
3. **T1 — 7 gün sonra.** Aynı 5 soru, aynı özgüven. Ayrıca **kendi `learning-report`'unu oku ve
   yorumla** (CLV eğilimi ne diyor, bahis oranın hangi bantta).
4. **Ölçüm:** `Δ = T1 − T0` (0–4) *ve* kendi metriklerini doğru okuyabildin mi (evet/hayır).

**Enstrüman v1 (jargon; 2026-10-12) — saha turunda elendi.**

| # | v1 sorusu | Doğru cevap |
| --- | --- | --- |
| 1 | Kasaya para eklemek (refill) **TWR**'yi artırır mı? | Hayır (I1) |
| 2 | Oranlarda "fair" olasılık ham `1/oran` mıdır? | Hayır (vig) |
| 3 | `p` = piyasa olasılığı ise Kelly kaçtır? | 0 (ADR-0006) |
| 4 | CLV pozitifse "iyi bahisçi" misin? | Hayır |
| 5 | 3 bahis sonrası Sharpe güvenilir mi? | Hayır (`t < 2`) |

**Saha turu (naif kişiler, 2026-10-12) — madde bazında bulgu ve karar.**

| # | Gözlem | Karar |
| --- | --- | --- |
| 1 | Kavram kolay: **genelde doğru** — tavan etkisi | Isınma; **puana sayılmaz** |
| 2 | Terim söylenmeden karışık; söylenince "tabii, yoksa bahisçi nasıl kazanır" → **yönlendirici** | Yeniden yaz: oran ver, **"gerçek şans % kaç?"** — sayı isteyen, ipucu vermeyen |
| 3 | "Kazanma beklentisi" anlaşılmadı; "piyasa olasılığıyla hep sıfır" mantığı **çok soyut** | Yeniden yaz: tahminin yoksa **karar verilemez** |
| 4 | **Ayırt edici madde:** çoğunluk yanlış; "iyi fiyat" ile "kârlı" farkı bilinmiyor (düzenli oynayanların bir kısmı doğru) | **Koru** — tam da öğretilmesi gereken şey |
| 5 | Çoğu "yetersiz" dedi ama **neden** bilinmiyor ("kısmen bilgi verir" kaçamağı) → tahmin edilebilir | Yeniden yaz: "güvenip büyütür müydün, **neden**" — gerekçe zorunlu |

**Metodolojik uyarı.** Bu tur **ölçüm değil, enstrüman geliştirmedir:** 2'de ipucu verildi, 5'te
cevaplar toplumsal beklentiye kaydı. Bu yüzden "anlamadı" ile "öğrenmedi" ayrılamaz; bulgular
**madde tasarımı** için kullanılır, puan için değil.

**Enstrüman v2 (sade; ÖN-KAYITLI — bu commit'le donduruldu).** Toplam **4 puan** (madde 1 puansız).

| # | Soru (birebir okunur; açıklama YOK) | Puan |
| --- | --- | --- |
| 1 | Kasaya 1.000 TL daha eklenirse **başarı yüzden** değişir mi? | 0 (ısınma) |
| 2 | Oranlar `1,95 / 3,50 / 4,10`. Arsenal'ın **gerçek** kazanma şansı yaklaşık **% kaç**? | 1 — `1/1,95`'ten (%51) **küçük** (≈%48) |
| 3 | Kendi tahminin yokken "bu bahis kârlı mı?" sorusu **cevaplanabilir mi**? | 1 — Hayır (piyasa olasılığıyla beklenti 0) |
| 4 | Kapanış oranını geçtin (daha iyi fiyat aldın). Bu, **kârlı olduğun** anlamına gelir mi? | 1 — Hayır; iyi fiyat ≠ kâr |
| 5 | 3 bahis sonrası araç bir "risk puanı" gösteriyor. Bu sayıya güvenip **bahsi büyütür müydün — neden**? | 1 — Hayır **+ gerekçe** (örneklem küçük) |

**Görüşmeci kuralı (enstrüman kadar önemli).** Sorular **birebir** okunur, **ipucu/açıklama
verilmez**; kaçamakta zorlanmaz. 4 ve 5'te **gerekçe** istenir; **gerekçesiz "hayır" puan almaz**.

**Arayüz bağlantısı.** Aynı bulgu ürünü de vurdu: varsayılan metin sadeleştirildi, teknik terimler
"İleri Düzey" yoluna taşındı (`DESIGN.md` "Bileşen kuralları").

**Yanlışlanma (bu kişide).** `Δ ≤ 0` ise **ya da** kendi metriklerini yanlış okuyorsan "öğretir"
iddiası bu vakada **düşer**.

**Sınırlar (yazılı ve ciddi).**

- **Tek vaka:** genellenemez; istatistik yok.
- **Körleme yok, üstelik yazar öz-testi:** soruları ve cevapları zaten biliyorsan **tavan etkisi**
  beklenir → `Δ` büyük olasılıkla 0 çıkar ve bu, ürün hakkında **hiçbir şey söylemez**. Yazar
  öz-testi bu yüzden en zayıf tasarımdır.
- **Bu yüzden Ö-1'in yerine geçmez.** Sonuç ne olursa olsun §4 koşulmamış sayılır.

**Ucuz mitigasyon (aynı enstrüman, daha anlamlı).** v2'yi, ürünü **hiç görmemiş bir naif** kişiye
(sınıf arkadaşı, yurt) T0/T1 olarak uygula. Naif T0 düşük + T1 yüksekse **asıl sinyal odur**; kendi
öz-testin yalnız enstrümanın çalıştığını (ne trivially kolay ne imkânsız) gösterir.

**T0 kaydı (tarih + cevaplar).**

_(koşulunca buraya yazılır; ön-kayıt olduğu için commit'lenir)_

## 5. Kapı

```bash
.venv/bin/pytest tests/golden -k g16     # formüller (aynı defter → aynı sayı)
.venv/bin/pytest tests/api -k learning   # uç: örneklem kuralı + tavsiye alanı yok
```

`docs/20` §6 ↔ `[G-16]` eşleşmesi `tests/test_docs_sync.py` tarafından zorlanır; sayı değişirse
golden kırılır.
