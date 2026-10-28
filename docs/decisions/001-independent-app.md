# ADR-001: `ec_hr` as an Independent App over `hrms`

- Status: accepted
- Date: 2026-10-28
- Context: Ecuadorian HR/payroll localization for Frappe v16

## Context

ERPNext keeps human resources in the independent [`frappe/hrms`](https://github.com/frappe/hrms) app instead of the ERPNext monolith: separate lifecycle, optional install, own release branches (`version-16` exists). Our tax localization already follows the same pattern (`cormaza/frappe_l10n_ec`, standalone `l10n_ec` app, own `version-16` branch, two-ring CI).

Ecuadorian payroll needs statutory rules (IESS, decimos, fondos de reserva, utilidades) that change on a legal calendar, not on the ERPNext calendar.

## Decision

Build Ecuadorian HR as the standalone app **`ec_hr`** (repo `frappe_ec_hr`, branch `version-16`), declared as a regional layer over `hrms`:

- `required_apps = ["frappe", "erpnext", "hrms"]`; bench installs in that order.
- Reuse `hrms` documents (`Employee`, `Salary Component`, `Salary Structure`, `Salary Slip`) via custom fields in code, fixtures, and hooks — never fork parallel structures.
- Pure statutory math lives in `ec_hr/payroll/` with no `frappe` import so Ring 1 stays `< 2s` without MariaDB/Redis.
- Share the proven harness with `l10n_ec`: same `pyproject`/`pre-commit`/CI shape, same `AGENTS.md` contract, same vendored skills, same Gettext `locale/` workflow.

## Alternatives Considered

1. Feature branch inside `frappe_l10n_ec`: rejected — HR has its own legal calendar and reviewer surface; mixing it into the SRI app doubles every review and risks the e-invoicing release train.
2. Submodule/monorepo: rejected — bench `get-app` resolves per-repo dependencies; a monorepo fights the tool instead of using it.
3. Forking `hrms` documents into custom DocTypes: rejected — upstream `hrms` updates would strand us; regional-customization-in-code is the documented Frappe pattern (`deep-app-audit` A07/A08).

## Consequences

- Two repos, two CIs, one shared contract: harness changes proven in either repo get ported consciously, not by drift.
- First functional milestone is Phase 1/2 of `docs/ROADMAP.md`; day-0 ships scaffold + IESS rate seed only.
