import unittest

import pytest

frappe = pytest.importorskip("frappe")

try:
	from frappe.tests import IntegrationTestCase
except ImportError:
	IntegrationTestCase = unittest.TestCase


class TestECFamilyCharge(IntegrationTestCase):
	"""Bench-only: EC Family Charge controller validation."""

	def test_invalid_charge_throws(self):
		doc = frappe.get_doc(
			{
				"doctype": "EC Family Charge",
				"relation": "child",
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
				"relation": "child",
				"birthdate": "2015-06-01",
				"accredited_on": "2020-01-01",
			}
		)
		doc.validate()
