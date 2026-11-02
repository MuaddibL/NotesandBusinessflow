# Architecture

## System overview
Notes&MJ, tek kişinin kendi makinesinde çalıştırdığı bir masaüstü çalışma alanıdır: günlük iş
planlama, odak oturumları ve not alma tek uygulamada ve birbirine bağlı biçimde toplanır. Ürünü
ayırt eden şey bu bağlar — bir görevden odak oturumu başlatmak, bir notu göreve iliştirmek —
yoksa üç ayrı araç zaten mevcuttur.

Stil: **modüler monolit** — tek süreç, tek repo, tek veritabanı dosyası; modül sınırları grimp
tabanlı bir mimari testle zorlanır. Gerekçe: tek kişilik, çevrimdışı ve tek süreçli bir masaüstü
aracında servis ayrıştırmanın hiçbir getirisi yoktur; sınırlar testle korunduğu için modüller yine
de birbirine yapışmaz (bootstrap kararı, 2026-11-02).

Teknoloji: Python 3.12 · **PySide6** (Qt Widgets + QSS) · stdlib **`sqlite3`** (şema sürümü
`PRAGMA user_version` ile) · uv. Sunucu yok, hesap yok, ağ yok.

> **Geçiş durumu (2026-11-02).** Repodaki kod hâlâ spec 0001'in FastAPI iskeletidir. Bu dokümanda
> anlatılan yapı **hedeftir**; geçişi spec 0002 yapar: FastAPI/uvicorn/Playwright bağımlılıklarının
> kaldırılması, `main.py` · `health.py` · `shared/http.py` · `static/` · `tests/e2e/` ve HTTP'ye
> bağlı integration testlerinin kaldırılması, PySide6 + pytest-qt eklenmesi, `scripts/check.conf`
> ve `tests/architecture_rules.py` yasak paket kümesinin güncellenmesi. O ana kadar docs ile kod
> arasındaki fark bilinçlidir ve burada kayıtlıdır (R-10 gerekmez).

Hedef paket düzeni:
```
app/
  __main__.py              # uygulama girişi: `uv run python -m app`
  ui/                      # PySide6 kabuğu: pencere, görünümler, QSS teması — INCE, iş kuralı yok
  shared/                  # errors.py (DomainError), db.py (bağlantı + user_version geçişleri)
                           # — hiçbir modüle bağımlı değil
  modules/<module>/
    public.py              # modülün TEK dış yüzü: facade fonksiyonlar + DTO'lar
    service.py             # use-case'ler, transaction sınırı
    domain/                # saf Python iş kuralları (BR-n) — Qt yok, IO yok, saat okumaz
    repository.py          # sqlite3 erişimi (parametreli SQL), yalnızca kendi tabloları
  resources/               # gömülü font, ikon, QSS — çevrimdışı (CDN yok)
tests/unit · tests/integration · tests/ui
```

## Modules / components and ownership

| Module | Single responsibility | Owns |
|---|---|---|
| `planner` | Günlük plan: görevler, zaman blokları, Eisenhower önceliklendirmesi, devir (BR-1, BR-6, BR-7) | Görev, Gün Planı, Zaman Bloğu, Günün 3 Büyük Odağı |
| `focus` | Odak oturumu ve Pomodoro döngüsü (BR-5) | Odak Oturumu, seans sayacı ve süreleri |
| `notes` | Not alma ve hızlı not sandığı (BR-2) | Not |
| `projects` | Görevleri gruplayan uzun ömürlü iş başlıkları | Proje |
| `tags` | Görev ve Notları kesen serbest sınıflandırma (BR-8) | Etiket, Etiketleme bağı |

`ui` bir modül değildir: modüllerin `public` yüzlerini çağırıp ekrana basan ince kabuktur.
Arşiv ve Çöp Kutusu da ayrı modül değildir — her modül kendi öğesinin durumunu (`active` →
`archived` → `trashed`) kendi tutar; "Etiketler & Arşiv" ekranı bu facade'lerden derlenir.

## Communication rules
- Modüller arası iletişim **yalnızca senkron facade çağrısıyla**: `app.modules.<m>.public`.
- `ui` yalnızca `public` facade'lerini çağırır; SQL, iş kuralı ve hesaplama içermez.
- Her modül yalnızca kendi tablolarını sorgular; başka modülün verisine referans **sadece ID** ile.
  Modüller arası JOIN yoktur — `tags` bağları da (`target_kind`, `target_id`) ile polimorfiktir,
  yabancı anahtarla başka modülün tablosuna bağlanmaz.
- Olay / mesaj kuyruğu yoktur; ihtiyaç doğarsa önce ADR yazılır.

## Forbidden dependencies (make them testable)
1–3, `tests/architecture_rules.py` içindeki genel kurallarla (grimp import grafı) `scripts/check`
içinde zorlanır: modül başı yapılandırma yoktur, yeni bir modül otomatik kapsanır. 4–6 review'da
kontrol edilir; 5'in import ayağı spec 0002'de teste bağlanır (yasak paket kümesi güncellenir).
1. Bir modül, başka bir modülün `public` dışındaki hiçbir alt paketini import etmez
   (`domain`, `service`, `repository`).
2. `app.modules.*.domain` şunları import etmez: `PySide6`, `sqlite3` ve her türlü ağ/IO paketi.
   Domain saati okumaz — "bugün" ve "şu an" parametre olarak verilir (import grafı çağrıyı
   göremez; bu kısım review'da kontrol edilir).
3. `app.shared` hiçbir `app.modules.*` paketini import etmez.
4. `app/ui` altında iş kuralı, hesaplama veya SQL bulunmaz; `ui` yalnızca `public` çağırır.
5. **Ürün kodu ağa çıkmaz.** Yasak: `fastapi`, `uvicorn`, `starlette`, `requests`, `httpx`,
   `urllib`, `socket` ve benzeri ağ yığını; ORM (`sqlalchemy`); telemetri/analitik ve bulut SDK'ları.
6. Çalışma anında ağdan varlık yüklenmez: font, ikon ve tema `app/resources/` içinde gömülüdür
   (tasarımdaki Tailwind/Google Fonts CDN bağımlılıkları yerelleştirilerek taşınır).

## Deliberately out of scope
- **Senkronizasyon, bulut hesabı, çoklu cihaz** — tasarımda görünen "Senkronize" öğeleri kapsam
  dışıdır ve arayüzden çıkarılır (bootstrap kararı, 2026-11-02). İstenirse önce ADR.
- Çok kullanıcılı / ekip özellikleri, paylaşım, yetkilendirme.
- Mobil uygulama ve web sürümü; macOS/Linux paketleme (çapraz platform yığın seçildi, yalnızca
  Windows'ta test edilir ve paketlenir).
- Takvim, e-posta ve bilet sistemi entegrasyonları (ağ yasağının doğal sonucu).
