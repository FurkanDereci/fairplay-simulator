# Ürün Değeri — "Öğrettiği" Nasıl Ölçülür

Alan 9'un **kapısı yoktu**, çünkü iddia ölçülemez biçimde yazılmıştı: *"bu simülatör öğretir."*
Yanlışlanamayan cümle kapı alamaz. Bu belge iddiayı ikiye ayırıp ölçülebilir yarısını sayıya bağlar.

## 1. İddia iki katman

| Katman | İfade | Durum |
| --- | --- | --- |
| **Ölçülen** | "Kullanıcı kendi davranışını sayıyla görür: bahis boyutu, favori yanlılığı, CLV eğilimi." | ✅ `GET /api/learning-report` · `[G-16]` · `tests/api` |
| **Ölçülmeyen** | "Bu sayıları gören kullanıcı zamanla daha iyi karar verir." | 🅿️ protokol §4'te yazılı, **koşulmadı** (insan çalışması ister) |

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

## 5. Kapı

```bash
.venv/bin/pytest tests/golden -k g16     # formüller (aynı defter → aynı sayı)
.venv/bin/pytest tests/api -k learning   # uç: örneklem kuralı + tavsiye alanı yok
```

`docs/20` §6 ↔ `[G-16]` eşleşmesi `tests/test_docs_sync.py` tarafından zorlanır; sayı değişirse
golden kırılır.
