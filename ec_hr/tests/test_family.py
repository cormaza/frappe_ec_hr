import unittest
from datetime import date

from ec_hr.payroll.family import count_valid_charges, is_valid_charge

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]

AS_OF = date(2026, 10, 28)


def _charge(**overrides):  # type: ignore[no-untyped-def]
	base = {
		"relation": "spouse",
		"birthdate": None,
		"disability_pct": 0.0,
		"accredited_on": date(2020, 1, 15),
		"ends_on": None,
	}
	base.update(overrides)
	return base


class TestFamilyCharges(UnitTestCase):
	"""Art. 97 family-charge set: spouse/partner, children under 18, children
	with disability at any age. Accreditation and end dates drive validity."""

	def test_accredited_spouse_counts(self) -> None:
		self.assertTrue(is_valid_charge(_charge(), AS_OF))

	def test_unaccredited_spouse_does_not_count(self) -> None:
		self.assertFalse(is_valid_charge(_charge(accredited_on=None), AS_OF))

	def test_ended_union_does_not_count(self) -> None:
		self.assertFalse(is_valid_charge(_charge(ends_on=date(2025, 5, 1)), AS_OF))

	def test_partner_counts_like_spouse(self) -> None:
		self.assertTrue(is_valid_charge(_charge(relation="partner"), AS_OF))

	def test_child_under_18_counts(self) -> None:
		charge = _charge(relation="child", birthdate=date(2015, 6, 1))
		self.assertTrue(is_valid_charge(charge, AS_OF))

	def test_child_exactly_18_excluded(self) -> None:
		charge = _charge(relation="child", birthdate=date(2008, 10, 28))
		self.assertFalse(is_valid_charge(charge, AS_OF))

	def test_child_with_disability_counts_at_any_age(self) -> None:
		charge = _charge(
			relation="child_with_disability",
			birthdate=date(1986, 3, 10),
			disability_pct=50.0,
		)
		self.assertTrue(is_valid_charge(charge, AS_OF))

	def test_child_with_disability_needs_evidence(self) -> None:
		charge = _charge(relation="child_with_disability", birthdate=date(1986, 3, 10))
		self.assertFalse(is_valid_charge(charge, AS_OF))

	def test_unknown_relation_fails_loud(self) -> None:
		with self.assertRaises(ValueError):
			is_valid_charge(_charge(relation="cousin"), AS_OF)

	def test_count_sums_only_valid(self) -> None:
		charges = [
			_charge(),
			_charge(relation="child", birthdate=date(2015, 6, 1)),
			_charge(relation="child", birthdate=date(2000, 1, 1)),
			_charge(accredited_on=None),
		]
		self.assertEqual(count_valid_charges(charges, AS_OF), 2)
		self.assertEqual(count_valid_charges([], AS_OF), 0)
