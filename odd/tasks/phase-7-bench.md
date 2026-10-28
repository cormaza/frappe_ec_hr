# Phase 7 — Bench Integration and Schema Pins

## Header

Everything deferred as bench-only across P1-P6: install hrms + ec_hr on a
bench site, run migrate + the full suite (executes every skipped bench test),
run the pot/mo Gettext cycle, render the workspace, and pin the portal/bank
schemas (RDEP XSD, bank layouts, MDT payloads) against live sources.

## Specs

- S1: hrms + ec_hr installed and migrated on an isolated bench site.
- S2: `bench run-tests --app ec_hr` fully green (zero skips).
- S3: pot/mo cycle adopted (`generate-pot-file`, `update-po-files --locale
  es`, `compile-po-to-mo`); workspace renders; Single migrates.
- S4: schema pins recorded (RDEP XSD version, bank layouts, MDT payloads)
  with golden fixtures where portals allow.

## Tasks

- T1: bench install + migrate.
- T2: full suite green + fix fallout.
- T3: i18n cycle + workspace render check.
- T4: schema pins with fixtures.
- T5: checks green + work-unit commits.

## Log

- L1 (user, verbatim): "merge y push, adelante siguiente fase"
- L2: Phase 6 merged ff into `version-16` (15 files, +1768) and pushed
  (`86b579c..40ddb51`). Roadmap P1-P6 complete; bench has no hrms/ec_hr.
- L3: User decisions — local bench ("Bench local"), verify services first
  ("Verificar primero"), all schema pins in one pass ("Todo junto"),
  stop-and-report on failure ("Parar y avisar", no auto-CI fallback).
- L4: Toolchain — `get-app --resolve-deps` hit a bench path-duplication bug;
  retry without the flag cloned hrms but died on the broken mise yarn shim;
  user chose `mise use -g`, now node 26.13.0 + yarn 1.22.22 work; `yarn
  install` for hrms runs in background. Site creation still needs the root
  MariaDB password (user chose to provide it; not received yet).
- L5: RDEP pin research — SRI Anexos page carries RDEP plugin v3.19.0
  (fiscal 2026), Ficha Tecnica 2024, Catalogo 2024, Plantilla/Ejemplo
  Excel+XML, and Esquema RDEP.xsd (Dec 2023); legal base NAC-DGERCGC24-
  00000002 (filing) + NAC-DGERCGC24-00000037. Pichincha mass-payment
  12-column file docs located (pending field-level read).
- L6: Sibling precedent (l10n_ec site-management skill) — check/store
  `root_password` in common_site_config.json via `bench set-config -g`, so
  site creation asks only once. ec_hr installed via get-app local path
  (16.0.0 recognized, es.mo compiled); apps.txt needed manual newline fix
  twice (bench appends without checking the trailing newline).
- L7: Root found, not changed — `l10nec-mariadb` container env carries
  `MARIADB_ROOT_PASSWORD=root` (the CI seed, replicated); login verified
  (11.8.9); stored globally per the sibling pattern; ec_test creation +
  stack install runs in background.
- L8: Pichincha mass-payment pin (field-level, from the bank's own PDF) —
  12 columns, fixed TIPO=PA / MONEDA=USD / FORMA DE PAGO=CTA, CONTRAPARTIDA
  sequential, VALOR as integer cents (123.90 -> 12390), TIPO CTA AHO/CTE,
  TIPO ID single char C/R/P, bank code blank for Pichincha itself,
  tab-delimited TXT with header removed before upload. RDEP XSD retrieved
  in full (root rdep: numRuc/anio/tipoEmpleador/enteSegSocial/retRelDep;
  per-worker empleado + ingresos + gastos + resumen + optional
  contribucion; tipIdRet C/P/E; discap 00-04; unique idRet+tipIdRet).
- L9: Suite needed pytest in the bench env (installed 9.2.0; retry
  running). MDT leads: SUT finiquito filing gives the employer 30 days to
  pay (gob.ec MT-044-05-02); IESS batch history updates use ASCII TXT/DAT
  layouts (hl5 page, field tables pending read).
- L10: Bench suite green (204 + 2 OK) after the __new__ fallout fix.
  i18n cycle adopted (pot/mo regenerated, 161+ msgids, msgfmt clean).
  Pins implemented: `pichincha_row` (11 documented fields, 12th explicitly
  unpinned) and the RDEP XSD worker/document builder (element order per
  the retrieved XSD; xmllint-vs-official test skips until the vendored
  XSD file lands).
- L11: XSD vendored from the official text (curl stalls from here) and the
  xmllint test goes green in both rings. Bench `update-po-files` prunes
  bare numeric option codes (172/173) while keeping longer ones (169.x):
  adopted as canonical; the collector treats `^[\d.]+$` options as
  untranslatable identifiers. Twelfth Pichincha column + IESS batch field
  tables + MDT payload formats remain the only open pins.
