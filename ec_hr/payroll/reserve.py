"""Reserve-fund eligibility and amount (pure Python, no frappe).

Art. 196 grants one full Art. 95 remuneration per complete year past the
first, paid monthly as base/12 (the exact twelfth per user decision — not the
8.33% shorthand). Monthly-vs-IESS-accumulation is a payout election owned by
the Frappe layer.
"""

from datetime import date

from ec_hr.payroll.vacations import service_years


def is_eligible(hire_date: date, as_of: date) -> bool:
	"""Return True once the worker passes one full year of service."""
	return service_years(hire_date, as_of) >= 1


def monthly_amount(art95_monthly_base: float) -> float:
	"""Return the monthly reserve leg: base/12."""
	return round(art95_monthly_base / 12, 2)
