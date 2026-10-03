---
title: FairPlay Echo — Vizyon
status: VISION
created: 2026-09-29
---

> **Etiket: VISION.** Bu belge **hedefi** anlatır, mevcut durumu değil.
> Mevcut durum `docs/30-architecture.md` → **CURRENT** bölümündedir. Buradaki bir vaat
> orada CURRENT olarak doğrulanmıyorsa, bu belge onu "var" diye okutmamalıdır.

# Vizyon

Gerçek para içermeyen, eğitici bir futbol tahmin/portföy simülatörü. Bir kupon, bir yatırım fonu
**pozisyonu** gibi ele alınır: kasa yerine **birim NAV** (GIPS), keyfi miktar yerine **Kelly**
ölçekleme, ham oran yerine **vig arındırılmış** olasılık, "kâr ettim" yerine **TWR / Sharpe / Sortino /
MDD** ve sonuç gürültüsünden bağımsız **CLV**. İflas bir çöküş değil, kayda geçen bir olaydır ve
kademeli bir bekleme kilidiyle karşılanır.

## Neden

Bahis ürünleri dopamin döngüsüyle dikkatsiz davranışı ödüllendirir. FairPlay tersini yapar:
tahmini bir **yatırım disiplini** problemi olarak modeller. Ölçü şans değil, **zaman-ağırlıklı
getiridir**; bu yüzden bakiyeye para eklemek performansı iyileştirmez (bkz. `20-accounting-spec.md` → I1).

## Kapsam (MVP)

Tek kullanıcı · tek süreç · SQLite · varsayılan olarak mock veri. Arayüz tek sayfa.

## Non-goal (bilinçli olarak dışarıda)

- **Gerçek para yok.** Ödeme, çekim, kripto yok. Tüm bakiyeler sanaldır ve eğiticidir.
- **Tavsiye yok.** Ürün karar vermez; seçenekleri, varsayımları ve sonuçlarını gösterir, kararı kullanıcıya bırakır.
- **Sosyal / kopya fon / lig** — Faz 2. Mimaride yer ayrılır, MVP'de kapalıdır.
- **PostgreSQL / TimescaleDB / Redis / mikroservis** — ölçülü bir tetikleyici gelene kadar yok
  (tetikleyiciler `30-architecture.md` → TARGET).
