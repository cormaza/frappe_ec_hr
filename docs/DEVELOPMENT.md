# Development Guide (`ec_hr`)

## Ring 1 — Fast Local Loop (default, `< 2s`)

```bash
uv venv --python 3.14
uv pip install -e ".[dev]"
uv run pre-commit run --all-files --show-diff-on-failure
uv run pytest -v --cov=ec_hr/payroll --cov-report=term-missing -W error
```

Run the CI job locally via `act` (GHCR image: Docker Hub `catthehacker` pulls return 401):

```bash
act workflow_dispatch -W .github/workflows/ci.yml -j fast-tdd-unit -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest
```

## Ring 2 — Bench Integration (on demand)

Bench app order is load-bearing: `frappe` -> `erpnext` -> `hrms` (`--branch version-16`) -> `ec_hr`.

```bash
bench get-app erpnext --branch version-16 --resolve-deps
bench get-app hrms --branch version-16 --resolve-deps
bench get-app ec_hr <path-or-url> --resolve-deps
bench --site test_site install-app erpnext
bench --site test_site install-app hrms
bench --site test_site install-app ec_hr
bench --site test_site migrate
bench --site test_site run-tests --app ec_hr
```

## Translations

Inside a bench environment:

```bash
bench generate-pot-file --app ec_hr
bench update-po-files --app ec_hr --locale es
bench compile-po-to-mo --app ec_hr --locale es
```

`PO-Revision-Date` uses `YYYY-MM-DD HH:MM`. Adopt regenerated `main.pot`/`es.po` as canonical.
