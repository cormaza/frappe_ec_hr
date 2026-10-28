import unittest

try:
	import frappe
except ImportError:  # pragma: no cover - Ring 1 has no frappe package.
	frappe = None  # type: ignore[assignment]

try:
	from frappe.tests import IntegrationTestCase, UnitTestCase
except ImportError:
	IntegrationTestCase = unittest.TestCase
	UnitTestCase = unittest.TestCase

from ec_hr.ecuador_hr.doctype.ec_family_charge.ec_family_charge import (
	ECFamilyCharge,
	_normalize_relation,
)


class TestNormalizeRelation(UnitTestCase):
	"""Display values normalize to the lowercase Art. 97 set (runs everywhere)."""

	def test_title_case_normalizes(self) -> None:
		self.assertEqual(_normalize_relation("Child With Disability"), "child_with_disability")
		self.assertEqual(_normalize_relation("Spouse"), "spouse")

	def test_lowercase_passes_through(self) -> None:
		self.assertEqual(_normalize_relation("child"), "child")

	def test_stub_instance_validates_title_case(self) -> None:
		act = ECFamilyCharge.__new__(ECFamilyCharge)
		vars(act).update(
			{
				"relation": "Child",
				"birthdate": "2015-06-01",
				"disability_pct": 0.0,
				"accredited_on": "2020-01-01",
				"ends_on": None,
			}
		)
		act.validate()


@unittest.skipUnless(frappe is not None, "bench-only: needs frappe.get_doc")
class TestECFamilyCharge(IntegrationTestCase):
	"""Bench-only: EC Family Charge controller validation."""

	def test_invalid_charge_throws(self):
		doc = frappe.get_doc(
			{
				"doctype": "EC Family Charge",
				"relation": "Child",
				"birthdate": "2000-01-01",
				"accredited_on": "2020-01-01",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.validate()

	def test_valid_charge_passes(self):
		doc = frappe.get_doc(
			{
				"doctype": "EC Family Charge",
				"relation": "Child",
				"birthdate": "2015-06-01",
				"accredited_on": "2020-01-01",
			}
		)
		doc.validate()
