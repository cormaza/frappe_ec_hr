import unittest

from ec_hr.payroll.income_tax import annual_tax, monthly_withholding
from ec_hr.payroll.severance import desahucio_bonus, untimely_award

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]

TABLE = [
	{"up_to": 12081.0, "base_tax": 0.0, "rate": 0.0},
	{"up_to": 15387.0, "base_tax": 0.0, "rate": 0.05},
	{"up_to": None, "base_tax": 165.0, "rate": 0.10},
]


class TestDesahucioBonus(UnitTestCase):
	"""Art. 185: 25% of the last monthly pay per year of service."""

	def test_bonus(self) -> None:
		self.assertEqual(desahucio_bonus(1000.0, 4), 1000.0)
		self.assertEqual(desahucio_bonus(1000.0, 0), 0.0)

	def test_negative_years_fail(self) -> None:
		with self.assertRaises(ValueError):
			desahucio_bonus(1000.0, -1)


class TestUntimelyAward(UnitTestCase):
	"""Art. 188: 3 months to 3 years, 1 month/year beyond capped at 25;
	fractions count as full years."""

	def test_scale(self) -> None:
		self.assertEqual(untimely_award(1000.0, 0), 3000.0)
		self.assertEqual(untimely_award(1000.0, 2), 3000.0)
		self.assertEqual(untimely_award(1000.0, 5), 5000.0)
		self.assertEqual(untimely_award(1000.0, 30), 25000.0)

	def test_fraction_rounds_up(self) -> None:
		self.assertEqual(untimely_award(1000.0, 2.3), 3000.0)
		self.assertEqual(untimely_award(1000.0, 3.2), 4000.0)

	def test_negative_years_fail(self) -> None:
		with self.assertRaises(ValueError):
			untimely_award(1000.0, -1)


class TestAnnualTax(UnitTestCase):
	"""SRI-bracket parameters (shape mirrors the SRI natural-persons table)."""

	def test_brackets(self) -> None:
		self.assertEqual(annual_tax(10000.0, TABLE), 0.0)
		self.assertEqual(annual_tax(14000.0, TABLE), 95.95)
		self.assertEqual(annual_tax(20000.0, TABLE), 626.3)

	def test_empty_table_fails(self) -> None:
		with self.assertRaises(ValueError):
			annual_tax(10000.0, [])


class TestMonthlyWithholding(UnitTestCase):
	"""(Annual tax - rebate - YTD withheld) / months left, floored at zero."""

	def test_monthly_split(self) -> None:
		self.assertEqual(monthly_withholding(14000.0, TABLE), 8.0)

	def test_rebate_and_floor(self) -> None:
		self.assertEqual(monthly_withholding(14000.0, TABLE, rebate=95.95), 0.0)
		self.assertEqual(monthly_withholding(14000.0, TABLE, withheld_ytd=500.0), 0.0)

	def test_no_months_left_fails(self) -> None:
		with self.assertRaises(ValueError):
			monthly_withholding(14000.0, TABLE, months_remaining=0)
