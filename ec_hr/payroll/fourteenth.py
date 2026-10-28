"""Fourteenth salary (Art. 113): twelfth of the SBU (pure Python, no frappe).

The SBU arrives as an explicit parameter (never a constant). Accumulation
counts elapsed months only — no cycle starts assumed per user decision; the
verified region cutoffs (Costa Mar 15, Sierra/Amazonia Aug 15) are exposed
for the filing layer.
"""

from enum import Enum

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


class Region(str, Enum):
	"""XIV school-regime circumscriptions."""

	COSTA = "costa"
	SIERRA = "sierra"


def monthly_amount(sbu: float) -> float:
	"""Return the monthly XIV leg: SBU/12."""
	if sbu < 0:
		raise ValueError(_("SBU cannot be negative."))
	return round(sbu / 12, 2)


def accumulated_due(sbu: float, elapsed_months: int) -> float:
	"""Return SBU/12 scaled by elapsed months in the accumulation cycle."""
	if elapsed_months < 0:
		raise ValueError(_("Elapsed months cannot be negative."))
	if elapsed_months > 12:
		raise ValueError(_("Elapsed months cannot exceed a 12-month cycle."))
	return round(sbu / 12 * elapsed_months, 2)


def cutoff(region: Region) -> tuple[int, int]:
	"""Return the (month, day) accumulation deadline for `region`."""
	return (3, 15) if region == Region.COSTA else (8, 15)
