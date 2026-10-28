import unittest
from datetime import date

from ec_hr.payroll.contract import (
	ContractKind,
	TERMINATION_CAUSES,
	ends_with_desahucio_bonus,
	is_provisional,
	probation_end_date,
	requires_visto_bueno,
)

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]


class TestContractKinds(UnitTestCase):
	"""Full 8-type set (user decision); LOAH emergent text still pending."""

	def test_all_kinds_present(self) -> None:
		self.assertEqual(
			{kind.value for kind in ContractKind},
			{
				"indefinite",
				"obra_cierta",
				"eventual",
				"occasional",
				"seasonal",
				"apprenticeship",
				"part_time",
				"special_emergent",
			},
		)

	def test_every_kind_has_termination_map(self) -> None:
		for kind in ContractKind:
			with self.subTest(kind=kind):
				self.assertTrue(TERMINATION_CAUSES[kind])

	def test_indefinite_covers_desahucio_and_obra_covers_completion(self) -> None:
		self.assertIn("169.9", TERMINATION_CAUSES[ContractKind.INDEFINITE])
		self.assertIn("169.3", TERMINATION_CAUSES[ContractKind.OBRA_CIERTA])

	def test_special_emergent_is_provisional(self) -> None:
		self.assertTrue(is_provisional(ContractKind.SPECIAL_EMERGENT))
		self.assertFalse(is_provisional(ContractKind.INDEFINITE))


class TestTerminationConsequences(UnitTestCase):
	"""Bonus/indemnity routing per verified Art. 184/185/621 consequences."""

	def test_mutual_agreement_and_desahucio_carry_bonus(self) -> None:
		self.assertTrue(ends_with_desahucio_bonus("169.2"))
		self.assertTrue(ends_with_desahucio_bonus("169.9"))
		self.assertFalse(ends_with_desahucio_bonus("169.3"))
		self.assertFalse(ends_with_desahucio_bonus("172"))

	def test_employer_and_worker_will_need_visto_bueno(self) -> None:
		self.assertTrue(requires_visto_bueno("172"))
		self.assertTrue(requires_visto_bueno("173"))
		self.assertFalse(requires_visto_bueno("169.2"))

	def test_unknown_cause_fails_loud(self) -> None:
		with self.assertRaises(ValueError):
			ends_with_desahucio_bonus("169.99")
		with self.assertRaises(ValueError):
			requires_visto_bueno("169.99")


class TestProbation(UnitTestCase):
	"""90-day default (MDT-2018-0135 text still to pin in bench)."""

	def test_default_90_days(self) -> None:
		self.assertEqual(probation_end_date(date(2026, 1, 15)), date(2026, 4, 15))

	def test_custom_length(self) -> None:
		self.assertEqual(probation_end_date(date(2026, 1, 15), days=30), date(2026, 2, 14))
