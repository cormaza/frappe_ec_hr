import json
import unittest
from pathlib import Path

try:
	import frappe

	_RING_ERRORS = (ValueError, frappe.ValidationError)
except ImportError:  # pragma: no cover - Ring 1 has no frappe package.
	frappe = None  # type: ignore[assignment]
	_RING_ERRORS = (ValueError,)

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]

from ec_hr.ecuador_hr.doctype.ec_settlement_act.ec_settlement_act import ECSettlementAct


class TestSettlementActJson(UnitTestCase):
	JSON_PATH = (
		Path(__file__).resolve().parent.parent
		/ "ecuador_hr"
		/ "doctype"
		/ "ec_settlement_act"
		/ "ec_settlement_act.json"
	)

	def test_json_is_valid_non_child_doctype(self) -> None:
		definition = json.loads(self.JSON_PATH.read_text())
		self.assertEqual(definition["name"], "EC Settlement Act")
		self.assertEqual(definition["istable"], 0)
		self.assertGreaterEqual(len(definition.get("permissions", [])), 1)
		names = [f["fieldname"] for f in definition["fields"]]
		self.assertEqual(definition["field_order"], names)
		for expected in (
			"employee",
			"cause",
			"termination_date",
			"last_monthly_remuneration",
			"service_years",
			"desahucio_amount",
			"untimely_amount",
			"sut_filing_reference",
		):
			self.assertIn(expected, names)


def _act(**overrides):  # type: ignore[no-untyped-def]
	# __new__ bypasses Document.__init__ so one path serves both rings (the
	# real base requires doctype at construction; the Ring-1 stub takes none).
	act = ECSettlementAct.__new__(ECSettlementAct)
	vars(act).update(
		{
			"cause": "169.2",
			"last_monthly_remuneration": 1000.0,
			"service_years": 4.0,
			"desahucio_amount": 0.0,
			"untimely_amount": 0.0,
		}
	)
	vars(act).update(overrides)
	return act


class TestSettlementComputation(UnitTestCase):
	"""Controller auto-fills award lines; runs in Ring 1 via the stub base."""

	def test_mutual_agreement_fills_bonus_only(self) -> None:
		act = _act()
		act.validate()
		self.assertEqual(act.desahucio_amount, 1000.0)
		self.assertEqual(act.untimely_amount, 0.0)

	def test_untimely_fills_award_only(self) -> None:
		act = _act(cause="untimely", service_years=5.0)
		act.validate()
		self.assertEqual(act.desahucio_amount, 0.0)
		self.assertEqual(act.untimely_amount, 5000.0)

	def test_unknown_cause_fails(self) -> None:
		with self.assertRaises(_RING_ERRORS):
			_act(cause="169.99").validate()

	def test_negative_inputs_fail(self) -> None:
		with self.assertRaises(_RING_ERRORS):
			_act(last_monthly_remuneration=-100.0).validate()
		with self.assertRaises(_RING_ERRORS):
			_act(service_years=-2.0).validate()


@unittest.skipUnless(frappe is not None, "bench-only: needs frappe.get_doc")
class TestSettlementBench(UnitTestCase):
	def test_invalid_cause_raises(self) -> None:
		doc = frappe.get_doc(
			{
				"doctype": "EC Settlement Act",
				"employee": "EMP-00001",
				"cause": "169.99",
				"termination_date": "2026-10-28",
				"last_monthly_remuneration": 1000.0,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.validate()

	def test_valid_act_computes_bonus(self) -> None:
		doc = frappe.get_doc(
			{
				"doctype": "EC Settlement Act",
				"employee": "EMP-00001",
				"cause": "169.9",
				"termination_date": "2026-10-28",
				"last_monthly_remuneration": 1000.0,
				"service_years": 4.0,
			}
		)
		doc.validate()
		self.assertEqual(doc.desahucio_amount, 1000.0)
