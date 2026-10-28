import json
import unittest
from itertools import pairwise
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
		options = [o for o in str(fields["ec_contract_kind"]["options"]).split("\n") if o]
		expected = [kind.value.replace("_", " ").title() for kind in ContractKind]
		self.assertEqual(sorted(options), sorted(expected))

	def test_selects_start_blank_and_sections_chain(self) -> None:
		fields = get_custom_fields()
		for doctype, first_anchor in (
			("Employee", "create_user_automatically"),
			("Salary Slip", "gross_pay"),
			("Leave Application", "sb_other_details"),
		):
			chain = fields[doctype]
			self.assertEqual(chain[0]["insert_after"], first_anchor)
			for previous, field in pairwise(chain):
				with self.subTest(doctype=doctype, field=field.get("fieldname")):
					self.assertEqual(field["insert_after"], previous["fieldname"])
		for field in fields["Employee"] + fields["Salary Slip"]:
			if field["fieldtype"] == "Select":
				with self.subTest(field=field.get("fieldname")):
					self.assertTrue(str(field["options"]).startswith("\n"))
		sections = [
			f for f in fields["Employee"] + fields["Salary Slip"] if f["fieldtype"] == "Section Break"
		]
		self.assertEqual(
			{str(f["label"]) for f in sections}, {"Ecuadorian Details", "Ecuadorian Payroll Inputs"}
		)

	def test_phase3_election_and_certificate_fields(self) -> None:
		fields = get_custom_fields()
		employee = {f["fieldname"] for f in fields["Employee"]}
		for expected in ("ec_xiii_accumulated", "ec_xiv_accumulated", "ec_xiv_region"):
			self.assertIn(expected, employee)
		leave = {f["fieldname"] for f in fields["Leave Application"]}
		self.assertIn("ec_medical_certificate", leave)

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
