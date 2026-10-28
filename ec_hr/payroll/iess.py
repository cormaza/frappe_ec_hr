"""IESS planilla legs and notice deadlines (pure Python, no frappe).

Planilla lines prorate the Art. 95 monthly base by billable days over the
30-day month and split legs with the seeded 9.45/11.15 rates. Notice
deadlines follow LSS Art. 73: entry within 15 days of hire, exit/salary news
within 3 days of the event.
"""

from datetime import date, timedelta

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


from ec_hr.payroll.legal import iess_contributions
from ec_hr.payroll.period import MONTH_BASE_DAYS


def planilla_line(monthly_base: float, billable_days: int) -> dict[str, float]:
	"""Build one worker's planilla legs for the month."""
	if not 0 <= billable_days <= MONTH_BASE_DAYS:
		raise ValueError(_("Billable days must fall within 0-30."))
	base = round(monthly_base * billable_days / MONTH_BASE_DAYS, 2)
	return {"base": base, **iess_contributions(base)}


def notice_deadlines(hire_date: date, exit_date: date | None) -> dict[str, date | None]:
	"""Return entry/exit notice deadlines for the employment dates."""
	return {
		"entry_by": hire_date + timedelta(days=15),
		"exit_by": exit_date + timedelta(days=3) if exit_date is not None else None,
	}


def overdue_days(deadline: date, as_of: date) -> int:
	"""Return days past `deadline` on `as_of` (zero when on time)."""
	return max((as_of - deadline).days, 0)
