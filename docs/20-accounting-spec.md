---
title: Muhasebe ve Metrik Sözleşmesi
status: CONTRACT
created: 2026-09-29
---

# Muhasebe ve Metrik Sözleşmesi

**Bu belge sözleşmedir.** `core/` buradaki formülleri 1:1 uygular. Buradaki işlenmiş örnekler
(`[G-x]`) koda geçtiğinde **golden test** olur; sayı birebir tutmazsa build kırılır.

---

## 1. Birimleştirme (Unit NAV)

Zaman `t`'de: `C_t` kasa, `E_t` kilitli kupon değeri, `V_t = C_t + E_t`, `U_t` birim sayısı,
`NAV_t = V_t / U_t`.

**Başlangıç:** `D₀ = 1000.00`, `NAV₀ = 100.0000` → `U₀ = D₀ / NAV₀ = 10.0000`

### 1.1 Bahis konulması
```
C ← C − stake        E ← E + stake        V değişmez → NAV değişmez
```
Bahis konulması NAV'ı **değiştirmez** (sadece kasa → kilitli transferi).

### 1.2 Bahis sonuçlanması
```
E ← E − stake        C ← C + payout        V ← V − stake + payout
```
Sonuç açıklandığında NAV burada değişir.

### 1.3 Refill (bakiye ekleme) — **değişmez I1**
```
ΔU = D / NAV⁻        U ← U⁻ + ΔU        C ← C⁻ + D
NAV⁺ = (V⁻ + D) / (U⁻ + D/NAV⁻) = NAV⁻
```
Yani: **para eklemek NAV'ı değiştirmez**; yalnız birim sayısını artırır.

> **Uygulama notu:** `Fund` refill'de (ve bahis konulmasında, §1.1) NAV'ı **yeniden hesaplamaz, taşır**.
> Sonsuz hassasiyette `V/U` zaten değişmez; `V/U`'yu yeniden hesaplamak yalnız yuvarlama artığı sokar
> (property testi I1 bunu yakaladı). NAV yalnız sonuçlanmada yeniden hesaplanır (§1.2).

> **[G-1] Refill invariance**
> `D₀ = 1000.00 · NAV₀ = 100.0000 · U₀ = 10.0000`
> Bahis: `stake = 100.00 @ 2.50` → `C = 900.00`, `E = 100.00`, `V = 1000.00`, `NAV = 100.0000`
> Kazandı: `payout = 250.00` → `C = 1150.00`, `E = 0`, `V = 1150.00`, `NAV = 115.0000`, `TWR = +15.00%`
> Refill `D = 1000.00` → `ΔU = 1000/115 = 8.6956522`, `U = 18.6956522`, `C = 2150.00`
> **Beklenen:** `NAV = 2150.00 / 18.6956522 = 115.0000` (değişmedi ✓), `U = 18.6956522`

### 1.4 İflas (V = 0) ve seri kapanışı
`V = 0` olduğunda: `NAV = 0`, seri kapanır ve `growth_s = NAV_son / NAV_base` **çarpana** eklenir.
Yeni refill **yeni seri** açar: `NAV = NAV_base = 100`, `U = D / 100`.

> **[G-2] İflas + seri bileşikliği**
> `D₀ = 1000.00 · NAV₀ = 100` → `U₀ = 10`
> Bahis `stake = 1000.00 @ 2.00` → `C = 0`, `E = 1000.00`, `V = 1000.00`, `NAV = 100.0000`
> Kaybetti → `C = 0`, `E = 0`, `V = 0` → `NAV = 0` → **seri 1 kapandı**, `growth₁ = 0/100 = 0.0000`
> Refill `1000.00` → seri 2: `NAV = 100.0000`, `U = 10.0000`
> Bahis `stake = 500.00 @ 2.00` kazandı → `payout = 1000.00` → `C = 1500.00`, `V = 1500.00`, `NAV = 150.0000`
> `growth₂ = 150/100 = 1.5000`
> **Beklenen:** `TWR_total = (growth₁ × growth₂) − 1 = 0 × 1.5 − 1 = −1.0000 → −100.00%`
> Yani iflas **kalıcı lekedir**; sonraki seri onu silmez.

### 1.5 TWR (Time-Weighted Return)
```
NAV_son
TWR = ( Π growth_s ) × ───────── − 1        (seriler arası BİLEŞİK)
         s               NAV_base
```
> **Dikkat:** `TWR ≠ NAV/NAV₀ − 1` (tek seri dışında). Mevcut projenin yaptığı kısa yol, çok serili
> (iflas görmüş) portföyde yanlış sonuç verir. Bkz. `[G-2]`: kısa yol `150/100 − 1 = +50%` derdi,
> doğrusu `−100%`.

---

## 2. Risk metrikleri

Kural: kesirli getiri serisi `r_i`; yetersiz örnekte **0.00** döner (çökmez).

### 2.1 Getiri serisi
`r_i = (NAV_i − NAV_{i−1}) / NAV_{i−1}`, `NAV_{i−1} > 0`; aksi hâlde `r_i = 0`.

### 2.2 Maximum Drawdown (MDD)
```
peak ← ilk değer; her t: peak ← max(peak, NAV_t);  dd_t = (peak − NAV_t)/peak
MDD = max_t dd_t        → yüzde
```
> **[G-3] MDD**
> `NAV = [100, 120, 90, 110, 80]` → dd: `0, 0, 0.25, 0.0833, 0.3333`
> **Beklenen:** `MDD = 33.33%`

### 2.3 Sharpe
```
μ   = ortalama(r)
σ   = sqrt( Σ(r_i − μ)² / (n − 1) )      # ÖRNEKLEM varyansı (n−1)
Sharpe = (μ − r_f) / σ                    # r_f = 0 varsayılan
```
`σ ≈ 0` ve `μ > 0` ise `Sharpe = μ × 10`; `μ ≤ 0` ise `0.00`. `n < 2` → `0.00`.

> **[G-4] Sharpe**
> `r = [0.10, −0.10, 0.10]` → `μ = 0.0333333`, örneklem `σ = 0.1154701`
> **Beklenen:** `Sharpe = 0.0333333 / 0.1154701 = 0.2887 → 0.29`

### 2.4 Sortino
```
DD     = sqrt( Σ min(0, r_i − hedef)² / n )    # AŞAĞI YÖNLÜ sapma, n'e bölünür
Sortino = (μ − hedef) / DD                      # hedef = 0 varsayılan
```
`DD ≈ 0` kuralları Sharpe ile aynı. `n < 2` → `0.00`.

> **[G-5] Sortino**
> `r = [0.10, −0.10, 0.10]` → aşağı yönlü kareler `[0, 0.01, 0]` → `DD = sqrt(0.01/3) = 0.0577350`
> **Beklenen:** `Sortino = 0.0333333 / 0.0577350 = 0.5774 → 0.58`

### 2.5 Beta ve Jensen Alpha
`n = min(len(player), len(benchmark))`; `n < 3` ise `(1.00, 0.00)`.
```
β = Cov(Rp, Rb) / Var(Rb)
α = (μ_p − r_f) − β (μ_b − r_f)          → yüzde
```
`Var(Rb) ≈ 0` ise `β = 1.00`, `α = (μ_p − μ_b) × 100`.

### 2.6 İşlem istatistikleri
Kazanç/kayıp **net** işaretinden türetilir: `net = payout − stake`. `net = 0` olan sonuçlar
(`VOID`/`PUSH`) **hariç** tutulur; yarım kazanç/kayıp doğru sayılır.
```
gross_profit = Σ max(net, 0)
gross_loss   = Σ (−min(net, 0))
ProfitFactor = gross_profit / gross_loss        # gl = 0 → gp > 0 ise 99.00, aksi 0.00
win_rate     = (net > 0 sayısı) / toplam        → yüzde
Expectancy   = Σ net / toplam                   # işlem başına net
```
> **[G-6] İşlem istatistikleri**
> Bir kazanan (`stake 100`, `payout 250`) + bir kaybeden (`stake 100`, `payout 0`)
> `gp = 150.00`, `gl = 100.00`, `win_rate = 50.00%`
> **Beklenen:** `ProfitFactor = 1.50`, `Expectancy = (+150 − 100)/2 = +25.00`

### 2.7 Risk-Adjusted Score (RAS)
```
mdd_f    = max(0, 1 − MDD/100)
sharpe_f = clamp((Sharpe + 1)/2, 0.2, 2.5)
RAS = TWR(%) × mdd_f × sharpe_f
```
> **[G-7] RAS**
> `TWR = 15.00`, `MDD = 20.00`, `Sharpe = 1.00` → `mdd_f = 0.80`, `sharpe_f = 1.00`
> **Beklenen:** `RAS = 15.00 × 0.80 × 1.00 = 12.00`

### 2.8 Anlamlılık kapısı — "bu sayı ne zaman anlamsız"

Sharpe'ın kendi bağıntısı: `t = SR × √T` (T = **getiri dönemi sayısı**, yıl değil).
`t < 2` iken metrik **istatistiksel olarak anlamsızdır**; çıplak sayı olarak sunulmaz,
"örneklem yetersiz" etiketiyle gelir. Aynı örneklem kuralı Sortino ve MDD için de geçerlidir
(hepsi aynı getiri serisinden hesaplanır).

`ProfitFactor` **hiç kayıp yokken tanımsızdır** (sonsuz); sayı uydurmak yerine
`tanımsız` olarak işaretlenir.

> **[G-14] Anlamlılık**
> `SR = 1.00, T = 4` → `t = 1.00 × √4 = 2.00` → **ANLAMLI**
> `SR = 1.00, T = 1` → `t = 1.00` → **ANLAMSIZ**
> `SR = 0.29` (`[G-4]`), `T = 3` → `t = 0.50` → **ANLAMSIZ**

---

## 3. Oran matematiği

### 3.1 Vig / overround ve fair odds
```
P_i = 1/O_i        S = Σ P_i        overround = S − 1
margin_% = (overround / S) × 100
P_fair,i = P_i / S        O_fair,i = 1 / P_fair,i
```
> **[G-8] Vig**
> `{HOME: 1.95, DRAW: 3.50, AWAY: 4.10}`
> `P = {0.5128205, 0.2857143, 0.2439024}`, `S = 1.0424372`
> **Beklenen:** `overround = 0.0424372 (4.2437%)`, `margin = 4.07%`
> `P_fair = {0.4919438, 0.2740830, 0.2339733}` (Σ ≈ 1)
> `O_fair = {2.03, 3.65, 4.27}`

**Girdi denetimi — reddet, kırpma.** Sisteme giren oran dizisi üç kuralı sağlamalı; sağlamazsa
istek `400` ile **reddedilir** (kırpılmaz):
- pazarın zorunlu sonuçları eksiksiz (1X2 için `HOME`/`DRAW`/`AWAY`),
- her oran `> 1` (`O ≤ 1` matematiksel olarak imkânsız orandır),
- `Σ(1/O_i) > 1` (aksi hâlde **negatif vig** vardır: bahisçi lehine garanti kâr, gerçek oran
  dizisinde olamaz).

`overround = max(0, …)` ile bozuk beslemeyi kırpmak onu **gizlemektir**; gizlemek kabul etmekten
kötüdür (orijinalin `03` Suite 3 gereksinimi).

> **[G-19] Oran temizliği (reddetme)**
> `{3.50, 3.50, 3.50}` → `Σ(1/O) = 0,857143 ≤ 1` → **reddedilir** (negatif vig)
> `{1.00, 2.00, 3.00}` → `HOME = 1.00 ≤ 1` → **reddedilir**
> `{1.95, 3.50, 4.10}` → `Σ = 1,0424372 > 1` → **kabul** (bkz. `[G-8]`)

### 3.2 Kelly kriteri ve EV
```
EV   = p × O − 1
f*   = max(0, (p × O − 1) / (O − 1))
```
`O ≤ 1` → `f* = 0`. Tek kupon kasasının %15'ini aşarsa **Risk-of-Ruin onay kapısı** devreye girer
(§3.4): sunucu isteği reddeder, istemci uyarıyı onaylayıp **aynı isteği** `confirm_ruin=true` ile
tekrar gönderir. `kelly_fraction` **tam hassasiyetle** döner; raporlarken 4 ondalığa yuvarlanır
(ör. `0.1409` → %14.09).

> **Uygulama notu — `p` kullanıcıdan gelir.** Piyasanın fair olasılığı `p` olarak kullanılırsa `f*`
> **her zaman 0** çıkar (`[G-9]`), çünkü bookmaker oranı fair orandan kısadır; yani Kelly sabit ve
> bilgi taşımayan bir metrik olur. Bu yüzden `p` kullanıcının kendi tahminidir (bkz. ADR-0006):
> `POST /api/estimate` ve `POST /api/wager` (opsiyonel `probability`) bu tahminle EV, Kelly ve
> **önerilen stake** üretir. Tahmin verilmezse Kelly gösterilmez — yanlış sayı göstermekten iyidir.

> **[G-9] Kelly — negatif EV**
> `p = 0.4919438` (fair), `O = 1.95` → `f* = (0.9592904 − 1)/0.95 = −0.0429`
> **Beklenen:** `f* = 0.00` (bahis yok)
>
> **[G-10] Kelly — pozitif EV**
> `p = 0.55`, `O = 2.10` → `EV = +0.1550 (+15.50%)`, `f* = 0.155/1.10 = 0.1409`
> **Beklenen:** `f* = 14.09%`

### 3.3 Closing Line Value (CLV)
```
CLV_% = (O_konulan / O_kapanış − 1) × 100
```
Kapanış oranı kupon konulduğunda **snapshot** alınır (sonradan değişmez).

> **Uygulama notu — kapanış çizgisi sentetiktir:** MVP'de gerçek bir kapanış akışı yok; kapanış
> oranı, açılışın **deterministik piyasa hareketi** olarak modellenir (±%6, iki yöne açık) — bkz.
> ADR-0005. (ADR-0004'teki "fair oranı vekil tut" yaklaşımı, `CLV`'yi yapı gereği hep negatife
> kilitlediği için **terk edildi**.)

> **[G-11] CLV**
> `O_konulan = 2.10`, `O_kapanış = 1.95` → **Beklenen:** `CLV = +7.69%`

### 3.4 Risk of Ruin ve onay kapısı

`Edge = p·o − 1` (bahis başına beklenen getiri), `Units = cash/stake` (kasadaki eşit-bahis sayısı):

```
R_ruin = ( (1 − Edge) / (1 + Edge) ) ^ Units        → yüzde
```

Tek kupon **kasanın %15'ini aşarsa** sistem bu değeri hesaplar ve **onay isteyen bir kapı** koyar:
istek `confirm_ruin` olmadan gelirse `409` + `ruin` gövdesi döner; istemci uyarıyı gösterip onay
alırsa **aynı istek** `confirm_ruin=true` ile tekrar gönderilir ve bahis işlenir. Kapı sunucudadır
(istemci yalnız gösterir, eşiği ve formülü kendisi hesaplamaz) ama **bahsi yasaklamaz** — kararı
kullanıcı verir.

`p` **kullanıcıdan** gelir (ADR-0006): verilmezse sayı **uydurulmaz**, `risk_of_ruin_pct = null`
döner ve uyarı niteliksel kalır. `Edge ≤ 0` ise iflas kaçınılmazdır → `100.00`.

> **[G-17] Risk of Ruin**
> `Edge = 0.01`, `Units = 100` → `(0.99 / 1.01)^100 = 0.135326…`
> **Beklenen:** `R_ruin = 13.53%`
> `Edge = 0.00` → **Beklenen:** `100.00%` (kenar yoksa iflas kaçınılmaz)

---

## 4. Politika katmanı

### 4.1 Enerji
Sabitler: `MAX = 100`, `cost = 10 / bahis`, `regen = 10 / saat`.
```
gained = floor(geçen_saniye × 10/3600)
energy = min(MAX, energy + gained)
```
Saat ilerlemesinin **iki** kuralı vardır:
- **Kısmi ilerleme saklanır:** `gained = 0` ise `last_update` ilerlemez; artık dakikalar durur
  (100 dakikanın 4 dakikalık artığı kaybolmaz).
- **Tavanda geçen süre yanar:** `energy ≥ MAX` ise `last_update = now` olur. Tavan **depolamayı**
  engellemek için vardır; yoksa oyuncu tavanda bekleyip biriken süreyi sonra arka arkaya
  bahislerle harcayabilirdi.

Bahis anında `energy < cost` ise **429**.

> **[G-12] Enerji**
> `100` enerji, 10 bahis → `0`; 30 dk sonra `+5` → `5`; `0`'dan 2 saat sonra `+20` → `20`

> **[G-15] Enerji tavanı ve artık**
> `energy = 100`, 3 saat geçti → `energy = 100`, `last_update = now` (süre yandı, birikmedi)
> `energy = 50`, 100 dk geçti → `energy = 66`, `last_update = +96 dk` (4 dk artık saklandı)

### 4.2 Cooldown
```
T(n) = min(tavan, 4^(n−1)) saat     # n = tier ≥ 1; tavan varsayılan 168
3 ardışık solvent gün → tier −= 1 (taban 0)
```

**Disiplin indirimi.** **3+ disiplin rozeti** tavanı 168 → 72 saate çeker (orijinalin
`01_gamification` §3 kuralı). Rozetler **var olan** öğrenme ölçütlerinden türetilir (§6):
`ölçülü-bahis` · `clv-ustası` · `pazar-gezgini`; her biri `N ≥ 6` örneklem ister ve üçünün
**tamamı** gerekir. Tavan `min(tavan, 4^(n−1))` ile uygulanır — yani tier 4'te (64 saat) indirim
görünmez, tier 5'te görünür.

> **[G-13] Cooldown**
> **Beklenen:** `T(1)=1s · T(2)=4s · T(3)=16s · T(4)=64s · T(5)=168s (tavan)`

> **[G-18] Disiplin indirimi**
> Tavan 72 iken **Beklenen:** `T(5)=72 · T(4)=64 · T(3)=16`
> Varsayılan tavanla: `T(5)=168` (indirim yok)
> Üç rozetin tamamı → indirim; iki rozet → indirim yok

---

## 5. Kenar durumlar (sözleşmeye bağlı)

| Durum | Kural |
| --- | --- |
| `VOID` / `PUSH` | `payout = stake`; net 0; kazanç/kayıp istatistiğine girmez |
| Yarım kazanç (asian) | `payout = stake + stake×(O−1)/2` |
| Yarım kayıp (asian) | `payout = stake/2` |
| `O ≤ 1` | Kelly `f* = 0`; normalize `O ≤ 0` olan sonuç atlanır |
| Sıfır birim (`U = 0`) | `NAV = 0`; iflas akışı (bkz. §1.4) |
| Eşzamanlı settlement | Aynı kupon ikinci kez settle edilemez (I3, `409`) |
| Restart ortasında `PENDING` | Defterden replay ile kupon durumu korunur (I2, S2) |
| `stake > cash` | `400` — kısmi doldurma yok |
| Bozuk oran dizisi (eksik sonuç · `O ≤ 1` · negatif vig) | `400` — kırpılmaz, **reddedilir** (§3.1, `[G-19]`) |

---

## 6. Öğrenme ölçütleri (ürün değeri)

"Bu simülatör öğretir" yanlışlanamaz bir cümledir. Yerine kullanıcının **kendi davranışı** ölçülür;
hepsi defterden türer, hiçbiri tavsiye değildir (kararı kullanıcı verir — ADR-0006). Eşikler
**politika** değerleridir (`docs/90-urun-degeri.md`).

| Ölçüt | Formül | Eşik |
| --- | --- | --- |
| Bahis sayısı | `N` = bahis anı yakalanan `WAGER_PLACED` sayısı | `N < 6` → hiçbir eğilim okunmaz |
| Bahis oranı | `mean(stake / portföy_değeri)` (bahis **anında**) | `> %15` → `aşırı` (tam Kelly tavanı) |
| Favori payı | oranı `< 2.00` olan bahislerin payı | `> %70` → `favori ağırlıklı` |
| Pazar çeşitliliği | kullanılan farklı market sayısı | — (bilgi) |
| CLV eğilimi | ilk yarı ortalaması vs ikinci yarı ortalaması | fark `≥ +1,00` → `iyileşiyor`; `≤ −1,00` → `kötüleşiyor`; arası → `yatay` |
| Disiplin rozeti | `ölçülü-bahis` (bahis oranı ≤ %15) · `clv-ustası` (ortalama CLV > 0) · `pazar-gezgini` (≥ 3 market) | her biri `N ≥ 6`; üçü birden → cooldown tavanı 168 → **72** (§4.2) |

Bahis oranında **portföy değeri** (`cash + locked`) kullanılır, NAV değil: NAV birim fiyatıdır
(100 tabanlı), bahis boyutu ise portföyün yüzdesi olarak anlamlıdır.

> **[G-16] Öğrenme ölçütleri**
> 1.000 TL portföy, 100 TL'lik 6 bahis; kapanış oranları `2,10 · 2,05 · 2,00 · 1,95 · 1,90 · 1,85`
> **Beklenen:** `N = 6` · bahis oranı `%10,00` → `ölçülü` · favori payı `%0,00` → `dengeli`
> CLV: ilk yarı `−2,40` · ikinci yarı `+5,31` · ortalama `1,46` → **`iyileşiyor`** (fark `+7,71`)
> Başlık: `CLV eğilimi yukarı`
