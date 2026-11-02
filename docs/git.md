# Git

Şablonun güvenli varsayılanları bootstrap'ta (2026-10-19) kabul edildi ve yeniden konumlandırmada
(2026-11-02) aynen korundu. Branch adları ve commit mesajları İngilizce.

## Branching
- `feature/<spec-no>-<short-name>` — **no branch without a spec.** Also for CHANGE-lane mini-specs.
- Refactors: `refactor/<spec-no>-<short-name>` (mini-spec with Changed behavior = none).
- Fixes: `fix/<report-id>-<short-name>` (bug fixes carry a report, not a spec number);
  incidents: `incident/<date>-<short-name>`; trivial changes: `trivial/<short-name>` (see below).

## Commits
- Conventional Commits, with a plan reference: `feat(catalog): paging endpoint [plan 0001/3]`.
- Agent commits follow the same standard: the agent writes the message, the human approves.

## Forbidden
- Direct commits to the default branch.
- Force push, history rewriting on shared branches. Undo = `git revert` (see recovery R-11).

## Trivial changes
<!-- Set at bootstrap. Applies only to requests the change-request triage rubric
     (workflows/change-request.md) classifies as TRIVIAL: no acceptance criterion changes, no shared code. -->
- Policy: **(1) PR + one reviewer, no spec** — seçildi (bootstrap, 2026-10-19). Ucuz güvenlik ağı:
  ikinci göz + CI'da check, "trivial sanılan" değişikliği yakalar.
- Tek kişilik projede "bir inceleyici" = ayrı oturumdaki **salt-okunur `reviewer` ajanı**
  (Kural 3 zaten bunu şart koşar); insan onayı PR'ı birleştirirken verilir (bootstrap, 2026-11-02).
- Always: one narrow commit, `scripts/check` green. A second file or a new test means re-triage.

## Pull requests
- PR template checklist completed; `scripts/check` green in CI; squash-merge.
- GitHub branch protection on `main` (insan tarafından bir kez açılır): PR zorunlu, `check` ve
  `doctor` job'ları zorunlu durum kontrolü, force push ve silme kapalı.
