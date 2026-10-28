import unittest
from datetime import date

from ec_hr.payroll.profit_sharing import distribute
from ec_hr.payroll.reserve import is_eligible, monthly_amount

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]

AS_OF = date(2026, 10, 28)


class TestReserve(UnitTestCase):
	"""Art. 196: one full Art. 95 remuneration per year past the first, paid
	as base/12 monthly (user decision: exact twelfth, not the 8.33% shorthand)."""

	def test_eligibility_gate(self) -> None:
		self.assertTrue(is_eligible(date(2020, 1, 1), AS_OF))
		self.assertTrue(is_eligible(date(2025, 10, 28), AS_OF))
		self.assertFalse(is_eligible(date(2026, 6, 1), AS_OF))

	def test_leap_day_eligibility_edge(self) -> None:
		# Hired leap day: not eligible the day before the first anniversary.
		self.assertFalse(is_eligible(date(2024, 2, 29), date(2025, 2, 28)))
		self.assertTrue(is_eligible(date(2024, 2, 29), date(2025, 3, 1)))

	def test_monthly_twelfth(self) -> None:
		self.assertEqual(monthly_amount(1200.0), 100.0)

	def test_negative_base_fails(self) -> None:
		with self.assertRaises(ValueError):
			monthly_amount(-1200.0)


class TestProfitSharing(UnitTestCase):
	"""Art. 97/97.1: 10% days-weighted, 5% charges-weighted, 24-SBU cap with
	solidarity excess. No day-count convention: weights run over the audited
	totals. No charges at all splits the 5% per capita (user decision)."""

	def test_standard_split(self) -> None:
		result = distribute(15000.0, {"a": 360.0, "b": 180.0}, {"a": 2, "b": 0}, sbu=550.0)
		self.assertEqual(result["shares"], {"a": 1750.0, "b": 500.0})
		self.assertEqual(result["solidarity_excess"], 0.0)

	def test_cap_feeds_solidarity(self) -> None:
		result = distribute(600000.0, {"a": 360.0}, {"a": 1}, sbu=550.0)
		self.assertEqual(result["shares"], {"a": 13200.0})
		self.assertEqual(result["solidarity_excess"], 76800.0)

	def test_no_charges_splits_five_pct_per_capita(self) -> None:
		result = distribute(15000.0, {"a": 360.0, "b": 180.0}, {"a": 0, "b": 0}, sbu=550.0)
		self.assertEqual(result["shares"], {"a": 1375.0, "b": 875.0})

	def test_empty_roster_fails_loud(self) -> None:
		with self.assertRaises(ValueError):
			distribute(15000.0, {}, {}, sbu=550.0)

	def test_zero_pool_splits_nothing(self) -> None:
		result = distribute(0.0, {"a": 360.0}, {"a": 1}, sbu=550.0)
		self.assertEqual(result["shares"], {"a": 0.0})
		self.assertEqual(result["solidarity_excess"], 0.0)

	def test_single_worker_no_charges_takes_all(self) -> None:
		result = distribute(1000.0, {"a": 360.0}, {"a": 0}, sbu=550.0)
		self.assertEqual(result["shares"], {"a": 150.0})

	def test_cap_boundary_keeps_full_share(self) -> None:
		# Gross exactly 24 SBU (13200): no excess skimmed.
		result = distribute(88000.0, {"a": 360.0}, {"a": 1}, sbu=550.0)
		self.assertEqual(result["shares"], {"a": 13200.0})
		self.assertEqual(result["solidarity_excess"], 0.0)

	def test_zero_days_still_share_charges(self) -> None:
		result = distribute(15000.0, {"a": 0.0, "b": 0.0}, {"a": 1, "b": 1}, sbu=550.0)
		self.assertEqual(result["shares"], {"a": 375.0, "b": 375.0})

	def test_negative_inputs_fail(self) -> None:
		with self.assertRaises(ValueError):
			distribute(15000.0, {"a": -5.0}, {"a": 1}, sbu=550.0)
		with self.assertRaises(ValueError):
			distribute(15000.0, {"a": 360.0}, {"a": -1}, sbu=550.0)
