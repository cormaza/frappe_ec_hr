"""Provisioning double-entry stubs (pure Python, no frappe).

Operational module with no statutory formula claimed: charts of accounts
vary per company, so account pairs arrive as an explicit caller map.
Missing mappings fail loud naming the concept.
"""

from typing import Any

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


def provision_lines(
	items: list[dict[str, Any]], account_map: dict[str, dict[str, str]]
) -> list[dict[str, Any]]:
	"""Expand provision items into balanced debit/credit lines."""
	lines = []
	for item in items:
		concept = str(item["concept"])
		if concept not in account_map:
			raise ValueError(_("No accounts mapped for provision concept: {0}.").format(concept))
		amount = round(float(item["amount"]), 2)
		lines.append({"account": account_map[concept]["expense"], "debit": amount, "credit": 0.0})
		lines.append({"account": account_map[concept]["liability"], "debit": 0.0, "credit": amount})
	return lines
