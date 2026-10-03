# ADR-0010 — Mutation Denetimi: Araç Değil, Sınır Tablosu

- **Durum:** Kabul edildi
- **Tarih:** 2026-09-30
- **Bağlam:** Alan 1'in açık sorusu şuydu: *"%96 kapsam var ama `<=` → `<` hiçbir testi kırmıyor."*
  Kapsam yüzdesi bu soruyu **cevaplamaz**, çünkü kapsam "satır çalıştı mı" der, "karar doğru mu"
  demez. Klasik cevap mutation testing'dir.

## Deneme (ölçüldü, tahmin değil)

| Araç | Sonuç |
| --- | --- |
| `mutmut 3.8` | Bu ortamda **çalışmadı**: kopyalama adımı `/run/udev/watch` symlink döngüsüne giriyor (`OSError: Too many levels of symbolic links`). Kurulum/yapılandırma denemeleri `tests_dir` liste tipi ve `--paths-to-mutate` uyuşmazlığı dahil üç ayrı hata verdi |
| Maliyet (çalışsaydı) | Test paketi ~28 sn; mutant başına bir tam koşu → 50 mutant ≈ 25 dk. Per-commit kapı olarak sürdürülemez |

## Karar

1. **Kapsam yüzdesi çıta değildir** (zaten böyleydi) ve **test sayısı da çıta değildir**.
2. Çita **kritik kararların sınırına** bağlanır: `docs/50` §9 tablosu, `core/` içindeki her kritik
   karşılaştırma/sabiti **onu öldüren testin adıyla** eşler. `tests/test_docs_sync.py` her adın
   gerçekten var olduğunu doğrular — tablo çüreyemez.
3. Sınır testleri `tests/test_boundaries.py` içinde yaşar; spec'e bağlı örnekler golden'a gider
   (`[G-15]`).
4. **Sınır davranışı yazılı olmalıdır.** Denetim sırasında bulunan örnek: enerji tavanı
   (`energy >= MAX` iken `last_update = now`) ne **test ediliyordu** ne **yazılıydı** — kod ile
   kendi docstring'i çelişiyordu. Karar verildi (tavanda geçen süre **yanar**, batarya yok),
   spec §4.1'e ve `[G-15]`'e yazıldı.
5. Araç denemesi **kapatılmadı, ertelendi**: yapılandırma repoda durmuyor (çalışmayan yapılandırma
   "denetim tekrarlanabilir" yalanı olurdu). Tekrar deneme komutu: `pip install mutmut` +
   `[tool.mutmut]` bloğu; koşulursa **hayatta kalan mutantlar** §9 tablosuna eklenir ya da yazılı
   gerekçeyle reddedilir.

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| `cosmic-ray` | Aynı sınıf: mutant başına tam paket; ölçülen maliyet değişmiyor |
| Kapsam eşiği (%95 kapısı) | Zaten %96 ve soruyu cevaplamıyor: yüzde, kararın doğruluğunu ölçmez |
| Çalışmayan `[tool.mutmut]` bloğunu repoda bırakmak | "Denetim tekrarlanabilir" iddiası yalan olurdu |
| Sınır denetimini araç gelene kadar ertelemek | Bulunan kural (enerji tavanı) tam da o yüzden yazısız kalmıştı |

## Sonuçlar

- (+) Araç bağımlılığı yok; tablo okunabilir, insan denetimine açık, maliyeti sıfıra yakın.
- (+) Denetim gerçek bir eksiği buldu: tavanda geçen süre kuralı **yazısız ve testsiz**di.
- (−) Tablo, testin mutantı gerçekten öldürdüğünü **kanıtlamaz**; kararın tek tek ele alındığını
  gösterir. Yeni kritik bir sınır doğduğunda tabloya satır eklenmelidir (aksi hâlde sessiz boşluk).
- (−) Araç yolu ileride (başka bir ortamda) yeniden denenmeli; erteleme, vazgeçme değil.
