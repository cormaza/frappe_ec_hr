import unittest

from ec_hr.payroll.remuneration import contribution_base, is_remuneration

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]


class TestIsRemuneration(UnitTestCase):
	"""Art. 95 inclusions (+) and exclusions (-), verbatim from the article."""

	def test_included_kinds(self) -> None:
		for kind in (
			"salary",
			"overtime_day",
			"overtime_night",
			"extraordinary",
			"commission",
			"piecework",
			"profit_share",
			"employer_paid_iess",
			"night_premium",
			"normal_bonus",
		):
			with self.subTest(kind=kind):
				self.assertTrue(is_remuneration(kind))

	def test_excluded_kinds(self) -> None:
		for kind in (
			"thirteenth",
			"fourteenth",
			"reserve_funds_monthly",
			"legal_profit_pct",
			"living_wage_compensation",
			"occasional_per_diem",
			"occasional_subsidy",
			"social_services",
			"pending_components",
		):
			with self.subTest(kind=kind):
				self.assertFalse(is_remuneration(kind))

	def test_unknown_kind_fails_loud(self) -> None:
		with self.assertRaises(ValueError):
			is_remuneration("crypto_bonus")


class TestContributionBase(UnitTestCase):
	def test_base_sums_only_remuneration(self) -> None:
		self.assertEqual(
			contribution_base(
				[
					{"kind": "salary", "amount": 1000.0},
					{"kind": "overtime_day", "amount": 50.0},
					{"kind": "thirteenth", "amount": 83.33},
					{"kind": "occasional_per_diem", "amount": 40.0},
				]
			),
			1050.0,
		)
		self.assertEqual(contribution_base([]), 0.0)

	def test_unknown_kind_propagates(self) -> None:
		with self.assertRaises(ValueError):
			contribution_base([{"kind": "crypto_bonus", "amount": 5.0}])
