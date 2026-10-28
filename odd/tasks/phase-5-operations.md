# Phase 5 — Contributions, Loans, Tax Filing, Pay, Reporting

## Header

Operational payroll outputs: IESS planilla legs + notice deadlines, BIESS
withholding/arrears legs, RDEP/Form-107 record datasets, generic bank-payment
rows, and the Frappe notice hook. Portal XSDs and bank layouts pin in bench;
this phase ships validated datasets, never invented file formats.

## Specs

- S1 (`iess.py`): planilla lines from Art. 95 bases + 9.45/11.15 legs,
  entry/exit notice deadlines (hire+15d, exit+3d), overdue computation.
- S2 (`loans.py`): BIESS notified-installment withholding + arrears carry.
- S3 (`rdep.py`): annual per-worker record validation + batch totals
  (Form 107 dataset shares the records).
- S4 (`payments.py`): payment-row validation + generic CSV renderer.
- S5 (Frappe): Employee notice-date fields + overdue hook.

## Tasks

- T1 (S1+S2): RED tests + `payroll/iess.py` + `payroll/loans.py`.
- T2 (S3+S4): RED tests + `payroll/rdep.py` + `payroll/payments.py`.
- T3 (S5): notice fields + hook + tests.
- T4: checks green + work-unit commits on `feat/phase-5-operations`.

## Log

- L1 (user, verbatim): "merge, push y vamos con fase 5"
- L2: Phase 4 merged ff into `version-16` (10 files, +567) and pushed
  (`6275e1a..7bc027d`).
- L3: User decisions — notice hook warns ("Advertir atraso"), per-bank
  formats ("Formatos por banco"), Frappe notices-only ("Avisos + hook"),
  accounting stubs now ("Stubs ahora"). Integrity note: bank layouts ship
  as Caller-provided specs (registry + sample in tests); no invented
  Pichincha/Bolivariano columns — real layouts pin in bench.
- L4: Slice is 535 lines across 4 commits (over the ~400 guide) — accepted
  as one phase; each commit verified green in isolation.
