# `ec_hr` Roadmap

Day-0 scaffold (Phase 0) is done: harness, CI, installability, IESS rate seed. Everything below is open and ordered; each phase lands with Ring 1 tests first, Ring 2 bench verification, and docs alongside the behavior.

## Phase 0 — Scaffold & Harness (done)

- Standalone app root (`ec_hr`, `version-16`), `hooks.py` with `required_apps = ["frappe", "erpnext", "hrms"]`.
- Ring 1 loop green: `pre-commit` (ruff `v0.14.10` pinned twice), `pytest` with coverage on `ec_hr/payroll`.
- CI: `fast-tdd-unit` on every dispatch; `frappe-v16-integration` (MariaDB 11.8, erpnext + hrms + ec_hr install, `run-tests`) on demand.
- `AGENTS.md` working contract, vendored `.agents/skills`, ADR-001, installability + discovery-compliance tests.
- Seed: statutory IESS rates (`9.45%` personal / `11.15%` employer) with rounding tests.

## Phase 1 — Pure Payroll Engine (`ec_hr/payroll/`)

No frappe, no hrms, fully Ring 1 covered:

1. Overtime surcharges: 50% daytime extra, 100% nights/weekends/holidays (`recargo`), midnight-crossing shifts.
2. SBU-parameterized amounts: every SBU-indexed figure takes the SBU as an explicit argument (never a constant; MDT sets it yearly).
3. Period helpers: payroll month boundaries, hire/termination proration in `America/Guayaquil`.
4. Decimo accrual math: decimo tercero (1/12 of taxable remuneration, monthly or accumulated), decimo cuarto (1 SBU per year, Sierra/Costa calendars).

## Phase 2 — hrms Integration (`ec_hr/ecuador_hr/`)

Reuse, never fork, `hrms` documents:

1. `create_custom_fields`: Ecuadorian fields on `Employee` (IESS affiliation state, entry/exit notices), `Salary Structure`, `Salary Slip`.
2. Salary Components seed (fixtures with explicit `name`): aporte personal deduction, aporte patronal employer contribution, fondos de reserva, decimos (monthly vs accumulated variants).
3. `Salary Slip` hooks: validate statutory floors/ceilings, fail loud naming the component.
4. First DocType (only if a setting truly needs storage): `EC HR Settings` (Single) for SBU-by-year table; otherwise settings stay fixtures.

## Phase 3 — Statutory Benefits

1. Fondos de reserva (8.33%, monthly vs IESS-accumulated choice per employee).
2. Utilidades (15%: 10% workers + 5% family charges), prior-year profits input.
3. Vacaciones: accrual, goce vs compensation rules.
4. Impuesto a la renta en relacion de dependencia: rebajas and gastos personales projection inputs.

## Phase 4 — MDT / IESS Reporting

1. IESS planillas: aviso de entrada/salida data exports, planilla de aportes reconciliation against computed contributions.
2. MDT contract registration data exports.
3. Report builders with JSON fixtures carrying explicit `name` keys.

## Phase 5 — i18n, Workspace, Hardening

1. `bench generate-pot-file` / `update-po-files --locale es` / `compile-po-to-mo`; `es.po` shipped, markers in `locale/i18n_markers.py`.
2. `Ecuador HR` workspace + role permissions (`HR Manager`, `HR User` reuse).
3. Hardening list (mirrors `l10n_ec` H1/H2/H3): every statutory formula cites its legal source (Ley de Seguridad Social, Codigo del Trabajo article) in the test docstring.

## Deliberate Non-Goals

- No SBU constant: the SBU is a yearly MDT resolution, always a parameter.
- No parallel Employee/Payroll DocTypes while `hrms` owns them.
- No legacy `translations/*.csv`; Gettext `locale/` workflow only.
- No Spanish identifiers in code; statutory Spanish terms live in data, markers, and `es.po`.
