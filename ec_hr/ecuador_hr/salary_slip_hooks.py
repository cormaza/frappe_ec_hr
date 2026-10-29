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


from ec_hr.payroll.company_currency import assert_single_company, assert_usd_only, require_company
from ec_hr.payroll.overtime import check_overtime_caps


def _fail(message: str) -> None:
	if frappe is None:
		raise ValueError(message)
	frappe.throw(message)


def _check_employee_company(doc: Any, company: str) -> None:
	"""Require the slip company to match the employee's company.

	Ring 1 compares the `employee_company` test seam when present; bench
	(frappe present) reads the linked Employee record instead.
	"""
	employee = getattr(doc, "employee", None)
	if not employee:
		return
	expected = getattr(doc, "employee_company", None)
	if expected is None and frappe is not None:
		expected = frappe.db.get_value("Employee", employee, "company")
	if expected is None:
		if frappe is None:
			return
		_fail(_("Employee {0} has no company; set it before running payroll.").format(employee))
	assert_single_company([company, expected], what="company")


def validate_salary_slip(doc: Any) -> None:
	"""Validate overtime caps and net pay on a Salary Slip document (doc_events hook)."""
	company = require_company(getattr(doc, "company", None))
	assert_usd_only(getattr(doc, "currency", None), getattr(doc, "exchange_rate", None))
	_check_employee_company(doc, company)
	daily_max = float(getattr(doc, "ec_overtime_daily_max_min", 0) or 0)
	weekly = float(getattr(doc, "ec_overtime_weekly_min", 0) or 0)
	violations = check_overtime_caps([daily_max], weekly)
	if violations:
		_fail("; ".join(violations))
	if float(getattr(doc, "net_pay", 0) or 0) < 0:
		_fail(_("Net pay cannot be negative."))
