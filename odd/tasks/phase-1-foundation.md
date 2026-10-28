# Phase 1 — Identity, Family, and Contract Foundation

## Header

Pure payroll modules (`identity`, `family`, `contract`, `age`) with Ring 1 tests,
plus the Frappe layer (Employee custom fields + validate hook with dual-ring
tests, green in bench CI). No amounts, no SBU, no reporting.

## Specs

- S1: `identity.py` — `is_valid_ci`, rejection reasons in English via `_()`,
  `classify_id` (ci / ruc_natural / ruc_private / ruc_public / unclassified),
  `is_valid_ruc`. Cedula checksum failure blocks save; RUC checksum failure
  only flags `ec_id_validated=False` and warns (user decision: "Solo marcar
  y avisar").
- S2: `family.py` — `count_valid_charges(charges, as_of)` over the Art. 97
  set (spouse/partner, children <18, children with disability any age) with
  accreditation/start/end dates. No profit-split math (Phase 4).
- S3: `contract.py` — `ContractKind` with the full 8-type set (user decision:
  "Set completo de 8", LOAH emergent text still pending, marked provisional),
  `TERMINATION_CAUSES` per Art. 169/172/173 numerals, `probation_end_date`.
  Cause enters as data, never inferred.
- S4: `age.py` — `age_on`, 4 youth bands (Art. 134/69), conservative
  `is_prohibited_assignment` for 15-18 night/hazardous/overtime (user
  decision: "Bloqueo conservador"), `vacation_annual_days` per Art. 69.
- S5: Frappe layer — `ec_id_*`, `ec_contract_*`, `ec_disability_*` custom
  fields on Employee, `validate` hook (cedula strict, RUC warn-only), tests
  via `frappe.get_doc`, `(ValueError, frappe.ValidationError)` expectations,
  explicit `import frappe`. Bench-CI green; bench-local not runnable (no hrms
  in ~/frappe-bench-v16).

## Tasks

- T1 (S1): RED tests + `payroll/identity.py` — route: inline.
- T2 (S2): RED tests + `payroll/family.py` — route: inline.
- T3 (S3): RED tests + `payroll/contract.py` — route: inline.
- T4 (S4): RED tests + `payroll/age.py` — route: inline.
- T5 (S5): custom fields + hook + dual-ring tests — route: inline (no bench
  locally; CI bench verifies).
- T6: pre-commit + pytest green, work-unit commits on `feat/phase-1-foundation`.

## Log

- L1 (user, verbatim): "bien vamos con la fase 1, explicame las decisiones
  tecnicas y consultame cuando tengas dudas de la implementacion"
- L2: User decisions — Frappe enters Phase 1 ("Puro + Frappe ahora"), RUC
  warn-only ("Solo marcar y avisar"), 8 contract kinds ("Set completo de 8"),
  conservative youth block ("Bloqueo conservador").
- L3: Scope note — `distribute_profit_sharing` stays in Phase 4; family.py
  ships only charge counting/validation.
- L4: T5 finished via `gentle-ai-worker` (bench-only test, setup.py, hooks
  wiring); worker-reported installability failure fixed inline — DocType JSON
  carries an HR Manager permission row and the controller imports Ring-1-safe
  (stub `Document` base, `ValueError` locally). Full suite: 62 passed,
  3 skipped (bench-only).
