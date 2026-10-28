"""Profit-sharing distribution (pure Python, no frappe).

Splits an audited 15% pool: 10% weighted by days worked, 5% weighted by
Art. 97 family charges (per capita across the roster when nobody accredits
charges, per user decision). Each worker caps at 24 SBU (Art. 97.1); capped
excess funds the social-security solidarity regime. Weights run over audited
totals, so no 360/365 day-count convention is assumed. Per-worker legs round
to cents, matching planilla presentation.
"""

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


def distribute(
	total_pool: float,
	days: dict[str, float],
	charges: dict[str, int],
	*,
	sbu: float,
) -> dict[str, object]:
	"""Split `total_pool` into per-worker shares plus the solidarity excess."""
	if not days:
		raise ValueError(_("Profit sharing needs a non-empty roster."))
	pool10 = total_pool * 0.10
	pool5 = total_pool * 0.05
	total_days = sum(days.values())
	total_charges = sum(charges.get(worker, 0) for worker in days)
	headcount = len(days)
	shares: dict[str, float] = {}
	excess = 0.0
	cap = 24 * sbu
	for worker, worked in days.items():
		leg10 = pool10 * worked / total_days if total_days else 0.0
		worker_charges = charges.get(worker, 0)
		if total_charges:
			leg5 = pool5 * worker_charges / total_charges
		else:
			leg5 = pool5 / headcount
		gross = round(leg10 + leg5, 2)
		share = min(gross, cap)
		shares[worker] = round(share, 2)
		excess = round(excess + gross - share, 2)
	return {"shares": shares, "solidarity_excess": excess}
