import unittest

from ec_hr.payroll import fourteenth, thirteenth
from ec_hr.payroll.fourteenth import Region

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]


class TestThirteenth(UnitTestCase):
	"""Art. 111: 1/12 of the Art. 95 YTD base; monthly vs accumulated is only
	payout timing, and exit pay is the same twelfth on the base to date."""

	def test_accrue_twelfth(self) -> None:
		self.assertEqual(thirteenth.accrue(12000.0), 1000.0)

	def test_negative_base_fails(self) -> None:
		with self.assertRaises(ValueError):
			thirteenth.accrue(-100.0)

	def test_monthly_and_accumulated_share_math(self) -> None:
		self.assertEqual(thirteenth.monthly_amount(1200.0), 100.0)
		self.assertEqual(thirteenth.accumulated_due(12000.0), 1000.0)
		self.assertEqual(thirteenth.proportional(6000.0), 500.0)


class TestFourteenth(UnitTestCase):
	"""Art. 113: SBU/12 monthly; accumulation counts elapsed months only —
	no cycle starts assumed (user decision)."""

	def test_monthly_twelfth_of_sbu(self) -> None:
		self.assertEqual(fourteenth.monthly_amount(550.0), 45.83)

	def test_accumulated_by_elapsed_months(self) -> None:
		self.assertEqual(fourteenth.accumulated_due(550.0, 7), 320.83)
		self.assertEqual(fourteenth.accumulated_due(550.0, 0), 0.0)
		self.assertEqual(fourteenth.accumulated_due(550.0, 12), 550.0)

	def test_beyond_cycle_fails(self) -> None:
		with self.assertRaises(ValueError):
			fourteenth.accumulated_due(550.0, 13)
		with self.assertRaises(ValueError):
			fourteenth.monthly_amount(-550.0)

	def test_negative_months_fail(self) -> None:
		with self.assertRaises(ValueError):
			fourteenth.accumulated_due(550.0, -1)

	def test_region_cutoffs(self) -> None:
		self.assertEqual(fourteenth.cutoff(Region.COSTA), (3, 15))
		self.assertEqual(fourteenth.cutoff(Region.SIERRA), (8, 15))
