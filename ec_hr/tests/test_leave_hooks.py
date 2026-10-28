import unittest
from types import SimpleNamespace

from ec_hr.ecuador_hr.leave_application_hooks import CLINICAL_LEAVE_TYPES, validate_leave_application

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


def _doc(**overrides):  # type: ignore[no-untyped-def]
	base = {"leave_type": "Annual Leave", "ec_medical_certificate": None}
	base.update(overrides)
	return SimpleNamespace(**base)


class TestLeaveCertificateHook(UnitTestCase):
	"""Clinical leaves need a certificate; ordinary leaves pass bare."""

	def test_clinical_types_covered(self) -> None:
		self.assertEqual(CLINICAL_LEAVE_TYPES, frozenset({"Sick Leave", "Maternity Leave", "Paternity Leave"}))

	def test_clinical_without_certificate_fails(self) -> None:
		for leave_type in ("Sick Leave", "Maternity Leave", "Paternity Leave"):
			with self.subTest(leave_type=leave_type):
				with self.assertRaises(_RING_ERRORS):
					validate_leave_application(_doc(leave_type=leave_type))

	def test_clinical_with_certificate_passes(self) -> None:
		validate_leave_application(_doc(leave_type="Sick Leave", ec_medical_certificate="/files/cert.pdf"))

	def test_ordinary_leave_passes_bare(self) -> None:
		validate_leave_application(_doc(leave_type="Annual Leave"))


@unittest.skipUnless(frappe is not None, "bench-only: needs frappe.get_doc")
class TestLeaveHookBench(UnitTestCase):
	def test_clinical_without_certificate_raises(self) -> None:
		doc = frappe.get_doc({"doctype": "Leave Application", "leave_type": "Sick Leave"})
		with self.assertRaises(frappe.ValidationError):
			validate_leave_application(doc)
