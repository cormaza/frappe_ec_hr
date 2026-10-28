"""Ecuadorian identification validation (pure Python, no frappe).

Covers the national `cedula` (10 digits: province prefix, third digit below 6,
modulo-10 check digit) and RUC numbers (13 digits: cedula-like base for natural
persons, modulo-11 for private/public entities). The checksum rules follow the
documented community consensus (Registro Civil / SRI): no official machine-
readable spec was found during research, so every vector is pinned in
`test_identity.py` and the algorithms stay `bench-verifiable`.
"""

from enum import Enum

try:
	from frappe import _
except ImportError:  # pragma: no cover - Ring 1 fallback, bench uses frappe._

	def _(message: str) -> str:
		return message


class IdKind(str, Enum):
	"""Structural identification kinds (no checksum implied)."""

	CI = "ci"
	RUC_NATURAL = "ruc_natural"
	RUC_PRIVATE = "ruc_private"
	RUC_PUBLIC = "ruc_public"
	UNCLASSIFIED = "unclassified"


_CI_COEFFICIENTS = (2, 1, 2, 1, 2, 1, 2, 1, 2)
_RUC_PRIVATE_COEFFICIENTS = (4, 3, 2, 7, 6, 5, 4, 3, 2)
_RUC_PUBLIC_COEFFICIENTS = (3, 2, 7, 6, 5, 4, 3, 2)


def _mod10_check(first_nine: str) -> int:
	total = 0
	for digit, coef in zip(first_nine, _CI_COEFFICIENTS, strict=True):
		product = int(digit) * coef
		total += product - 9 if product >= 10 else product
	return (10 - total % 10) % 10


def _mod11_check(base: str, coefficients: tuple[int, ...]) -> int:
	total = sum(int(digit) * coef for digit, coef in zip(base, coefficients, strict=True))
	return (11 - total % 11) % 11


def _province_valid(first_two: str) -> bool:
	province = int(first_two)
	return 1 <= province <= 24 or province == 30


def ci_rejection_reason(number: str) -> str | None:
	"""Return why `number` is not a valid cedula, or None when it is valid."""
	value = number.strip()
	if len(value) != 10 or not value.isdigit():
		return _("Cedula must be exactly 10 digits.")
	if not _province_valid(value[:2]):
		return _("Cedula province code must be 01-24 or 30.")
	if int(value[2]) > 5:
		return _("Cedula third digit must be below 6.")
	if _mod10_check(value[:9]) != int(value[9]):
		return _("Cedula check digit is invalid.")
	return None


def is_valid_ci(number: str) -> bool:
	"""Return True when `number` passes every cedula check."""
	return ci_rejection_reason(number) is None


def ruc_rejection_reason(number: str) -> str | None:
	"""Return why `number` is not a valid RUC, or None when it is valid."""
	value = number.strip()
	if len(value) != 13 or not value.isdigit():
		return _("RUC must be exactly 13 digits.")
	third = int(value[2])
	if third < 6:
		if ci_rejection_reason(value[:10]) is not None:
			return _("RUC natural-person base is not a valid cedula.")
		return None
	if third == 6:
		if _mod11_check(value[:8], _RUC_PUBLIC_COEFFICIENTS) != int(value[8]):
			return _("RUC public-entity check digit is invalid.")
		if value[9:] != "0001":
			return _("RUC public-entity suffix must be 0001.")
		return None
	if third == 9:
		if _mod11_check(value[:9], _RUC_PRIVATE_COEFFICIENTS) != int(value[9]):
			return _("RUC private-entity check digit is invalid.")
		return None
	return _("RUC third digit is not a known entity kind.")


def is_valid_ruc(number: str) -> bool:
	"""Return True when `number` passes every RUC check."""
	return ruc_rejection_reason(number) is None


def classify_id(number: str) -> IdKind:
	"""Classify `number` by structure alone (no checksum evaluated)."""
	value = number.strip()
	if len(value) == 10 and value.isdigit():
		return IdKind.CI
	if len(value) == 13 and value.isdigit():
		third = int(value[2])
		if third < 6:
			return IdKind.RUC_NATURAL
		if third == 6:
			return IdKind.RUC_PUBLIC
		if third == 9:
			return IdKind.RUC_PRIVATE
	return IdKind.UNCLASSIFIED
