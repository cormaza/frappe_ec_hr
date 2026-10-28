"""Thirteenth salary (Art. 111): twelfth of Art. 95 remuneration (pure Python).

Monthly payment is the default; accumulation to Dec 24 happens only on the
worker's written request (an election, owned by the Frappe layer). Exit pay
is the same twelfth over the base earned to date. Bases cannot be negative.
"""

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


def accrue(ytd_base: float) -> float:
	"""Return 1/12 of the year-to-date Art. 95 base."""
	if ytd_base < 0:
		raise ValueError(_("Thirteenth base cannot be negative."))
	return round(ytd_base / 12, 2)


def monthly_amount(period_base: float) -> float:
	"""Return the monthly XIII leg over the period's Art. 95 base."""
	return accrue(period_base)


def accumulated_due(ytd_base: float) -> float:
	"""Return the accumulated XIII due over the year-to-date base."""
	return accrue(ytd_base)


def proportional(base_to_date: float) -> float:
	"""Return the proportional XIII on exit over the base earned to date."""
	return accrue(base_to_date)
