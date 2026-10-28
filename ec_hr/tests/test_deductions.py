import unittest

from ec_hr.payroll.deductions import (
	amortize,
	apply_waterfall,
	check_alimony_floor,
	cona_floor_pct,
)

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]

LEVEL_1_2025 = [{"up_to_sbu": 1.25, "pct": {1: 0.2812, 2: 0.3971, 3: 0.5218}}]


def _deduction(kind: str, label: str, amount: float) -> dict[str, object]:
	return {"kind": kind, "label": label, "monthly_amount": amount}


class TestWaterfall(UnitTestCase):
	"""Judicial > statutory > voluntary; net never drops below the floor."""

	def test_priority_order_applies(self) -> None:
		result = apply_waterfall(
			1000.0,
			[
				_deduction("voluntary", "store", 200.0),
				_deduction("judicial", "alimony", 300.0),
				_deduction("statutory", "iess", 100.0),
			],
		)
		self.assertEqual(result["applied"], {"alimony": 300.0, "iess": 100.0, "store": 200.0})
		self.assertEqual(result["net"], 400.0)
		self.assertEqual(result["shortfall"], {})

	def test_shortfall_carries_unapplied_remainder(self) -> None:
		result = apply_waterfall(500.0, [_deduction("judicial", "alimony", 600.0)])
		self.assertEqual(result["applied"], {"alimony": 500.0})
		self.assertEqual(result["net"], 0.0)
		self.assertEqual(result["shortfall"], {"alimony": 100.0})

	def test_floor_protects_net(self) -> None:
		result = apply_waterfall(500.0, [_deduction("judicial", "alimony", 600.0)], floor=100.0)
		self.assertEqual(result["applied"], {"alimony": 400.0})
		self.assertEqual(result["net"], 100.0)
		self.assertEqual(result["shortfall"], {"alimony": 200.0})

	def test_duplicate_labels_merge_first(self) -> None:
		result = apply_waterfall(
			1000.0,
			[_deduction("voluntary", "store", 200.0), _deduction("judicial", "store", 150.0)],
		)
		# One combined 350 claim at judicial priority.
		self.assertEqual(result["applied"], {"store": 350.0})
		self.assertEqual(result["net"], 650.0)

	def test_unknown_kind_fails_loud(self) -> None:
		with self.assertRaises(ValueError):
			apply_waterfall(1000.0, [_deduction("mystery", "x", 10.0)])


class TestAmortize(UnitTestCase):
	"""French-system schedule on the outstanding balance (no anatocismo)."""

	def test_interest_free_splits_evenly(self) -> None:
		schedule = amortize(1200.0, monthly_rate=0.0, months=12)
		self.assertEqual(len(schedule), 12)
		self.assertTrue(all(row["installment"] == 100.0 for row in schedule))
		self.assertEqual(schedule[-1]["balance"], 0.0)

	def test_interest_bearing_schedule(self) -> None:
		schedule = amortize(1200.0, monthly_rate=0.01, months=12)
		self.assertEqual(len(schedule), 12)
		self.assertEqual(schedule[0]["interest"], 12.0)
		capital = round(sum(row["capital"] for row in schedule), 2)
		self.assertEqual(capital, 1200.0)
		self.assertAlmostEqual(schedule[-1]["balance"], 0.0, places=2)

	def test_single_month_schedule(self) -> None:
		schedule = amortize(1000.0, monthly_rate=0.05, months=1)
		self.assertEqual(len(schedule), 1)
		self.assertEqual(schedule[0]["interest"], 50.0)
		self.assertEqual(schedule[0]["capital"], 1000.0)
		self.assertEqual(schedule[0]["balance"], 0.0)

	def test_invalid_terms_fail(self) -> None:
		with self.assertRaises(ValueError):
			amortize(1200.0, months=0)
		with self.assertRaises(ValueError):
			amortize(-100.0, months=12)
		with self.assertRaises(ValueError):
			amortize(1200.0, monthly_rate=-0.01, months=12)


class TestConaFloor(UnitTestCase):
	"""CONA percentages arrive as a yearly table parameter (2025 level-1
	structure pinned here: MIES/Funcion Judicial PDFs)."""

	def test_level_lookup_and_child_columns(self) -> None:
		self.assertEqual(cona_floor_pct(1.0, 1, LEVEL_1_2025), 0.2812)
		self.assertEqual(cona_floor_pct(1.0, 2, LEVEL_1_2025), 0.3971)
		self.assertEqual(cona_floor_pct(1.0, 5, LEVEL_1_2025), 0.5218)

	def test_two_level_table(self) -> None:
		table = [*LEVEL_1_2025, {"up_to_sbu": 2.0, "pct": {1: 0.25, 2: 0.35, 3: 0.45}}]
		self.assertEqual(cona_floor_pct(1.25, 1, table), 0.2812)
		self.assertEqual(cona_floor_pct(1.26, 1, table), 0.25)
		self.assertEqual(cona_floor_pct(9.99, 3, table), 0.45)

	def test_no_children_fails(self) -> None:
		with self.assertRaises(ValueError):
			cona_floor_pct(1.0, 0, LEVEL_1_2025)

	def test_floor_warning(self) -> None:
		warning = check_alimony_floor(200.0, 1000.0, 1, LEVEL_1_2025, income_sbu=1.0)
		self.assertIsNotNone(warning)
		self.assertIsNone(check_alimony_floor(300.0, 1000.0, 1, LEVEL_1_2025, income_sbu=1.0))

	def test_order_at_floor_is_quiet(self) -> None:
		self.assertIsNone(check_alimony_floor(281.2, 1000.0, 1, LEVEL_1_2025, income_sbu=1.0))
