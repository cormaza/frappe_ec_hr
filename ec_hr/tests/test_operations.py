import unittest
from datetime import date

from ec_hr.payroll.iess import notice_deadlines, overdue_days, planilla_line
from ec_hr.payroll.loans import carry_arrears, withholding

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]


class TestPlanillaLine(UnitTestCase):
	"""Base prorated by billable days over 30, legs via the 9.45/11.15 seed."""

	def test_full_month(self) -> None:
		self.assertEqual(
			planilla_line(1000.0, 30),
			{"base": 1000.0, "personal": 94.5, "employer": 111.5, "total": 206.0},
		)

	def test_half_month(self) -> None:
		self.assertEqual(
			planilla_line(1000.0, 15),
			{"base": 500.0, "personal": 47.25, "employer": 55.75, "total": 103.0},
		)

	def test_zero_days(self) -> None:
		self.assertEqual(
			planilla_line(1000.0, 0),
			{"base": 0.0, "personal": 0.0, "employer": 0.0, "total": 0.0},
		)

	def test_out_of_range_days_fail(self) -> None:
		with self.assertRaises(ValueError):
			planilla_line(1000.0, 31)
		with self.assertRaises(ValueError):
			planilla_line(1000.0, -1)


class TestNoticeDeadlines(UnitTestCase):
	"""LSS Art. 73: entry within 15 days of hire, exit within 3 of exit."""

	def test_deadlines(self) -> None:
		deadlines = notice_deadlines(date(2026, 10, 1), date(2026, 10, 20))
		self.assertEqual(deadlines, {"entry_by": date(2026, 10, 16), "exit_by": date(2026, 10, 23)})

	def test_no_exit_no_deadline(self) -> None:
		deadlines = notice_deadlines(date(2026, 10, 1), None)
		self.assertIsNone(deadlines["exit_by"])

	def test_overdue_days(self) -> None:
		self.assertEqual(overdue_days(date(2026, 10, 16), date(2026, 10, 20)), 4)
		self.assertEqual(overdue_days(date(2026, 10, 16), date(2026, 10, 16)), 0)
		self.assertEqual(overdue_days(date(2026, 10, 16), date(2026, 10, 10)), 0)


class TestBiessLegs(UnitTestCase):
	"""Payroll only withholds the notified installment and carries arrears."""

	def test_withholding_passthrough(self) -> None:
		self.assertEqual(withholding(150.5), 150.5)
		with self.assertRaises(ValueError):
			withholding(-10.0)

	def test_arrears_carry(self) -> None:
		self.assertEqual(carry_arrears(100.0, 150.0, 150.0), 100.0)
		self.assertEqual(carry_arrears(100.0, 150.0, 0.0), 250.0)
