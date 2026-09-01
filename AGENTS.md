# FairPlay Simulator - Workspace Agent Rules & Guidelines

Bu dosya FairPlay Simulator projesinde çalışan tüm AI geliştirici ve uzman alt ajanlar (Gatekeeper, Data Math, UI/UX, PM vb.) için bağlayıcı proje kurallarını içerir.

---

## 1. Genel Geliştirme & İletişim İlkeleri
- **Varsayım Yapma:** Emin olunmayan konularda asla kendi kendine varsayımda bulunma; kullanıcıya açıkça sor.
- **Doğrudan ve Net Ol:** Fikir uyuşmazlığında veya teknik olarak zayıf bir yaklaşımda lafı dolandırmadan doğrudan açıkla.
- **Gereksiz Övgüden Kaçın:** Yanıtlarda gereksiz övgü ve laf kalabalığı yapma; doğrudan teknik çözüme ve eyleme odaklan.
- **GIPS Fon Muhasebesi Bütünlüğü:** Tüm portföy metriklerinde (Unit NAV, TWR, Sharpe, Sortino, MDD) matematiksel ve finansal kurumsal standartlara sadık kal.

---

## 2. Frontend & Vanilla JS SPA Güvenlik Kuralları (Önemli Dersler)

### 2.1. Obje Anahtarları ve Sözdizimi (Object Literals & Dot Notation)
- **Nokta İçeren Anahtarlar:** İçinde nokta veya özel karakter barındıran obje anahtarları (`"OVER_2.5"`, `"UNDER_2.5"`, vb.) **mutlaka tırnak içinde tanımlanmalı** (`{ "OVER_2.5": 1.85 }`) ve erişirken **köşeli parantez kullanılmalıdır** (`outcomes["OVER_2.5"]`).
- **Asla Yapma:** `outcomes.OVER_2.5` veya `{ OVER_2.5: 1.85 }` yazma! JavaScript motoru bunu parse hatası (`SyntaxError`) veya `TypeError: Cannot read properties of undefined (reading '5')` olarak değerlendirip tüm `<script>` bloğunun çalışmasını durdurur.

### 2.2. Global Window Fonksiyon Bağlantıları (Window Bindings)
- `window.<fonksiyonAdı> = <fonksiyonAdı>;` bağlaması yapmadan önce, o fonksiyonun script içinde **kesinlikle tanımlanmış olduğunu** doğrula.
- Tanımsız bir fonksiyonu `window` nesnesine atamaya çalışmak `Uncaught ReferenceError` oluşturur ve altındaki tüm fonksiyon tanımları ile `init()` yaşam döngüsünü tamamen öldürür.

### 2.3. Hata İzolasyonu (Error Boundaries) & Yaşam Döngüsü
- `init()` gibi açılış fonksiyonlarında Chart.js veya harici kütüphane çağrılarını `try-catch` ve `typeof Chart !== "undefined"` ile koru. Bir bileşenin gecikmesi veya hata vermesi diğer bileşenlerin (fikstürler, kimlik doğrulama, bakiye) yüklenmesini engellememelidir.
- Eski veya geçersiz oturum verileri (`localStorage` token'ları) backend tarafından 401/403/404 ile reddedildiğinde otomatik temizlenmeli ve temiz bir oturum başlatılmalıdır.

---

## 3. Kod Değişikliği Doğrulama Standardı (Verification Checklist)
Her frontend veya backend değişikliğinden sonra:
1. `python -m unittest discover tests -v` çalıştırılmalı ve tüm testlerin geçtiği doğrulanmalıdır.
2. `src/frontend/index.html` içinde tanımlanmamış değişken, tırnaksız noktalı obje anahtarı veya asılı kalmış debug logları taranmalıdır.
