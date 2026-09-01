# FairPlay Simulator: Master Architectural Blueprint & Development Roadmap

## 1. Ürün Vizyonu ve Çıkış Noktası (The "Why")
FairPlay Simulator; gerçek para yatırmadan spor müsabakalarına tahmin yapan, ancak bu tahminlerin performansını şans yerine **yatırım fonu disiplini (GIPS / Unit NAV)**, **Kelly Kriteri** ve **matematiksel risk yönetimi** ile ölçmek isteyenler için tasarlanmış eğitici bir simülasyon platformudur.

---

## 2. Çekirdek Oyun Modları (Dual Core Loops)

```
+-----------------------------------------------------------------------------------+
| 1. CANLI MAÇ GÜNÜ MODU (Matchday Fund Manager)                                     |
| - Gerçek dünya fikstürü (Haftalık bültenler: PL, UCL, Süper Lig).                  |
| - Haftalık 100 Risk Bütçesi (Weekly Risk Units).                                  |
| - Maçlar bittiğinde NAV ve CLV (Closing Line Value) güncellenir.                 |
| - İflas durumunda: Fon tasfiye edilir ("Fund Series Liquidation"), geçmişe kalıcı |
|   leke sürülür, Seri 2 için sonraki maç haftası beklenir.                         |
+-----------------------------------------------------------------------------------+
| 2. ZAMAN MAKİNESİ / TARİHSEL BACKTEST MODU (Historical Sandbox)                   |
| - Hafta içi / maç olmayan günlerde sıkılmayı engeller.                            |
| - Geçmiş sezonların (örn: 2023-24 PL) 380 maçı 10 dakikada simüle edilir.         |
| - Farklı kasa stratejileri (Kelly, Sabit Stake, Martingale) test edilir.          |
+-----------------------------------------------------------------------------------+
```

---

## 3. Matematiksel ve Finansal Temeller

### A. GIPS Uyumlu Unit NAV Fon Muhasebesi
* **Birim NAV:** $NAV_t = \frac{\text{Kasa Balance} + \text{Kilitli Kuponlar}}{\text{Toplam Birim Sayısı (Units)}}$
* **Sanal Bakiye Yenileme (Refill Invariance):** Bakiye eklendiğinde mevcut NAV değişmez; güncel NAV fiyatından yeni birim (unit) ihraç edilir.
  $$\Delta \text{Units} = \frac{\text{Refill Amount}}{NAV_{\text{current}}}$$

### B. Bookmaker Vig / Overround Arındırma (Fair Odds)
* $\text{Implied Probability}: P_i = \frac{1}{O_i}$
* $\text{Total Implied}: S = \sum P_i$
* $\text{Overround (Vig)}: S - 1.0$
* $\text{Fair Probability}: P_{\text{fair}, i} = \frac{P_i}{S}$
* $\text{Fair Odds}: O_{\text{fair}, i} = \frac{1}{P_{\text{fair}, i}}$

### C. Kelly Kriteri Stake Boyutlandırma
$$f^* = \max\left(0, \; \frac{p \cdot o - 1}{o - 1}\right)$$
* Tekil kupon kasasının $\%15$'ini aştığında Risk of Ruin uyarısı tetiklenir.

---

## 4. İki Ajanlı Geliştirme Protokolü (Dev Workflow)

* **Rol 1 (Coder / Builder - örn. Claude Code):** `ROADMAP.md`'deki atomik görevleri alır, kodu yazar, syntax ve yerel testleri çalıştırır, commit atar.
* **Rol 2 (Gatekeeper & QA - Antigravity):** Git diff'i inceler, `pytest` ile deterministik testleri koşturur, matematiksel ve mimari açıkları denetler, PASS / REVISE verir.

---

## 5. Fazlandırılmış Geliştirme Yol Haritası (Master Backlog)

### [FAZ 1: Çekirdek Altyapı ve Veri Tabanı Onarımı]
- [x] **Görev 1.1:** `src/backend/nav_engine.py` içindeki `calculate_twr()` metodundaki `self` hatasını düzelt ve testleri güncelle. (QA PASS: 15/15 testler doğrulandı)
- [x] **Görev 1.2:** SQLAlchemy veritabanı modellerini (`src/backend/models/database.py`) aktifleştir; hardcoded Linux yolunu kaldırıp SQLite/Postgres uyumlu hale getir. (QA PASS: 17/17 testler doğrulandı)
- [x] **Görev 1.3:** `src/backend/app.py` içindeki RAM tabanlı sözlükleri (`user_portfolios`, `user_cooldowns`) kaldır; bakiye, bahis ve NAV geçmişini DB transaction'larına bağla. (QA PASS: 18/18 testler doğrulandı)
- [x] **Görev 1.4:** `auth_jwt.py` kopyasını sil; `auth.py` içinde `bcrypt` şifreleme ve güvenli JWT standardına geç. (QA PASS)

### [FAZ 2: Oyun Döngüsü ve Simülasyon Motoru]
- [x] **Görev 2.1:** Bahis Sonuçlandırma motoru (`settle_wager`) ve API endpoint'i yaz (`/api/wager/settle`). (QA PASS)
- [x] **Görev 2.2:** Hızlı test ve Zaman Makinesi modu için Monte Carlo / Poisson tabanlı Sanal Maç Motoru (Virtual Match Engine) geliştir. (Data/Math PASS: 23/23 testler doğrulandı)
- [x] **Görev 2.3:** Benchmark endekslerini (Random Walk, Favorite Heavy) formül uydurmak yerine gerçek bot simülasyonları olarak işlet. (Data/Math PASS: 26/26 testler doğrulandı)

### [FAZ 3: Frontend ve Görselleştirme Entegrasyonu]
- [x] **Görev 3.1:** `src/frontend/index.html` içindeki sahte JS state'ini kaldır; gerçek REST API istemcisi (`fetch`) ekle. (UI/UX PASS: 27/27 testler doğrulandı)
- [x] **Görev 3.2:** Kullanıcı giriş (Login/Register) ekranı ve Token yönetimini arayüze ekle. (UI/UX PASS)
- [x] **Görev 3.3:** Backend'den gelen gerçek NAV serisini ve Benchmark eğrilerini Chart.js grafiğine bağla. (UI/UX PASS)
- [x] **Görev 3.4:** Sosyal Paylaşım / Fon Bülteni (Factsheet Card) görselleştirme bileşeni ekle. (UI/UX PASS)

### [FAZ 4: Açık Kaynak ve Yayın Hazırlığı]
- [x] **Görev 4.1:** `.env.example` ve kapsamlı `.gitignore` oluşturarak tüm anahtar/gizli bilgileri repodan izole et. (Tamamlandı)
- [x] **Görev 4.2:** Yasal sorumluluk reddi (Educational Disclaimer) içeren profesyonel bir `README.md` hazırla. (Tamamlandı)
