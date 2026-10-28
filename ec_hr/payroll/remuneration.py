"""Art. 95 remuneration classifier (pure Python, no frappe).

Included: everything received in money, services, or kind — overtime,
piece-work, commissions, profit participation, the IESS personal contribution
when assumed by the employer, night premium, and any accessory retribution
normal in the industry. Excluded: legal profit-share percentage, monthly
reserve funds, occasional viaticos/subsidies, thirteenth/fourteenth,
living-wage compensation, components being incorporated, and social-order
services. `contribution_base` sums only the included legs.
"""

from typing import Any

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


_INCLUDED = frozenset(
	{
		"salary",
		"overtime_day",
		"overtime_night",
		"extraordinary",
		"commission",
		"piecework",
		"profit_share",
		"employer_paid_iess",
		"night_premium",
		"normal_bonus",
	}
)

_EXCLUDED = frozenset(
	{
		"thirteenth",
		"fourteenth",
		"reserve_funds_monthly",
		"legal_profit_pct",
		"living_wage_compensation",
		"occasional_per_diem",
		"occasional_subsidy",
		"social_services",
		"pending_components",
	}
)


def is_remuneration(kind: str) -> bool:
	"""Return True when `kind` enters the Art. 95 remuneration base."""
	if kind in _INCLUDED:
		return True
	if kind in _EXCLUDED:
		return False
	raise ValueError(_("Unknown remuneration kind: {0}.").format(kind))


def contribution_base(items: list[dict[str, Any]]) -> float:
	"""Sum the amounts of the items that count as remuneration."""
	return round(sum(float(item["amount"]) for item in items if is_remuneration(str(item["kind"]))), 2)
