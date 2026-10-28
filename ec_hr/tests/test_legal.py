import unittest

from ec_hr.payroll.legal import IESS_EMPLOYER_RATE_PCT, IESS_PERSONAL_RATE_PCT, iess_contributions

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]


class TestIessContributions(UnitTestCase):
	"""Statutory IESS contribution rates (day-0 payroll domain seed)."""

	def test_statutory_rates(self) -> None:
		self.assertEqual(IESS_PERSONAL_RATE_PCT, 9.45)
		self.assertEqual(IESS_EMPLOYER_RATE_PCT, 11.15)

	def test_contributions_split_and_round_to_cents(self) -> None:
		parts = iess_contributions(1000.0)
		self.assertEqual(parts["personal"], 94.5)
		self.assertEqual(parts["employer"], 111.5)
		self.assertEqual(parts["total"], 206.0)

	def test_zero_base_contributes_zero(self) -> None:
		self.assertEqual(iess_contributions(0.0), {"personal": 0.0, "employer": 0.0, "total": 0.0})
