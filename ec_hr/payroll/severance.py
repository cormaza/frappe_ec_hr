"""Termination awards (pure Python, no frappe).

Art. 185 pays 25% of the last monthly remuneration per year of service on
desahucio (and mutual-agreement exits). Art. 188 scales untimely dismissal to
3 months pay up to 3 years of service, then 1 month per year capped at 25 —
fractions count as full years, so this module ceils internally.
"""

import math

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


def desahucio_bonus(last_monthly: float, service_years: float) -> float:
	"""Return the Art. 185 bonus; fractions floor to completed years."""
	if service_years < 0:
		raise ValueError(_("Service years cannot be negative."))
	return round(0.25 * last_monthly * math.floor(service_years), 2)


def untimely_award(monthly: float, years: float) -> float:
	"""Return the Art. 188 award; fractional years round up (statute)."""
	if years < 0:
		raise ValueError(_("Service years cannot be negative."))
	complete = math.ceil(years)
	if complete <= 3:
		return round(3 * monthly, 2)
	return round(min(complete, 25) * monthly, 2)
