# Ecuador HR for Frappe / ERPNext v16 (`ec_hr`)

Ecuadorian Human Resources and Payroll Localization for **Frappe Framework v16**, **ERPNext v16**, and **HRMS v16** on **Python 3.14** (version `16.0.0`, branch `version-16`).

`ec_hr` is a regional layer over [`frappe/hrms`](https://github.com/frappe/hrms) — the same independent-app model `hrms` itself follows relative to ERPNext: own lifecycle, own releases, reusable `hrms` documents (`Employee`, `Salary Component`, `Salary Structure`, `Salary Slip`) extended with Ecuadorian statutory rules (IESS contributions, decimo tercero/cuarto, fondos de reserva, utilidades, vacaciones, overtime surcharges). See [`docs/decisions/001-independent-app.md`](docs/decisions/001-independent-app.md) and [`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## Architecture Overview

1. **Pure Payroll Domain Core ([`ec_hr/payroll/`](ec_hr/payroll/))**:
   - [`ec_hr/payroll/legal.py`](ec_hr/payroll/legal.py): Statutory IESS contribution rates and base-splitting helpers as pure functions (no `frappe`, no `hrms`), covered by Ring 1 tests.
   - Future phases add overtime surcharges, decimo accruals, fondos de reserva, utilidades, and SBU-parameterized amounts here first — controllers only call in.

2. **Frappe v16 + HRMS Layer ([`ec_hr/ecuador_hr/`](ec_hr/ecuador_hr/))**:
   - Frappe v16 module (`Ecuador HR`) holding DocType JSON definitions, controllers, `create_custom_fields` definitions, and hooks into `hrms` payroll flow. Empty on day 0; Phase 2 opens it.

3. **Two-Ring TDD & Static Analysis Guardrails** (ported from `l10n_ec`):
   - **Ring 1 (Fast Inner Loop, `< 2s`, No DB required)**: `pytest` (`UnitTestCase`) + `pre-commit` (`ruff` `v0.14.10` pinned in both `pyproject.toml` and `.pre-commit-config.yaml`) on Python 3.14.
   - **Ring 2 (Full Frappe v16 + HRMS v16 + MariaDB 11.8 Integration)**: `bench --site test_site run-tests --app ec_hr` via `frappe.tests.UnitTestCase` / `IntegrationTestCase`.

---

## Quick Start: Fast Local TDD Loop (< 2 seconds)

```bash
# 1. Create an isolated Python 3.14 virtual environment using uv
uv venv --python 3.14

# 2. Install ec_hr in editable mode with test/linter dependencies
uv pip install -e ".[dev]"

# 3. Run pre-commit hooks (Ruff import sorter, linter, formatter, AST/JSON/TOML/YAML checks)
uv run pre-commit run --all-files

# 4. Run the fast unit & payroll domain suite with coverage
uv run pytest -v --cov=ec_hr/payroll --cov-report=term-missing -W error
```

---

## Documentation & Roadmap

- **[`docs/ROADMAP.md`](docs/ROADMAP.md)**: Phased build plan (Phase 0 scaffold done; Phases 1–5: payroll engine → hrms integration → statutory benefits → MDT/IESS reporting → i18n/workspace).
- **[`docs/decisions/001-independent-app.md`](docs/decisions/001-independent-app.md)**: Why `ec_hr` is an independent app over `hrms` instead of a feature branch or an `l10n_ec` submodule.
- **[`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)**: Ring 1 / Ring 2 commands, bench app order, translation workflow.
- **[`AGENTS.md`](AGENTS.md)**: Agent working contract (layering, test discovery, i18n, vendored skills).
