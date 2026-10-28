import unittest
from datetime import date

from ec_hr.payroll.period import MONTH_BASE_DAYS, iess_billable_days, month_bounds, worked_fraction

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]


class TestFullMonthInvariant(UnitTestCase):
	"""A fully-worked month bills 30 for every calendar length (2024 leap +
	2025 common), from either boundary."""

	def test_all_month_lengths(self) -> None:
		for year in (2024, 2025):
			for month in range(1, 13):
				first, last = month_bounds(year, month)
				with self.subTest(year=year, month=month):
					self.assertEqual(iess_billable_days(year, month), 30)
					self.assertEqual(iess_billable_days(year, month, hire_date=first), 30)
					self.assertEqual(iess_billable_days(year, month, exit_date=last), 30)
					self.assertEqual(
						iess_billable_days(year, month, hire_date=first, exit_date=last), 30
					)


class TestFebruaryEdges(UnitTestCase):
	"""February carries every scaling edge: 28 vs 29 days and the only exact
	.5 banker's-rounding cases in the calendar."""

	def test_common_february_exact_halves(self) -> None:
		# Hired day 8: 21 of 28 remain -> 30*21/28 = 22.5 -> 22 (even).
		self.assertEqual(iess_billable_days(2026, 2, hire_date=date(2026, 2, 8)), 22)
		# Hired day 22: 7 of 28 remain -> 30*7/28 = 7.5 -> 8 (even).
		self.assertEqual(iess_billable_days(2026, 2, hire_date=date(2026, 2, 22)), 8)

	def test_common_february_last_day(self) -> None:
		# Hired 28th: 1 of 28 -> 30/28 = 1.07 -> 1.
		self.assertEqual(iess_billable_days(2026, 2, hire_date=date(2026, 2, 28)), 1)

	def test_leap_february_edges(self) -> None:
		# Hired 29th: 1 of 29 -> 30/29 = 1.03 -> 1.
		self.assertEqual(iess_billable_days(2024, 2, hire_date=date(2024, 2, 29)), 1)
		# Hired 15th: 15 of 29 -> 30*15/29 = 15.52 -> 16.
		self.assertEqual(iess_billable_days(2024, 2, hire_date=date(2024, 2, 15)), 16)
		# Exit 1st: 1 of 29 -> 1.
		self.assertEqual(iess_billable_days(2024, 2, exit_date=date(2024, 2, 1)), 1)

	def test_february_exit_last_day_is_full(self) -> None:
		self.assertEqual(iess_billable_days(2026, 2, exit_date=date(2026, 2, 28)), 30)
		self.assertEqual(iess_billable_days(2024, 2, exit_date=date(2024, 2, 29)), 30)


class TestRangeConsistency(UnitTestCase):
	"""Inconsistent ranges fail loud instead of silently billing zero."""

	def test_hire_after_exit_fails(self) -> None:
		with self.assertRaises(ValueError):
			iess_billable_days(
				2026, 3, hire_date=date(2026, 3, 20), exit_date=date(2026, 3, 10)
			)

	def test_cross_year_boundary_month_is_full(self) -> None:
		# Hired Dec 2025: January 2026 counts whole (outer-side rule).
		self.assertEqual(iess_billable_days(2026, 1, hire_date=date(2025, 12, 20)), 30)
		self.assertEqual(worked_fraction(2026, 1, hire_date=date(2025, 12, 20)), 1.0)

	def test_billable_never_exceeds_base(self) -> None:
		for year in (2024, 2025):
			for month in range(1, 13):
				first, last = month_bounds(year, month)
				with self.subTest(year=year, month=month):
					for day in (first.day, last.day):
						probe = date(year, month, day)
						self.assertLessEqual(
							iess_billable_days(year, month, hire_date=probe), MONTH_BASE_DAYS
						)
						self.assertLessEqual(
							iess_billable_days(year, month, exit_date=probe), MONTH_BASE_DAYS
						)
