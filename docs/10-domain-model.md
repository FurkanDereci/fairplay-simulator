# Alan Modeli

Bu belge varlıkları, durum makinelerini ve **değişmezleri** tanımlar. Değişmezler
`docs/50-test-strategy.md`'de property testlere bağlanır.

## 1. Varlıklar

| Varlık | Anlamı | Not |
| --- | --- | --- |
| **Fund** | Bir kullanıcının portföyü | MVP: tek kullanıcı = tek fon |
| **Series** | Bir birimleştirme çağı | İflas (V=0) seriyi kapatır; refill yeni seri açar |
| **Unit / NAV** | Birim sayısı `U`, birim fiyatı `NAV = V/U` | Fon fiyatı; refill'den etkilenmez |
| **LedgerEntry** | Append-only kayıt | **Tek gerçek kaynak**; bakiye/NAV projeksiyondur |
| **Fixture** | Bir maç | |
| **Market / Selection** | 1X2 · OVER_UNDER_2.5 · BTTS | |
| **OddsSnapshot** | Açılış/kapanış oranı | Kapanış → CLV |
| **Wager** | Kupon | Bkz. §2 yaşam döngüsü |
| **Settlement** | Sonuç kaydı | Sunucu üretir, istemci bildirmez |
| **EnergyAccount** | Simülasyon enerjisi (kota) | Bahis başına düşer, zamanla yenilenir |
| **CooldownState** | İflas sonrası kademeli kilit | tier + streak + expires_at |
| **Badge** | Disiplin rozeti | Oyunlaştırma katmanı (ICP değil, politika) |

**Sınır çizgisi:** `Fund`, `Ledger`, `NAV`, metrikler ve `settlement` **çekirdektir** (saf, I/O yok).
`EnergyAccount` ve `CooldownState` bir **politika katmanıdır**: çekirdeğin üstünde çalışır, çekirdeği
kirletmez. Örneğin enerji muhasebe matematiğine girmez; yalnız "bu bahis kabul edilir mi" kapısını besler.

## 2. Durum makineleri

### 2.1 Wager
```
PENDING ──┬─▶ WON    (payout = stake × odds)
          ├─▶ LOST   (payout = 0)
          ├─▶ VOID   (payout = stake)   # maç iptal
          └─▶ PUSH   (payout = stake)   # beraberlik iadesi / asian push
```
- `VOID` ve `PUSH` **iadedir**: net etki 0. Kazanç/kayıp istatistiğine **girmez**.
- Terminal durumdan çıkış yok. İkinci settlement **reddedilir** (I3).
- Yarım kazanç (asian): `payout = stake + stake × (odds − 1) / 2`; yarım kayıp: `payout = stake / 2`.
  **Altyapı hazır ama kullanılmıyor:** Asya handikapı pazarı MVP kapsamı dışıdır (`docs/70` §7.2, R7).
- **Maç üretimi tek yönlüdür (Suite 4):** bir maç ilk `simulate` çağrısında üretilip kaydedilir;
  sonraki çağrılar sonucu **kayıtlı seed'den** yeniden üretir (aynı skor + olaylar). Böylece aynı
  finalizasyon iki kez işlenmez, tek ödeme yapılır (ADR-0014).

### 2.2 Series
```
OPEN ──(V == 0)──▶ CLOSED   # growth = NAV/base kaydedilir
                      │
                  (refill)  ──▶ yeni Series: NAV = base (100), U = D / base
```
Seri kapanışı **ayrı bir defter olayı değildir**: V=0'a indiği sonuçlanma kaydından **türetilir**
(deterministik projeksiyon kuralı). Böylece "olay var ama türetme farklı" durumu oluşamaz.

### 2.3 Cooldown
```
ACTIVE ──(iflas)──▶ COOLDOWN_LOCKED(tier↑, expires_at = now + T(tier))
COOLDOWN_LOCKED ──(now ≥ expires_at)──▶ ACTIVE
ACTIVE ──(3 solvent gün)──▶ tier ↓ (taban 0)
```
Tavan varsayılan **168 saat**; **3+ disiplin rozeti** toplayan kullanıcıda tavan **72 saate**
iner (disiplin indirimi, spec §4.2). Rozetler öğrenme ölçütlerinden türetilir (§1'deki `Badge`
varlığı).

## 3. Değişmezler

| # | Değişmez | İfade |
| --- | --- | --- |
| **I1** | Refill invariance | Refill öncesi ve sonrası `NAV` **eşit**; yalnız `U` ve `cash` değişir |
| **I2** | Defter tutarlılığı | `V = cash + locked`; `replay(entries) == son durum` |
| **I3** | Settlement idempotentliği | Aynı settlement iki kez uygulanınca durum değişmez |
| **I4** | Seri bileşikliği | `TWR = Π(1 + R_s) − 1`; iflas kayıtta kalır, refill onu sıfırlamaz |
| **I5** | Enerji monotonluğu | Geçen süreyle enerji **azalmaz**; `< 10` iken bahis reddi; tavan `100` |
| **I6** | Cooldown | `T(n) = min(tavan, 4^(n−1))` saat (tavan 168, **3+ rozetle 72**); 3 solvent gün tier'ı 1 düşürür |

## 4. Hata sözleşmesi (durum kodları)

| Durum | Kod | Örnek |
| --- | --- | --- |
| Kimlik yok/geçersiz | 401 | Eksik/expired token |
| Yetki yok (başkasının kuponu) | 403 | — |
| Doğrulama hatası | 400 | `stake ≤ 0`, bilinmeyen market, bilinmeyen maç |
| Kilitli | 423 | Cooldown aktifken bahis/refill |
| Kota bitti | 429 | `energy < 10` |
| Onay gerekli (ruin) | 409 | Kasa eşiğini aşan stake, `confirm_ruin` olmadan (spec §3.4) |
| Çakışma / zaten uygulanmış | 409 | Aynı idempotency anahtarı, zaten settle edilmiş kupon |

**Önemli:** Bilinmeyen bir maç veya market **asla sessiz bir varsayılana düşmez** (mevcut projede
`odds = 2.0` varsayılanı bu yüzden kaldırılıyor) — `400` döner.
