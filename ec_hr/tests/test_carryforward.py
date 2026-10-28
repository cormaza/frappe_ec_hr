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

from ec_hr.ecuador_hr.carry_hooks import _row_dict, apply_injection, compute_writebacks
from ec_hr.ecuador_hr.doctype.ec_deduction_balance.ec_deduction_balance import (
	ECDeductionBalance,
	normalize_kind,
)


class TestBalanceJson(UnitTestCase):
	JSON_PATH = (
		Path(__file__).resolve().parent.parent
		/ "ecuador_hr"
		/ "doctype"
		/ "ec_deduction_balance"
		/ "ec_deduction_balance.json"
	)

	def test_json_shape(self) -> None:
		definition = json.loads(self.JSON_PATH.read_text(encoding="utf-8"))
		self.assertEqual(definition["name"], "EC Deduction Balance")
		self.assertEqual(definition["istable"], 0)
		self.assertGreaterEqual(len(definition.get("permissions", [])), 1)
		names = [f["fieldname"] for f in definition["fields"]]
		self.assertEqual(definition["field_order"], names)
		for expected in (
			"employee",
			"label",
			"kind",
			"balance",
			"monthly_amount",
			"salary_component",
			"slip_field",
		):
			self.assertIn(expected, names)


def _balance(**overrides):  # type: ignore[no-untyped-def]
	doc = ECDeductionBalance.__new__(ECDeductionBalance)
	vars(doc).update(
		{
			"employee": "HR-EMP-00001",
			"label": "alimony",
			"kind": "Judicial",
			"balance": 100.0,
			"monthly_amount": 300.0,
			"salary_component": "EC Alimony Withholding",
			"slip_field": "ec_alimony_order",
		}
	)
	vars(doc).update(overrides)
	return doc


class TestBalanceValidation(UnitTestCase):
	"""Controller rules run in Ring 1 via the stub base."""

	def test_title_case_kind_normalizes(self) -> None:
		self.assertEqual(normalize_kind("Judicial"), "judicial")
		doc = _balance()
		doc.validate()
		self.assertEqual(doc.kind, "Judicial")

	def test_unknown_kind_fails(self) -> None:
		with self.assertRaises(_RING_ERRORS):
			_balance(kind="Mystery").validate()

	def test_blank_label_fails(self) -> None:
		with self.assertRaises(_RING_ERRORS):
			_balance(label="  ").validate()


class TestCarryOrchestration(UnitTestCase):
	"""Namespace-level orchestration (runs in both rings)."""

	def test_apply_writes_carried_fields(self) -> None:
		class Doc:
			ec_alimony_order = 0.0
			ec_alimony_carried = 0.0
			ec_advance_deduction = 50.0
			ec_advance_carried = 0.0

		doc = Doc()
		apply_injection(
			doc,
			[
				{"slip_field": "ec_alimony_order", "monthly_amount": 300.0, "balance": 100.0},
				{"slip_field": "ec_advance_deduction", "monthly_amount": 0.0, "balance": 25.0},
			],
		)
		# Order inputs untouched; carried fields hold the owed months.
		self.assertEqual(doc.ec_alimony_order, 0.0)
		self.assertEqual(doc.ec_alimony_carried, 400.0)
		self.assertEqual(doc.ec_advance_deduction, 50.0)
		self.assertEqual(doc.ec_advance_carried, 25.0)

	def test_compute_writebacks_maps_components(self) -> None:
		balances = [
			{
				"label": "alimony",
				"monthly_amount": 300.0,
				"balance": 100.0,
				"salary_component": "EC Alimony Withholding",
			},
			{
				"label": "manual",
				"monthly_amount": 50.0,
				"balance": 0.0,
				"salary_component": "",
			},
		]
		rows = [{"salary_component": "EC Alimony Withholding", "amount": 250.0}]
		self.assertEqual(compute_writebacks(balances, rows), {"alimony": 150.0})

	def test_apply_injection_is_idempotent(self) -> None:
		# Assignment (not accumulation): repeated runs land the same owed.
		class Doc:
			ec_alimony_order = 0.0
			ec_alimony_carried = 0.0

		doc = Doc()
		balances = [{"slip_field": "ec_alimony_order", "monthly_amount": 300.0, "balance": 100.0}]
		apply_injection(doc, balances)
		apply_injection(doc, balances)
		self.assertEqual(doc.ec_alimony_carried, 400.0)
		self.assertEqual(doc.ec_alimony_order, 0.0)

	def test_apply_unknown_field_fails(self) -> None:
		class Doc:
			pass

		with self.assertRaises(ValueError):
			apply_injection(Doc(), [{"slip_field": "ec_nope", "monthly_amount": 1.0}])

	def test_row_dict_accepts_document_like_rows(self) -> None:
		# Bench child rows expose as_dict() instead of mapping protocol.
		class Row:
			def as_dict(self):
				return {"salary_component": "EC Alimony Withholding", "amount": 250.0}

		self.assertEqual(
			_row_dict(Row()),  # type: ignore[arg-type]
			{"salary_component": "EC Alimony Withholding", "amount": 250.0},
		)
		self.assertEqual(_row_dict({"a": 1}), {"a": 1})


@unittest.skipUnless(frappe is not None, "bench-only: needs frappe.get_doc")
class TestBalanceBench(UnitTestCase):
	def test_invalid_kind_raises(self) -> None:
		doc = frappe.get_doc(
			{
				"doctype": "EC Deduction Balance",
				"employee": "HR-EMP-00001",
				"label": "alimony",
				"kind": "Mystery",
				"balance": 0.0,
				"monthly_amount": 300.0,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.validate()
