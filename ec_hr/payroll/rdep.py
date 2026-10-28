"""RDEP / Form 107 record datasets (pure Python, no frappe).

Builds validated per-worker annual dicts plus batch totals shared by the
RDEP annex and the Form 107 certificate. Serialization to the SRI XML/XSD
pins in bench against the live schema — this module never invents it.
"""

from typing import Any

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


REQUIRED_KEYS = ("id_number", "full_name", "gross", "taxable", "tax_caused", "withheld")
MONEY_KEYS = ("gross", "taxable", "tax_caused", "withheld")


def _check_record(record: dict[str, Any]) -> None:
	for key in REQUIRED_KEYS:
		if key not in record:
			raise ValueError(_("RDEP record lacks required key: {0}.").format(key))
	for key in MONEY_KEYS:
		if float(record[key]) < 0:
			raise ValueError(_("RDEP record field cannot be negative: {0}.").format(key))


def build_record(**fields: Any) -> dict[str, Any]:
	"""Validate and return one worker's annual RDEP record."""
	record = dict(fields)
	_check_record(record)
	return record


def validate_batch(records: list[dict[str, Any]]) -> dict[str, float]:
	"""Validate every record and return batch totals."""
	for record in records:
		_check_record(record)
	return {
		"workers": len(records),
		"gross": round(sum(float(record["gross"]) for record in records), 2),
		"taxable": round(sum(float(record["taxable"]) for record in records), 2),
		"tax_caused": round(sum(float(record["tax_caused"]) for record in records), 2),
		"withheld": round(sum(float(record["withheld"]) for record in records), 2),
	}
