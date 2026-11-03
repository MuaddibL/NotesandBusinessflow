# Testing

## The contract
- Every acceptance criterion maps to at least one test (criterion ↔ test map lives in the plan).
- Tests assert **behavior**, not implementation details or mere status codes.
- The whole suite runs inside `scripts/check` — one command, everywhere.

## Frameworks & layout
- **pytest** (`uv run --frozen pytest`), ayarlar `pyproject.toml` `[tool.pytest.ini_options]`.
- `tests/unit/` — domain kuralları; saf Python, DB/Qt/saat yok ("bugün" ve "şu an" parametre).
- `tests/integration/` — service + repository, **test başına geçici SQLite dosyası**; transaction
  davranışı ve şema geçişleri (`PRAGMA user_version`).
- `tests/ui/` — **pytest-qt** (`qtbot`), `QT_QPA_PLATFORM=offscreen` ile pencere açılmadan,
  `@pytest.mark.ui` ile işaretli. Kabuk ince olduğu için (`docs/architecture.md`, yasak 4) bu
  testler **azdır ve kalabalıklaşmamalıdır**: görünüm montajı, sinyal–slot bağları, hata gösterimi
  ve kritik akışın uçtan uca çalıştığı. İş kuralı buradan değil, `tests/unit/` üzerinden kanıtlanır.
- `QApplication` yaşam döngüsünün tek sahibi pytest-qt'dir; test sonunda açık pencere, zamanlayıcı
  veya olay döngüsü bırakılmaz (Resource hygiene).
- `tests/ui/` altındaki her test, conftest tarafından otomatik `ui` işaretlenir — işaret unutulsa
  da fast'e kaçamaz.
- Profil ayrımı seçiciyle: `--fast` → `pytest -m "not ui"`, full → ek olarak `pytest -m ui`.
- Adlandırma: `test_<davranış>.py`, `test_<ne>_<koşul>_<beklenen>` (`docs/conventions.md`).
- Coverage yüzdesi kapısı **yok**; güvence kabul kriteri ↔ test haritasından gelir.

## What must be tested
- Her iş kuralı **BR-n** en az bir birim testle, sınır değerleriyle: BR-1 devir sayacı ve gün
  sınırı, BR-5 tek etkin oturum, BR-6 blok çakışması (bitişik vs. örtüşen), BR-7 üçüncü/dördüncü
  odak, BR-8 büyük/küçük harf.
- Her yasak bağımlılık mimari testle (`tests/architecture_rules.py`; `docs/architecture.md`).
  **Ağ yasağı da testtir**: ürün kodunda ağ paketi importu bulunmadığı import grafından doğrulanır.
- **Şema geçişi**: eski `user_version`'lı bir veritabanından yenisine geçişte veri korunur; geçiş
  idempotenttir (iki kez çalıştırmak bozmaz).
- Silme ve arşiv geçişleri: `active → archived → trashed`, geri alma, ve kalıcı silmenin onay
  gerektirmesi (BR-3, BR-4).
- Hata yolu: `DomainError` kullanıcıya Türkçe gösterilir; stack trace, SQL, dosya yolu ve kullanıcı
  içeriği **arayüze** sızmaz. Loga yalnızca ID, olay adı, korelasyon ID'si ve beklenmeyen hataların
  yığın izi girer (`docs/security.md`, Veri ve gizlilik — yığın izi istisnası).
- Kritik akış ui testi: görev oluştur → odak oturumu başlat → nota bağla → gün sonunda devret.

## Protected-tests rule
Weakening asserts, deleting, or skipping tests to reach green is forbidden. A red test triggers
`prompts/recovery/red-test.md` (R-02) — first decide what is wrong: code, test, or spec.

## Characterization tests
Before refactoring untested code (`workflows/refactor.md`) and for brownfield change requests
(`workflows/change-request.md`, Preserved behavior), pin the current behavior first — warts
included. They are written from observation, not from what the code "should" do.

## Evidence for UI criteria
A screenshot is evidence for a UI criterion; for change requests, before/after screenshots that
also show the preserved behavior. Screenshots go into the PR, not the repo (Evidence policy).
A screenshot proves a criterion only against the spec's "User experience": every state it lists
(empty, loading, error, success), compared with the linked design. Bu projede tasarım bağı her
zaman vardır: `docs/design/` (bkz. oradaki `README.md`).

## Evidence policy
1. **Evidence is referenced, not stored.** Each acceptance criterion's evidence is a pointer: the
   test's name and the command that reproduces it (`./scripts/check`). The criterion ↔ evidence
   table in the spec/plan is the only evidence artifact that lives in the repo.
2. **Reproducible evidence is never filed.** No saved check output, console dumps, coverage reports
   or log copies in the repo — git history and CI runs already archive every execution.
3. **Non-reproducible evidence** (a screenshot of a manual UI check, a one-off measurement, an
   external-system confirmation) goes into the pull request (description or attachment); the
   evidence table links to it. It is the exception, not the rule.
4. **Never clone or copy the repository inside its own working tree.** Clean-clone verification
   runs in a temporary directory outside the repo; only the one-line result (command + green/red)
   is recorded in the evidence table. The clone is always deleted, never kept.
5. **There is no `evidence/` (or `.evidence/`) directory in this workspace.** An agent that feels
   the need to create one is about to violate rule 1. `scripts/doctor` warns on both violations.

## Resource hygiene
1. **A check run leaves nothing of its own running.** No survivor check started, of any kind:
   build/compile daemons, package-manager services, test hosts and parallel workers, watch modes,
   browsers, the application under test, containers or emulators started for the run. Agents run
   check an order of magnitude more often than humans; per-run residue compounds into machine
   starvation. Processes the operating system starts meanwhile are not check's and are not
   residue — the rule is about ownership, not about the machine's process count.
2. **The residue test** (the rule's definition, not advice): run `./scripts/check` twice back to
   back; after each run, no process check could have started is still alive, and memory has
   returned to the baseline measured before the first within the tolerance.
   `./scripts/residue` runs it (`--fast` for the fast profile). A process that appears while it
   measures and is still alive one settle period later is judged by its ancestry: one that
   descends from a root check cannot start under — the kernel thread parent on POSIX, the service
   control manager or System on Windows — is listed under its own heading with the reason and
   does not decide the result; everything else, **including anything whose ancestry cannot be
   walked**, is named with its command line and fails the run. Init (pid 1) is deliberately not
   such a root: an orphaned process of check's own is reparented to it. The ancestry is read
   after the fact, so a recycled pid can in principle place a survivor under an OS root; the
   window is seconds, and the alternative — counting every passing system process — is what made
   this test unreliable. Memory still reads best on an otherwise idle machine.
   Rerun it whenever `scripts/check.conf` changes.
3. Warm-process caches trade memory for speed for humans who build rarely; with an agent, trade the
   seconds back for a flat memory profile.
4. Interactive modes (watchers, dev servers, REPLs) never belong in check. UI tests run
   single-worker and offscreen (`QT_QPA_PLATFORM=offscreen`) by default; one component owns the
   `QApplication` lifecycle — created for the run, torn down at the end, including on failure and
   timeout. No window, timer or event loop outlives a run.

## Two speeds, one contract
1. `./scripts/check` is still the one way to ask "is this good?"; `--fast` is a speed of the
   contract, not a second contract.
2. **Fast green is a working state; only full green is evidence.** Per step, per finding, per
   iteration → `--fast`. Segment exits, PROVE steps, recovery-ramp exits, the verify table and CI
   → `CHECK GREEN (full, …)`. `scripts/doctor` warns when a shipped spec, or in CI the pull
   request description, shows `CHECK GREEN (fast, …)` and no `(full, …)`.
3. Fast: compile and the quick tests (unit, lint). Full only: UI tests, long integration suites, and
   any single step over ~a minute — the minute is a per-step threshold, not a total for the fast
   profile; fast has no fixed total. Bootstrap decides per stack and tags the steps `[fast]` in
   check.conf. When fast grows too long to iterate with, take steps out in this order: lint
   first, then formatting, then unit tests; compilation stays longest.
4. **Split a test step by a selector, never by a list.** The fast step selects with a filter
   (a category, trait, tag or namespace) and the full-only step runs the same filter inverted,
   so "fast ∪ the rest = every test" holds by construction: a test added later still runs in
   one of them. Splitting by naming projects or files leaves a silent hole — a new one that is
   not added to check.conf runs in neither profile while check stays green.
5. Durations come from check itself (`<== <step> (n s)` per step, the total in the green line).
   Decide a split, or report a profile's duration, on the median of at least 3 runs — single
   runs vary too much to decide on.

## Determinism
Flaky tests are fixed, not retried or skipped — see R-03. Evidence of a fix: 5 consecutive green runs.
