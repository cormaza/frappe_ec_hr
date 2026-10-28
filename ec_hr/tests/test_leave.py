import unittest

from ec_hr.payroll.leave import maternity_days, mother_death_transfer, paternity_days, sickness_legs

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]


class TestMaternity(UnitTestCase):
	"""Art. 152: 12 weeks, +10 days on multiple birth."""

	def test_durations(self) -> None:
		self.assertEqual(maternity_days(), 84)
		self.assertEqual(maternity_days(multiple=True), 94)


class TestPaternity(UnitTestCase):
	"""Art. 152 ladder applied by maximum (user decision): 15 base,
	20 multiple/cesarean, 23 premature/special-care, 25 severe/terminal."""

	def test_ladder(self) -> None:
		self.assertEqual(paternity_days(), 15)
		self.assertEqual(paternity_days(multiple=True), 20)
		self.assertEqual(paternity_days(cesarean=True), 20)
		self.assertEqual(paternity_days(premature_or_special=True), 23)
		self.assertEqual(paternity_days(severe_or_terminal=True), 25)

	def test_combined_conditions_take_maximum(self) -> None:
		self.assertEqual(paternity_days(multiple=True, premature_or_special=True), 23)
		self.assertEqual(paternity_days(cesarean=True, severe_or_terminal=True), 25)


class TestSicknessLegs(UnitTestCase):
	"""Days 1-3 at 100% employer, day 4+ on the IESS rate (user decision:
	no employer top-up; rate is an explicit parameter, never assumed)."""

	def test_first_three_days_employer(self) -> None:
		self.assertEqual(sickness_legs(1, 100.0, 75.0), (100.0, 0.0))
		self.assertEqual(sickness_legs(3, 100.0, 75.0), (100.0, 0.0))

	def test_from_day_four_iess(self) -> None:
		self.assertEqual(sickness_legs(4, 100.0, 75.0), (0.0, 75.0))
		self.assertEqual(sickness_legs(30, 100.0, 75.0), (0.0, 75.0))

	def test_day_zero_fails(self) -> None:
		with self.assertRaises(ValueError):
			sickness_legs(0, 100.0, 75.0)


class TestMotherDeathTransfer(UnitTestCase):
	"""Art. 152: the father takes the remaining maternity leave."""

	def test_remainder(self) -> None:
		self.assertEqual(mother_death_transfer(84, 30), 54)
		self.assertEqual(mother_death_transfer(84, 84), 0)

	def test_over_enjoyed_fails(self) -> None:
		with self.assertRaises(ValueError):
			mother_death_transfer(84, 90)
