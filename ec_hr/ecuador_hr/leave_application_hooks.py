"""Leave Application validate hook: clinical certificate rule (dual-ring).

Ring 1 runs this with a plain namespace object and gets `ValueError`; bench
converts the same failure to `frappe.ValidationError` via `frappe.throw`.
"""

from typing import Any

try:
	import frappe
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 has no frappe package.
	frappe = None  # type: ignore[assignment]

	def _(message: str) -> str:
		return message


#: Leave types requiring a medical certificate on file.
CLINICAL_LEAVE_TYPES = frozenset({"Sick Leave", "Maternity Leave", "Paternity Leave"})


def _fail(message: str) -> None:
	if frappe is None:
		raise ValueError(message)
	frappe.throw(message)


def validate_leave_application(doc: Any) -> None:
	"""Require a medical certificate for clinical leaves (doc_events hook)."""
	if getattr(doc, "leave_type", None) in CLINICAL_LEAVE_TYPES:
		if not getattr(doc, "ec_medical_certificate", None):
			_fail(
				_("A medical certificate is required for {0}.").format(doc.leave_type)
			)
