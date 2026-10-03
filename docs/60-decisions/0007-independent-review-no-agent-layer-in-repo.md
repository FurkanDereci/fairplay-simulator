# ADR-0007 — Geliştirme Süreci: Bağımsız İnceleme, Ajan Katmanı Ürün Repo'sunda Değil

- **Durum:** Kabul edildi
- **Tarih:** 2026-09-30
- **Bağlam:** Devralınan projede (`fairplay_simulator_src`) bir "çok ajanlı" geliştirme iskeleti
  denendi: `tooling/agent_workflow/agent_router.py` (coder → uzman → PM gatekeeper → yönlendirme
  durum makinesi) + `docs/agents/*.md` (PM / UI-UX / QA / Security / Data-Math / DevOps rol
  promptları) + `.agents/skills/frontend_runtime_qa`. Soru: aynı yapı burada kurulmalı mı?

## Tespit

- `agent_router.py`'deki "uzmanlar" **LLM değil**: `_default_ui_ux`, `_default_qa` gibi fonksiyonlar
  sabit `"[PASS]"` dizesi döndürüyor. İskelet, ajanları olmayan bir **yönlendirme iskeletiydi** —
  gerçek bağımsız inceleme üretmiyor, kendi kendini onaylayan bir döngü kuruyordu.
- Rol promptları (`docs/agents/*.md`) ise **değerli**: her rol için "neye bakılır" tanımı net
  (ör. UI/UX: bilişsel yük, yükleme/hata/boş durumları, kontrast, tablo taranabilirliği).
- `.agents/skills/frontend_runtime_qa` değerli bir runbook (nokta içeren obje anahtarları, `window`
  bağlamaları, init hata sınırları, bayat oturum kurtarma) — ama **ürün** değil, geliştirme aracı.

## Karar

1. **Ürün repo'suna ajan katmanı konmaz.** Router, rol promptları, subagent artefaktları ürün
   deposunda yaşamaz; onlar geliştirme aracıdır (bkz. `AGENTS.md` §8).
2. **Rol bilgisi yaklaşım olarak girer, dosya olarak değil.** UI kalite eşiği `AGENTS.md`'de kural
   olur; işletimi kullanıcının kendi skill'leri yapar (`ui-ux-pro-max`, `model-yonlendirme`).
3. **Bağımsız inceleme gerçek bir farklı modelle yapılır.** Tek kişinin hem üretip hem onaylaması
   yapısal bir kör noktadır; inceleme, yazarın bağlamını paylaşmayan **salt-okur** bir alt ajana
   (farklı model ailesi, ağsız) delege edilir ve kanıt paketiyle sınırlı tutulur.
   Kayıt: `🧠 500-Knowledge/Model-Secimi/model-karar-gunlugu.md`.

## Sonuçlar

- (+) Ürün deposu temiz kalır; geliştirme aracı ürünle karışmaz.
- (+) İnceleme gerçekten bağımsız olur: farklı model, paylaşılmayan bağlam, kanıtla sınırlı.
- (+) Model seçimi kullanıcının mevcut yönlendirme tablosuna bağlanır; yeni bir yapı icat edilmez.
- (−) İnceleme arka planda yürür: gecikme ve ek maliyet (bilinçli kabul).
- (−) Rol promptları repo'da olmadığı için kalite eşikleri `AGENTS.md`'de **açıkça** yazılmalı,
  aksi hâlde bilgi kaybolur.
