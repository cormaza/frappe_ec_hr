import unittest

from ec_hr.payroll.identity import IdKind, ci_rejection_reason, classify_id, is_valid_ci, is_valid_ruc

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]


class TestCedulaValidation(UnitTestCase):
	"""Ecuadorian cedula: 10 digits, province 01-24/30, third digit 0-5, modulo-10 check.

	Test vectors: 1710034065 is the public example from ecuador-validator-js;
	check arithmetic (2,1 coefficients, sum 25, check digit 5) verified by hand.
	"""

	def test_known_valid_cedula(self) -> None:
		self.assertTrue(is_valid_ci("1710034065"))
		self.assertIsNone(ci_rejection_reason("1710034065"))

	def test_wrong_check_digit_rejected(self) -> None:
		self.assertFalse(is_valid_ci("1710034060"))
		self.assertIsNotNone(ci_rejection_reason("1710034060"))

	def test_invalid_province_rejected(self) -> None:
		self.assertFalse(is_valid_ci("3110034065"))

	def test_third_digit_for_juridical_prefix_rejected(self) -> None:
		self.assertFalse(is_valid_ci("1790034065"))

	def test_wrong_length_and_non_digits_rejected(self) -> None:
		self.assertFalse(is_valid_ci("171003406"))
		self.assertFalse(is_valid_ci("17100340655"))
		self.assertFalse(is_valid_ci("171003406A"))

	def test_whitespace_is_tolerated(self) -> None:
		self.assertTrue(is_valid_ci("  1710034065  "))


class TestRucValidation(UnitTestCase):
	"""RUC consensus algorithm (no official SRI checksum spec found).

	Natural: 10-digit cedula base + 3-digit suffix. Private (3rd digit 9):
	mod-11 over the first 9 digits with coefficients 4,3,2,7,6,5,4,3,2 —
	vector 1790000028001 hand-verified (weighted sum 47, remainder 3, check 8).
	Public (3rd digit 6): mod-11 over the first 8 digits with coefficients
	3,2,7,6,5,4,3,2 — vector 1760000070001 hand-verified (sum 59, remainder
	4, check 7), suffix 0001.
	"""

	def test_valid_natural_ruc(self) -> None:
		self.assertTrue(is_valid_ruc("1710034065001"))

	def test_natural_ruc_with_bad_base_rejected(self) -> None:
		self.assertFalse(is_valid_ruc("1710034060001"))

	def test_valid_private_ruc(self) -> None:
		self.assertTrue(is_valid_ruc("1790000028001"))

	def test_mod11_strict_ten_is_invalid(self) -> None:
		# Weighted sum 45, remainder 1 -> check digit 10: no digit matches.
		self.assertFalse(is_valid_ruc("1970000000001"))

	def test_branch_suffix_accepted(self) -> None:
		# Establishments beyond 001 share the checksum base.
		self.assertTrue(is_valid_ruc("1710034065002"))

	def test_private_ruc_with_bad_check_rejected(self) -> None:
		self.assertFalse(is_valid_ruc("1790000027001"))

	def test_valid_public_ruc(self) -> None:
		self.assertTrue(is_valid_ruc("1760000070001"))

	def test_wrong_length_rejected(self) -> None:
		self.assertFalse(is_valid_ruc("171003406500"))


class TestClassifyId(UnitTestCase):
	"""Structural classification only; checksums belong to the validators."""

	def test_classifies_cedula_rucs_and_unknown(self) -> None:
		self.assertEqual(classify_id("1710034065"), IdKind.CI)
		self.assertEqual(classify_id("1710034065001"), IdKind.RUC_NATURAL)
		self.assertEqual(classify_id("1790000028001"), IdKind.RUC_PRIVATE)
		self.assertEqual(classify_id("1760000070001"), IdKind.RUC_PUBLIC)
		self.assertEqual(classify_id("AB123456"), IdKind.UNCLASSIFIED)
		self.assertEqual(classify_id(""), IdKind.UNCLASSIFIED)

	def test_unicode_digits_do_not_crash(self) -> None:
		# Full-width digits pass isdigit(); the validators must answer bool.
		full_ci = "１７１００３４０６５"  # noqa: RUF001
		full_ruc = "１７１００３４０６５００１"  # noqa: RUF001
		self.assertIsInstance(is_valid_ci(full_ci), bool)
		self.assertIsInstance(is_valid_ruc(full_ruc), bool)
