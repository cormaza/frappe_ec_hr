# Phase 4 — Benefits II: Reserve, Profit-Sharing, Severance, Income Tax

## Header

Closing the statutory-benefit loop: reserve-fund eligibility/amount
(Art. 196 + C.D. 316), 15% profit split with the 24-SBU cap (Art. 97/97.1),
termination awards (Art. 185/188), and dependency income-tax withholding over
SRI-bracket parameters. Pure Ring 1 first, EC Settlement Act DocType after.

## Specs

- S1 (`reserve.py`): >1-year eligibility gate, monthly amount, election input.
- S2 (`profit_sharing.py`): days-weighted 10%, charges-weighted 5%,
  24-SBU cap with solidarity excess, undistributed bucket.
- S3 (`severance.py`): Art. 185 desahucio bonus, Art. 188 untimely scale.
- S4 (`income_tax.py`): annual table tax + monthly withholding net of rebate
  and YTD withholdings, tables always parameters.
- S5 (Frappe): EC Settlement Act DocType + controller + dual-ring tests.

## Tasks

- T1 (S1+S2): RED tests + `payroll/reserve.py` + `payroll/profit_sharing.py`.
- T2 (S3+S4): RED tests + `payroll/severance.py` + `payroll/income_tax.py`.
- T3 (S5): settlement DocType + controller + tests.
- T4: checks green + work-unit commits on `feat/phase-4-benefits-2`.

## Log

- L1 (user, verbatim): "adelante con el merge, vamos con fase 4"
- L2: Phase 3 merged ff into `version-16` (16 files, +497) and pushed
  (`71de9ac..6275e1a`).
- L3: User decisions — reserve base/12 exact ("Base / 12 exacto"), 5% split
  per-capita with no charges ("Reparto igualitario"), jubilación
  proportional deferred ("Diferir proporcional"), Settlement Act now
  ("DocType ahora").
