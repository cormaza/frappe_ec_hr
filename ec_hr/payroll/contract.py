"""Contract kinds and termination routing (pure Python, no frappe).

Kinds follow CT Art. 11/14/17 plus part-time (CT Art. 82, guaranteed by
Mandato 8 Art. 2) and apprenticeship. `special_emergent` (LOAH) is carried as
provisional: its statutory text was not pinned during research, so its cause
map mirrors the general Art. 169 set until the LOAH text is verified in bench.

Cause codes are Art. 169 numerals ("169.1"-"169.9"), "172" (employer will with
visto bueno), and "173" (worker will with visto bueno). Causes enter as data
and are never inferred.
"""

from datetime import date, timedelta
from enum import Enum

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


class ContractKind(str, Enum):
	"""Statutory contract kinds relevant to payroll routing."""

	INDEFINITE = "indefinite"
	OBRA_CIERTA = "obra_cierta"
	EVENTUAL = "eventual"
	OCCASIONAL = "occasional"
	SEASONAL = "seasonal"
	APPRENTICESHIP = "apprenticeship"
	PART_TIME = "part_time"
	SPECIAL_EMERGENT = "special_emergent"


_ALL_169 = frozenset(f"169.{numeral}" for numeral in range(1, 10))

TERMINATION_CAUSES: dict[ContractKind, frozenset[str]] = {
	kind: _ALL_169 | frozenset({"172", "173"}) for kind in ContractKind
}

_PROVISIONAL = frozenset({ContractKind.SPECIAL_EMERGENT})

_DESAHUCIO_BONUS_CAUSES = frozenset({"169.2", "169.9"})
_VISTO_BUENO_CAUSES = frozenset({"172", "173"})


def is_provisional(kind: ContractKind) -> bool:
	"""Return True when `kind` awaits statutory text confirmation in bench."""
	return kind in _PROVISIONAL


def parse_contract_kind(value: str) -> ContractKind:
	"""Normalize a displayed (Title Case) kind to its identifier."""
	try:
		return ContractKind(value.strip().lower().replace(" ", "_"))
	except ValueError:
		raise ValueError(_("Unknown Ecuadorian Contract Kind: {0}.").format(value)) from None


def _check_known(cause: str) -> None:
	if cause not in _ALL_169 and cause not in _VISTO_BUENO_CAUSES:
		raise ValueError(_("Unknown termination cause: {0}.").format(cause))


def ends_with_desahucio_bonus(cause: str) -> bool:
	"""Return True when `cause` triggers the Art. 185 bonus (169.2, 169.9)."""
	_check_known(cause)
	return cause in _DESAHUCIO_BONUS_CAUSES


def requires_visto_bueno(cause: str) -> bool:
	"""Return True when `cause` needs prior inspector approval (172, 173)."""
	_check_known(cause)
	return cause in _VISTO_BUENO_CAUSES


def probation_end_date(start: date, days: int = 90) -> date:
	"""Return the probation end date `days` after `start` (default 90)."""
	return start + timedelta(days=days)
