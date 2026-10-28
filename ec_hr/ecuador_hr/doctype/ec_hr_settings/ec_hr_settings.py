"""EC HR Settings controller: yearly statutory parameters (dual-ring).

The Single stores the SBU-by-year table plus the active CONA/SRI table years
and RDEP schema version. Years must be unique and positive, amounts positive.
Ring 1 imports this with a stub `Document` base and gets `ValueError`.
"""

from typing import Any

try:
	import frappe
	from frappe import _
	from frappe.model.document import Document
except ImportError:  # pragma: no cover - Ring 1 has no frappe package.
	frappe = None  # type: ignore[assignment]
	Document = object  # type: ignore[assignment,misc]

	def _(message: str) -> str:
		return message


def _fail(message: str) -> None:
	if frappe is None:
		raise ValueError(message)
	frappe.throw(message)


class ECHRSettings(Document):
	def validate(self) -> None:
		seen = set()
		for row in getattr(self, "sbu_rates", None) or []:  # type: ignore[attr-defined]
			year = int(row.get("year") or 0)
			amount = float(row.get("amount") or 0.0)
			if year <= 0:
				_fail(_("SBU rate year must be positive."))
			if year in seen:
				_fail(_("Duplicate SBU rate year: {0}.").format(year))
			seen.add(year)
			if amount <= 0:
				_fail(_("SBU amount must be positive for year {0}.").format(year))

	def get_sbu(self, year: int) -> float:
		"""Return the SBU amount for `year`, failing loud when missing."""
		for row in getattr(self, "sbu_rates", None) or []:  # type: ignore[attr-defined]
			if int(row.get("year") or 0) == year:
				return float(row.get("amount") or 0.0)
		if frappe is None:
			raise ValueError(_("No SBU rate stored for year {0}.").format(year))
		frappe.throw(_("No SBU rate stored for year {0}.").format(year))
		return 0.0
