# ADR-0015 — Solvent Gün Sayacı ve İlk Şema Göçü

- **Durum:** Kabul edildi
- **Tarih:** 2026-10-03
- **Bağlam:** Orijinalin `01_gamification` §3'ü *"3 active solvent days reduce effective tier n by 1"*
  diyor. Çekirdekte `record_solvent_day` **vardı ve I6 ile testliydi**, ama **hiçbir yerden
  çağrılmıyordu** (ölçüm: `register_solvent_day` yalnız `core/cooldown.py` içinde tanımlı, `app/`
  katmanında tek çağrı yok) — yani uygulamada tier **hiç düşmüyordu**: yazılı ve testli ama **ölü**
  bir mekanizma (`docs/70` §6.1, F5). Ayrıca duvar saati sınırını işlemek için **kalıcı bir imleç**
  gerekiyordu; depo şeması `CREATE TABLE IF NOT EXISTS` ile kurulduğu için yeni bir kolon var olan
  dosyalara kendiliğinden eklenmez.

## Karar

1. **Gün sınırı etkileşim anında işlenir.** `portfolio` ve `wager` çağrılarının her biri bir
   "tick"tir: imleçten (`last_solvent_day`, ISO gün) bugüne geçen her **tam gün sınırı** işlenir.
   Hesap **solventse** (`V > 0`) günler birikir; **iflastaysa** (`V = 0`) o günler **yanar** —
   imleç ilerler, ileriye taşınmaz.
2. **İlk gözlem yalnız imleci kurar** (geçmiş gün uydurulmaz) ve tek tick'te en fazla
   `MAX_ACCRUAL_DAYS = 30` gün işlenir (uzun aradan sonra döngü şişmesin).
3. **İmleç `trigger`ta bugüne çekilir:** iflas seriyi sıfırlar, iflastan önceki günler yeni sayaca
   taşınmaz.
4. **Şema göçü açık ve idempotenttir:** `Repository._migrate()` `PRAGMA table_info` ile kolonu
   denetler, eksikse `ALTER TABLE ... ADD COLUMN` çalıştırır. Bu, projenin **ilk göçüdür**; defter
   biçimi (ADR-0009) değişmediği için `LEDGER_SCHEMA_VERSION` **artırılmaz**.

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| Solvent günleri **defterden** türetmek (kayıt zaman damgalarıyla gün gün replay) | Doğru ama her tick'te gün-gün projeksiyon demek; ölçüsüz maliyet, gözlemlenebilir kazanç yok |
| Yeni bir tablo (`solvent_days`) | Tek bir tarih için tablo fazla; göç yüzeyi büyür |
| Tabloyu yeniden kurmak (`DROP`+`CREATE`) | Var olan dosyalarda veri kaybı |
| Tam bir göç çerçevesi (alembic) | Ölçüsüz ağırlık: depo "tek dosya + tek süreç" varsayımıyla çalışıyor (`docs/30`) |
| Gün sınırını zamanlayıcıyla (cron/worker) işlemek | Uygulama tek süreç ve arka plan işi yok; tick yaklaşımı aynı sonucu dış bağımlılık olmadan verir |
| Hiç yapmamak (F5'i kapsam-dışı bırakmak) | Yazılı + testli bir mekanizmanın **ölü** kalması, "doküman yalan söylemez" ilkesini zedeler |

## Sonuçlar

- (+) F5 kapandı: mekanizma gerçekten çalışıyor ve arayüzde görünüyor (`t-solvent`, `streak-bar`).
- (+) Sınır **yazılı**: solvency yalnız tick anında okunur; bir tick'te birden çok gün birikmişse
  hesabın o pencerede hiç iflas etmediği varsayılır (spec §4.2).
- (+) Göç testli: eski şemalı bir dosya açıldığında kolon eklenir ve veri okunur (`tests/repo`).
- (−) Tick, kullanıcı **hiç açmazsa** çalışmaz; günler bir sonraki açılışta toplu işlenir. Sonuç
  aynı (kilit zaten dolmuştur), yalnız sayaç gecikmeli görünür.
- (−) İki günü aşan iflas→refill penceresi görülemez; sınır bilinçli ve belgede yazılı.
