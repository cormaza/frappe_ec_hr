"""Salary Slip validate hook: overtime caps and negative net pay guard.

Dual-ring contract: Ring 1 runs this with a plain namespace object and gets
`ValueError`; bench (frappe present) converts the same failures to
`frappe.ValidationError` via `frappe.throw`.
"""

from typing import Any

try:
	import frappe
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 has no frappe package.
	frappe = None  # type: ignore[assignment]

	def _(message: str) -> str:
		return message


from ec_hr.payroll.overtime import check_overtime_caps


def _fail(message: str) -> None:
	if frappe is None:
		raise ValueError(message)
	frappe.throw(message)


def validate_salary_slip(doc: Any) -> None:
	"""Validate overtime caps and net pay on a Salary Slip document (doc_events hook)."""
	daily_max = float(getattr(doc, "ec_overtime_daily_max_min", 0) or 0)
	weekly = float(getattr(doc, "ec_overtime_weekly_min", 0) or 0)
	violations = check_overtime_caps([daily_max], weekly)
	if violations:
		_fail("; ".join(violations))
	if float(getattr(doc, "net_pay", 0) or 0) < 0:
		_fail(_("Net pay cannot be negative."))
