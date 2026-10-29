# Multi-company / multi-currency hardening — tests + flows

Objective: fail-closed multi-company isolation and USD-only enforcement across pure payroll layer and Frappe flows. Branch: `feat/multi-company-currency-hardening`. Delivery: `ask-on-risk`. Runner: `.venv/bin/pytest -v --cov=ec_hr/payroll --cov-report=term-missing -W error` + `pre-commit`.

## Specs

- S1 (user verbatim): "bien, quiero hacer un hardening a nivel de test y flujos, para el tema multi compañía y multi moneda"
- S2 (currency policy, user choice verbatim): "USD-only estricto" — every amount is USD; any Salary Slip / flow carrying another currency or an exchange rate != 1 is rejected fail-closed. Ecuador is dollarized; no FX conversion is offered in this hardening.
- S3 (company policy, user choice verbatim): "Aislamiento total" — every Slip / Employee / batch line belongs to exactly one company; batches, RDEP totals, provision maps and payment rows reject mixed RUC/company inputs fail-closed.
- S4 (pure-layer constraint, from AGENTS.md): `ec_hr/payroll/` MUST NOT gain a top-level `import frappe`; currency/company guards are pure functions over explicit parameters.
- S5 (Frappe discovery rule, from AGENTS.md): every test in `test_*.py` MUST be a method on `UnitTestCase`/`IntegrationTestCase`; bare `def test_...()` functions are silently ignored by bench.

## Tasks

- T1 (S2+S4): RED+GREEEN pure guards `assert_usd_only` + `assert_single_company` (+ unit tests). Route: inline. Status: done (12 passed `test_company_currency.py`; files `payroll/company_currency.py`, `tests/test_company_currency.py`).
- T2 (S2+S3+S4): Harden batch/operational builders (`iess_batch`, `rdep`, `accounting.provision_lines`, `payments`) to require single RUC/company + USD rows. Route: inline. Status: done (14 passed `test_company_isolation.py`; full Ring 1 309 passed; files `payroll/iess_batch.py`, `payroll/rdep.py`, `payroll/accounting.py`, `payroll/payments.py`, `locale/i18n_markers.py`, `locale/es.po`).
- T3 (S1+S2+S3+S5): Harden Frappe flows (`validate_salary_slip` company/currency, `validate_employee` company coherence) + dual-ring tests. Route: inline. Status: done (6 new isolation tests; full Ring 1 315 passed; files `ecuador_hr/salary_slip_hooks.py`, `ecuador_hr/employee_hooks.py`, hook test bases + `locale/*`).
- T4: Full Ring 1 green + pre-commit + doc/i18n markers if new strings added. Route: inline. Status: done (315 passed, 9 skipped; pre-commit all Passed).

## Log

- L1 (user, verbatim): "bien, quiero hacer un hardening a nivel de test y flujos, para el tema multi compañía y multi moneda"
- L2 (2026-10-29): user decisions via prompt — currency "USD-only estricto", company "Aislamiento total". Scope is fail-closed rejection, not FX conversion.
- L3: evidence — `ec_hr/payroll/` has zero company/currency params today (only `accounting.py` mentions per-company maps as caller arg); `Salary Slip`/`Employee` custom Currency fields exist but hooks ignore `company`/`currency`/`exchange_rate`. Hardening therefore adds explicit guards, it does not change statutory math.
- L4 (2026-10-29): work units on feat/multi-company-currency-hardening — c1 pure-layer hardening (~324 lines), c2 Frappe flows + i18n (97 lines). Slice total ~421 past the ~400 guide; delivery cached: chain_strategy=stacked-to-main (user 2026-10-29). Push/PR/merge stay user decisions.
