# ADR-0009 — Olay Şeması Evrimi ve Snapshot Tetikleyicisi

- **Durum:** Kabul edildi
- **Tarih:** 2026-09-30
- **Bağlam:** Defter **tek gerçek kaynaktır** (ADR-0002) ve kayıtlar değişmezdir. İki soru
  cevaplanmadan bırakılmıştı: (1) kayıt biçimi değişirse **eski kayıtlar ne olacak**, (2) defter
  uzayınca **replay maliyeti** ne olacak. İkisi de sessiz borç biriktirir: yanlış okunan eski kayıt
  hata vermez, sadece **yanlış durum** üretir.

## Karar

1. **Biçim sürümlenir.** `LEDGER_SCHEMA_VERSION` iki yerde yaşar: dosyada (`PRAGMA user_version`
   — veritabanı damgası) ve dışa aktarılan defter belgesinde (`{"schema_version": 1, "entries": […]}`).
2. **Alan/olay eklemek geriye uyumludur; var olanın anlamını değiştirmek sürümü artırır** ve bir
   **upcaster** gerektirir (eski kayıt okunurken yeni biçime çevrilir).
3. **Bilinmeyen sürüm sessizce okunmaz.** `decode_ledger` ve `Repository` açık hata fırlatır
   (`UnsupportedLedgerVersion`): eski sürüm upcaster, koddan yeni sürüm kod güncellemesi ister.
4. **Donmuş kayıt fixture'ı biçimi kilitler:** `tests/data/ledger_v1.json` (v1 semantiği, `[G-1]`
   senaryosu). Biçim değişirse bu test kırılır; v2 gerektiğinde **yeni** fixture eklenir ve
   upcaster yazılır — eski fixture silinmez.
5. **Snapshot tetikleyicisi sayısaldır ve ölçülmüştür.** Ölçüm (2026-09-30): **5.001 olay → 7,1 ms**
   replay (`Fund.replay`). Tetikleyici: **kullanıcı başına 100.000 olay** veya **`cli replay` > 250 ms**.
   O eşiğe kadar defter her seferinde baştan oynatılır (snapshot yok).

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| Sürümleme yok, "dikkatli oluruz" | Sessiz yanlış okuma üretir; hata görünmez, **durum yanlış** olur |
| Eski olayları güncellemek | "Değişmez kayıt" sözünü bitirir; defter tek gerçek kaynak olmaktan çıkar |
| Şimdi snapshot eklemek | Ölçülen maliyet 5.000 olayda 7 ms — ihtiyaçtan doğmayan soyutlama |
| Avro/Protobuf gibi şema çerçevesi | Tek süreç + SQLite ölçeğinde ağır; JSON + sürüm + upcaster yeter |
| Fixture'ı test içinde üretmek | Donmuş olmaz: biçim değişince test de birlikte değişir, koruma kalmaz |

## Sonuçlar

- (+) Eski kayıt **yanlış** okunamaz: ya doğru okunur ya açık hata verir.
- (+) Biçim değişikliği **gürültülü** olur (fixture + sürüm), sessiz olmaz.
- (+) Snapshot kararı "gerekirse" değil, **ölçülmüş sayıya** bağlı.
- (−) Sürüm artışı bir upcaster dalı yazmayı zorunlu kılar (küçük ama gerçek maliyet).
- (−) Fixture bilinçli olarak güncellenir; kazara "düzeltmek" korumayı zayıflatır.
