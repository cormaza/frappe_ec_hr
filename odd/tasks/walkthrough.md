# Walkthrough — Payroll Flows on ec_test Desk

## Header

Browser-driven walkthrough of the general payroll processes on the local
bench site `ec_test` (frappe/erpnext/hrms/ec_hr): login, workspace, employee
onboarding scenarios (A-G), salary slip flow, clinical leave hook, settlement
act, settings. Screenshots + results recorded here; UI/UX, readability, and
consistency findings fixed inline as they appear.

## Specs

- S1: Login + Ecuador HR workspace visible with all cards/links working.
- S2: Employee scenarios — A valid cedula/indefinite, B invalid
  cedula-blocked + invalid-RUC-warned, C foreign passport/visa, D under-15
  blocked + 16-17 vacation band, E disability/substitute, F family charges,
  G contract kinds/probation.
- S3: Salary Structure/Slip with EC components (overtime, caps, alimony).
- S4: Leave Application certificate hook, Settlement Act computation,
  Settings SBU lookup.
- S5: Findings fixed (labels/order/help text/hooks), docs with screenshots.

## Tasks

- T1: access (hosts, login) + workspace tour.
- T2: employee scenarios A-D + fixes.
- T3: employee scenarios E-G + slip flow + fixes.
- T4: leave/settlement/settings + fixes.
- T5: walkthrough doc with evidence + commits.

## Log

- L1 (user, verbatim): "bien, quiero que hagamos el walktrough para los
  proceos generales de la nomina, alta de empleado(diferentes escenarios), y
  la prueba de los flujos con sus resultados, con capturas y explicaciones,
  lo que identifiques necesita para mejorar UI/UX, legibilidad y
  consistencia vamos a irlo corrigiendo"
- L2: Bench serve restarted (old process predated hrms/ec_hr: No module
  named 'hrms'); ec_test login 200 on :8000.
- L3: Findings fixed — F-001 EC fields dumped above standard fields (now a
  chained `Ecuadorian Details` section anchored on
  `create_user_automatically`, verified in screenshot); F-002 Selects
  silently defaulted to the first option (now blank-first `\n` options).
  Anchors verified against installed erpnext/hrms JSON (Employee lives in
  erpnext/setup, not hrms).
- L4: Walkthrough bugs — fresh docs carry ISO date strings: `_as_date`
  normalization in employee/notice hooks + settlement (server 500s fixed);
  doc_events handlers receive the method name positionally (sight unseen
  until bench): `*_args` tolerated everywhere (after catching `*_`
  shadowing gettext `_`).
- L5: Readability — F-003 redundant cedula message rephrased; F-004 added
  an explanatory description to the validated checkbox; F-005 Title Case
  display for kinds/regions/relations with lowercase normalization at the
  validate boundary (`parse_contract_kind`, `_normalize_relation`).
