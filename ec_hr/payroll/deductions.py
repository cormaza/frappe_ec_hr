"""Deduction waterfall, loan amortization, and alimony floor (pure Python).

Priority order is judicial first, then statutory, then voluntary; the net pay
never drops below `floor` and unapplied remainders return as shortfall
(carried forward by the caller). Loan schedules use the French system on the
outstanding balance only. CONA minimum percentages arrive as a yearly table
parameter — never hardcoded.
"""

from typing import Any

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


_PRIORITY = {"judicial": 0, "statutory": 1, "voluntary": 2}


def apply_waterfall(
	gross: float, deductions: list[dict[str, Any]], *, floor: float = 0.0
) -> dict[str, dict[str, float] | float]:
	"""Apply deductions by priority; return applied, net, and shortfall.

	Same-label rows merge first (amounts summed, highest priority wins), so a
	creditor listed twice is treated as one combined claim.
	"""
	for deduction in deductions:
		if deduction.get("kind") not in _PRIORITY:
			raise ValueError(_("Unknown deduction kind: {0}.").format(deduction.get("kind")))
	merged: dict[str, dict[str, Any]] = {}
	for deduction in deductions:
		label = str(deduction["label"])
		entry = merged.setdefault(label, {"kind": deduction["kind"], "label": label, "monthly_amount": 0.0})
		if _PRIORITY[str(deduction["kind"])] < _PRIORITY[str(entry["kind"])]:
			entry["kind"] = deduction["kind"]
		entry["monthly_amount"] = round(
			float(entry["monthly_amount"]) + float(deduction["monthly_amount"]), 2
		)
	ordered = sorted(merged.values(), key=lambda item: _PRIORITY[str(item["kind"])])
	applied: dict[str, float] = {}
	shortfall: dict[str, float] = {}
	available = gross - floor
	for deduction in ordered:
		label = str(deduction["label"])
		amount = round(float(deduction["monthly_amount"]), 2)
		taken = round(min(amount, max(available, 0.0)), 2)
		applied[label] = taken
		available = round(available - taken, 2)
		if taken < amount:
			shortfall[label] = round(amount - taken, 2)
	return {"applied": applied, "net": round(floor + max(available, 0.0), 2), "shortfall": shortfall}


def amortize(principal: float, *, monthly_rate: float = 0.0, months: int) -> list[dict[str, float]]:
	"""Build a French-system schedule (interest on outstanding balance only)."""
	if months < 1:
		raise ValueError(_("Loan term must be at least one month."))
	if principal <= 0:
		raise ValueError(_("Loan principal must be positive."))
	if monthly_rate < 0:
		raise ValueError(_("Loan rate cannot be negative."))
	if monthly_rate == 0.0:
		installment = round(principal / months, 2)
	else:
		installment = round(principal * monthly_rate / (1 - (1 + monthly_rate) ** -months), 2)
	schedule = []
	balance = principal
	for _month in range(months):
		interest = round(balance * monthly_rate, 2)
		capital = round(installment - interest, 2)
		balance = round(balance - capital, 2)
		schedule.append(
			{"installment": installment, "interest": interest, "capital": capital, "balance": balance}
		)
	schedule[-1]["capital"] = round(schedule[-1]["capital"] + schedule[-1]["balance"], 2)
	schedule[-1]["installment"] = round(schedule[-1]["capital"] + schedule[-1]["interest"], 2)
	schedule[-1]["balance"] = 0.0
	return schedule


def cona_floor_pct(income_sbu: float, children: int, table: list[dict[str, Any]]) -> float:
	"""Return the CONA minimum percentage for `income_sbu` and `children`.

	`table` rows are `{"up_to_sbu": float, "pct": {1: .., 2: .., 3: ..}}`
	where key 3 covers 3 or more children; income above the last row uses the
	last row.
	"""
	if children < 1:
		raise ValueError(_("Alimony needs at least one child."))
	row = next((item for item in table if income_sbu <= float(item["up_to_sbu"])), table[-1])
	bracket = dict(row["pct"])
	return float(bracket[min(children, 3)])


def check_alimony_floor(
	order_amount: float,
	income: float,
	children: int,
	table: list[dict[str, Any]],
	*,
	income_sbu: float,
) -> str | None:
	"""Warn when a court-ordered amount sits below the CONA minimum."""
	floor_amount = round(income * cona_floor_pct(income_sbu, children, table), 2)
	if order_amount < floor_amount:
		return _("Court-ordered alimony {0} is below the CONA minimum {1}.").format(
			order_amount, floor_amount
		)
	return None


def carry_shortfall(owed: float, applied: float) -> float:
	"""Return the unpaid remainder to carry, floored at zero."""
	return round(max(owed - applied, 0.0), 2)
