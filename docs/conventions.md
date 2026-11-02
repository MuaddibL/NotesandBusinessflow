# Conventions

Buradaki her kural ya araçla zorlanır (tercih edilen) ya da review'da kontrol edilir.

## Language
<!-- Set at bootstrap (step 0) and mirrored in AGENTS.md. Changing it later is allowed — edit both
     places; existing documents are not translated retroactively. -->
- Chat language (interviews, sessions): Turkish (`tr`)
- Document language (docs/, specs, plans, ADRs, review and verify reports): Turkish (`tr`)
- Always English (protocol, not prose): ANEW core files, template headings and field labels,
  `Status:` values (Draft / Approved / In progress / Shipped), `Approved by / on:`, `Source:`.
- Code identifiers, branch names, commit messages: English (domain sözlüğündeki İngilizce
  karşılıklarla). Kullanıcıya görünen metinler (UI, hata başlık/açıklamaları) Türkçe.
- Agent messages (handoff summaries, refusals, `Next:` lines): chat language; command names, file
  paths and protocol fields verbatim.

## Language & framework versions
- Python 3.12 (`.python-version`, `requires-python = ">=3.12,<3.13"`), ortam ve kilit: **uv**
  (`uv.lock` commit edilir; check `--frozen` çalışır).
- Arayüz: **PySide6** (Qt Widgets + QSS). Qt Quick/QML kullanılmaz — tek bir arayüz teknolojisi.
- Veri: stdlib **`sqlite3`**, tek dosya. ORM yoktur (`docs/architecture.md`, yasak 5).
- Paketleme: PyInstaller, tek Windows çalıştırılabiliri. npm ve build adımı yoktur.

## Naming
- Python: PEP 8 — modül/fonksiyon/değişken `snake_case`, sınıf `PascalCase`, sabit `UPPER_CASE`.
- Domain tipleri sözlükteki İngilizce adlarla: `Task`, `DayPlan`, `TimeBlock`, `FocusSession`,
  `Note`, `Project`, `Tag`.
- Hata sınıfları `<Neden>Error` (`OverlappingTimeBlockError`), hepsi `DomainError` alt sınıfı.
- Qt widget alanları `_` önekiyle örnek değişkeni, sinyal slotları `_on_<nesne>_<olay>`.
- Testler: dosya `test_<davranış>.py`, fonksiyon `test_<ne>_<koşul>_<beklenen>`; BR testinin adı
  veya docstring'i kuralı anar (`BR-1`).
- Tablo adları çoğul `snake_case` (`tasks`, `time_blocks`); sütunlar `snake_case`.
- Branch ve commit: `docs/git.md`.

## Error handling
- İş kuralı ihlali → `app.shared` içindeki `DomainError` alt sınıfı fırlatılır (`code` taşır,
  makine okunur ve İngilizce).
- `sqlite3` hataları `repository` sınırında sarmalanır; `sqlite3` tipleri modül dışına sızmaz.
- `ui` katmanı `DomainError`'ı yakalar ve kullanıcıya Türkçe başlık + açıklama gösterir; tek bir
  yardımcı (`show_problem`) kullanılır, her yerde ayrı diyalog kurulmaz.
- Beklenmeyen hata → korelasyon ID'li log kaydı + kullanıcıya genel mesaj. Stack trace, SQL, dosya
  yolu ve kullanıcı içeriği kullanıcıya **asla** gösterilmez (`docs/security.md`).
- Uygulama, veritabanı açılamadığında sessizce boş başlamaz: açık bir hata ekranı gösterir.

## Data rules
- Takvim günü `datetime.date`, zaman bloğu saatleri `datetime.time` — **yerel saat**; 09:00 her
  zaman 09:00'dır, saat dilimi değişse de geçmiş plan saatleri kaymaz (bootstrap kararı, 2026-11-02).
- Oluşturma / değiştirme damgaları UTC, timezone-aware `datetime` (`DTZ` kuralı zorlar).
- Süreler tam sayı **dakika** (`int`) — asla float. Sayaçlar saniye cinsinden `int`.
- ID'ler UUID v4, veritabanında metin.
- Silme yok: `active` → `archived` → `trashed`; kalıcı silme ayrı ve açık eylem (BR-3, BR-4).
- Şema sürümü `PRAGMA user_version` ile yönetilir. Her geçiş ileri yönlü ve idempotent; geçişten
  önce veritabanı dosyasının yedeği alınır. Geçiş atlanmaz, sürümler sırayla uygulanır.
- Kullanıcı içeriği (not metni, görev başlığı, proje adı) loglara yazılmaz; loglarda yalnızca ID.

## UI conventions
- Arayüz tasarımının kaynağı: `docs/design/` (bkz. oradaki `README.md`). Renk, tipografi ve boşluk
  değerleri tasarımdaki **Material 3 belirteç seti**dir; bunlar tek bir QSS tema dosyasına çevrilir.
  Widget'ların içine doğrudan renk veya piksel değeri yazılmaz — her değer bir belirteçten gelir.
- Varsayılan tema koyudur.
- Fontlar (Inter, JetBrains Mono) ve ikonlar uygulamayla birlikte `app/resources/` içinde gömülür;
  çalışma anında ağdan yüklenmez (`docs/architecture.md`, yasak 6).
- `ui` ince kabuktur: iş kuralı, hesaplama ve SQL içermez (yasak 4).
- Kullanıcıya görünen her metin Türkçe; tarih ve saat biçimi yerel.

## Enforced by tooling
- `ruff check` — pyflakes, pycodestyle, isort, bugbear, pyupgrade, bandit (`S`), naive datetime
  yasağı (`DTZ`), simplify, ruff kuralları. `ruff format --check` — biçim.
- `mypy --strict` — `app/` için tam tip denetimi.
- Mimari test (`tests/architecture_rules.py`, grimp) — `docs/architecture.md` "Forbidden
  dependencies" 1–3 ve 5; `pytest` adımında koşar. Ağ ve ORM yasağı gerçek import grafında da
  doğrulanır.
- `uv lock --check` — `uv.lock` `pyproject.toml` ile tutarlı.
- Hepsi `scripts/check` içinde (`scripts/check.conf`).
