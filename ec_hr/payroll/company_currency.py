"""Single-company isolation and USD-only guards (pure Python, no frappe).

Operational hardening with no statutory formula claimed: Ecuador payroll is
dollarized, so every amount is USD and every batch belongs to one company.

Operational hardening for multi-company / multi-currency flows: Ecuador
payroll is dollarized, so every amount is USD and every document batch
belongs to exactly one company. Mixed inputs fail closed.
"""

from collections.abc import Iterable
from typing import Any

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


def assert_usd_only(currency: str | None = None, exchange_rate: float | str | None = None) -> str:
	"""Require USD with a unit exchange rate; return the normalized code."""
	code = (currency or "").strip().upper() or "USD"
	if code != "USD":
		raise ValueError(_("Payroll amounts must be in USD, got currency: {0}.").format(currency))
	if exchange_rate is not None and abs(float(exchange_rate) - 1.0) > 1e-9:
		raise ValueError(_("Payroll exchange rate must be 1 (USD), got: {0}.").format(exchange_rate))
	return "USD"


def require_company(value: Any) -> str:
	"""Require a non-blank company identifier; return it stripped."""
	text = str(value or "").strip()
	if not text:
		raise ValueError(_("A company is required for this payroll operation."))
	return text


def assert_single_company(values: Iterable[Any], *, what: str = "company") -> str:
	"""Require at most one distinct company across `values`; return it.

	Blank entries are ignored. An empty input returns "" (nothing to mix);
	mixed identifiers raise fail-closed.
	"""
	distinct: list[str] = []
	for value in values:
		text = str(value or "").strip()
		if text and text not in distinct:
			distinct.append(text)
	if len(distinct) > 1:
		raise ValueError(_("Mixed {0} values are not allowed: {1}.").format(what, ", ".join(distinct)))
	return distinct[0] if distinct else ""
