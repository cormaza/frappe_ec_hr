"""EC Deduction Balance controller: one carried shortfall (dual-ring).

Ring 1 imports this with a stub `Document` base and gets `ValueError`;
bench converts the same failures to `frappe.ValidationError`.
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


_KINDS = frozenset({"judicial", "statutory", "voluntary"})


def _fail(message: str) -> None:
	if frappe is None:
		raise ValueError(message)
	frappe.throw(message)


def normalize_kind(value: Any) -> str:
	"""Normalize a displayed kind to its identifier."""
	text = str(value or "").strip().lower()
	if text not in _KINDS:
		_fail(_("Unknown deduction kind: {0}.").format(value))
	return text


class ECDeductionBalance(Document):
	def validate(self) -> None:
		# Stored Title Case (Frappe validates Select options after this hook);
		# logic normalizes via normalize_kind(), mirroring contract kinds.
		normalize_kind(self.kind)  # type: ignore[attr-defined]
		if not str(self.label or "").strip():  # type: ignore[attr-defined]
			_fail(_("Deduction label is required."))
