# Phase 8 — Pin Closure

## Header

Close every remaining pin from prior phases: the 12th Pichincha column
(annex hunt), IESS batch ASCII field tables (hl5 page), MDT SUT payload
shape, and the RDEP 2026 XSD check (ours is 2023; plugin v3.19.0 is fiscal
2026). Research-first; code only what the sources support, no invention.

## Specs

- S1: 12th Pichincha column resolved or recorded unresolvable with source.
- S2: IESS batch ASCII builders from the hl5 field tables.
- S3: SUT payload shape (acta/contract/registration datasets).
- S4: RDEP 2026 schema check; upgrade or documented delta.

## Tasks

- T1: annex + hl5 + SUT + 2026-XSD research pass.
- T2: builders + fixtures for whatever the sources support.
- T3: bench verify + commits on `feat/phase-8-pins`.

## Log

- L1 (user, verbatim): "merge y push, siguiente fase" + "Cerrar pins".
- L2: Phase 7 merged ff into `version-16` and pushed (`40ddb51..b8ed6ff`).
- L3: User decisions — hunt annexes ("Cazar anexos"), SUT manual dataset
  ("Dataset manual"), version XSD builders ("Versionar"), IESS builders +
  fixtures ("Builders + fixtures").
- L4: Research verdicts — Pichincha 12th column unresolvable from public
  sources (template + bank codes download behind portal login; Colombian
  lookalike spec discarded as wrong bank/country); IESS hl5 batch tables
  complete (ENT/SAL/MSU/INS/PFR/PFM/PPF/PFN/PRA/RRT, `;`-separated, `.`
  decimals, one record per affiliate, coded fields reference unpublished
  annexes); SUT acta is portal-form + signed PDF + payment-proof PDF with
  a 30-day payment term (MDT-2017-0135 Art 6-7); no public 2026 XSD (plugin
  v3.19.0 ships no schema link) so builders version by year with 2023
  pinned.
- L5: Implemented `iess_batch` (golden vectors from the hl5 examples),
  `sut` checklist + 30-day deadline, RDEP `schema=` versioning. Bench
  214 + 2 OK. Provenance pattern extended with MDT/SUT markers.
- L6: Slice rebuilt twice for per-commit-green (translations-then-code
  ordering + a bad catalog splice recovered from the bench copy). RUF005
  fixed via unpacking. Bench copy synced file-by-file; final bench
  214 + 2 OK.
