"""EC SBU Rate controller: one SBU row (dual-ring, validation lives up)."""

try:
	from frappe.model.document import Document
except ImportError:  # pragma: no cover - Ring 1 has no frappe package.
	Document = object  # type: ignore[assignment,misc]


class ECSBURate(Document):
	pass
