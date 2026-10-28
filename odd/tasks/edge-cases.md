# Edge Cases per Phase — INTEGRATED

> Status 2026-10-28: all batches integrated + hardened (`feat/edge-cases`).
> Ring 1: 265 passed. Bench ec_test: 271 + 2 OK. The `!` items below all
> resolve to explicit rejection except where noted.

Candidates found by reading every module for boundaries, error-type
consistency, garbage-in behavior, and untested branches. `+` = pure test
addition (no behavior change). `!` = needs a behavior decision first.

## P1 — identity / family / contract / age (11)

- identity: RUC ending 002+ accepted (pin branch-RUC behavior) `+`; mod-11
  strict-10 vector `1970000000001` → invalid (pins the disputed edge) `+`;
  Unicode-digit input behavior pin `+`.
- family: accreditation in the future → invalid `+`; `ends_on == as_of`
  boundary (valid, `<` invalid) `+`; `disability_pct > 100` currently silent
  → propose reject `!`.
- contract: `requires_visto_bueno("169.9")` False `+`;
  `parse_contract_kind(" OBRA CIERTA ")` normalization `+`.
- age: newborn `age_on == as_of` → 0 `+`; future birthdate fails closed
  (negative → UNDER_15) pin `+`; UNDER_15 with all flags True `+`;
  negative seniority → base 15 pin `+`.

## P2 — period / overtime / deductions / remuneration (14)

- period: Feb-29 hire scaling `+`; same-day hire+exit `+`; absences exactly
  equal billable → 0 `+`; invalid month raises IllegalMonthError, not
  ValueError → propose normalize `!`.
- overtime: zero-length shift `==` → ValueError `+`; exact 06:00–19:00 and
  19:00–06:00 boundary splits `+`; 48h multi-midnight shift `+`; sub-minute
  flooring pin `+`; money rounding (7.77, 90min → 17.48) `+`.
- deductions: `floor > 0` waterfall (500/600/floor-100) `+`; duplicate
  labels accumulate-then-cap — current math is suspect, propose explicit
  sum-first rule `!`; 1-month amortize vector `+`; 2-level CONA table `+`;
  order == floor → no warning boundary `+`.
- remuneration: `contribution_base` propagates unknown-kind ValueError `+`.

## P3 — decimos / vacations / leave (10)

- decimos: negative base currently yields negative accrual → propose reject
  `!`; elapsed 12 → full SBU `+`; elapsed > 12 → propose reject `!`.
- vacations: same-day accrual → 0.0 `+`; seniority-5 integration pin through
  `accrued_days` `+`; `accrued_days` exit-before-hire raises `+`;
  liquidation(0) → 0.0 `+`.
- leave: all-flags paternity → 25 `+`; transfer with enjoyed=0 → full `+`;
  zero IESS rate documents the uninsured gap (policy question, pin only) `+`.

## P4 — reserve / profit / severance / tax (12)

- reserve: Feb-29 hire ±1 day eligibility edge `+`; negative base → propose
  reject `!` (same rule as decimos).
- profit: zero pool → all-zero shares `+`; single worker no charges → 100%
  `+`; gross exactly at 24-SBU cap → no excess `+`; all-zero days with
  charges `+`; negative days → propose reject `!`.
- severance: exactly 3.0 and 25.0/25.2 cap edges `+`; float years to
  `desahucio_bonus` silently multiplies → propose floor to completed `!`.
- tax: base exactly on bracket edges (12081 → 0.0, 12082 → 0.05) `+`;
  unsorted/overlapping table → propose reject `!`.

## P5+ — ops / i18n / pins / hooks (13)

- iess/loans: zero-day planilla covered; withholding(0) → 0.0 `+`;
  over-withheld arrears go negative (credit balance) pin `+`.
- rdep: extra keys ignored in totals pin `+`; empty batch → zeros `+`;
  empty workers → no retRelDep block `+`; bad tipoEmpleador → ValueError `+`.
- payments: empty rows → header-only CSV `+`; cents rounding documents
  banker's behavior (0.125 → 12) `+`.
- accounting: zero amount → zero lines `+`; negative amount → propose
  reject `!`.
- settings: negative year → ValueError `+`.
- hooks: whitespace-only ID bypasses type-required (treated as missing) pin
  `+`; valid-RUC happy path `+`; notice exactly on deadline → silent `+`.
- iess_batch: real death date path `+`; 64-char position boundary `+`.
- sut: zero-amount line → `line-not-positive` `+`.

Totals: ~60 pins, 8 behavior decisions (`!`).
