"""EC Settlement Act controller: termination cause + computed awards.

Dual-ring contract: Ring 1 imports this with a stub `Document` base and gets
`ValueError`; bench converts the same failures to `frappe.ValidationError`.
On validate, the Art. 185 bonus fills for 169.2/169.9 causes and the Art. 188
award fills for untimely dismissals; service years arrive fractional —
desahucio uses completed years, untimely rounds up per statute.
"""

import math
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


from ec_hr.payroll.contract import ends_with_desahucio_bonus
from ec_hr.payroll.severance import desahucio_bonus, untimely_award


def _fail(message: str) -> None:
	if frappe is None:
		raise ValueError(message)
	frappe.throw(message)


class ECSettlementAct(Document):
	def validate(self) -> None:
		cause = self.cause  # type: ignore[attr-defined]
		try:
			bonus_cause = ends_with_desahucio_bonus(cause)
		except ValueError:
			if cause != "untimely":
				_fail(_("Unknown termination cause: {0}.").format(cause))
				return
			bonus_cause = False
		last_monthly = float(self.last_monthly_remuneration or 0.0)  # type: ignore[attr-defined]
		if last_monthly < 0:
			_fail(_("Last monthly remuneration cannot be negative."))
		years = float(self.service_years or 0.0)  # type: ignore[attr-defined]
		if years < 0:
			_fail(_("Service years cannot be negative."))
		self.desahucio_amount = (  # type: ignore[attr-defined]
			desahucio_bonus(last_monthly, math.floor(years)) if bonus_cause else 0.0
		)
		self.untimely_amount = untimely_award(last_monthly, years) if cause == "untimely" else 0.0  # type: ignore[attr-defined]
