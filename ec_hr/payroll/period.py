"""Payroll month and IESS billable-day helpers (pure Python, no frappe).

The IESS contribution month operates on a 30-day base: a fully-worked month
bills 30 days however long the calendar month is (operational consensus across
planilla guides and payroll calculators; exact manual wording is still
to-verify-in-bench). Partial months scale calendar days onto the base:
`round(30 * calendar_days / month_length)`, absences subtract day-for-day
with a floor at zero.
"""

import calendar
from datetime import date

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


#: IESS contribution month base, in days.
MONTH_BASE_DAYS = 30


def month_bounds(year: int, month: int) -> tuple[date, date]:
	"""Return the first and last calendar dates of `year`-`month`."""
	last_day = calendar.monthrange(year, month)[1]
	return date(year, month, 1), date(year, month, last_day)


def _scaled(calendar_days: int, month_length: int) -> int:
	return round(MONTH_BASE_DAYS * calendar_days / month_length)


def iess_billable_days(
	year: int,
	month: int,
	*,
	hire_date: date | None = None,
	exit_date: date | None = None,
	absence_days: int = 0,
) -> int:
	"""Return billable days (0-30) for the month.

	`hire_date`/`exit_date` outside the month raise `ValueError`; dates on the
	outer side (hired before, exited after) count as a full month.
	"""
	if absence_days < 0:
		raise ValueError(_("Absence days cannot be negative."))
	first, last = month_bounds(year, month)
	if hire_date is not None and hire_date > last:
		raise ValueError(_("Hire date is after the payroll month."))
	if exit_date is not None and exit_date < first:
		raise ValueError(_("Exit date is before the payroll month."))
	month_length = (last - first).days + 1
	start = max(hire_date, first) if hire_date is not None else first
	end = min(exit_date, last) if exit_date is not None else last
	if end < start:
		raise ValueError(_("Hire date is after exit date."))
	present = (end - start).days + 1
	return max(_scaled(present, month_length) - absence_days, 0)


def worked_fraction(
	year: int,
	month: int,
	*,
	hire_date: date | None = None,
	exit_date: date | None = None,
	absence_days: int = 0,
) -> float:
	"""Return the worked fraction of the 30-day month (0.0-1.0)."""
	return (
		iess_billable_days(year, month, hire_date=hire_date, exit_date=exit_date, absence_days=absence_days)
		/ MONTH_BASE_DAYS
	)
