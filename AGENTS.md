# Agent Instructions (`ec_hr` — Frappe v16 Ecuadorian HR Localization)

This repository is a standalone **Frappe Framework v16 / ERPNext v16 / HRMS v16** application (`ec_hr`, version `16.0.0`, branch `version-16`), targeting **Python 3.14**, providing Ecuadorian human resources and payroll localization (IESS contributions, statutory benefits: decimo tercero/cuarto, fondos de reserva, utilidades, vacaciones, overtime surcharges) as a regional layer over **frappe/hrms** — the same independent-app model as `frappe/hrms` itself. See `docs/decisions/001-independent-app.md`.

---

## 1. Repository Layout & Execution Context

Unlike a multi-app `frappe-bench` workspace (`apps/`, `sites/`, `env/`), this repository is the **standalone `ec_hr` app root**:

- **Ring 1 (Fast Local TDD & Static Analysis — Default Local Loop, `< 2s`)**:
  - Uses `.venv` (Python 3.14 managed via `uv`).
  - Run `pre-commit` hooks (Ruff import sorter, Ruff linter, Ruff formatter, JSON/TOML/YAML/AST checks):
    ```bash
    .venv/bin/pre-commit run --all-files --show-diff-on-failure
    ```
  - Run unit and payroll domain test suite:
    ```bash
    .venv/bin/pytest -v --cov=ec_hr/payroll --cov-report=term-missing -W error
    ```
  - Run the GitHub Actions `workflow_dispatch` job locally via `act` (note: `ubuntu-latest` must map to a Node 20+ image; Docker Hub `catthehacker` pulls return 401, use GHCR):
    ```bash
    act workflow_dispatch -W .github/workflows/ci.yml -j fast-tdd-unit -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest
    ```
- **Ring 2 (Full Frappe v16 + HRMS v16 + MariaDB 11.8 Bench Integration)**:
  - Note that `.agents/skills/frappe-app-dev/` supports both Standalone App Repository Mode and Full `frappe-bench` Mode.
  - Use **Frappe-Manager (`fm`)**, **`frappe_docker`**, or the `frappe-v16-integration` job in `.github/workflows/ci.yml` when executing full database-backed `bench` commands (`bench --site test_site migrate`, `bench --site test_site run-tests --app ec_hr`).
  - Bench app order matters: `frappe` -> `erpnext` -> `hrms` (`--branch version-16`) -> `ec_hr`; `hrms` resolves its own `erpnext` dependency, but install explicitly in that order on a fresh bench.

---

## 2. Architectural & Domain Layering Rules

1. **Pure Python Payroll Domain Layer (`ec_hr/payroll/`)**:
   - Contains statutory computation helpers (IESS contribution rates, overtime surcharges, decimo accruals) as pure functions over plain numbers/dicts.
   - **MUST NOT** have top-level `import frappe` dependencies so that Ring 1 tests execute in `< 2s` without a running MariaDB or Redis service.
   - **NEVER** hardcode the Annual Basic Salary (`Salario Basico Unificado`, SBU): it is set yearly by the Ministry of Labor (MDT) and must arrive as an explicit parameter (or a dated settings record), never as a constant.

2. **Frappe v16 + HRMS Module & DocType Layer (`ec_hr/ecuador_hr/`)**:
   - Contains Frappe v16 DocType JSON definitions, controllers (`Document` subclasses with `TYPE_CHECKING` `DF` annotations), programmatic custom field definitions, and co-located `test_<doctype>.py` modules.
   - Controllers integrate with `hrms` (`Salary Component`, `Salary Structure`, `Salary Slip`, `Employee`) via hooks and server-side rules, and delegate statutory computations to `ec_hr/payroll/`.

3. **Frappe v16 Test Runner Discovery Rule (Mandatory)**:
   - Frappe's `bench run-tests` uses `unittest.TestLoader().loadTestsFromModule(module)`, which **only** discovers methods on `unittest.TestCase` (`UnitTestCase` / `IntegrationTestCase`) subclasses and **silently ignores** bare top-level `def test_...()` functions.
   - Every test in any `test_*.py` file **MUST** be a method inside a `UnitTestCase` or `IntegrationTestCase` class (`from frappe.tests import IntegrationTestCase, UnitTestCase`, with `unittest.TestCase` fallback for standalone `pytest`).
   - `TestAppInstallability::test_frappe_test_runner_discovery_compliance` in `ec_hr/tests/test_app_installability.py` enforces this invariant automatically.

4. **Ring 2 Hard Lessons (Mandatory, ported from `l10n_ec`)**:
   - Fixture records in `ec_hr/fixtures/*.json` MUST include an explicit `"name"` key: bench's `import_doc` reads `doc["name"]` before insert (`KeyError: 'name'` otherwise), even for DocTypes with `autonome: field:<field>`.
   - Controller and hook tests MUST follow the dual-ring contract: build documents via `frappe.get_doc({...})` when frappe is present (direct `MyDoc(field=...)` instantiation has no DocType context under real Frappe and fails with `DocType None not found`), expect `(ValueError, frappe.ValidationError)` for validation errors (Ring 1 raises `ValueError`, bench converts `frappe.throw`), and bind the name with an explicit `import frappe` (`from frappe.tests import X` does NOT bind it, so a module-level `frappe.ValidationError` reference raises `NameError` at discovery). See `.agents/skills/frappe-app-dev/references/testing.md`.
   - App hooks (`hooks.py` `doc_events`) are cached by bench: syncing files manually into `apps/<app>` requires `bench --site <site> clear-cache` before the new handlers fire (`install-app`/`migrate` do it automatically).
   - Never sync code with multi-file `cp` into a directory: a mistyped destination silently scatters stray test copies that break bench discovery. Sync one file at a time with an explicit destination.
   - Bench v16 Redis ports come from `sites/common_site_config.json` (`11001`/`13001` on local no-sudo benches), not the classic `11000`/`12000`/`13000` — always confirm before assuming.
   - The Ruff version pinned in `pyproject.toml` MUST match the `rev:` in `.pre-commit-config.yaml`; an unpinned `ruff>=` drifts and the CI formatter step fails on upstream formatter changes (see `l10n_ec` history: formatter 0.17.x rewrote valid `except (A, B)` tuples).

5. **Verify Against Core Sources Before Assuming (Mandatory)**:
   - When implementation depends on framework behavior, read the installed core sources (`~/frappe-bench-v16/apps/frappe`, `.../erpnext`, `.../hrms`, pinned to the target branches) instead of assuming from docs or memory. See `.agents/skills/frappe-app-dev/references/existing-app.md`.
   - `hrms` owns `Employee`, `Salary Structure`, `Salary Slip`: reuse those DocTypes via regional customization (custom fields in code, fixtures, hooks) instead of forking parallel structures — the same reuse rule `l10n_ec` applies to ERPNext selling/buying documents.

---

## 3. Language Domain & Frappe v16 Gettext Translation (`i18n`) Contract

Following official Frappe v16 internationalization (`frappe/gettext/translate.py`) and regional localization apps (such as `resilient-tech/india-compliance` and `alyf-de/erpnext_germany`):

1. **100% English Source Code & Metadata**:
   - All Python/JS identifiers, module names, class names, comments, docstrings, commit messages, and markdown documentation **MUST** be in clean professional English.
   - All Frappe DocType names, `fieldname`s, `label`s, `description`s, Select `options`, Workspace titles, and Report labels **MUST** be defined in English in `.json` and `.py` files.
   - All user-facing strings in Python must be wrapped in `frappe._("...")` (in English), and all user-facing strings in JavaScript must be wrapped in `__("...")` (in English).

2. **Official Ecuadorian Labor-Law Protocol Exception**:
   - Only literal statutory identifiers mandated by Ecuadorian authorities stay in Spanish: IESS contribution concepts (`aporte personal`, `aporte patronal`), benefit names (`decimo tercero`, `decimo cuarto`, `fondos de reserva`), MDT/IESS form and report codes, and planilla line identifiers.

3. **Frappe v16 Gettext `locale/` Workflow (`es.po`)**:
   - Do **not** use legacy `translations/*.csv` files.
   - Spanish (`es`) UI translations live in `ec_hr/locale/main.pot` and `ec_hr/locale/es.po` (the exact Frappe v16 counterpart to OCA's `i18n/es.po`).
   - Extract, update, and compile translations using Frappe's Gettext CLI inside a bench environment:
     ```bash
     bench generate-pot-file --app ec_hr
     bench update-po-files --app ec_hr --locale es
     bench compile-po-to-mo --app ec_hr --locale es
     ```
   - User-facing literals in pure Python modules (no top-level `import frappe` allowed) use `from frappe import _` with an identity fallback (`def _(message: str) -> str: return message`), which keeps Ring 1 green while giving the bench pot scanner real `_()` call literals to extract.
   - `create_custom_fields` labels and Select options stay raw English (they are stored in the database and translated at display time); their translations are collected via extraction markers in `ec_hr/locale/i18n_markers.py`, which MUST never be imported at runtime.
   - `bench update-po-files` PRUNES msgids its scanner cannot see: every shipped msgid needs a real `_()` call or a marker entry. After the bench cycle, adopt the regenerated `main.pot`/`es.po` (headers, `#:` refs) as canonical.
   - `PO-Revision-Date` MUST use the full `YYYY-MM-DD HH:MM` format; a bare date breaks `bench build --app` translation compilation.
   - Core-owned strings (e.g. the `HR Manager` / `HR User` roles, `hrms` Salary Component labels) stay untranslated in our catalog; core ships their translations.

---

## 4. Workspace Skills (`.agents/skills/`)

The following skills from [`frappe/skills`](https://github.com/frappe/skills) are vendored in `.agents/skills/` for automatic and on-demand invocation (same set as `l10n_ec`):

- [`.agents/skills/frappe-app-dev/SKILL.md`](.agents/skills/frappe-app-dev/SKILL.md): Reference patterns for Frappe v16 DocTypes, controllers, hooks, permissions, background jobs, and testing (aligned for both Standalone App Repository Mode and Full `frappe-bench` Mode).
- [`.agents/skills/frappe-code-review/SKILL.md`](.agents/skills/frappe-code-review/SKILL.md): Structured checklist for reviewing Frappe pull requests and controller/database changes.
- [`.agents/skills/deep-app-audit/SKILL.md`](.agents/skills/deep-app-audit/SKILL.md): Comprehensive security (`S01`–`S42`) and correctness/customization (`A`/`B`/`C`/`D`) audit rules for Frappe applications.
- [`.agents/skills/code-style/SKILL.md`](.agents/skills/code-style/SKILL.md): Python/JS formatting, naming, early returns, and readability standards across the Frappe ecosystem.
