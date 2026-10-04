# ADR-0016 — Tasarım Değişikliği Süreci: Invariant vs Tasarıma Özgü

- **Durum:** Kabul edildi
- **Tarih:** 2026-10-04
- **Bağlam:** Arayüz sözleşmesi (`DESIGN.md` + `AGENTS.md` §9 + testler) görsel dilin **kendisini**
  kapıya bağlamıştı: `test_design_tokens_have_no_raw_hex_outside_root`, `DESIGN.md` "Nevers"
  (gradyan/cam/glow yasak), "font ağdan çekilmez" kuralı ve teal/yeşil renk-rolü. Prototip
  portu gibi **köklü** bir görsel değişiklik yalnız bu maddeleri değiştirmeyi gerektirdi.
  Ölçüm: re-skin'de görsel dil neredeyse tamamen değişti; **150 testin tamamı** (14'ü gerçek
  Chromium) yalnız tasarım-özgü maddeler çıkarılınca yeşil kaldı — yani tasarım-özgü olan,
  tasarımdan bağımsız invariantlardan **ayrılabiliyor**. Ayrım yazılı olmadığı için her köklü
  değişiklik "kalite" testini silmeyi gerektiriyordu (testlere güven erozyonu) ve doküman kayması
  doğuyordu (`docs/80` Alan 7, silinen token testine işaret ediyordu).

## Karar

1. **İki katman ayrılır ve yalnız biri makineyle kaplanır.**
   - **(i) İşlevsel sözleşme + (ii) tasarımdan bağımsız invariantlar → kapılı.**
     DOM id/class/state işaretleri, API tabanı, `[hidden]`, kontrast, taşma/kırpılma/örtüşme,
     "renk tek başına anlam taşımaz", sayı biçimi, klavye erişimi.
   - **(iii) Tek bir tasarımın özgülleri → kaplı değil, `DESIGN.md`'de prose.**
     Hex nerede yaşar, hangi font, gradyan/cam/glow var mı gibi olgular test olmaz; görsel dil
     değişince **silinecek test yoktur**, yalnız prose güncellenir.
   - Kural cümlesi: **"Tasarıma özgü olgular makineyle kaplanmaz; invariantlar kaplanır."**
2. **Köklü görsel değişiklik proposal ister.** Proposal: problem · hedef görünüm · değişenler ·
   risk altındaki invariantlar · güncellenecek dokümanlar. **Onay ölçütü:** 4 genişlikte
   (375/900/1200/1440) ekran görüntüsü + invariant suite yeşil + kontrast kontrolü. Kayıt bu
   dosyanın yaşadığı yerde (`docs/60-decisions/`) tutulur.
3. **Entegrasyon atomik.** Tek değişiklikte `DESIGN.md` + kod + (gerekiyorsa `docs/80`) birlikte
   güncellenir; pre-commit zaten `pytest` koşar, yarım iş giremez.
4. **Renk tek kaynak.** `web/assets/app.css` `:root`; Tailwind `theme` ona `var()` ile referans
   verir; **markup ham hex yazmaz** (Tailwind'in nötr paleti chrome için serbesttir).

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| Tasarım-özgü maddeleri test olarak bırakmak | Her köklü değişiklik "kalite" testi silmeyi gerektirir; silme sıradanlaşır ve testlere güven erozyona uğrar |
| Tüm görsel kapıları kaldırmak | Kalite kapısı büsbütün kaybolur; taşma/kontrast/anlamsız-renk geri sızar |
| Ağır proposal (tam tasarım dokümanı) | Hız tercih edilen işte atlatılır; atlanan süreç, olmayan süreçtir |
| Her köklü değişiklikte konsey/panel | Ölçüm ve kapı varken gereksiz; konsey ölçüsüz kararda anlamlıdır |
| Renkleri Tailwind config'de tutmak | `:root` ile ikinci bir kaynak doğar; tema tek yerden çevrilemez |

## Sonuçlar

- (+) Köklü tasarım değişikliği artık kalite testlerini **silmeden** yapılabilir (kanıt: bu re-skin — 150 test yeşil kaldı).
- (+) Kapı kaliteye saklandı: invariantlar (taşma/kontrast/anlam) korunur, tasarım serbesttir.
- (−) Tasarım-özgü maddeler otomatik kapılı değil; `DESIGN.md` disiplini inceleme + bağımsız gözle ayakta kalır (§9 "inceleme").
- (−) "Köklü" eşiği yorum ister; küçük görsel ayarlar proposalsız serbest, görsel-dil değişimi proposal ister.
