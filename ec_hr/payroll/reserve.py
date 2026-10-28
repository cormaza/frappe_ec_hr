"""Reserve-fund eligibility and amount (pure Python, no frappe).

Art. 196 grants one full Art. 95 remuneration per complete year past the
first, paid monthly as base/12 (the exact twelfth per user decision — not the
8.33% shorthand). Monthly-vs-IESS-accumulation is a payout election owned by
the Frappe layer.
"""

from datetime import date

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


from ec_hr.payroll.vacations import service_years


def is_eligible(hire_date: date, as_of: date) -> bool:
	"""Return True once the worker passes one full year of service."""
	return service_years(hire_date, as_of) >= 1


def monthly_amount(art95_monthly_base: float) -> float:
	"""Return the monthly reserve leg: base/12."""
	if art95_monthly_base < 0:
		raise ValueError(_("Reserve base cannot be negative."))
	return round(art95_monthly_base / 12, 2)
