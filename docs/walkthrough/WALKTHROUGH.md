# Payroll Walkthrough — ec_test Desk Evidence

Browser-driven pass over the general payroll processes on the local bench
site `ec_test` (frappe 16.52 / erpnext 16.51 / hrms 16.52 / ec_hr 16.0.0,
company EC Test Company, USD, America/Guayaquil). Each flow states the
result; every finding was fixed inline and is recorded below with its fix.

## W1 — Access and workspace

- Bench serve restarted: the running process predated the hrms/ec_hr
  installs (`No module named 'hrms'` on first hit).
- Site routing headless: no sudo for `/etc/hosts`, so Chrome runs with
  `--host-resolver-rules="MAP ec_test 127.0.0.1"`.
- Setup wizard completed (English / Ecuador / America/Guayaquil / USD,
  EC Test Company / ECTC, no demo data).
- The Ecuador HR workspace renders with all cards and links working
  (`01-ecuador-hr-workspace.png`). It has no Desk-home app icon; users reach
  it via search or `/app/ecuador-hr` — accepted, standard for module
  workspaces.

## W2 — Employee onboarding scenarios

- **A (valid cedula, indefinite).** Juan Perez, Cedula 1710034065 → saved
  HR-EMP-00001 with `ec_id_validated` checked (`02-scenario-a-saved.png`).
- **B (invalid cedula → blocked).** 1710034060 → clean ValidationError and
  the doc stays unsaved (`03-scenario-b-blocked.png`). Same form with an
  invalid RUC Natural → saves with `ec_id_validated` unchecked, visible in
  the form (`04-scenario-b-ruc-flagged.png`, HR-EMP-00002).
- **C (foreign passport).** Carlos Mendoza, Passport P12345678, Venezuela,
  visa + permit expiry → saved HR-EMP-00003, validated. Visa/permit fields
  appear only for Passport via `depends_on` (`05-scenario-c-passport.png`).
- **D (under 15 → blocked).** Dob 2015-05-01 → "Employees under 15 cannot
  be hired (Codigo del Trabajo Art. 134)." (`06-scenario-d-under15-blocked.png`).
- **E (disability).** Luis Vega, 45%, CONADIS card + expiry + substitute →
  saved HR-EMP-00004; conditional card fields render on `disability_pct > 0`
  (`07-scenario-e-disability.png`).
- **F (family charges).** Spouse + Child rows on Juan via the child table →
  saved, 2 charges persisted (`08-scenario-f-charges-saved.png`).
- **G (kinds/probation).** Indefinite / Eventual / Apprenticeship saved with
  probation end 2027-01-10.

## W3 — Salary slip flow

- Holiday List + assignment + submitted Salary Structure required first
  (standard hrms preconditions; the assignment must be *submitted*).
- Slip for Juan, Oct 2026 (`09-slip-overtime-cap.png` header): Basic 1000,
  Daytime 15.00, Night 11.25, Premium 10.00 → gross 1036.25, advance 100 →
  net 936.25, every figure matching the pure modules to the cent
  (`11-slip-earnings.png`, with the Ecuadorian Payroll Inputs section).
- Zero-minute components (Extraordinary, Alimony) correctly skipped.
- The negative-net guard fired live during setup (gross 36.25 vs advance
  100) before Basic was configured.

## W4 — Leave, settlement, settings

- Sick Leave without certificate → "A medical certificate is required for
  Sick Leave." (`12-leave-cert-blocked.png`); with the file attached the
  application saves (HR-LAP-2026-00001, 3 days, `13-leave-saved.png`).
- EC Settlement Act 169.9 over 6 years at 1000 → desahucio 1500.00,
  numbered EC-SA-2026-0001 (`14-settlement-saved.png`).
- EC HR Settings Single saves the SBU table; `get_sbu(2025)` → 470.0
  (`15-settings-saved.png`).

## W5 — Deduction carryforward ledger

- Subject: Maria Lopez (HR-EMP-00002, Active, joined 2026-10-05), Nov 2026
  slip. Preconditions per standard hrms: submitted Salary Structure
  Assignment (EC Test Structure-1) plus a submitted Holiday List Assignment
  (HR-HLA-2026-00002 → EC Test Holidays 2026). Nov was the free period:
  Juan's Oct/Nov/Dec 2026 slips were already submitted by the earlier
  mechanics pass (recorded in `odd/tasks/carryforward.md` L2).
- Ledger entry: Walkthrough Alimony, Judicial, carried 0.00, monthly
  400.00, component EC Alimony Withholding, slip field `ec_alimony_order`
  (`16-carry-balance-form.png`, showing the U-001/U-002 descriptions).
- Slip `Sal Slip/HR-EMP-00002/00001` on save: `before_validate` injected
  `ec_alimony_carried = 400.00`; deduction row EC Alimony Withholding
  400.00; Basic 1000 → gross 1000, total deduction 400, net 600
  (`17-carry-slip-submitted.png`, Earnings & Deductions tab).
- On submit: `on_submit` wrote back `max(400 − 400, 0) = 0`; the ledger
  list shows Carried Balance $0.00 against Monthly Amount $400.00
  (`18-carry-balance-list.png`).
- Partial path (250 owed, 100 applied → 150 carried) stays covered by the
  bench mechanics evidence in `odd/tasks/carryforward.md` L2; forcing a
  partial through the Desk UI is not possible (hrms applies formula rows
  in full and guards negative net instead).

## Findings fixed during the pass

- **F-001 field order.** EC fields rendered above standard Employee fields.
  Fixed: chained `Ecuadorian Details` section anchored on
  `create_user_automatically` (anchors verified against the installed
  erpnext/hrms JSON; Employee lives in erpnext/setup).
- **F-002 silent Select defaults.** New docs silently defaulted to the first
  option (`indefinite`, `costa`). Fixed: blank-first `\n` options.
- **F-003 redundant message.** "not a valid cedula for Cedula" → "not a
  valid {type} number".
- **F-004 unexplained flag.** Added a description to `ec_id_validated`.
- **F-005 raw codes in UI.** Kinds/regions/relations display Title Case now
  (`Eventual`, `Costa`, `Child`), normalized to identifiers at the validate
  boundary (`parse_contract_kind`, `_normalize_relation`).
- **F-006 missing child table.** Family charges had no Table field on
  Employee → added `ec_family_charges`.
- **F-007 autoname mix.** Settlement used `format:` with dotted tokens and
  saved a literal name → `format:EC-SA-{YYYY}-{####}`.
- **Bugs caught by real saves.** Fresh docs carry ISO date strings:
  `_as_date` normalization in employee/notice hooks (two server 500s). Frappe
  passes the method name positionally to `doc_events` handlers: `*_args`
  tolerated (after catching `*_` shadowing gettext `_`). Salary Component
  seeds need `amount_based_on_formula = 1` plus an **upsert** in `ensure_*`
  (insert-only left stale rows); slip formulas use **bare field names**
  (`doc.` does not exist in the eval namespace).
- **Data migration lesson.** Renaming Select options orphans stored values
  (Frappe validates against the new list before our hook runs): existing
  docs were remapped (`indefinite` → `Indefinite`) and the rollout note is:
  option renames always ship a data patch.
- **F-008 unexplained tracking fields.** `salary_component` (silent
  no-carry when blank) and `slip_field` (raw `ec_*` field names, a hook
  contract that must stay) had no help text. Fixed: descriptions on both,
  with markers + `es.po` entries (`test_markers_covered` caught a partial
  sync mid-pass — markers without `es.po` — so both files now sync
  together).
- **F-009 amount-blind ledger list.** The balance list showed only
  ID/Employee/Label/Kind — no amounts on a ledger whose whole point is
  amounts. Fixed: `in_list_view` on Carried Balance and Monthly Amount
  (`18-carry-balance-list.png` proves the columns).
- **Accepted as-is.** EC-prefixed component names truncate in narrow grid
  columns (namespace clarity in shared lists wins over renaming seeded
  records); the workspace has no Desk-home icon (standard).
