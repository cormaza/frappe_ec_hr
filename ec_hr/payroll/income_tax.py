"""Dependency income-tax withholding (pure Python, no frappe).

SRI-bracket tables always arrive as parameters (`{"up_to": float | None,
"base_tax": float, "rate": float}` rows, `None` closing the top bracket):
yearly tables change, code must not. Monthly withholding spreads the net
annual figure over the remaining months with a floor at zero.
"""

from typing import Any

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


def annual_tax(base: float, table: list[dict[str, Any]]) -> float:
	"""Apply the SRI-bracket `table` to the projected annual `base`."""
	if not table:
		raise ValueError(_("Tax table cannot be empty."))
	previous: float | None = None
	for position, row in enumerate(table):
		up_to = row["up_to"]
		if up_to is None and position != len(table) - 1:
			raise ValueError(_("Only the last tax bracket may be open-ended."))
		if up_to is not None:
			if previous is not None and float(up_to) <= previous:
				raise ValueError(_("Tax brackets must be strictly increasing."))
			previous = float(up_to)
		if float(row["base_tax"]) < 0 or float(row["rate"]) < 0:
			raise ValueError(_("Tax bracket figures cannot be negative."))
	floor = 0.0
	for row in table:
		up_to = row["up_to"]
		if up_to is None or base <= float(up_to):
			return round(float(row["base_tax"]) + (base - floor) * float(row["rate"]), 2)
		floor = float(up_to)
	last = table[-1]
	return round(float(last["base_tax"]) + (base - floor) * float(last["rate"]), 2)


def monthly_withholding(
	projected_base: float,
	table: list[dict[str, Any]],
	*,
	rebate: float = 0.0,
	withheld_ytd: float = 0.0,
	months_remaining: int = 12,
) -> float:
	"""Spread (annual tax - rebate - YTD withheld) over `months_remaining`."""
	if months_remaining < 1:
		raise ValueError(_("Months remaining must be at least one."))
	if rebate < 0 or withheld_ytd < 0:
		raise ValueError(_("Rebate and withheld amounts cannot be negative."))
	net = annual_tax(projected_base, table) - rebate - withheld_ytd
	return round(max(net, 0.0) / months_remaining, 2)
