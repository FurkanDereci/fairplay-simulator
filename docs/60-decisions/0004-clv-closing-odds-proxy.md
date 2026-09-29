# ADR-0004 — CLV için Kapanış Oranı Vekili

> **DURUM: YERİNİ ADR-0005 ALDI.** Bu karar **yanlış** çıktı: fair oranı kapanış vekili yapmak
> `CLV = O_konulan / O_fair − 1` sonucunu yapı gereği **hep negatife** kilitliyor (fair oran her
> zaman bookmaker oranından uzundur), yani metrik hiçbir bilgi taşımıyordu. Aşağısı tarihsel
> kayıt olarak duruyor; geçerli karar ADR-0005'tir.

- **Durum:** ~~Kabul edildi~~ → **ADR-0005 ile değiştirildi**
- **Tarih:** 2026-09-29
- **Bağlam:** `CLV` (Closing Line Value) "kuponu kapatış çizgisine göre iyi mi aldım?" sorusunu
  ölçer. MVP'de gerçek bir oran akışı yok (fikstür kataloğu sabit), dolayısıyla gerçek bir
  "kapanış oranı" da yok. Alan boş bırakılırsa CLV hiç hesaplanamaz.

## Karar

Kapanış oranı olarak **vig'siz fair oran** (`O_fair = 1 / P_fair`) saklanır.

`CLV = O_konulan / O_fair − 1`

Gerekçe: kapanış çizgisi, piyasanın bilgiyi sindirdikten sonraki en verimli fiyatıdır; vig'siz fair
oran bu fiyatın MVP'deki en yakın vekilidir (marj arındırılmış, olasılık toplamı 1).

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| Kapanış = kuponun kendi oranı | CLV her zaman 0 olur; metrik anlamsızlaşır |
| Kapanış = rastgele sapma | Determinizmi bozar, açıklanamaz |
| CLV'yi MVP'de hiç hesaplamama | Sözleşmede (`20-accounting-spec.md` §3.3) var; alan sessizce boş kalırdı |
| Gerçek oran akışı (The Odds API) | MVP'de ağ + anahtar bağımlılığı; ileride aynı alan doldurulur |

## Sonuçlar

- (+) Deterministik ve açıklanabilir: "fair çizgiyi geçtin mi?" sorusuna cevap verir.
- (+) Sözleşme değişmez: gerçek kapanış akışı gelince aynı alan gerçek değerle doldurulur.
- (−) Vig arındırılmış fiyat, gerçek kapanıştan daha "verimli" olduğu için CLV **muhafazakâr**
  (olduğundan düşük) çıkar; bu bilinen ve kabul edilen bir sapmadır.
