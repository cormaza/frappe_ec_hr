"""Vacation accrual and liquidation (pure Python, no frappe).

Accrual is anniversary-based: the Art. 69 annual entitlement (age band via
`age.youth_category` plus the seniority uplift) prorated by full elapsed
months. Liquidation is the Art. 71 twenty-fourth of period earnings — one
linear function serving enjoyment pay, exit proportional, and the monthly
provision input.
"""

from datetime import date

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


from ec_hr.payroll.age import vacation_annual_days, youth_category


def service_years(hire_date: date, as_of: date) -> int:
	"""Return completed years of service on `as_of`."""
	years = as_of.year - hire_date.year
	if (as_of.month, as_of.day) < (hire_date.month, hire_date.day):
		years -= 1
	if years < 0:
		raise ValueError(_("Reference date is before the hire date."))
	return years


def _full_months(hire_date: date, as_of: date) -> int:
	months = (as_of.year - hire_date.year) * 12 + (as_of.month - hire_date.month)
	if as_of.day < hire_date.day:
		months -= 1
	if months < 0:
		raise ValueError(_("Reference date is before the hire date."))
	return months


def accrued_days(hire_date: date, as_of: date, birthdate: date) -> float:
	"""Return vacation days accrued on `as_of` for service since `hire_date`."""
	annual = vacation_annual_days(youth_category(birthdate, as_of), service_years(hire_date, as_of))
	return round(annual * _full_months(hire_date, as_of) / 12, 2)


def liquidation(period_earnings: float) -> float:
	"""Return the Art. 71 twenty-fourth of period earnings."""
	return round(period_earnings / 24, 2)


def provision(month_base: float) -> float:
	"""Return the monthly vacation provision over the month's earnings base."""
	return liquidation(month_base)
