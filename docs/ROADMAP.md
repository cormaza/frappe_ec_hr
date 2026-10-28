# `ec_hr` Roadmap — Ecuadorian HR Localization (v16)

Day-0 scaffold (Phase 0) is done: harness, CI, installability, IESS rate seed.
This document is the build plan for the full localization requested: identity,
family, contracts, time, absences, benefits, termination, deductions, tax, pay,
and statutory reporting. Each phase lands with Ring 1 tests first, Ring 2 bench
verification, and docs alongside the behavior.

Legal baseline: `Codigo del Trabajo` (Codificacion 2005-017, Registro Oficial
Suplemento 167), consolidated text verified against `vigente.ec` on 2026-10-28
for Art. 11, 14, 17, 49, 55, 65, 69, 71, 111, 113, 152, 172, 184, 188, plus
`Ley de Seguridad Social` Art. 73 (IESS entry/exit notices) and the MDT accords
cited inline. Anything marked `to-verify-in-bench` was not verifiable from the
read-only research pass and must be confirmed against the pinned core sources
(`apps/frappe`, `apps/erpnext`, `apps/hrms`, MDT/SRI/IESS portals) before code.

Layering (from `AGENTS.md`, non-negotiable):

- `ec_hr/payroll/` — pure Python statutory math over numbers/dicts. No
  top-level `import frappe`. SBU is always an explicit parameter, never a
  constant. Every formula cites its legal source in the test docstring.
- `ec_hr/ecuador_hr/` — Frappe v16 DocTypes, controllers, `create_custom_fields`,
  fixtures (explicit `name` keys), and hooks into `hrms` (`Employee`, `Salary
  Component`, `Salary Structure`, `Salary Slip`). Reuse, never fork, `hrms`
  documents.
- `ec_hr/locale/` — English source strings only; Spanish UI via `main.pot` /
  `es.po` Gettext workflow. Statutory Spanish terms (`aporte personal`, `decimo
  tercero`, etc.) live in data, markers, and `es.po` only.

## Phase 0 — Scaffold & Harness (done)

- Standalone app root (`ec_hr`, `version-16`), `hooks.py` with
  `required_apps = ["frappe", "erpnext", "hrms"]`.
- Ring 1 loop green: `pre-commit` (ruff `v0.14.10` pinned twice), `pytest` with
  coverage on `ec_hr/payroll`.
- CI: `fast-tdd-unit` on every dispatch; `frappe-v16-integration`
  (MariaDB 11.8, erpnext + hrms + ec_hr install, `run-tests`) on demand.
- `AGENTS.md` working contract, vendored `.agents/skills`, ADR-001,
  installability + discovery-compliance tests.
- Seed: statutory IESS rates (`9.45%` personal / `11.15%` employer) with
  rounding tests.

## Phase 1 — Identity, Family, and Contract Foundation

Goal: no payroll math runs on an unidentified person or an unclassified contract.

### 1A. National / foreign identification and validation

- Scope: Ecuadorian `cedula` (10 digits, modulo-10 check, province code
  01-24 + 30 for abroad, third digit < 6), RUC (natural / juridical / public
  with third digit 6/9 and modulo-11, `to-verify-in-bench` against SRI spec),
  foreign residents (passport + visa type, no checksum — presence + format +
  expiry), work-permit flag for MDT registration.
- Legal source: Registro Civil identity rules; SRI RUC spec
  (`to-verify-in-bench`); MDT-SUT foreign-worker registration
  (`to-verify-in-bench`).
- Payroll layer: `ec_hr/payroll/identity.py` — `validate_ci()`,
  `validate_ruc()`, `classify_id()` pure functions, Ring 1 table tests
  including known-valid / known-invalid numbers.
- Frappe layer: custom fields on `Employee` (`ec_id_type`, `ec_id_number`,
  `ec_id_validated`, `ec_nationality`, `ec_visa_type`, `ec_work_permit_expiry`);
  `Employee.validate` hook rejects invalid checksum with the component named.

### 1B. Family charges (`cargas familiares`)

- Scope: spouse / civil-union partner, children under 18, children with
  disability any age — the exact Art. 97 set. Accreditation date + document
  reference per charge; start/end dates drive proration.
- Legal source: Codigo del Trabajo Art. 97 (10% equal split + 5% by family
  charges); MDT-2023-140 Art. 16 accreditation cutoff March 31
  (`to-verify-in-bench` for the cutoff mechanics).
- Payroll layer: `family.py` — `count_valid_charges(charges, as_of)`,
  `distribute_profit_sharing()` takes the count, never the civil record.
- Frappe layer: `EC Family Charge` child table on `Employee` (or a dedicated
  DocType if history/audit needs it — decide at implementation); fixture for
  utilidades 5% wiring in Phase 4.

### 1C. Contract types

- Scope: indefinite as the typical/stable modality (Art. 14); exceptions —
  fixed work (`obra cierta`), eventual / occasional / seasonal (Art. 17),
  apprenticeship, plus project-specific needs (part-time permanent, special
  emergent LOAH Art. 19 `to-verify-in-bench`). Hourly hiring was removed by
  Mandato Constituyente 8 (`to-verify-in-bench` — roadmap assumes no new
  per-hour contract type; extra hours are overtime, not a contract class).
  90-day probation (`to-verify-in-bench` against MDT-2018-0135), SUT
  registration payload per type.
- Legal source: Art. 11 (classification), Art. 14 (indefinite as typical),
  Art. 17 (eventual/occasional/seasonal), Art. 169 (termination causes),
  MDT contract-registration accords (`to-verify-in-bench`).
- Payroll layer: `contract.py` — contract-kind enum + allowed-termination map
  + probation-end helper in `America/Guayaquil`; no amounts here.
- Frappe layer: custom fields on `Employee` / `Employment Type`
  (`ec_contract_kind`, `ec_sut_contract_id`, probation dates); MDT export
  builder stub (full payload in Phase 5).

### 1D. Youth-work age computation

- Scope: age-at-date in `America/Guayaquil`; under-15 prohibited
  (`to-verify-in-bench` Art. 134-136), 15-18 restricted (night work / hazardous
  / overtime bans, authorization), vacation uplift (under-16: 20 days,
  16-18: 18 days — verified Art. 69 para. 3).
- Payroll layer: `age.py` — `age_on(birthdate, as_of)`,
  `youth_category()`, `is_prohibited_assignment()` guard.
- Frappe layer: `Employee.validate` warning/block on prohibited assignment;
  vacation-days resolver consumes the category (Phase 3).

### 1E. Disability registry (employee and dependents)

- Scope: disability percentage + CONADIS card reference, expiry, work
  adjustments; substitute (`sustituto directo`) flag; 4% hiring quota context
  (Ley Organica de Discapacidades Art. 47, `to-verify-in-bench`); dependent
  with severe disability extends paternity leave to 25 days (verified
  Art. 152) and counts as Art. 97 family charge at any age.
- Payroll layer: fields flow into leave-duration and utilidades inputs; no
  separate math module — `leave.py` and `family.py` consume flags.
- Frappe layer: custom fields + card-expiry report; quota headcount report in
  Phase 5 (`to-verify-in-bench` for the exact quota base).

## Phase 2 — Time Engine (the 30-day month, day/night, overtime)

Goal: every later benefit divides by the same day and values the same hour.

### 2A. IESS 30-day month and period helpers

- Scope: payroll month boundaries, hire/termination proration, absence-day
  proration, all in `America/Guayaquil`. IESS contribution month is always
  30 days regardless of calendar length (`to-verify-in-bench` against IESS
  planilla manual — universally applied, needs a cited test docstring at
  implementation).
- Payroll layer: `period.py` — `month_fraction(start, end, month)`,
  `iess_billable_days()`; property tests for Feb / 31-day / leap edge cases.

### 2B. Day / night hours and surcharges

- Scope (verified): max 8h/day, 40h/week (Art. 47); night shift 19:00-06:00
  paid at +25% over the equal-length day shift (Art. 49); overtime only by
  written agreement + inspector authorization, max 4h/day and 12h/week
  (Art. 55.1); daytime supplement (until 24:00) +50%, night supplement
  (24:00-06:00, day-hour base) +100%, piece-work units marked up identically
  (Art. 55.2-55.3); Saturday/Sunday work +100% (Art. 55.4). Midnight-crossing
  shifts split legs at 24:00. Night overtime stacks night-base then the
  Art. 55 supplement on the day-hour base — implementation must pin the
  stacking order with a test (`to-verify-in-bench` for the stacking reading).
- Payroll layer: `overtime.py` — `split_day_night()`, `value_supplement()`,
  `value_extraordinary()`, midnight-crossing cases first.
- Frappe layer: `Salary Component` formulas call in; `Salary Slip` hook caps
  daily/weekly overtime and fails loud naming the component.

### 2C. Advances, loans, discounts, judicial withholdings

- Scope: salary advances, company loans (installment schedule, outstanding
  balance), fines/discounts within statutory limits (`to-verify-in-bench`
  Art. 44-46 caps), alimony withholdings (CONA pension table,
  `to-verify-in-bench` — judicial order reference, priority over voluntary
  deductions, floor-protection).
- Payroll layer: `deductions.py` — amortization + priority waterfall
  (judicial > statutory > voluntary), each deduction names its cap source.
- Frappe layer: `Salary Component` deduction set + `EC Judicial Withholding`
  record (order number, beneficiary, monthly amount); negative-net-pay guard.

### 2D. Per-diem and expense reimbursements

- Scope: `viaticos` (travel allowance, tax treatment per SRI,
  `to-verify-in-bench`) vs reimbursements of actual spend (receipt-backed,
  non-remuneration, excluded from IESS base and XIII base —
  `to-verify-in-bench` against Art. 95 inclusions).
- Payroll layer: classification predicate `is_remuneration()` feeding the
  Art. 95 base builder; reimbursement never enters contribution bases.
- Frappe layer: Expense Claim integration mapping (`to-verify-in-bench`
  against `hrms`/`erpnext` expense flow).

## Phase 3 — Absences, Leave, and Vacations

### 3A. Holidays (`feriados`)

- Scope (verified Art. 65): national list (Jan 1, Good Friday, May 1/24,
  Aug 10, Oct 9, Nov 2/3, Dec 25, Carnival Mon/Tue) + local specials;
  Tuesday→Monday, Wed/Thu→Friday moves; Sat/Sun→Fri/Mon moves; Jan 1, Dec 25,
  Carnival-Tuesday never move. Worked-holiday pay follows Art. 55.4 (+100%)
  via the time engine.
- Payroll layer: `holidays.py` — dated holiday table as parameter (yearly MDT
  calendar input), `observed_date()`, `is_paid_rest_day()`.
- Frappe layer: Holiday List seeder for the EC calendar; Leave Type wiring.

### 3B. Vacations: accrual, pay, provisioning, reporting

- Scope (verified Art. 69/71/76): 15 uninterrupted days incl. non-working
  days yearly; +1 day per excedent year after 5 years, cap +15 days (contract
  may widen); under-16: 20 days, 16-18: 18 days; pay in advance; liquidation
  = 1/24 of everything earned in the full year (ordinary + supplementary +
  extraordinary + normal accessory per Art. 95); proportional on exit without
  enjoyment; untaken days paid without surcharge (Art. 76,
  `to-verify-in-bench` for the exact no-surcharge reading).
- Payroll layer: `vacations.py` — `accrued_days()`, `liquidation_24th()`,
  `provision_monthly()`; youth + seniority variants as parameter cases.
- Frappe layer: Leave Type `Vacaciones`, accrual job, provision ledger,
  IESS/MDT vacation report stub (full export in Phase 5).

### 3C. Medical leave, maternity, paternity, unpaid care leave

- Scope (verified Art. 152): maternity 12 weeks + 10 days multiple birth
  (IESS certificate); paternity 15 days normal / +5 multiple-or-cesarean /
  +8 premature-or-special-care / 25 days severe-disability-or-terminal
  illness; mother-death transfer of the remaining leave to the father;
  adoption and unpaid-care leaves under Ley Organica del Derecho al Cuidado
  Humano (`to-verify-in-bench`). Medical leave salary rules: IESS subsidy
  percentages and employer top-up policy (`to-verify-in-bench` — IESS pays
  75% from day 4 in general regime; implementation must confirm and pin).
- Payroll layer: `leave.py` — `leave_days(kind, facts)`,
  `paid_fraction(kind, day_index, insurant)` returning employer vs IESS legs.
- Frappe layer: Leave Types per kind with certificate-attachment validation;
  salary-rule split (employer leg provisions, IESS leg informational).

## Phase 4 — Benefits and Termination

### 4A. Thirteenth / fourteenth (`decimos`): monthly vs accumulated, provision, report

- Scope (verified Art. 111/113 + MDT-2019-199): XIII = 1/12 of Art. 95
  remuneration over the calendar year, paid monthly by default, accumulated
  to Dec 24 only on written request; XIV = 1/12 SBU monthly by default,
  accumulated to Mar 15 (Costa/Insular) or Aug 15 (Sierra/Amazonia) on written
  request; school-regime calendar per district; XIV also covers employer
  retirees and IESS/military/police pensioners (informational for payroll);
  proportional on exit.
- Payroll layer: `thirteenth.py` / `fourteenth.py` — `accrue()`,
  `accumulated_due()`, `provision_monthly()`, SBU always a parameter.
- Frappe layer: per-employee accumulation-election record, monthly vs
  accumulated `Salary Component` variants, MDT-2019-199 registration export
  (Phase 5 wires the portal format).

### 4B. Reserve funds (`fondos de reserva`)

- Scope: 8.33% (one full remuneration per year after the first) Cause, monthly
  direct payment vs IESS accumulation per employee election (Art. 196-200,
  `to-verify-in-bench` for the article range and first-year exclusion).
- Payroll layer: `reserve.py` — eligibility gate (service > 1 year) +
  `monthly_amount()`; election as input.
- Frappe layer: election field + component variants + IESS accumulation
  reconciliation input.

### 4C. Profit sharing (`utilidades`): computation with family charges

- Scope (verified Art. 97 + 97.1 `to-verify-in-bench` for the 24-SBU cap):
  15% of liquid profits — 10% equal by days worked, 5% by Art. 97 family
  charges via the majority worker association (direct if none); partial-year
  proration; complementary-activity split (MDT-2020-079,
  `to-verify-in-bench`); undistributed cap allocation
  (`to-verify-in-bench`).
- Payroll layer: `profit_sharing.py` — `split_10_5()` consuming audited
  `days_worked` and `family.py` charge counts; cap as parameter.
- Frappe layer: prior-year profit input DocType (`to-verify-in-bench`
  whether Single or yearly record), distribution worksheet, MDT filing
  export (Phase 5).

### 4D. Living wage (`salario digno`) and compensation

- Scope: dignified-salary components per COPCI Art. 9 (`to-verify-in-bench`):
  base salary/wage + XIII/12 + XIV/12 + variable commissions + profit-sharing
  share + reserve funds + registration-period benefits vs the yearly MDT
  dignified-salary figure; compensation = shortfall paid to qualifying workers.
- Payroll layer: `living_wage.py` — `shortfall(components, threshold)`;
  threshold always a parameter (yearly MDT figure).
- Frappe layer: yearly threshold settings row + compensation component +
  SUT calculator cross-check (`to-verify-in-bench`).

### 4E. Settlement acts (`actas de finiquito`): all variants

- Scope: termination causes (Art. 169 `to-verify-in-bench`), employer-cause
  dismissal with prior administrative approval (`visto bueno`, Art. 172/173/
  621 `to-verify-in-bench`), worker notice (`desahucio`, verified Art. 184:
  written/electronic, 15-day notice reducible by employer acceptance,
  bonus also on Art. 169.2 exits), eviction bonus 25% of last monthly
  remuneration per year of service (Art. 185 `to-verify-in-bench`), untimely
  dismissal scale (verified Art. 188: 3 months pay to 3 years; 1 month/year
  beyond, cap 25 months, fraction = full year; +20-to-<25-year employer
  retirement proportional), strike/legal-lockdown and business-liquidation
  variants (Art. 191/193 `to-verify-in-bench`), SUT `acta` payload + payment
  proof.
- Payroll layer: `severance.py` — `desahucio_bonus()`, `untimely_award()`,
  `proportional_benefits()` composing XIII/XIV/vacation/reserve functions;
  cause as enum input, never inferred.
- Frappe layer: `EC Settlement Act` DocType (cause, dates, computed lines,
  SUT filing reference); validate hook blocks negative/unsigned acts.

## Phase 5 — Contributions, Loans, Tax, Pay, and Reporting

### 5A. IESS contributions and employer obligations

- Scope: personal 9.45% / employer 11.15% on the Art. 95 base (seed done);
  sector-specific rates (`to-verify-in-bench`); entry notice within 15 days
  from day one, exit/salary/illness notices within 3 days (verified Ley de
  Seguridad Social Art. 73 via IESS employer portal); contribution-planilla
  reconciliation and regeneration flow (`to-verify-in-bench` portal spec).
- Payroll layer: extend `legal.py` bases; `iess.py` planilla-line builder.
- Frappe layer: entry/exit custom fields + notice-date validations +
  planilla export; `clear-cache` note for hook rollout (bench lesson).

### 5B. IESS loans: mortgage and unsecured (`quirografarios`)

- Scope: informational payroll deductions — BIESS grants and amortizes;
  payroll only withholds the notified installment (`to-verify-in-bench` for
  file layout and reserve-fund collateral rules).
- Payroll layer: deduction leg with external-schedule input; no amortization
  math in `ec_hr`.
- Frappe layer: installment import + slip-line mapping; arrears report.

### 5C. Income tax in dependency: RDEP, personal-expense projection, Form 107

- Scope: SRI employer annex (RDEP) + withholding certificate (Form 107);
  personal-expense (`gastos personales`) projection and rebate inputs,
  monthly withholding vs year-end settlement (`to-verify-in-bench` for the
  current SRI tables, utara thresholds, and RDEP schema version).
- Payroll layer: `income_tax.py` — `monthly_withholding()` over SRI-bracket
  parameters (brackets always parameters, never constants).
- Frappe layer: projection DocType + RDEP file builder + Form 107 dataset;
  SRI schema version pinned in tests.

### 5D. Payroll payment: bank transfers, checks, provisions

- Scope: net-pay instruction files per bank (`to-verify-in-bench` layouts),
  check-print dataset, provision ledger (XIII/XIV/vacations/desahucio
  monthly provisions), cost-center accounting bridge
  (`to-verify-in-bench` against `erpnext` payroll accounting).
- Frappe layer: payment-file export + check format + provision report;
  no new Employee/Payroll DocTypes while `hrms` owns them.

### 5E. MDT / IESS reporting suite

- Scope: SUT contract registration, XIII/XIV registration (MDT-2019-199),
  utilidades filing (MDT-2020-079), entry/exit notices, contribution
  planillas, vacation/settlement filings. Builders carry JSON fixtures with
  explicit `name` keys; portal formats pinned per accord version.
- Frappe layer: one builder per filing with versioned golden files; workspace
  + role permissions (`HR Manager` / `HR User` reuse).

## Phase 6 — i18n, Workspace, Hardening

1. `bench generate-pot-file --app ec_hr` / `update-po-files --app ec_hr
   --locale es` / `compile-po-to-mo`; ship `es.po`; markers in
   `locale/i18n_markers.py` (never imported at runtime). `PO-Revision-Date`
   in full `YYYY-MM-DD HH:MM`.
2. `Ecuador HR` workspace + role permissions.
3. Hardening list (mirrors `l10n_ec` H1/H2/H3): every statutory formula cites
   its legal source in the test docstring; `frappe.get_doc({...})` in hook
   tests; `(ValueError, frappe.ValidationError)` expectations; explicit
   `import frappe` where `frappe.ValidationError` is named; one-file-at-a-time
   bench syncs; Redis ports from `common_site_config.json`; ruff pinned twice.

## Deliberate Non-Goals

- No SBU constant: yearly MDT resolution, always a parameter.
- No parallel Employee/Payroll DocTypes while `hrms` owns them.
- No legacy `translations/*.csv`; Gettext `locale/` workflow only.
- No Spanish identifiers in code; statutory Spanish terms live in data,
  markers, and `es.po`.
- No per-hour contract class: extra hours are Art. 55 overtime.

## Research Log (2026-10-28 pass)

- Verified from consolidated Codigo del Trabajo via `vigente.ec`: indefinite
  as typical (14), night +25% 19:00-06:00 (49), overtime caps/surcharges incl.
  Sat/Sun +100% (55), holidays + bridge rules (65), vacations 15 days +
  seniority/youth variants + 1/24 liquidation (69/71), XIII 1/12 to Dec 24
  (111), XIV 1/12 SBU to Mar 15 / Aug 15 (113), maternity 12w + paternity
  15/20/25-day ladder (152), desahucio written 15-day (184), untimely
  dismissal 3-month / 1-month-per-year cap-25 scale (188), 15% profit split
  10-equal + 5-family (97).
- IESS entry within 15 days / exit within 3 days confirmed via IESS employer
  portal (Ley de Seguridad Social Art. 73).
- Exa rate-limited the second half of the pass: SRI RDEP/107 schemas, BIESS
  loan files, CONA alimony table, COPCI Art. 9 components, LOD quota, Mandato
  8 hourly ban, visto-bueno procedure, Art. 185/191/193 scales, Art. 95 base
  inclusions, and IESS 30-day-month wording are carried as
  `to-verify-in-bench` items above and must be pinned before their phase
  starts. Do not invent them from memory.
