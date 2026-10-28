"""Family charges for profit-sharing distribution (pure Python, no frappe).

Implements the Art. 97 charge set: spouse or civil-union partner, children
under 18, and children with disabilities at any age. Each charge carries its
own accreditation and end dates; only charges valid on the reference date
count. This module counts and validates — the 10/5 profit split itself lives
in Phase 4.
"""

from datetime import date
from typing import Any

from ec_hr.payroll.age import age_on

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


_PARTNER_RELATIONS = frozenset({"spouse", "partner"})
_KNOWN_RELATIONS = frozenset({"spouse", "partner", "child", "child_with_disability"})


def charge_rejection_reason(charge: dict[str, Any], as_of: date) -> str | None:
	"""Return why `charge` is invalid on `as_of`, or None when it counts."""
	relation = charge.get("relation")
	if relation not in _KNOWN_RELATIONS:
		raise ValueError(_("Unknown family-charge relation: {0}.").format(relation))
	accredited_on = charge.get("accredited_on")
	if accredited_on is None or accredited_on > as_of:
		return _("Family charge is not accredited on the reference date.")
	ends_on = charge.get("ends_on")
	if ends_on is not None and ends_on < as_of:
		return _("Family charge ended before the reference date.")
	if relation in _PARTNER_RELATIONS:
		return None
	birthdate = charge.get("birthdate")
	if birthdate is None:
		return _("Child charge needs a birthdate.")
	if relation == "child":
		if age_on(birthdate, as_of) >= 18:
			return _("Child charge is 18 or older.")
		return None
	if float(charge.get("disability_pct") or 0.0) <= 0.0:
		return _("Child-with-disability charge needs disability evidence.")
	return None


def is_valid_charge(charge: dict[str, Any], as_of: date) -> bool:
	"""Return True when `charge` counts on `as_of` (Art. 97 set)."""
	return charge_rejection_reason(charge, as_of) is None


def count_valid_charges(charges: list[dict[str, Any]], as_of: date) -> int:
	"""Count the charges valid on `as_of` for the 5% profit-share leg."""
	return sum(1 for charge in charges if is_valid_charge(charge, as_of))
