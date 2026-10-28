"""Employee IESS notice hook: warn-only deadlines (dual-ring).

Late or missing entry/exit notices draw fines, but stale data must never
block saving — so this hook warns via `frappe.msgprint` in bench and stays
silent in Ring 1. Pure warning builders stay directly testable.
"""

from datetime import date
from typing import Any

try:
	import frappe
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 has no frappe package.
	frappe = None  # type: ignore[assignment]

	def _(message: str) -> str:
		return message


from ec_hr.payroll.iess import notice_deadlines, overdue_days


def _as_date(value: Any) -> Any:
	# Fresh docs carry dates as ISO strings; normalize before comparing.
	if isinstance(value, str):
		return date.fromisoformat(value)
	return value


def _warn(message: str) -> None:
	if frappe is None:
		return
	frappe.msgprint(message, alert=True)


def entry_warning(doc: Any, as_of: date) -> str | None:
	"""Warn when the entry notice is late or missing past its deadline."""
	hire = _as_date(getattr(doc, "date_of_joining", None))
	if hire is None:
		return None
	deadline = notice_deadlines(hire, None)["entry_by"]
	assert isinstance(deadline, date)
	noticed = _as_date(getattr(doc, "ec_entry_notice_date", None))
	late_by = overdue_days(deadline, noticed or as_of)
	if late_by:
		return _("IESS entry notice is {0} days late.").format(late_by)
	return None


def exit_warning(doc: Any, as_of: date) -> str | None:
	"""Warn when the exit notice is late or missing past its deadline."""
	exit_date = _as_date(getattr(doc, "relieving_date", None))
	if exit_date is None:
		return None
	deadline = notice_deadlines(exit_date, exit_date)["exit_by"]
	assert isinstance(deadline, date)
	noticed = _as_date(getattr(doc, "ec_exit_notice_date", None))
	late_by = overdue_days(deadline, noticed or as_of)
	if late_by:
		return _("IESS exit notice is {0} days late.").format(late_by)
	return None


def validate_employee_notices(doc: Any, *_args: Any) -> None:
	"""Warn on overdue IESS notices; never blocks (doc_events hook)."""
	# Frappe passes the method name as a second positional arg; only today counts.
	today = date.today()
	for warning in (entry_warning(doc, today), exit_warning(doc, today)):
		if warning is not None:
			_warn(warning)
