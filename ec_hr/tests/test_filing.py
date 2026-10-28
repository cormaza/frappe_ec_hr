import unittest
from typing import ClassVar

from ec_hr.payroll.accounting import provision_lines
from ec_hr.payroll.payments import matches_layout, register_layout, render_csv, validate_row
from ec_hr.payroll.rdep import build_record, validate_batch

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]

SAMPLE_BANK = "Test Bank Layout"


def _worker(**overrides):  # type: ignore[no-untyped-def]
	record = {
		"id_number": "1710034065",
		"full_name": "Test Worker",
		"gross": 12000.0,
		"taxable": 12000.0,
		"tax_caused": 95.95,
		"withheld": 95.95,
	}
	record.update(overrides)
	return record


class TestRdepRecords(UnitTestCase):
	"""Annual per-worker RDEP/Form-107 dataset: validated dicts + totals.
	XML/XSD serialization pins in bench against the live SRI schema."""

	def test_valid_record_builds(self) -> None:
		record = build_record(**_worker())
		self.assertEqual(record["id_number"], "1710034065")

	def test_missing_key_and_negatives_fail(self) -> None:
		broken = _worker()
		del broken["taxable"]
		with self.assertRaises(ValueError):
			build_record(**broken)
		with self.assertRaises(ValueError):
			build_record(**_worker(gross=-1.0))

	def test_batch_totals(self) -> None:
		totals = validate_batch([_worker(), _worker(gross=6000.0, taxable=6000.0)])
		self.assertEqual(totals["workers"], 2)
		self.assertEqual(totals["gross"], 18000.0)
		self.assertEqual(totals["withheld"], 191.9)


class TestBankLayouts(UnitTestCase):
	"""Layouts are caller-provided specs (no invented bank columns); the
	sample layout below lives in tests only until bench pins real ones."""

	def test_register_render_and_validate(self) -> None:
		register_layout(SAMPLE_BANK, ["id_number", "full_name", "amount"])
		rows = [{"id_number": "1710034065", "full_name": "Test Worker", "amount": 950.0}]
		for row in rows:
			validate_row(row)
		self.assertTrue(matches_layout(rows, SAMPLE_BANK))
		rendered = render_csv(rows, SAMPLE_BANK)
		self.assertEqual(rendered, "id_number,full_name,amount\r\n1710034065,Test Worker,950.0\r\n")

	def test_bad_rows_fail(self) -> None:
		with self.assertRaises(ValueError):
			validate_row({"id_number": "", "amount": 10.0})
		with self.assertRaises(ValueError):
			validate_row({"id_number": "1710034065", "amount": 0.0})
		with self.assertRaises(ValueError):
			render_csv([{"id_number": "x"}], SAMPLE_BANK)


class TestProvisionLines(UnitTestCase):
	"""Double-entry provision stubs: the chart of accounts always arrives as
	an explicit map (it varies per company)."""

	ACCOUNT_MAP: ClassVar[dict[str, dict[str, str]]] = {
		"thirteenth": {"expense": "5101", "liability": "2110"}
	}

	def test_lines_balance(self) -> None:
		lines = provision_lines([{"concept": "thirteenth", "amount": 100.0}], self.ACCOUNT_MAP)
		self.assertEqual(
			lines,
			[
				{"account": "5101", "debit": 100.0, "credit": 0.0},
				{"account": "2110", "debit": 0.0, "credit": 100.0},
			],
		)

	def test_missing_mapping_fails_loud(self) -> None:
		with self.assertRaises(ValueError):
			provision_lines([{"concept": "mystery", "amount": 10.0}], self.ACCOUNT_MAP)
