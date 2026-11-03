# Review 0002 — desktop shell

- Spec: `specs/active/0002-desktop-shell.md`
- Plan: `specs/plans/0002-plan.md`
- Change set: `git diff main..HEAD` (`feature/0002-desktop-shell`, `0581f1c..3d1d848`; 48 dosya, +2170/-1106)
- Reviewed by / on: bağımsız salt-okunur reviewer oturumu, 2026-11-03
- Status: Fix round #2 in progress (2026-11-03) — re-review done, triaged, no third review round

Bu dosya bir plan değildir (`scripts/doctor` yalnızca `NNNN-plan.md` dosyalarını okur). REVIEW
segmentinin handoff'u olarak durur; VERIFY ve PR açıklaması buradan beslenir.

## Verification run (reviewer's own)

`./scripts/check` → `CHECK GREEN (full, 6 steps, 9 s)`; `test-unit-integration` 37 passed /
8 deselected, `test-ui` 8 passed / 37 deselected. 37 + 8 = 45 = toplam → **PB-1 sağlanıyor.**
(Ana oturumun aynı gün koşumu: `CHECK GREEN (full, 6 steps, 11 s)`, aynı sayılar.)

## Verdict

Temiz değil — 2 High, 3 Medium, 1 Medium-Low, 4 Low, 1 Info. Kriterlerin çoğu gerçekten
karşılanmış; boşluklar ağırlıklı olarak **uygulama girişinin (`app/__main__.py`) kanıtsız olması**
ve **log hedefinin hiç kurulmamış olması** etrafında toplanıyor. Security ve Performance boyutları
clean.

## Triage

Triage: MuaddibL, 2026-11-03. Reviewer'ın sınıflandırması kanıtlıydı ve tersini savunacak bir
temel çıkmadı, bu yüzden olduğu gibi kabul edildi. Son kolon reviewer'ın önerisidir; karar
`Triage` kolonudur.

| # | Severity | Dimension | Konu | Triage | Reviewer's proposal |
|---|---|---|---|---|---|
| F-1 | HIGH | Correctness + Tests | Korelasyon kimliği hiçbir yere yazılmıyor (CB-7, PB-5) | **real** — bu PR | real, bu PR |
| F-2 | HIGH | Tests + Correctness | `app/__main__.py` hiç test edilmiyor (CB-1/CB-6/CB-7) | **real** — bu PR | real, bu PR |
| F-3 | MEDIUM | Edge cases | Şema geçişi atomik değil, başarısız geçiş testsiz (CB-4) | **investigate** — önce gözlem | investigate (R-05) |
| F-4 | MEDIUM | Correctness (a11y) + Tests | Klavye gezinimi ve odak görünürlüğü ne uygulandı ne haritalandı | **real** — bu PR | real, bu PR |
| F-5 | MEDIUM | Plan conformance / process | Silinecek kod, spec ve plan doğmadan önce silinmiş | **real (process)** — docs kararı insana soruldu | real (process), docs kararı |
| F-6 | MEDIUM-LOW | Tests | İki test adının iddia ettiğini kanıtlamıyor | **real** — bu PR | real, bu PR |
| F-7 | LOW | Maintainability | `StorageError` mesajı kullanıcıya ulaşmıyor, yolu testsiz | **real** — bu PR | real, ucuz |
| F-8 | LOW | Maintainability (a11y) | `TEXT_PAIRS` ile stylesheet arasında zorlayıcı bağ yok | **real** — bu PR | real, ucuz |
| F-9 | LOW | Maintainability | `docs/conventions.md` Qt adlandırma kuralı ihlal ediliyor | **real** — docs kararı insana soruldu | real, docs kararı |
| F-10 | LOW | Plan conformance (R-07) | Plan listesi dışında bir dosya değişti (`docs/conventions.md`) | **real** — bu PR | real, ucuz |
| F-11 | INFO | Docs/code tension | `app/resources/` yok, iki doküman var sayıyor | **noise** — plan R-3'te zaten kayıtlı, aksiyon yok | noise, aksiyon yok |

Fix round (`prompts/build.md` §fixes): bulgu başına tek commit, `[review 0002/F-n]` referansıyla;
her commit sonrası `--fast` yeşil, fix diff'i review'a dönmeden önce full yeşil.

## Fix round — ne yapıldı

| # | Commit | Ne değişti |
|---|---|---|
| F-1 | `6d0bdc7` | `configure_logging`: veri dizinine tek dosya handler'ı, formatta `correlation_id`, alanı garantileyen filtre. Kayıt artık gerçekten okunabilir. |
| F-2 | `28c2790` | `main()` yolları ve kutu gösterimini parametre alıyor, excepthook adlandırılmış fonksiyon. `tests/ui/test_entry_point.py` ile 3 test. |
| F-4 | `9f3b7ad` | Açılışta odak kenar menüsüne veriliyor (önce hiçbir yerde değildi, ok tuşları tıklamadan çalışmıyordu) + 3 test. |
| F-6 | `1f72f79` | Test adı iddiasına indirildi; `test_dialog_hides_exception_details` kimlik eşitliğini doğrudan doğruluyor. |
| F-7 | `f6bf2f7` | `SchemaTooNewError` kendi Türkçe metniyle; reddetme yolunun testi. |
| F-8 | `55fc974` | Eksik çiftler ve dekoratif renkler bildirildi; "stylesheet'in çizdiği her renk denetlenmiştir" testi. |
| F-3 | `02307aa` | Geçiş adımı başına açık transaction + rollback. **Gözlem bulguyu ağırlaştırdı:** yarıda kalan geçiş dosyayı kalıcı açılamaz bırakıyordu. |
| F-10 | `c21c68b` | Plan dosya listesi diff ile hizalandı (tarihli notlarla). |
| F-5 | — | Kod değişmedi. `workflows/bootstrap.md`'ye "bootstrap ürün kodu silmez" kuralı eklendi; sapma PR açıklamasına yazılacak (aşağıda). |
| F-9 | — | `docs/conventions.md` koda uyduruldu: testlerin okuduğu widget alanları öneksiz; `show_problem` adı fiilî API ile hizalandı. |
| F-11 | — | Noise; aksiyon yok. |

**F-4'te reviewer'ın önerisinden sapıldı.** Reviewer `QListWidget#sections::item:focus` için bir
QSS kuralı önermişti; o kural yazılmadı çünkü Qt onu yok sayıyor. Ölçümün tam hali aşağıda,
"Fix round #2" bölümünde (F-R1): ilk yazdığım gerekçe fazlasını iddia ediyordu ve 2026-11-03'te
düzeltildi.

## Pull request'e yazılacak (F-5)

0002'nin sileceği 12 kod/test dosyası, spec ve plan var olmadan önce `4081853`
("docs: reposition the workspace for Notes&MJ") ile silindi — AGENTS.md invariant 1 ve 2'nin
ihlali, ve `docs:` tipiyle plan referanssız bir commit (`docs/git.md`). Üründe kalıcı kusur yok:
HEAD'de sonuç planın hedeflediği yer. Geri alınmadı, çünkü revert + yeniden commit net zarardı.
Tekrarı `workflows/bootstrap.md`'ye eklenen kuralla kapatıldı.

## Findings

Aşağısı reviewer'ın raporudur, kelimesi kelimesine; yumuşatılmadı, kısaltılmadı.

---

### F-1 · HIGH · Correctness + Tests — korelasyon kimliği hiçbir yere yazılmıyor (CB-7, PB-5)

**Evidence:**
- `C:\Projeler\notesandbusinessflow\app\shared\logging.py:13` — `_LOGGER = logging.getLogger("notes_mj")`
- `C:\Projeler\notesandbusinessflow\app\shared\logging.py:19-23` — `extra={"correlation_id": correlation_id}`
- Uygulamanın hiçbir yerinde handler/formatter/log hedefi yok:
  `rg -n "basicConfig|addHandler|Formatter|FileHandler" app/` → yalnızca `logging.py:13`'teki
  `getLogger` eşleşiyor, yapılandırma yok.

**Impact:** Gerçek çalıştırmada `notes_mj` logger'ının handler'ı olmadığı için kayıt
`logging.lastResort`'a düşer: stderr'e yalnızca `"unexpected error"` + yığın izi basılır ve
**`correlation_id` hiçbir çıktıda görünmez** (varsayılan formatter `%(message)s`'tir, `extra`
alanlarını render etmez). Pencereli bir Qt uygulamasında (ileride `pythonw`/PyInstaller `--windowed`)
stderr de yoktur → hiç kayıt kalmaz. CB-7'nin sözü olan "diyalogdaki kimlik, log kaydındaki kimliğin
**aynısıdır**" kullanıcı için işletilemez; PB-5'in "loga yazılır" ifadesi yalnızca `caplog` ile,
yani test altyapısının kendi handler'ıyla kanıtlanmış durumda
(`tests/unit/test_error_logging.py:17-24`, `record.correlation_id` attribute'u üzerinden).

**Recommended action (benim önerim):** `app/__main__.py` içinde, veri dizinine yazan tek bir
handler + `correlation_id`'yi içeren bir format kurmak (ör. `%(asctime)s %(levelname)s
%(correlation_id)s %(message)s`, `logging.Filter` ile alanı garanti altına alarak) ve testi
"formatlanmış çıktıda kimlik var" düzeyine çıkarmak. Alternatif (daha ucuz ama zayıf): log hedefini
spec'te açıkça kapsam dışı ilan etmek — bu bir spec değişikliğidir (R-08) ve CB-7'nin "aynı kimlik"
vaadini anlamsızlaştırdığı için **önermiyorum**.

---

### F-2 · HIGH · Tests + Correctness — `app/__main__.py` hiç test edilmiyor; CB-1/CB-6/CB-7'nin uygulama ayağı kanıtsız

**Evidence:**
- `C:\Projeler\notesandbusinessflow\app\__main__.py:18-37` — `main()`: QApplication, tema,
  `open_database`, `StorageError` → `storage_error_box(...).exec()`, `sys.excepthook` kurulumu,
  `MainWindow(on_close=connection.close)`.
- Hiçbir test bu modülü import etmiyor:
  `rg -n "app.__main__|from app import" tests/` → eşleşme yok;
  `rg -n "report_unexpected|excepthook" --include=*.py .` çıktısında `app/__main__.py` dışında
  ürün tarafı yok.
- Testler bileşenleri **doğrudan** kuruyor: `tests/ui/test_main_window.py:12` (`MainWindow()`),
  `tests/ui/test_error_paths.py:23` (`storage_error_box(...)`), `:32` (`unexpected_error_box(...)`).

**Impact:** CB-1 "belgelenen tek komut çalıştırıldığında bir pencere açılır", CB-6 "uygulama
sessizce boş başlamaz" ve CB-7 "beklenmeyen hata bir diyalogla gösterilir" — üçü de *kutuların
metni doğru* düzeyinde kanıtlanmış, *uygulamanın onları gerçekten gösterdiği* düzeyinde değil.
`sys.excepthook` ataması (`app/__main__.py:33`) özellikle kırılgan: PySide6'da bir slot içinden
yükselen istisnanın excepthook'a ulaşıp ulaşmadığı ve excepthook içinde `exec()` ile iç içe olay
döngüsü açmanın davranışı sürüme bağlıdır; hiçbir test bu yolu yürütmüyor. Bugün yeşil olan ağaç
bu üç kriter için yanlış güven veriyor.

**Recommended action:** `main()`'i enjekte edilebilir hale getirmek (veritabanı yolu ve
`QApplication` parametre olarak) ve `tests/ui/` altına iki test eklemek: (a) açılamayan veri
dosyasıyla `main()` çağrıldığında pencere **açılmaz**, hata kutusu kurulur ve dönüş kodu 1'dir;
(b) kurulu excepthook tetiklendiğinde `report_unexpected` çağrılır ve kutudaki kimlik log
kaydındakiyle aynıdır (F-6 ile birlikte çözülür). Bu, R-05 anlamında "investigate" değil, doğrudan
eksik kanıt.

---

### F-3 · MEDIUM · Edge cases — şema geçişi atomik değil; başarısız geçişin testi yok (CB-4)

**Evidence:** `C:\Projeler\notesandbusinessflow\app\shared\db.py:65-68`

```python
for index in range(current, target):
    migrations[index](connection)
    _set_schema_version(connection, index + 1)
connection.commit()
```

Açık bir transaction sınırı yok. Python 3.12 `sqlite3` varsayılanında (`isolation_level=""`)
implicit BEGIN yalnızca DML için atılır; `CREATE TABLE`/`ALTER TABLE` gibi DDL autocommit'te
çalışır. Dolayısıyla çok adımlı bir geçişte 2. adım patlarsa 1. adımın DDL'i dosyada kalır,
`user_version` ise adımla aynı transaction'da olmayabilir. `tests/integration/test_migrations.py`
yalnızca başarılı yolları kuruyor — "geçiş ortasında hata" senaryosu hiç yok.

**Impact:** CB-4'ün "geçiş ileri taşınır ve veri korunur" sözü, başarısızlık durumunda içeriği
sürümüyle tutarsız bir dosya bırakabilir. CB-5'in yedeği kurtarma yolunu açık tutuyor, bu yüzden
veri kaybı değil, **tutarsız durum** riski.

**Recommended action:** Her geçiş adımını açık transaction'a sarmak (`with connection:` ya da
`BEGIN`/`COMMIT`) ve `test_migrations.py`'ye "ikinci geçiş `RuntimeError` atıyor → dosya hâlâ
sürüm 1 ve eski içerikte" testini eklemek. Önerim: adım başına transaction — tüm geçişi tek
transaction'a almak büyük dosyalarda kilit süresini uzatır ve SQLite'ta DDL sonrası geri alma
davranışı adım bazında daha okunabilirdir.

---

### F-4 · MEDIUM · Correctness (UI/accessibility) + Tests — klavye gezinimi ve odak görünürlüğü ne uygulandı ne haritalandı

**Evidence:**
- Spec, `specs/active/0002-desktop-shell.md:88-89`: "kenar menüsünde klavyeyle (Tab/ok tuşları)
  gezinilebilir ve **odaklanan öğe görsel olarak bellidir**".
- Plan kriter↔test haritası, `specs/plans/0002-plan.md:120`: "Erişilebilirlik (UX)" satırı
  **yalnızca** `test_theme_contrast.py::test_every_text_surface_pair_meets_wcag_aa`'ya bağlı.
- QSS'te `:focus` ya da odak göstergesi için hiçbir kural yok:
  `C:\Projeler\notesandbusinessflow\app\ui\theme.py:37-46` — yalnızca `::item` ve `::item:selected`.
  Seçili öğe `surface-container-high` ile boyanıyor; **klavye odağı ile seçim** arasında görsel
  ayrım tanımlanmamış.
- `tests/ui/test_main_window.py` içinde `qtbot.keyClick` / `setFocus` / `focusPolicy` geçmiyor.

**Impact:** Spec'in "User experience / Erişilebilirlik" fıkrasının yarısı kanıtsız. Qt'nin
varsayılanı muhtemelen işi görüyor (QListWidget `StrongFocus`, ok tuşlarıyla gezinir), ama QSS ile
`::item` boyandığında odak çerçevesinin görünürlüğü stile bağlıdır ve burada hiç ele alınmamış.
DoD'deki "Criterion ↔ evidence table complete" bu haliyle tamamlanamaz.

**Recommended action:** (1) `theme.py`'ye `QListWidget#sections::item:focus` için belirteçten gelen
görünür bir çerçeve eklemek ve o çift de `TEXT_PAIRS`'a girmeli; (2) `tests/ui/test_main_window.py`'ye
`qtbot.keyClick(window.sections, Qt.Key_Down)` ile currentRow'un ilerlediğini ve
`sections.focusPolicy()`'nin klavyeyi kabul ettiğini doğrulayan bir test; (3) plan haritasına
"Erişilebilirlik (UX) — klavye" satırını eklemek. (Odak görünürlüğü için ekran görüntüsü DoD gereği
PR'a eklenmeli.)

---

### F-5 · MEDIUM · Plan conformance / process — 0002'nin sileceği kod, spec ve plan var olmadan **önce** silinmiş

**Evidence:**
```
git log --oneline --diff-filter=D --name-status main..HEAD -- app tests
4081853 docs: reposition the workspace for Notes&MJ
D app/health.py  D app/main.py  D app/shared/http.py  D app/static/index.html
D app/static/styles.css  D tests/e2e/conftest.py  D tests/e2e/test_landing_page.py
D tests/integration/conftest.py  D tests/integration/test_errors.py
D tests/integration/test_health.py  D tests/integration/test_security_headers.py
D tests/unit/test_run_settings.py
```
`4081853` → `bbc3d19` ("docs(spec): add spec 0002 ... and its approved plan") sıralaması, yani
**silme commit'i spec'ten öncedir**. Ayrıca `git show 4081853:app/__main__.py` hâlâ
`uvicorn.run("app.main:app", ...)` çağırıyor — o commit'te uygulama çalıştırılamaz durumdaydı.
Planın 1. adımı ("Yukarıdaki silme listesi... Ağaç yeşil kalır",
`specs/plans/0002-plan.md:56-58`) karşılığı olan `0581f1c` ise yalnızca 6 dosya değiştirmiş
(`git show --stat 0581f1c`), silme listesini **uygulamamış** çünkü iş zaten yapılmıştı.

**Impact:** AGENTS.md invariant 1 ("No spec, no code") ve 2 ("Plan before build") ihlali; ayrıca
12 kod/test dosyası silen bir commit `docs:` tipiyle ve plan referansı olmadan atılmış
(`docs/git.md:13`, Conventional Commits + plan referansı). Üründe kalıcı bir kusur bırakmıyor —
HEAD'de sonuç planın hedeflediği yer — ama planın 1. adımı denetlenebilir olmaktan çıkıyor ve
"ağaç her commit'te yeşil" güvencesi bu aralıkta geçerli değil.

**Recommended action:** Kod değişikliğini düzeltmek için bir şey yapmaya gerek yok (geri alıp
yeniden commit'lemek net zarar). Önerim: PR açıklamasına bu sapmayı ve nedenini (bootstrap yeniden
konumlandırma turu) yazmak, ve bootstrap/yeniden konumlandırma akışına "kod dosyası silmez; silme
ilk spec'in planına yazılır" kuralını eklemek. İnsan triage'ı bunu "real (process)" veya "accepted,
bootstrap artefaktı" olarak işaretlemeli.

---

### F-6 · MEDIUM-LOW · Tests — iki test adının iddia ettiğini kanıtlamıyor

**Evidence:**
1. `C:\Projeler\notesandbusinessflow\tests\unit\test_error_logging.py:34-41` —
   `test_log_record_excludes_user_content`: `_boom("gizli not metni")` ile üretilen istisnanın
   metni `exc_info` üzerinden kayda **girer**; test yalnızca `record.getMessage()` ve `record.args`
   kontrol ediyor, `"gizli not metni"` ifadesinin kaydın formatlanmış çıktısında olmadığını hiç
   iddia etmiyor (ve olmadığı da doğru değil).
2. `C:\Projeler\notesandbusinessflow\tests\ui\test_error_paths.py:39` —
   `def test_dialog_hides_exception_details(qtbot, caplog: pytest.LogCaptureFixture)`: `caplog`
   fixture'ı alınmış ama gövdede **hiç kullanılmamış**. CB-7'nin özü olan "diyalogdaki kimlik =
   log kaydındaki kimlik" eşitliği hiçbir tek testte uçtan uca kurulmuyor; iki ayrı testin
   transitifliğine bırakılmış.

**Impact:** (1) için: spec PB-5 "yığın izi dışında ... kullanıcı içeriği bulunmaz" diyerek yığın
izine muafiyet tanıyor, dolayısıyla davranış **spec'e uygun**; sorun testin adının daha fazlasını
vaat etmesi — ileride biri bu teste güvenip gerçek bir sızıntıyı kaçırabilir. Ayrıca
`docs/security.md`'deki "Kullanıcı içeriği loglara yazılmaz; loglarda yalnızca ID, olay adı ve
korelasyon ID'si bulunur" ifadesi bu muafiyeti **içermiyor** → docs ile spec arasında küçük bir
gerilim var. (2) için: CB-7'nin "aynısıdır" ifadesi için doğrudan kanıt yok.

**Recommended action:** (1) testi `test_log_message_has_no_interpolated_content` olarak adlandırmak
**ve** `docs/security.md`'ye yığın izi muafiyetini bir cümleyle yazmak (hangi yazının doğru olduğuna
insan karar vermeli — benim önerim muafiyeti docs'a yazmak, çünkü yığın izini atmak hata ayıklamayı
imkânsız kılar). (2) `test_dialog_hides_exception_details` içinde `caplog` ile
`caplog.records[-1].correlation_id == correlation_id and correlation_id in box.informativeText()`
iddiasını eklemek — fixture zaten orada duruyor.

---

### F-7 · LOW · Maintainability — `StorageError`'a geçirilen mesaj kullanıcıya hiç ulaşmıyor, yolu test edilmiyor

**Evidence:**
- `C:\Projeler\notesandbusinessflow\app\shared\db.py:59-62`:
  `raise StorageError("Veri dosyası, bu sürümün tanıdığından daha yeni bir şema sürümü taşıyor.")`
- `C:\Projeler\notesandbusinessflow\app\ui\error_dialog.py:37-39`: kutu `error.title` ve
  `error.detail` **sınıf özniteliklerini** gösterir; `Exception.args` hiç okunmaz.
- `current > target` dalı için `tests/integration/test_migrations.py` içinde test yok.

**Impact:** "Gelecekten gelen" bir veri dosyasıyla karşılaşan kullanıcı, gerçek nedeni ("dosya daha
yeni bir sürümden") değil, genel "dosya bozuk olabilir veya yazma izni olmayabilir" metnini görür.
Ölü bir string ve yanıltıcı bir kullanıcı mesajı. Yeni bir kriter değil, CB-6'nın "ne olduğunu
Türkçe anlatan açık bir hata ekranı" sözüne ters düşen bir kenar durumu.

**Recommended action:** Ya ayrı bir `SchemaTooNewError(StorageError)` (kendi `detail`'iyle) tanımlayıp
ona geçmek, ya da mesaj argümanını kaldırmak. Önerim: ayrı alt sınıf + `test_migrations.py`'ye
"sürüm 2 dosya, 1 geçişli koşucuyla açılınca StorageError ve dosya değişmemiş" testi.

---

### F-8 · LOW · Maintainability (accessibility) — `TEXT_PAIRS` ile gerçek stylesheet arasında zorlayıcı bir bağ yok

**Evidence:**
- `C:\Projeler\notesandbusinessflow\app\ui\tokens.py:67-69` yorumu: "The foreground/background token
  pairs the interface **actually** puts together ... a new pairing in the stylesheet belongs here
  too, or it goes unchecked."
- Ama `C:\Projeler\notesandbusinessflow\app\ui\theme.py:13` genel yüzey olarak `background`
  belirtecini kullanıyor ve `background` hiçbir çiftte geçmiyor (`tokens.py:70-80`). Bugün
  `background` ve `surface` aynı değere sahip (`#0b1326`, `tokens.py:13-14`), bu yüzden test yeşil —
  ama biri `background`'ı değiştirirse boş durum metinlerinin kontrastı **sessizce** denetim dışı
  kalır.
- Ters yönde: `("on-primary-container", "primary-container")` ve `("error", "surface")`,
  `("on-error-container", "error-container")` çiftleri stylesheet'te hiç kullanılmıyor → yorumun
  "actually" iddiası bugün bile doğru değil.

**Impact:** Erişilebilirlik kanıtı elle bakımda kalan bir listeye bağlı; yorum bunu otomatik
sanmaya davet ediyor.

**Recommended action:** `tests/unit/test_theme_contrast.py`'ye "`stylesheet()` içinde geçen her renk
değeri, denetlenen bir çiftte yer alır" testi eklemek (QSS'ten hex'leri regex ile toplayıp
`TEXT_PAIRS`'ın kapsadığı küme ile karşılaştırmak). Tek satırlık alternatif: `background`'ı
`TEXT_PAIRS`'a eklemek — ucuz ama drift'i çözmez.

---

### F-9 · LOW · Maintainability — `docs/conventions.md`'deki Qt adlandırma kuralı ihlal ediliyor

**Evidence:**
- `C:\Projeler\notesandbusinessflow\docs\conventions.md:29`: "Qt widget alanları `_` önekiyle örnek
  değişkeni, sinyal slotları `_on_<nesne>_<olay>`."
- `C:\Projeler\notesandbusinessflow\app\ui\main_window.py:61,67,79`: `self.brand`, `self.sections`,
  `self.pages` — önek yok. (`self._on_close`, `main_window.py:58`, kurala uyuyor.) Testler bu
  alanlara doğrudan eriştiği için (`tests/ui/test_main_window.py:16,25,42`) seçim bilinçli görünüyor.
- İlgili ikinci küçük sapma: `docs/conventions.md:40` tek yardımcının adını `show_problem` olarak
  yazıyor; uygulama iki ayrı kurucu sunuyor (`app/ui/error_dialog.py:27,37`).

**Impact:** Araçla zorlanmayan, review'da kontrol edilen bir kural; bugün tek ekranda zararsız ama
ikinci ekranla birlikte tutarsızlık yayılır. Not: `docs/conventions.md` bu kuralı **bu değişiklik
kümesinde** kazandı, yani kural ile ilk uygulaması aynı anda doğdu ve uyuşmuyor.

**Recommended action:** Kuralı koda uydurmak yerine kodu kurala uydurmak daha pahalı (testler
erişiyor). Önerim: `docs/conventions.md:29`'u "testlerin okuduğu widget alanları önek almaz, iç
alanlar `_` alır" diye netleştirmek ve `:40`'taki `show_problem` adını fiilen kullanılan API ile
hizalamak — her ikisi de insan onayı gerektiren bir docs düzeltmesidir, kod değişikliği değil.

---

### F-10 · LOW · Plan conformance (R-07) — plan dosya listesi dışında bir dosya değişti

**Evidence:** Planın 7. adımı (`specs/plans/0002-plan.md:69-70`) ve dosya listesi
(`:35`) yalnızca `README.md`, `AGENTS.md`, `docs/architecture.md` ve `scripts/check.conf`'u anıyor.
`git show --stat 3d1d848` → `AGENTS.md`, `README.md`, `docs/architecture.md`, **`docs/conventions.md`**.
Değişiklik iki satırlık, aynı türden bir geçiş notu temizliği
(`git diff 0581f1c~1..HEAD -- docs/conventions.md`).

**Impact:** İhmal edilebilir; ama R-07 gereği her liste dışı dosya bir bulgudur ve plan, 1. adımda
`test_architecture_boundaries.py` eklenirken usulünce güncellenmişti (`:30`) — burada aynı titizlik
gösterilmemiş.

**Recommended action:** `specs/plans/0002-plan.md`'nin 7. adım satırına `docs/conventions.md`'yi,
1. adımdaki gibi tarihli bir not düşerek eklemek.

---

### F-11 · INFO · Docs/code tension — `app/resources/` yok, ama iki doküman var sayıyor

**Evidence:** `docs/architecture.md:29` (paket düzeninde `resources/`), `docs/architecture.md:69`
(yasak 6: "font, ikon ve tema `app/resources/` içinde gömülüdür"), `docs/conventions.md:61`
(Inter / JetBrains Mono gömülür). Dizin yok; `app/ui/tokens.py:4-5` sistem fontuna düştüğünü yazıyor.

**Impact:** Yok — plan bunu R-3'te (`specs/plans/0002-plan.md:86-91`) önceden bildirmiş ve ilk ekran
spec'ine ertelemiş; hiçbir 0002 kriteri font gerektirmiyor, ağ yasağı da delinmiyor. **Sapma
değildir**, yalnızca açık bir kalem.

**Recommended action:** Aksiyon gerekmez. İstenirse `docs/conventions.md:61`'e "(ilk ekran spec'ine
kadar sistem fontu)" şerhi.

---

## Dimension summary

| Dimension | Sonuç |
|---|---|
| **Correctness** | F-1, F-2, F-4, F-7. CB-2, CB-3, CB-4 (başarılı yol), CB-5, CB-8 ve PB-1/PB-2/PB-4 gerçekten karşılanıyor ve davranış düzeyinde test ediliyor. |
| **Plan conformance** | F-5 (ciddi, süreç), F-10 (önemsiz). Silme/değiştirme/ekleme listesinin **içeriği** HEAD'de birebir tutuyor; sapma sıralamada ve iki dosyada. |
| **Security** | **Clean.** Parametresiz SQL yok; tek interpolasyon `app/shared/db.py:36-39`, `int()` ile zorlanmış kendi geçiş indeksi ve yorumla gerekçelendirilmiş — kabul edilebilir. Hata kutuları yol/istisna metni taşımıyor (`tests/ui/test_error_paths.py:28,48-50` davranışla kanıtlıyor). `rg -i "fastapi\|uvicorn\|playwright\|httpx\|PLM_" app/ docs/ scripts/ README.md AGENTS.md` → ürün tarafında kalıntı yok; ağ yasağı gerçek import grafında da doğrulanıyor (`tests/integration/test_architecture_boundaries.py:15-18`). Tek açık uç F-6'daki docs/spec gerilimi. |
| **Edge cases** | F-3 (atomik olmayan geçiş). Ayrıca testlenmemiş ama spec dışı kalan iki durum — aynı dosyayı açan iki eşzamanlı örnek için kilit/WAL yok, ve aynı gün aynı sürümden ikinci bir yedek aynı adı ezer (`app/shared/db.py:42-44`); spec yedek temizliğini açıkça kapsam dışı bıraktığı için **bulgu saymıyorum**. CB-6'nın "yazma izni yok" ayağı yalnızca "dosya yerine dizin" senaryosuyla test ediliyor (`tests/integration/test_db_lifecycle.py:39-47`) — Windows'ta salt-okunur dosya yolu kanıtsız, düşük öncelikli. |
| **Performance** | **Clean.** Ölçüm: `test-unit-integration` 0.53 s, `test-ui` 0.16 s, tüm check 9 s. N+1 ya da gereksiz materyalizasyon yok. Not (iddia değil, ölçülmüş etkisi sıfır): `tests/integration/test_architecture_boundaries.py:12,17` grimp grafını iki kez kuruyor ve `tests/architecture_rules.py:114-120` `_imports()`'u dört kez sıralıyor — süre büyürse ilk bakılacak yer burası (R-12). |
| **Tests** | Kriter↔test haritasındaki **18 testin 18'i mevcut ve adları birebir tutuyor** (kontrol ettim). Testler davranış iddia ediyor, durum kodu değil (ör. `test_backup_written_before_upgrading_existing_file` yedeği açıp içeriğini doğruluyor; `test_second_run_reuses_existing_file` marker satırı okuyor). Boşluklar: F-2 (girişin hiç test edilmemesi), F-4 (klavye ayağı haritada yok), F-6 (iki testin adı/kapsamı). |
| **Maintainability** | F-7, F-8, F-9, F-11. Katman ihlali yok: `app/ui` SQL/iş kuralı içermiyor, `app/shared` hiçbir modülü import etmiyor (gerçek grafta doğrulanıyor). Ölü kod yok; eski yığından kalıntı yok. `app/ui/tokens.py` belirteçleri tasarımdaki `tailwind.config` değerleriyle birebir eşleşiyor (karşılaştırdım). Küçük tasarım sapması: kenar çubuğu tasarımda `surface-container-low` + seçili öğe `primary-container`, uygulamada `surface-container` + `surface-container-high` (`app/ui/theme.py:19,44`) — spec yalnızca belirteç setini aldığı için ihlal saymıyorum, ileride tasarıma dönülürse hatırlanmalı. |

---

**Segment handoff — REVIEW (spec 0002)**
Next: human triage (real / noise / investigate) → düzeltmeler builder'a, "investigate" kalemler QA'ya.

---

# Fix round #1 review (2026-11-03)

Fix diff'in (`62e0164..HEAD`) bağımsız ikinci turu koşuldu. Reviewer kendi koşumu:
`CHECK GREEN (full, 6 steps, 7 s)`, 45 + 14 = 59 test, `-m ui` 5 ardışık koşumda yeşil (yeni
render testi flaky değil). Security ve Performance boyutları clean. Önceki turun 11 bulgusundan
7'si "kapandı", 3'ü "kısmen", 1'i noise olarak doğrulandı; 9 yeni kalem açıldı.

## Triage — fix round #1

Triage: MuaddibL, 2026-11-03, "A" seçeneği: aşağıdakiler düzeltilir, **üçüncü bir review turu
koşulmaz**, doğrudan VERIFY'a geçilir. Gerekçe: bu turun bulguları artık kayıt doğruluğu
seviyesinde; ürünü etkileyen bir kalem kalmadı.

| # | Severity | Konu | Triage |
|---|---|---|---|
| F-R1 | MEDIUM | Odak görünürlüğü test edilmiyor; F-4'ün gerekçesi fazlasını iddia ediyor | **real** — bu turda |
| F-R2 | MEDIUM-LOW | `open_database` sonrası açılış adımları korumasız: sessiz ölüm | **real** — bu turda |
| F-R3 | MEDIUM-LOW | Kriter↔test haritası bayat (VERIFY doğrudan buradan besleniyor) | **real** — bu turda |
| F-R4 | LOW | `docs/testing.md` ile `docs/security.md` yığın izi konusunda çelişiyor | **real** — ucuz |
| F-R5 | LOW | İki dosya yine plan listesi dışında | **real** — ucuz |
| F-R6 | LOW | `tokens.py` yorumu testin kanıtladığından fazlasını vaat ediyor | **real** — ucuz |
| F-R7 | LOW | `main([])` boş argv'yi sessizce `sys.argv` ile değiştiriyor | **real** — tek kelime |
| F-R8 | INFO | Açık transaction'lı bağlantıda `migrate()` patlar (bugün erişilemez) | **noise** |
| F-R9 | INFO | `main()` paylaşılan QApplication'ın stylesheet'ini değiştiriyor | **noise** |

## F-R1 — ölçümün tam hali

Reviewer, F-4'ün gerekçesini "yanlış ölçüme dayanıyor" diye işaretledi ve `::item:focus`'un
boyadığını gösteren bir komut verdi. **O komut burada tekrarlanmadı:** aynı komut, aktif pencere
ve odaklı widget ile (`active True hasFocus True`) `red pixels present: False` veriyor. Ayırt
edici ölçüm, kural **var** ve **yok** hâlleriyle aynı düzenekte:

```
without ::item:focus rule: active=True hasFocus=True -> focus changes pixels: True
with    ::item:focus rule: active=True hasFocus=True -> focus changes pixels: True
```

Sonuç ikiye ayrılıyor:

1. **`::item:focus` gerçekten ölü** — fark kuralın varlığından bağımsız ve birebir aynı. Kuralı
   yazmama kararı doğruydu; reviewer'ın bu yöndeki olgu iddiası tekrarlanmıyor.
2. **Ama odak yine de görünür** — Qt odaklı/odaksız seçimi kendisi farklı çiziyor. İlk ölçüm bunu
   kaçırmıştı, çünkü odaksız referans görüntüsü pencere aktive edilmeden önce alınmıştı. Bu
   yüzden "Qt odak için hiçbir şey boyamıyor" cümlesi yanlıştı ve kaldırıldı.

F-R1'in asıl sonucu bu düzeltmeyle ayakta kalıyor: odak görünürlüğü **ölçülebilir**, dolayısıyla
test edilebilirdi ve edilmemişti.

