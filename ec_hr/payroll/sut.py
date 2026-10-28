"""SUT manual-filing dataset (pure Python, no frappe).

The SUT acta is a portal web form (gob.ec MT-044-05-02): online worker data,
a system-generated acta signed by both parties (PDF), and the payment proof
(PDF), payable within 30 days (MDT-2017-0135 Art 6-7). This module checks an
EC Settlement Act-shaped dict for filing readiness — it never pretends the
portal accepts files.
"""

from datetime import date, timedelta
from typing import Any


def payment_deadline(filing_date: date) -> date:
	"""Return the 30-day payment deadline for a filed acta."""
	return filing_date + timedelta(days=30)


_REQUIRED = (
	"id_number",
	"full_name",
	"hire_date",
	"exit_date",
	"cause",
	"signed_acta",
	"payment_proof",
)


def sut_checklist(act: dict[str, Any]) -> list[str]:
	"""List filing blockers for `act`; empty means ready to file in SUT."""
	issues = []
	for field in _REQUIRED:
		if not act.get(field):
			issues.append(f"missing:{field}")
	lines = act.get("lines") or []
	if not lines:
		issues.append("missing:lines")
	for line in lines:
		if float(line.get("amount") or 0.0) <= 0:
			issues.append("line-not-positive")
			break
	if lines:
		total = round(sum(float(line.get("amount") or 0.0) for line in lines), 2)
		if round(float(act.get("total") or 0.0), 2) != total:
			issues.append("total-mismatch")
	return issues
