import json
import unittest
from pathlib import Path

from ec_hr.ecuador_hr.custom_fields import get_custom_fields
from ec_hr.payroll.contract import ContractKind

try:
	from frappe.tests import UnitTestCase
except ImportError:  # pragma: no cover
	UnitTestCase = unittest.TestCase  # type: ignore[misc,assignment]


class TestCustomFieldsStructure(UnitTestCase):
	"""Custom-field definitions stay valid without a bench."""

	def test_employee_fields_have_required_keys(self) -> None:
		fields = get_custom_fields()["Employee"]
		self.assertTrue(fields)
		for field in fields:
			with self.subTest(field=field.get("fieldname")):
				self.assertIn("fieldname", field)
				self.assertIn("label", field)
				self.assertIn("fieldtype", field)

	def test_contract_kind_options_match_enum(self) -> None:
		fields = {f["fieldname"]: f for f in get_custom_fields()["Employee"]}
		options = str(fields["ec_contract_kind"]["options"]).split("\n")
		self.assertEqual(sorted(options), sorted(kind.value for kind in ContractKind))

	def test_salary_slip_fields_have_expected_fieldnames(self) -> None:
		fields = get_custom_fields()["Salary Slip"]
		self.assertTrue(fields)
		names = [f["fieldname"] for f in fields]
		for expected in (
			"ec_hourly_rate",
			"ec_overtime_day_min",
			"ec_overtime_night_min",
			"ec_extraordinary_min",
			"ec_night_min",
			"ec_overtime_daily_max_min",
			"ec_overtime_weekly_min",
			"ec_alimony_order",
			"ec_advance_deduction",
		):
			self.assertIn(expected, names)
		for field in fields:
			with self.subTest(field=field.get("fieldname")):
				self.assertIn("fieldname", field)
				self.assertIn("label", field)
				self.assertIn("fieldtype", field)


class TestFamilyChargeDoctypeJson(UnitTestCase):
	"""DocType JSON parses and declares the Art. 97 charge shape."""

	JSON_PATH = (
		Path(__file__).resolve().parent.parent
		/ "ecuador_hr"
		/ "doctype"
		/ "ec_family_charge"
		/ "ec_family_charge.json"
	)

	def test_json_is_valid_child_table(self) -> None:
		definition = json.loads(self.JSON_PATH.read_text())
		self.assertEqual(definition["name"], "EC Family Charge")
		self.assertEqual(definition["istable"], 1)
		names = [f["fieldname"] for f in definition["fields"]]
		for expected in ("relation", "birthdate", "disability_pct", "accredited_on", "ends_on"):
			self.assertIn(expected, names)
