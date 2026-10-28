"""EC Family Charge controller: one Art. 97 family charge row.

Dual-ring contract: Ring 1 imports this with a stub `Document` base and gets
`ValueError` from `validate`; bench uses the real `Document` and converts the
same failure to `frappe.ValidationError` via `frappe.throw`.
"""

from datetime import date
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


from ec_hr.payroll.family import charge_rejection_reason


def _as_date(value: Any) -> Any:
	if isinstance(value, str):
		return date.fromisoformat(value)
	return value


class ECFamilyCharge(Document):
	def validate(self) -> None:
		reason = charge_rejection_reason(
			{
				"relation": self.relation,  # type: ignore[attr-defined]
				"birthdate": _as_date(self.birthdate),  # type: ignore[attr-defined]
				"disability_pct": float(self.disability_pct or 0.0),  # type: ignore[attr-defined]
				"accredited_on": _as_date(self.accredited_on),  # type: ignore[attr-defined]
				"ends_on": _as_date(self.ends_on),  # type: ignore[attr-defined]
			},
			date.today(),
		)
		if reason is not None:
			message = _("Invalid family charge: {0}").format(reason)
			if frappe is None:
				raise ValueError(message)
			frappe.throw(message)
