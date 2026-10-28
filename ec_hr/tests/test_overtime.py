import unittest
from datetime import datetime

from ec_hr.payroll.overtime import (
	check_overtime_caps,
	extraordinary_pay,
	night_overtime_pay,
	night_premium_pay,
	split_day_night,
	supplement_pay,
)

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]


def _dt(day: int, hour: int, minute: int = 0) -> datetime:
	return datetime(2026, 10, day, hour, minute)


class TestSplitDayNight(UnitTestCase):
	"""Night runs 19:00-06:00 (Art. 49); legs split at every boundary."""

	def test_day_shift(self) -> None:
		self.assertEqual(split_day_night(_dt(26, 8), _dt(26, 17)), (540, 0))

	def test_night_shift(self) -> None:
		self.assertEqual(split_day_night(_dt(26, 22), _dt(27, 6)), (0, 480))

	def test_evening_crossing(self) -> None:
		self.assertEqual(split_day_night(_dt(26, 17), _dt(26, 21)), (120, 120))

	def test_early_morning_crossing(self) -> None:
		self.assertEqual(split_day_night(_dt(26, 5), _dt(26, 8)), (120, 60))

	def test_midnight_crossing(self) -> None:
		self.assertEqual(split_day_night(_dt(26, 23), _dt(27, 1)), (0, 120))

	def test_exact_day_and_night_boundaries(self) -> None:
		self.assertEqual(split_day_night(_dt(26, 6), _dt(26, 19)), (780, 0))
		self.assertEqual(split_day_night(_dt(26, 19), _dt(27, 6)), (0, 660))

	def test_two_midnights_split(self) -> None:
		day, night = split_day_night(_dt(26, 8), _dt(28, 8))
		# Day legs: 26th 8-19 (660) + 27th 6-19 (780) + 28th 6-8 (120) = 1560;
		# night legs: 26th 19-24 (300) + 27th 0-6/19-24 (660) + 28th 0-6 (360).
		self.assertEqual((day, night), (1560, 1320))

	def test_partial_minutes_floor(self) -> None:
		from datetime import timedelta

		day, night = split_day_night(_dt(26, 8), _dt(26, 9) + timedelta(seconds=30))
		self.assertEqual((day, night), (60, 0))

	def test_end_before_start_fails(self) -> None:
		with self.assertRaises(ValueError):
			split_day_night(_dt(26, 17), _dt(26, 8))
		with self.assertRaises(ValueError):
			split_day_night(_dt(26, 8), _dt(26, 8))


class TestValuation(UnitTestCase):
	"""Art. 49/55 surcharges on the day-hour base; rate 10/h, 60 minutes."""

	def test_night_premium_25(self) -> None:
		self.assertEqual(night_premium_pay(10.0, 60), 2.5)

	def test_supplements(self) -> None:
		self.assertEqual(supplement_pay(10.0, 60, night=False), 15.0)
		self.assertEqual(supplement_pay(10.0, 60, night=True), 20.0)

	def test_extraordinary_weekend(self) -> None:
		self.assertEqual(extraordinary_pay(10.0, 60), 20.0)

	def test_night_overtime_full_stack_225(self) -> None:
		# User decision: day base + 25% night + 100% supplement = 225%.
		self.assertEqual(night_overtime_pay(10.0, 60), 22.5)

	def test_money_rounding(self) -> None:
		self.assertEqual(supplement_pay(7.77, 90, night=False), 17.48)


class TestCaps(UnitTestCase):
	"""Art. 55.1: at most 4h/day and 12h/week; violations reported, not raised."""

	def test_compliant_week(self) -> None:
		self.assertEqual(check_overtime_caps([240, 240, 240], 720), [])

	def test_daily_breach(self) -> None:
		violations = check_overtime_caps([241], 241)
		self.assertEqual(len(violations), 1)

	def test_weekly_breach(self) -> None:
		violations = check_overtime_caps([240, 240, 240], 721)
		self.assertEqual(len(violations), 1)

	def test_empty_week(self) -> None:
		self.assertEqual(check_overtime_caps([], 0), [])
