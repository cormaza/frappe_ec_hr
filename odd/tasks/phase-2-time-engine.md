# Phase 2 — Time Engine

## Header

One shared day/hour foundation for every later benefit: 30-day month and
period helpers, day/night split with Art. 49/55 surcharges, overtime caps,
deduction waterfall (advances/loans/judicial), and the Art. 95
remuneration/viaticos classifier. Pure Ring 1 first, Frappe salary components
and slip hooks after (same dual-ring pattern as Phase 1).

## Specs

- S1 (`period.py`): month boundaries, hire/exit proration, absence-day
  proration on the IESS month base in `America/Guayaquil`.
- S2 (`overtime.py`): day/night split (night 19:00-06:00), +25% night premium,
  +50%/+100% supplements, +100% weekend/holiday, midnight-crossing legs,
  4h/day + 12h/week cap checks.
- S3 (`deductions.py`): advance/loan amortization, priority waterfall
  (judicial > statutory > voluntary), CONA alimony floor from yearly tables,
  negative-net-pay guard.
- S4 (`remuneration.py`): Art. 95 `is_remuneration(kind)` classifier feeding
  every contribution/benefit base.
- S5 (Frappe): Salary Slip input custom fields + `salary_components` fixture
  specs (formulas calling the pure modules) + slip validate hook (overtime
  caps fail, negative net fails). Alimony CONA floor stays pure-only until
  the judicial-withholding record flow (Phase 5). Bench-CI green.

## Tasks

- T1 (S1): RED tests + `payroll/period.py` — route: inline.
- T2 (S2): RED tests + `payroll/overtime.py` — route: inline.
- T3 (S3): RED tests + `payroll/deductions.py` — route: inline.
- T4 (S4): RED tests + `payroll/remuneration.py` — route: inline.
- T5 (S5): components + slip hooks + dual-ring tests — route: inline.
- T6: checks green + work-unit commits on `feat/phase-2-time-engine`.

## Log

- L1 (user, verbatim): "termina con el merge directamente, y sigue con fase 2"
- L2: Phase 1 merged ff into `version-16` (18 files, +1148), branch deleted.
- L3: User decisions — night overtime full stack 225% ("Stack completo
  225%"), IESS 30-day base assumed now ("Asumir 30 ahora"), amortization
  with optional rate ("Cuotas + tasa opcional"), court-ordered alimony +
  CONA floor warning ("Orden + piso CONA").
- L4: T5 scoping — slip hook covers caps + net guard only; alimony floor
  enforced at the withholding record (Phase 5), pure helper tested in T3.
- L5: T5 via `gentle-ai-worker`; inline corrections — formulas use plain
  arithmetic (hrms sandbox has no payroll modules in scope; factors pinned
  per component in tests), fixed ruff B905 `zip strict` in identity.py,
  setup.py normalized to tabs. Suite: 106 passed, 4 skipped; pre-commit
  fully green.
