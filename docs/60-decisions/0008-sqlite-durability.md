# ADR-0008 — SQLite Dayanıklılığı: WAL, synchronous ve Geri Yükleme Tatbikatı

- **Durum:** Kabul edildi
- **Tarih:** 2026-09-30
- **Bağlam:** Defter **tek gerçek kaynaktır** (ADR-0002) ve tek bir SQLite dosyasında durur. Buna
  rağmen bugüne kadar: journal modu, `synchronous` seviyesi ve yabancı anahtar zorlaması **SQLite
  varsayılanlarına** bırakılmıştı; hiç **yedek alınmamış ve geri yükleme denenmemişti**. Yani
  "kayıt kaybolmaz" iddiası kanıtsızdı.
  Ek olarak: şema `REFERENCES` bildiriyor ama SQLite yabancı anahtarları **varsayılan olarak
  uygulamaz** — yani kısıtlar yazılıydı, **yürürlükte değildi**.

## Karar

1. **`journal_mode = WAL`.** İstek başına bağlantı açıyoruz (FastAPI sync uçları thread pool'da);
   WAL okuma/yazma çakışmasını azaltır.
2. **`synchronous = NORMAL`.** Tutarlılık korunur; bedeli, elektrik kesintisinde **son commit'in
   geri alınabilmesi**dir. Eğitim amaçlı, tek kullanıcılı, gerçek para içermeyen veri için kabul
   edildi — **bilinçli karar**, varsayılana bırakılmadı. Kayıp toleransı sıkılaşırsa `FULL`'a
   çekilir (tek satır).
3. **`foreign_keys = ON`.** Yazılı kısıtlar yürürlüğe girer.
4. **Yedek yalnız online backup API'siyle alınır** (`Repository.backup_to`, stdlib
   `Connection.backup()`). Düz dosya kopyası WAL'da **yırtılır**.
5. **Kanıt geri yükleme tatbikatıdır.** `tests/repo/test_backup_and_durability.py`: yedek al →
   **yeni dosyaya** geri yükle → defter ve fon durumu birebir karşılaştır; ayrıca yedekten sonra
   yazılan kaydın yedeğe **girmediği** doğrulanır (anlık görüntü, canlı görünüm değil).

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| Varsayılan journal modu (rollback) | Tek yazarla okumaları bloklar; istek başına bağlantıda gereksiz sürtünme |
| `synchronous = FULL` | Her commit'te dayanıklılık senkronu; bu veri için gereğinden pahalı (karar yazılı, geri alınabilir) |
| Yedeği `cp` ile almak | WAL'da yırtık/eksik yedek üretir (sessiz) |
| Yedeği yalnız `integrity_check` ile doğrulamak | **Bayat** kopya da kontrolü geçer; eksik olan son commit'lerdir |
| Yedek/geri yükleme için dış araç (Litestream vb.) | Ölçülü tetikleyici yok; tek dosya + tek süreç için stdlib yeter |

## Sonuçlar

- (+) Kurtarma **kanıtlı**: tatbikat, commit'li kaydın geri geldiğini gösteriyor.
- (+) Gizli bir doğruluk açığı kapandı: FK'ler artık gerçekten uygulanıyor (test bunu kilitliyor).
- (+) Yedek, yedekten sonra yazılanı içermiyor → "anlık görüntü" davranışı test edilmiş.
- (−) WAL, veritabanına `-wal`/`-shm` yan dosyaları ekler: **dosya kopyası artık daha da yanlış**;
  bu yüzden yedek yolu tek (API) tutuldu.
- (−) `NORMAL` seviyesinde son commit kaybolabilir; bu bedel kararda yazılı.
- (−) Tatbikat testi dosya sistemiyle çalışır; Windows/9P üzerinden koşulursa yavaş olabilir
  (repo testleri tmp_path kullanır, yerel ext4).
