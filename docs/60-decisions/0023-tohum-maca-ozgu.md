# ADR-0023 — Tohum Maça Özgüdür (aynı tohum farklı maçta farklı akış)

- **Durum:** Kabul edildi
- **Tarih:** 2026-10-12
- **Bağlam (kullanıcı bildirimi + ölçüm):** "Maçların sonucu neredeyse hep ev sahibi lehine
  **6-2**, farklı simülasyonlarda bile skor değişmiyor." Ölçüm: arayüzün **varsayılan tohumu 5**
  (`web/index.html`), ve `simulate_match` `random.Random(seed)` kuruyordu — **maç kimliği yok**.
  Aynı tohum + aynı çekiliş sırası (önce ev, sonra dep) yüzünden `seed=5` ile **beş fikstürün
  beşi de 6-2** çıkıyordu (md-05: 6-0). Poisson normalde 0–4 bandında gezer; 6 **zorlanmıştır**:
  sorun λ'larda değil, tüm maçların **aynı rastgele akışı** paylaşmasındadır.

## Karar

Tohum **maç kimliğiyle tuzlanır**:

```python
def _rng(match_id: str, seed: int | None) -> random.Random:
    if seed is None:
        return random.Random()            # sistem entropisi (rastgele)
    return random.Random(f"{match_id}:{seed}")
```

Determinizm **korunur**: aynı **(maç, tohum)** çifti yine aynı skoru ve aynı olay zaman çizelgesini
üretir (`[G-…]`/S5 sözleşmesi). ADR-0003 geçerliliğini korur — rastgelelik yine **enjekte edilen**
rng'den gelir; değişen tek şey, "tohum"un artık **maç bağlamıyla birlikte** anlamlı olmasıdır.

## Değerlendirilen alternatifler

| Seçenek | Neden değil |
| --- | --- |
| Fikstür oranlarını değiştirmek | Sorun oranlarda değil, ortak akışta; belirti maskelenir, hata kalır |
| Yalnız **varsayılan tohumu** değiştirmek (5 → başka) | Aynı hata başka bir tohumda tekrar eder; kök neden durur |
| Her maça **sabit** farklı tohum | "Aynı tohum → aynı senaryo" anlamını bozar; kullanıcının tohum kontrolü kaybolur |
| `run_monte_carlo`'yu da tuzlamak | Orada tek maç yok; özet bir **dağılım**dır, maç kimliğine bağlı değil — kapsam dışı |
| ADR-0014'ü değiştirip her simülasyona yeni skor | "Tek maç bir kez üretilir / tek ödeme" güvenliğini bozar — ayrı konu (§Sonuçlar) |

## Sonuçlar

- (+) Varsayılan tohumla skorlar **çeşitlenir** (ölçüm, `seed=5`: 2-1 · 0-1 · 3-1 · 3-2 · 2-1).
- (+) Determinizm ve ADR-0014 **dokunulmadı**; mevcut testler skor sabitlemediği için kırılmadı.
- (−) **Kayıtlı** maçlar eski skorlarını korur; yeni simülasyonlar yeni tuzu kullanır. Yani bir maçı
  kaydetmeden önce/sonra aynı tohum farklı skor verebilir — bilinçli (kayıt değişmez).
- (−) "Tohumu değiştirdim ama skor değişmedi" gözleminin **ikinci** sebebi bu değişiklikle ilgisiz:
  **ADR-0014** (maç bir kez üretilir, kayıtlı skor döner). Arayüzün bunu **söylemesi** ayrı bir iştir
  (dil/UX turu); bu ADR yalnız motoru düzeltir.
