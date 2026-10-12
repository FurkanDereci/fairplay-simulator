# ADR-0017 — `JWT_SECRET_KEY` Sır Politikası

- **Durum:** Kabul edildi
- **Tarih:** 2026-10-12
- **Bağlam:** Devralınan projede `auth.py`, `JWT_SECRET_KEY` verilmediğinde **bilinen bir sabit**
  anahtara düşüyordu (token sahteleme açığı). Bu depoda kapatıldı: anahtar verilmezse `secrets`
  ile **rastgele** üretilir ve `RuntimeWarning` basılır (`app/config.py`, `docs/70` §2).
  Ama §7/`AGENTS.md §7` "sır için güvensiz varsayılan yok" derken sır **opsiyonel** kalıyor; PM
  raporu (2026-10-07, Ö-2) bu iki ifadenin gerilimini bir **ADR ile kapatmayı** istedi. Soru:
  rastgele üretim, "güvensiz varsayılan yok" ilkesini ihlal ediyor mu; yoksa bilinçli mi?

## Karar

1. **Rastgele üretim güvensiz varsayılan değildir.** İlke *bilinen sabit sırrın yasaklanmasıdır*;
   her süreçte `secrets.token_urlsafe(32)` ile tahmin edilemez bir anahtar üretmek bu ilkeyi
   **ihlal etmez, korur**. Yasak olan tek şey, saldırganın önceden bildiği bir sabittir.
2. **Tek süreç varsayımıyla `JWT_SECRET_KEY` opsiyoneldir** (`docs/30`: tek süreç + SQLite). Sır
   verilmezse uyarı basılır ve **yeniden başlatmada mevcut token'lar geçersiz olur** — kabul edilen,
   yazılı sonuç.
3. **Çok süreç / çok worker / çok örnek `JWT_SECRET_KEY`'i zorunlu kılar.** Ayrı süreçler ayrı
   rastgele anahtar üretirse token'lar süreçler arası geçersiz olur; ölçek göçü tetikleyicisi
   (`docs/30` TARGET) ateşlendiğinde sır **verilmelidir**.
4. **Sır verilmemesi hata değil, uyarıdır.** Tek kullanıcılı MVP'de fail-fast, hızlı başlangıcı ve
   CI'yı kırar ve güvenlik kazancı sağlamaz (rastgele anahtar zaten güvenli). Durum `RuntimeWarning`
   ile **görünür** kılınır; sessiz davranış yasak (`AGENTS.md §9`, enerji-görünürlük dersi).

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| Sırrı **zorunlu** kıl, yoksa başlama (fail-fast) | Rastgele anahtar zaten güvenli; fail-fast güvenlik eklemez, yalnız hızlı başlangıcı/CI'yi kırar |
| **Bilinen sabit** varsayılana düş | Devralınan açık; token sahteleme — reddedildi (`docs/70` §2) |
| **Sessizce** rastgele üret (uyarısız) | Yeniden başlatma sürprizi görünmez kalır; sessiz davranış yasak |
| Anahtarı **diske yaz** (otomatik kalıcılaştır) | Sır dosyada dolaşır; tek süreç varsayımında ölçüsüz karmaşıklık |
| Parola gibi zorunlu kıl ama hızlı başlangıç için "geliştirme modu" istisnası | İki davranış + mod ayrımı; test yüzeyi büyür, kazanç yok |

## Sonuçlar

- (+) İlke korunur: hiçbir koşulda **bilinen** sabit sır yok.
- (+) Karar **görünür ve ölçülür**: `RuntimeWarning` + `docs/70` §2 satırı + token akışı testi
  (`tests/api`).
- (−) Sır verilmemişse her yeniden başlatma token'ları düşürür; bu, uyarı metninde yazılıdır.
- (−) Çok-süreçli bir dağıtımda bu politika **yanlış kullanılırsa** sessiz token geçersizliğine yol
  açar; bu yüzden madde 3 çok-süreçte sırrı zorunlu kılar.
