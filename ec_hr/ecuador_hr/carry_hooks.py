"""Deduction-balance carry hooks for Salary Slip (dual-ring).

`before_validate` injects open balances into the slip's `ec_` inputs while
hrms has not calculated yet; `on_submit` writes the frozen shortfall back
into the ledger. Pure orchestration stays namespace-testable; only the two
entry points touch the database (no-ops without frappe).
"""

from typing import Any

try:
	import frappe
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 has no frappe package.
	frappe = None  # type: ignore[assignment]

	def _(message: str) -> str:
		return message


from ec_hr.payroll.deductions import carry_shortfall

_BALANCE_FIELDS = ("label", "kind", "balance", "monthly_amount", "salary_component", "slip_field")

#: Order field -> carried field written by the hook (assignment semantics).
_CARRIED_FIELD = {
	"ec_alimony_order": "ec_alimony_carried",
	"ec_advance_deduction": "ec_advance_carried",
}


def _row_dict(row: Any) -> dict[str, Any]:
	# Child rows arrive as Documents in bench, plain dicts in tests.
	if hasattr(row, "as_dict"):
		return dict(row.as_dict())
	return dict(row)


def apply_injection(doc: Any, balances: list[dict[str, Any]]) -> None:
	"""Write each balance's owed month into its carried field (assignment).

	Assignment (not accumulation) keeps repeated validates idempotent: the
	same owed value lands no matter how often the hook runs.
	"""
	for balance in balances:
		field = str(balance.get("slip_field") or "")
		if field not in _CARRIED_FIELD:
			raise ValueError(_("Unknown balance slip field: {0}.").format(field))
		owed = round(float(balance.get("monthly_amount") or 0.0) + float(balance.get("balance") or 0.0), 2)
		setattr(doc, _CARRIED_FIELD[field], owed)


def compute_writebacks(balances: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, float]:
	"""Map each component-tracked balance to its new carried balance."""
	applied_by_component = {str(row.get("salary_component")): float(row.get("amount") or 0.0) for row in rows}
	writebacks = {}
	for balance in balances:
		component = balance.get("salary_component")
		if not component:
			continue
		owed = round(float(balance.get("monthly_amount") or 0.0) + float(balance.get("balance") or 0.0), 2)
		writebacks[str(balance.get("label"))] = carry_shortfall(
			owed, applied_by_component.get(str(component), 0.0)
		)
	return writebacks


def _load_balances(employee: Any) -> list[dict[str, Any]]:
	assert frappe is not None
	return [
		dict(row)
		for row in frappe.get_all(
			"EC Deduction Balance", filters={"employee": employee}, fields=list(_BALANCE_FIELDS)
		)
	]


def inject_balances_into_slip(doc: Any, *_args: Any) -> None:
	"""before_validate: inflate `ec_` inputs with carried balances."""
	if frappe is None:  # pragma: no cover - no database in Ring 1.
		return
	apply_injection(doc, _load_balances(getattr(doc, "employee", None)))


def write_back_shortfall(doc: Any, *_args: Any) -> None:
	"""on_submit: persist the frozen shortfall per tracked component."""
	if frappe is None:  # pragma: no cover - no database in Ring 1.
		return
	rows = [
		_row_dict(row)
		for row in list(getattr(doc, "earnings", []) or []) + list(getattr(doc, "deductions", []) or [])
	]
	balances = _load_balances(getattr(doc, "employee", None))
	for label, new_balance in compute_writebacks(balances, rows).items():
		frappe.db.set_value(
			"EC Deduction Balance",
			{"employee": getattr(doc, "employee", None), "label": label},
			"balance",
			new_balance,
		)
