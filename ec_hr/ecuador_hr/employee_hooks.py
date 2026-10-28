"""Employee validate hook: Ecuadorian identity, contract, and youth rules.

Dual-ring contract: Ring 1 runs this with a plain namespace object and gets
`ValueError`; bench (frappe present) converts the same failures to
`frappe.ValidationError` via `frappe.throw`. RUC checksum failures never
block: they flag `ec_id_validated = 0` and warn.
"""

from datetime import date
from typing import Any

try:
	import frappe
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 has no frappe package.
	frappe = None  # type: ignore[assignment]

	def _(message: str) -> str:
		return message


from ec_hr.payroll.age import YouthCategory, youth_category
from ec_hr.payroll.contract import ContractKind
from ec_hr.payroll.identity import IdKind, is_valid_ci, is_valid_ruc

_ID_TYPE_KIND = {
	"Cedula": IdKind.CI,
	"RUC Natural": IdKind.RUC_NATURAL,
	"RUC Private": IdKind.RUC_PRIVATE,
	"RUC Public": IdKind.RUC_PUBLIC,
	"Passport": None,
}


def _fail(message: str) -> None:
	if frappe is None:
		raise ValueError(message)
	frappe.throw(message)


def _warn(message: str) -> None:
	if frappe is None:
		return
	frappe.msgprint(message, alert=True)


def validate_employee(doc: Any) -> None:
	"""Validate Ecuadorian fields on an Employee document (doc_events hook)."""
	id_type = getattr(doc, "ec_id_type", None)
	id_number = (getattr(doc, "ec_id_number", None) or "").strip()
	if id_number:
		expected = _ID_TYPE_KIND.get(id_type) if id_type else None
		if id_type == "Passport":
			doc.ec_id_validated = 1
		elif expected == IdKind.CI:
			if not is_valid_ci(id_number):
				_fail(_("Ecuadorian ID Number is not a valid cedula for {0}.").format(id_type))
			doc.ec_id_validated = 1
		elif expected in (IdKind.RUC_NATURAL, IdKind.RUC_PRIVATE, IdKind.RUC_PUBLIC):
			if not is_valid_ruc(id_number):
				doc.ec_id_validated = 0
				_warn(_("Ecuadorian ID Number checksum is invalid; flagged for review."))
			else:
				doc.ec_id_validated = 1
		elif id_type is None:
			_fail(_("Ecuadorian ID Type is required with Ecuadorian ID Number."))
		else:
			_fail(_("Unknown Ecuadorian ID Type: {0}.").format(id_type))

	contract_kind = getattr(doc, "ec_contract_kind", None)
	if contract_kind:
		try:
			ContractKind(contract_kind)
		except ValueError:
			_fail(_("Unknown Ecuadorian Contract Kind: {0}.").format(contract_kind))

	disability_pct = float(getattr(doc, "ec_disability_pct", 0.0) or 0.0)
	if not 0.0 <= disability_pct <= 100.0:
		_fail(_("Disability Percentage must be between 0 and 100."))

	birthdate = getattr(doc, "date_of_birth", None)
	if birthdate and youth_category(birthdate, date.today()) == YouthCategory.UNDER_15:
		_fail(_("Employees under 15 cannot be hired (Codigo del Trabajo Art. 134)."))
