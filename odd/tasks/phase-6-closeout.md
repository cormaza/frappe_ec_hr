# Phase 6 — i18n, Workspace, Hardening

## Header

Closing phase: Gettext `locale/` catalog (markers + hand-authored es.po with
a Ring-1 consistency guard until the bench extraction cycle runs), the
Ecuador HR workspace JSON, and the l10n_ec-style hardening audit automated
wherever possible locally.

## Specs

- S1 (`locale/i18n_markers.py`): `_()` markers for every custom-field label,
  Select option, and component label. Never imported at runtime (tested).
- S2 (`locale/main.pot` + `locale/es.po`): hand-authored catalog with full
  headers; Ring-1 test pins markers/code msgids ⊆ catalog and headers valid.
  Bench `generate-pot-file/update-po-files/compile-po-to-mo` adopts and
  verifies in its cycle.
- S3 (workspace JSON): Ecuador HR desk workspace, shortcuts to operational
  DocTypes, JSON-validated in Ring 1, `bench build` validates in bench.
- S4 (hardening): automated citation test (every payroll module docstring
  names its legal source), plus the manual checklist recorded here.

## Tasks

- T1 (S1): markers + import-guard test.
- T2 (S2): pot/po + consistency test.
- T3 (S3): workspace JSON + test.
- T4 (S4): citation test + audit record.
- T5: checks green + work-unit commits on `feat/phase-6-closeout`.

## Log

- L1 (user, verbatim): "adelante, vamos fase 6"
- L2: User decisions — full es.po now ("es.po completo"), full workspace
  ("Operativo completo"), EC HR Settings Single now ("Settings Single
  ahora").
- L3: Hardening audit — provenance test enforces a legal citation (or the
  operational disclaimer) in every payroll module docstring; hooks-wiring
  test imports every doc_events handler in Ring 1; discovery-compliance,
  fixture-name, and dual-ring rules hold suite-wide; ruff 0.14.10 pinned in
  pyproject + pre-commit config; bench-only remainder: pot/mo regeneration,
  workspace render, Single migrate, portal/bank schema pins.
- L4: Slice is 1777 lines across 4 commits (over the ~400 guide) — bulk is
  the es.po catalog data; code commits stay reviewable; each verified green
  in isolation.
