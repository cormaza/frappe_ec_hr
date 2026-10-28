# Phase 3 — Benefits I: Decimos, Vacations, Leave

## Header

Time-adjacent statutory benefits on top of the Phase 1-2 foundation:
XIII/XIV accrual (monthly vs accumulated), vacation accrual/liquidation/
provision (Art. 69/71), and leave durations with the employer/IESS salary
split (Art. 152 + sickness day-3/4 rule). Pure Ring 1 first, Frappe elections
and clinical-leave hooks after.

## Specs

- S1 (`thirteenth.py`): 1/12 of Art. 95 YTD base, monthly vs accumulated
  election, proportional on exit.
- S2 (`fourteenth.py`): SBU/12 monthly, accumulated by elapsed months,
  region cutoff dates (Costa Mar 15, Sierra Aug 15).
- S3 (`vacations.py`): anniversary-based accrual via age bands + seniority,
  1/24 liquidation, monthly provision.
- S4 (`leave.py`): maternity/paternity ladders (Art. 152), sickness
  employer/IESS split legs with explicit IESS rate.
- S5 (Frappe): Employee accumulation elections + region, Leave Application
  clinical-certificate hook. Bench-CI green.

## Tasks

- T1 (S1+S2): RED tests + `payroll/thirteenth.py` + `payroll/fourteenth.py`.
- T2 (S3): RED tests + `payroll/vacations.py`.
- T3 (S4): RED tests + `payroll/leave.py`.
- T4 (S5): elections + certificate hook + dual-ring tests.
- T5: checks green + work-unit commits on `feat/phase-3-benefits-1`.

## Log

- L1 (user, verbatim): "adelante fase 3"
- L2: User decisions — paternity max-ladder ("Escalera por máximo"), XIV
  elapsed-months only ("Solo meses corridos"), no sickness top-up
  ("Sin top-up"), elections + certificate hook ("Elecciones + hook").
- L3: T4 inline (small); overtime pairwise() per ruff RUF007.
