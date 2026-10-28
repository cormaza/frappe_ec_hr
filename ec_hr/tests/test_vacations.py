import unittest
from datetime import date

from ec_hr.payroll.vacations import accrued_days, liquidation, provision, service_years

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]

ADULT_BORN = date(1990, 1, 1)


class TestServiceYears(UnitTestCase):
	def test_completed_years(self) -> None:
		self.assertEqual(service_years(date(2020, 3, 10), date(2026, 10, 28)), 6)
		self.assertEqual(service_years(date(2026, 10, 28), date(2026, 10, 28)), 0)

	def test_exit_before_hire_fails(self) -> None:
		with self.assertRaises(ValueError):
			service_years(date(2026, 5, 1), date(2026, 1, 1))


class TestAccruedDays(UnitTestCase):
	"""Anniversary-based accrual: annual entitlement (age band + seniority)
	prorated by full elapsed months."""

	def test_full_year_adult(self) -> None:
		days = accrued_days(date(2025, 10, 28), date(2026, 10, 28), ADULT_BORN)
		self.assertEqual(days, 15.0)

	def test_partial_months(self) -> None:
		days = accrued_days(date(2026, 7, 28), date(2026, 10, 28), ADULT_BORN)
		self.assertEqual(days, 3.75)
		# Anniversary day not reached: only 2 full months -> 2.5.
		days = accrued_days(date(2026, 7, 29), date(2026, 10, 28), ADULT_BORN)
		self.assertEqual(days, 2.5)

	def test_youth_rate_applies(self) -> None:
		days = accrued_days(date(2026, 1, 1), date(2026, 7, 1), date(2011, 1, 1))
		self.assertEqual(days, 10.0)


class TestLiquidation(UnitTestCase):
	"""Art. 71: 1/24 of period earnings — one linear function for enjoyment,
	exit proportional, and monthly provision."""

	def test_liquidation_twenty_fourth(self) -> None:
		self.assertEqual(liquidation(24000.0), 1000.0)

	def test_monthly_provision(self) -> None:
		self.assertEqual(provision(2000.0), 83.33)
