import unittest
from datetime import date

from ec_hr.payroll.period import MONTH_BASE_DAYS, iess_billable_days, month_bounds, worked_fraction

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]


class TestMonthBounds(UnitTestCase):
	def test_bounds_include_leap_day(self) -> None:
		self.assertEqual(month_bounds(2026, 2), (date(2026, 2, 1), date(2026, 2, 28)))
		self.assertEqual(month_bounds(2024, 2), (date(2024, 2, 1), date(2024, 2, 29)))

	def test_invalid_month_raises_value_error(self) -> None:
		with self.assertRaises(ValueError):
			month_bounds(2026, 13)


class TestBillableDays(UnitTestCase):
	"""IESS month operates on a 30-day base (user decision: assume 30 now;
	operational consensus across planilla guides, manual wording still
	to-verify-in-bench). Calendar dates scale onto the 30-day base."""

	def test_full_month_is_always_30(self) -> None:
		self.assertEqual(MONTH_BASE_DAYS, 30)
		self.assertEqual(iess_billable_days(2026, 1), 30)
		self.assertEqual(iess_billable_days(2026, 2), 30)
		self.assertEqual(iess_billable_days(2024, 2), 30)

	def test_hire_mid_month_scales(self) -> None:
		# Jan has 31 days, 16 remaining (16-31): 30*16/31 = 15.48 -> 15.
		self.assertEqual(iess_billable_days(2026, 1, hire_date=date(2026, 1, 16)), 15)
		# Feb 2026 has 28 days, hired day 1: full 30.
		self.assertEqual(iess_billable_days(2026, 2, hire_date=date(2026, 2, 1)), 30)

	def test_exit_mid_month_scales(self) -> None:
		# Mar has 31 days, exit day 10: 30*10/31 = 9.68 -> 10.
		self.assertEqual(iess_billable_days(2026, 3, exit_date=date(2026, 3, 10)), 10)

	def test_leap_day_hire_and_single_day(self) -> None:
		# Feb 2024: hired 29th, 1 of 29 days remain: 30*1/29 = 1.03 -> 1.
		self.assertEqual(iess_billable_days(2024, 2, hire_date=date(2024, 2, 29)), 1)
		# Single day (Jan 15-15): 30*1/31 = 0.97 -> 1.
		self.assertEqual(
			iess_billable_days(2026, 1, hire_date=date(2026, 1, 15), exit_date=date(2026, 1, 15)),
			1,
		)

	def test_absences_equal_to_billable_floor_at_zero(self) -> None:
		# 15 billable (hired Jan 16) minus 15 absences -> 0, never negative.
		self.assertEqual(iess_billable_days(2026, 1, hire_date=date(2026, 1, 16), absence_days=15), 0)

	def test_hire_and_exit_same_month(self) -> None:
		# Mar 10-20 inclusive = 11 days: 30*11/31 = 10.65 -> 11.
		self.assertEqual(
			iess_billable_days(2026, 3, hire_date=date(2026, 3, 10), exit_date=date(2026, 3, 20)),
			11,
		)

	def test_absences_subtract_with_floor_at_zero(self) -> None:
		self.assertEqual(iess_billable_days(2026, 1, absence_days=2), 28)
		self.assertEqual(iess_billable_days(2026, 1, absence_days=40), 0)

	def test_out_of_range_inputs_fail_loud(self) -> None:
		with self.assertRaises(ValueError):
			iess_billable_days(2026, 1, absence_days=-1)
		with self.assertRaises(ValueError):
			iess_billable_days(2026, 1, hire_date=date(2026, 2, 5))
		with self.assertRaises(ValueError):
			iess_billable_days(2026, 3, exit_date=date(2026, 2, 27))

	def test_hire_before_and_exit_after_month_are_full(self) -> None:
		self.assertEqual(iess_billable_days(2026, 3, hire_date=date(2026, 1, 10)), 30)
		self.assertEqual(iess_billable_days(2026, 3, exit_date=date(2026, 5, 1)), 30)


class TestWorkedFraction(UnitTestCase):
	def test_fractions(self) -> None:
		self.assertEqual(worked_fraction(2026, 1), 1.0)
		self.assertEqual(worked_fraction(2026, 1, hire_date=date(2026, 1, 16)), 0.5)
