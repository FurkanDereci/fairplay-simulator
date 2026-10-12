# ADR-0020 — Kod Haritası: Toplulukları Baskın Modüle Göre Adlandırma

- **Durum:** Kabul edildi
- **Tarih:** 2026-10-12
- **Bağlam:** PM raporu E5/Ö-10. `graphify` grafiği **~50 isimsiz topluluk** ve ~1,1 MB
  `graph.json` üretiyor; yeni geliştirici (veya bir devralan) için oryantasyon maliyeti yüksek
  ("Community 0..N" hiçbir şey anlatmıyor). graphify'ın kendi etiketleme yolu (`graphify label`)
  bir **LLM backend'i** ister: bu ortamda çevrimdışı koşamaz ve **deterministik değildir**
  (etiketler koşudan koşuya değişebilir).

## Karar

1. **Topluluklar deterministik adlandırılır.** Her topluluğun adı, üyelerinin `source_file`
   değerlerinin **baskın modülüdür**; uyum **%50'nin altındaysa** ilk iki modül birleşik ad olur
   (ör. `app/services + core/odds` — bağımlılık sızmasını da görünür kılar).
2. Üretilen **`docs/85-kod-haritasi.md` commit edilir** (ürün haritası). Üretim:
   `graphify extract . --code-only --no-label` (yerel AST, **API anahtarı yok**) →
   `python3 scripts/kod-haritasi.py`.
3. Belge **anlık görüntüdür**: başlıkta **kaynak commit** yazılıdır. **Kapı yoktur** (CI'da
   graphify yok) — bu bilinçli: harita, koda bağlı bir türev değil, okuyucuya yön veren bir özettir.
4. **LLM etiketleme reddedildi** (madde: bkz. alternatifler).

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| `graphify label` (LLM) | Deterministik değil; API anahtarı/ağ ister; etiketler her koşuda değişir → "doküman yalan söylemez" ilkesiyle gerilimli |
| Toplulukları isimsiz bırakmak | E5'in şikâyeti tam bu: grafik okunamıyor |
| Toplulukları **elle** isimlendirmek | ~50 topluluk; bakım yükü, kaynağı belirsiz, kod değişince çürür |
| `graph.json`'u commit'lemek | ~1,1 MB üretilen artefakt; harita **özeti** yeterli, ham grafik gerekmez |
| Modül bazlı (topluluk değil) harita | `docs/30-architecture.md` zaten bunu prose olarak yapıyor; asıl boşluk **grafiğin** okunurluğuydu |

## Sonuçlar

- (+) Topluluklar okunur; ad **koddaki modüle** bağlıdır (uydurma etiket değil).
- (+) Deterministik ve **anahtarsız**; herkes aynı çıktıyı üretir.
- (−) Belge bayatlayabilir (kapı yok); başlıktaki kaynak commit bunu açıkça işaretler.
- (−) "Modül sınırı" ile "topluluk kümesi" birebir değil; harita bir **yaklaşımdır**, mimari sözleşme
  değil (`docs/30` sözleşmedir).
