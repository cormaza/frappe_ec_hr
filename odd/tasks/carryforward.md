# Carryforward — Deduction Balances

## Header

Close the shortfall loop the walkthrough question exposed: erpnext Lending
auto-carries, hrms Advances do not, and our waterfall `shortfall` had no
consumer. v1: EC Deduction Balance ledger + `before_validate` injection into
`ec_` inputs + `on_submit` shortfall write-back with frozen amounts.

## Specs

- S1 (pure): `inject_balances` (owed = monthly + balance per slip field,
  unknown fields fail loud), `carry_shortfall` (max(owed - applied, 0)).
- S2 (DocType): EC Deduction Balance — employee, label, kind (Title Case,
  normalized at use), balance, monthly_amount, salary_component Link,
  slip_field (blank/ec_alimony_order/ec_advance_deduction).
- S3 (hooks): `before_validate` injects; `on_submit` recomputes from frozen
  rows and upserts balances. Cancellation rollback explicitly out of scope.
- Tests dual-ring; es.po covered; bench green.

## Tasks

- T1: pure helpers + tests.
- T2: DocType + controller + tests.
- T3: hooks + tests + catalog.
- T4: bench verify + commits — DONE (290 unit + 2 integration green on ec_test; format commit b59769e).

## Log

- L1 (user): shortfall carry-forward — erpnext contemplates? Partially
  (Lending auto-carries via set_loan_repayment; Advances/manual Additional
  Salary do not). User chose ledger + auto-injection.
- L2: Mechanics proven in bench (inject 400 → apply 400 → balance 0;
  partial 250 → 100 applied → 150 carried). Two hard lessons: (a) injection
  must ASSIGN into dedicated carried fields — accumulating into order
  inputs double-injects on every re-validate (caught live: 300→600);
  (b) structure rows snapshot component formulas, and manual row edits do
  not survive save recalculation — seed formula changes need structure
  refresh, open question below.
- L3: CLOSED — `ensure_salary_components()` in `ecuador_hr/setup.py` already refreshes formula + amount_based_on_formula on existing rows (never user amounts), so seed formula changes propagate via migrate/install without manual refresh.
- L4 (walkthrough UX): U-001 `slip_field` shows raw field names (hook contract, must stay) → description added; U-002 optional `salary_component` silently disables carry → description added; permissions (HR Manager only) match sibling DocTypes, no change; bench 290 + 2 green after migrate (one self-caused red: markers synced without es.po, fixed by syncing es.po).
